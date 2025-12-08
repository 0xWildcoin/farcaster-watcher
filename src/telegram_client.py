import logging
from typing import Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import BOT_TOKEN, CHAT_ID

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    before_sleep=lambda retry_state: logger.warning(
        "Retry %s for Telegram API, error: %s",
        retry_state.attempt_number,
        retry_state.outcome.exception()
    )
)
def send_telegram_message(text: str, parse_mode: str = "HTML") -> bool:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")
    if not CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID is not set.")
    
    if not text or not text.strip():
        logger.warning("Attempted to send empty message")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
        "parse_mode": parse_mode,
        "disable_notification": False,
    }
    
    try:
        logger.debug("Sending message to Telegram (length: %d chars)", len(text))
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        
        response_data = resp.json()
        if response_data.get("ok"):
            logger.debug("Message sent successfully to Telegram")
            return True
        else:
            logger.error("Telegram API returned error: %s", response_data.get("description"))
            return False
            
    except requests.Timeout:
        logger.error("Timeout while sending message to Telegram")
        return False
    except requests.ConnectionError:
        logger.error("Connection error while sending message to Telegram")
        return False
    except requests.HTTPError as e:
        status_code = e.response.status_code if e.response else "unknown"
        logger.error("HTTP error %s from Telegram: %s", status_code, str(e))
        
        # Логируем тело ответа для отладки
        if e.response:
            try:
                error_body = e.response.json()
                logger.debug("Telegram error response: %s", error_body)
            except:
                pass
        return False
    except Exception as e:
        logger.error("Unexpected error sending to Telegram: %s", e)
        return False

def send_telegram_message_safe(text: str, parse_mode: str = "HTML") -> None:
    try:
        send_telegram_message(text, parse_mode)
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)