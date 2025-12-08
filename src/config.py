import os
import sys
import logging
from dotenv import load_dotenv

# Настраиваем логирование раньше всего
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Конфигурация API
NEYNAR_URL = "https://api.neynar.com/v2/farcaster/feed/user/casts"
NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY", "").strip()

# Конфигурация Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Параметры приложения
try:
    POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "5"))
except ValueError:
    logger.warning("Invalid POLL_INTERVAL_SEC, using default: 5")
    POLL_INTERVAL_SEC = 5

try:
    LAST_N = int(os.getenv("LAST_N_CASTS", "2"))
except ValueError:
    logger.warning("Invalid LAST_N_CASTS, using default: 2")
    LAST_N = 2

SEEN_FILE = os.getenv("SEEN_FILE", "data/seen_casts.json")

def validate_config() -> None:
    errors = []
    
    if not NEYNAR_API_KEY:
        errors.append("NEYNAR_API_KEY is not set or empty")
    
    if not BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set or empty")
    
    if not CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID is not set or empty")
    
    if POLL_INTERVAL_SEC < 1:
        errors.append(f"POLL_INTERVAL_SEC must be >= 1, got {POLL_INTERVAL_SEC}")
    
    if LAST_N < 1 or LAST_N > 100:
        errors.append(f"LAST_N_CASTS must be between 1 and 100, got {LAST_N}")
    
    if errors:
        logger.error("Configuration errors found:")
        for error in errors:
            logger.error("  - %s", error)
        logger.error("\nPlease check your .env file or environment variables.")
        sys.exit(1)