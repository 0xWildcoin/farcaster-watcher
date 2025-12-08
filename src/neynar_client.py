import logging
from typing import Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import NEYNAR_API_KEY, NEYNAR_URL

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    before_sleep=lambda retry_state: logger.warning(
        "Retry %s for Neynar API, error: %s",
        retry_state.attempt_number,
        retry_state.outcome.exception()
    )
)
def fetch_latest_casts(fid: int, limit: int = 3) -> List[Dict]:
    if not NEYNAR_API_KEY:
        raise RuntimeError("NEYNAR_API_KEY is not set.")
    
    if limit < 1 or limit > 100:
        logger.warning("Limit %d out of bounds, using default: 3", limit)
        limit = 3
    
    headers = {
        "accept": "application/json",
        "x-api-key": NEYNAR_API_KEY,
    }
    params = {
        "fid": fid, 
        "limit": limit,
        "cursor": None  # Можно добавить для пагинации
    }
    
    try:
        logger.debug("Fetching %d casts for FID=%d", limit, fid)
        resp = requests.get(
            NEYNAR_URL, 
            headers=headers, 
            params=params, 
            timeout=15
        )
        resp.raise_for_status()
        
        data = resp.json()
        casts = data.get("casts", [])
        
        if not isinstance(casts, list):
            logger.warning("'casts' field is not a list in response.")
            return []
        
        logger.debug("Received %d casts for FID=%d", len(casts), fid)
        return casts
        
    except requests.Timeout:
        logger.error("Timeout while fetching casts for FID=%d", fid)
        raise
    except requests.ConnectionError:
        logger.error("Connection error while fetching casts for FID=%d", fid)
        raise
    except requests.HTTPError as e:
        logger.error("HTTP error %s for FID=%d: %s", 
                    e.response.status_code if e.response else "unknown", 
                    fid, str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error fetching casts for FID=%d: %s", fid, e)
        raise