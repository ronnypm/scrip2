"""Config loader for scraper with environment variable support."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .schema import validate_config

# Load .env file if exists (for local development)
load_dotenv()


DEFAULT_CONFIG = {
    "scraper": {
        "pages": 5,
        "max_retries": 3,
        "timeout": 30,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "output": {
        "directory": "./output",
        "filename_prefix": "buscalibre"
    },
    "scheduler": {
        "enabled": False,
        "hour": 9,
        "minute": 0
    }
}


def get_config_path() -> Path:
    """Get the config file path."""
    # Check environment variable first
    env_path = os.environ.get("SCRAPER_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    
    # Default: config.yaml in project root
    return Path(__file__).parent.parent / "config.yaml"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file or environment variables.
    
    Priority: env vars > config.yaml > defaults
    """
    if config_path is None:
        config_path = get_config_path()
    
    # Try to load from config.yaml if exists
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # Override with environment variables (for Railway)
    config = _merge_env_vars(config)
    
    # Merge with defaults
    config = merge_defaults(config, DEFAULT_CONFIG)
    
    # Validate
    validate_config(config)
    
    return config


def _merge_env_vars(config: Dict) -> Dict:
    """Merge environment variables into config."""
    # Telegram
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        config.setdefault("telegram", {})["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    if os.getenv("TELEGRAM_CHAT_ID"):
        config.setdefault("telegram", {})["chat_id"] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Gmail
    if os.getenv("GMAIL_EMAIL"):
        config.setdefault("gmail", {})["email"] = os.getenv("GMAIL_EMAIL")
    if os.getenv("GMAIL_APP_PASSWORD"):
        config.setdefault("gmail", {})["app_password"] = os.getenv("GMAIL_APP_PASSWORD")
    if os.getenv("GMAIL_TO"):
        config.setdefault("gmail", {})["to"] = os.getenv("GMAIL_TO")
    
    # Scraper config
    if os.getenv("SCRAPER_PAGES"):
        config.setdefault("scraper", {})["pages"] = int(os.getenv("SCRAPER_PAGES"))
    if os.getenv("SCRAPER_BASE_URL"):
        config.setdefault("scraper", {})["base_url"] = os.getenv("SCRAPER_BASE_URL")
    if os.getenv("SCRAPER_TIMEOUT"):
        config.setdefault("scraper", {})["timeout"] = int(os.getenv("SCRAPER_TIMEOUT"))
    
    return config


def merge_defaults(config: Dict, defaults: Dict) -> Dict:
    """Merge config with default values."""
    result = defaults.copy()
    
    for key, value in config.items():
        if isinstance(value, dict) and key in result:
            result[key] = merge_defaults(value, result[key])
        else:
            result[key] = value
    
    return result


def load_required_env_vars(config: Dict) -> None:
    """Check that required configuration values are set."""
    missing = []
    
    # Check telegram config
    if not config.get("telegram", {}).get("bot_token") or \
       config["telegram"]["bot_token"] == "TU_BOT_TOKEN_AQUI":
        missing.append("telegram.bot_token")
    
    if not config.get("telegram", {}).get("chat_id") or \
       config["telegram"]["chat_id"] == "TU_CHAT_ID_AQUI":
        missing.append("telegram.chat_id")
    
    if missing:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}\n"
            f"Please set environment variables or edit config.yaml."
        )