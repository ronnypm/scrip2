"""Config schema validation."""
from typing import Dict, Any, List


REQUIRED_FIELDS = [
    "telegram.bot_token",
    "telegram.chat_id",
    "scraper.base_url"
]


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure and required fields.
    
    Args:
        config: Configuration dictionary to validate.
    
    Raises:
        ValueError: If validation fails.
    """
    errors = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if not _get_nested(config, field):
            errors.append(f"Missing required field: {field}")
    
    # Validate types
    if "scraper" in config:
        scraper = config["scraper"]
        
        if "pages" in scraper:
            if not isinstance(scraper["pages"], int) or scraper["pages"] < 1:
                errors.append("scraper.pages must be a positive integer")
        
        if "max_retries" in scraper:
            if not isinstance(scraper["max_retries"], int) or scraper["max_retries"] < 0:
                errors.append("scraper.max_retries must be a non-negative integer")
        
        if "timeout" in scraper:
            if not isinstance(scraper["timeout"], (int, float)) or scraper["timeout"] <= 0:
                errors.append("scraper.timeout must be a positive number")
    
    if "scheduler" in config:
        scheduler = config["scheduler"]
        
        if "enabled" in scheduler and not isinstance(scheduler["enabled"], bool):
            errors.append("scheduler.enabled must be a boolean")
        
        if "hour" in scheduler:
            if not isinstance(scheduler["hour"], int) or not 0 <= scheduler["hour"] <= 23:
                errors.append("scheduler.hour must be between 0 and 23")
        
        if "minute" in scheduler:
            if not isinstance(scheduler["minute"], int) or not 0 <= scheduler["minute"] <= 59:
                errors.append("scheduler.minute must be between 0 and 59")
    
    if errors:
        raise ValueError("\n".join(errors))


def _get_nested(data: Dict, path: str) -> Any:
    """Get nested dictionary value using dot notation."""
    keys = path.split(".")
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value