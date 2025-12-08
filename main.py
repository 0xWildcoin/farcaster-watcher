import logging
import signal
import sys
import time
from typing import Dict, List, Set
import requests

from src.config import (
    NEYNAR_API_KEY, BOT_TOKEN, CHAT_ID, 
    POLL_INTERVAL_SEC, LAST_N, SEEN_FILE,
    validate_config
)
from src.storage import load_seen, save_seen
from src.neynar_client import fetch_latest_casts
from src.telegram_client import send_telegram_message_safe

# Настройка логирования с файлом
log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"

# Создаем директорию для логов
import os
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler("logs/watcher.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Глобальная переменная для graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame) -> None:
    """
    Обработчик сигналов для graceful shutdown.
    """
    global shutdown_requested
    logger.info("Received shutdown signal (SIGINT/SIGTERM)")
    shutdown_requested = True

def format_cast(cast: Dict) -> str:
    author = (cast.get("author") or {}).get("username") or "unknown"
    text = (cast.get("text") or "").strip()
    
    # Убираем лишние переносы, но сохраняем смысл
    text_singleline = " ".join(text.splitlines())
    if len(text_singleline) > 300:
        text_singleline = text_singleline[:297] + "..."
    
    cast_hash = cast.get("hash") or ""
    link = f"https://warpcast.com/{author}/{cast_hash}"
    
    # Можем добавить дополнительные данные
    timestamp = cast.get("timestamp")
    date_str = ""
    if timestamp:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    if date_str:
        return f"👤 <b>@{author}</b> ({date_str})\n📝 {text_singleline}\n🔗 {link}"
    else:
        return f"👤 <b>@{author}</b>\n📝 {text_singleline}\n🔗 {link}"

def print_banner(fid: int) -> None:
    banner = f"""
============================================================
                   Farcaster Watcher 👀
============================================================
Watching FID : {fid}
Interval     : {POLL_INTERVAL_SEC} sec
Last N casts : {LAST_N}
Output       : Telegram chat {CHAT_ID}
Log file     : logs/watcher.log
Data file    : {SEEN_FILE}
------------------------------------------------------------
            Press Ctrl+C to stop gracefully 🛑
============================================================
"""
    print(banner)

def initialize_seen_set(fid: int) -> Set[str]:
    seen: Set[str] = load_seen(SEEN_FILE)
    
    if not seen:
        try:
            logger.info("Initializing seen set with existing casts...")
            init_casts = fetch_latest_casts(fid, LAST_N)
            
            for c in init_casts:
                h = c.get("hash")
                if h:
                    seen.add(h)
            
            save_seen(seen, SEEN_FILE)
            logger.info("Marked %d existing casts as seen.", len(seen))
            
        except Exception as e:
            logger.warning("Initialization error: %s. Starting with empty seen set.", e)
    
    return seen

def process_new_casts(fid: int, seen: Set[str]) -> Set[str]:
    try:
        casts = fetch_latest_casts(fid, LAST_N)
        new_casts: List[Dict] = []
        
        for c in casts:
            h = c.get("hash")
            if not h:
                continue
            if h not in seen:
                new_casts.append(c)
                seen.add(h)
        
        if new_casts:
            logger.info("Found %d new casts for FID=%d", len(new_casts), fid)
            
            # Отправляем в обратном порядке (старые -> новые)
            for c in reversed(new_casts):
                try:
                    formatted = format_cast(c)
                    send_telegram_message_safe(formatted)
                    logger.debug("Sent cast: %s", c.get("hash", "unknown"))
                    
                    # Небольшая пауза между сообщениями
                    time.sleep(0.5)
                    
                except Exception as te:
                    logger.error("Failed sending cast to Telegram: %s", te)
            
            # Сохраняем состояние
            save_seen(seen, SEEN_FILE)
            
        else:
            logger.debug("No new casts for FID=%d", fid)
            
    except requests.HTTPError as he:
        body = getattr(he.response, "text", "")[:200] if he.response else ""
        logger.warning("Neynar HTTP error: %s | body: %s", he, body)
        time.sleep(5)
    except Exception as e:
        logger.error("Error processing casts: %s", e)
        time.sleep(3)
    
    return seen

def main() -> None:
    """
    Основная функция приложения.
    """
    global shutdown_requested  # Добавлено: объявляем глобальную переменную
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Валидация конфигурации
    validate_config()
    
    # Получаем FID от пользователя
    fid = None
    while fid is None and not shutdown_requested:
        try:
            fid_input = input("Enter FID to watch (or 'q' to quit): ").strip()
            
            if fid_input.lower() == 'q':
                logger.info("Exiting by user request")
                return
                
            fid = int(fid_input)
            if fid <= 0:
                print("FID must be a positive number.")
                fid = None
                
        except ValueError:
            print("Invalid FID, numeric expected.")
        except KeyboardInterrupt:
            logger.info("Exiting by user request")
            return
    
    # Инициализация
    seen = initialize_seen_set(fid)
    print_banner(fid)
    
    logger.info("Started watching FID=%s", fid)
    
    # Основной цикл
    while not shutdown_requested:
        try:
            seen = process_new_casts(fid, seen)
            
            # Проверяем shutdown между итерациями
            if shutdown_requested:
                break
                
            # Sleep с проверкой shutdown
            for _ in range(POLL_INTERVAL_SEC * 2):  # Проверяем каждые 0.5 сек
                if shutdown_requested:
                    break
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            shutdown_requested = True
        except Exception as e:
            logger.error("Unexpected error in main loop: %s", e)
            time.sleep(3)
    
    # Graceful shutdown
    logger.info("Shutting down gracefully...")
    save_seen(seen, SEEN_FILE)
    logger.info("Saved %d casts to %s", len(seen), SEEN_FILE)
    logger.info("Farcaster Watcher stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical("Unhandled exception: %s", e, exc_info=True)
        sys.exit(1)