import json
import logging
import os
import tempfile
from typing import Set
from src.config import SEEN_FILE

logger = logging.getLogger(__name__)

def load_seen(path: str = SEEN_FILE) -> Set[str]:
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return set(str(x) for x in data)
        
        logger.warning("Unexpected format in %s, list expected.", path)
        return set()
        
    except FileNotFoundError:
        logger.info("File %s not found, starting with empty seen set.", path)
        return set()
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in %s: %s", path, e)
        return set()
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
        return set()

def save_seen(seen: Set[str], path: str = SEEN_FILE) -> None:
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Создаем временный файл для атомарной записи
        with tempfile.NamedTemporaryFile(
            mode='w', 
            encoding='utf-8', 
            dir=os.path.dirname(path), 
            delete=False,
            suffix='.tmp'
        ) as tmp:
            json.dump(sorted(list(seen)), tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name
        
        # Атомарно заменяем старый файл
        os.replace(tmp_path, path)
        logger.debug("Successfully saved %d casts to %s", len(seen), path)
        
    except PermissionError as e:
        logger.error("Permission denied when saving to %s: %s", path, e)
    except Exception as e:
        logger.error("Failed to save %s: %s", path, e)