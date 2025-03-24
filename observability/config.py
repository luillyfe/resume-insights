from typing import Dict, Any
import os
import logging

# Default observability configuration
DEFAULT_OBSERVABILITY_CONFIG = {
    "logging": {
        "level": os.environ.get("LOG_LEVEL", "INFO"),
        "format": "json",
        "output": ["console"],
        "file_path": os.environ.get("LOG_FILE_PATH", "logs/resume_insights.log")
    }
}

# Global observability configuration
OBSERVABILITY_CONFIG: Dict[str, Any] = DEFAULT_OBSERVABILITY_CONFIG.copy()


def configure_observability(config: Dict[str, Any]) -> None:
    """Configure observability settings.
    
    Args:
        config: Custom configuration to override defaults
    """
    global OBSERVABILITY_CONFIG
    
    if config:
        # Deep merge configuration
        for section, settings in config.items():
            if section in OBSERVABILITY_CONFIG:
                OBSERVABILITY_CONFIG[section].update(settings)
            else:
                OBSERVABILITY_CONFIG[section] = settings
                
    # Configure logging based on settings
    log_level = OBSERVABILITY_CONFIG["logging"]["level"]
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Configure file logging if enabled
    if "file" in OBSERVABILITY_CONFIG["logging"]["output"]:
        file_path = OBSERVABILITY_CONFIG["logging"]["file_path"]
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(getattr(logging, log_level))
        logging.getLogger().addHandler(file_handler)