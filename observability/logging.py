import json
import logging
import datetime
import traceback
from typing import Any, Dict, Optional


class Logger:
    """Wrapper around Python's logging module with structured JSON logging."""
    
    def __init__(self, name: str, level: str = ""):
        """Initialize logger with name and level.
        
        Args:
            name: The name of the logger, typically the module name
            level: The logging level (DEBUG, INFO, WARNING, ERROR), if None, uses the configured level
        """
        self.logger = logging.getLogger(name)
        
        # Set level from parameter or use the configured level
        if level:
            self.logger.setLevel(getattr(logging, level))
            
        self.name = name
        
        # Add handlers if not already configured
        if not self.logger.handlers and not logging.getLogger().handlers:
            # Console handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _format_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Format log message as JSON.
        
        Args:
            level: Log level
            message: Log message
            context: Additional context data
            
        Returns:
            JSON formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
            "level": level,
            "service": "resume_insights",
            "component": self.name,
            "message": message
        }
        
        if context:
            log_data["context"] = context
            
        return json.dumps(log_data)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message.
        
        Args:
            message: Log message
            context: Additional context data
        """
        self.logger.debug(self._format_log("DEBUG", message, context))
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message.
        
        Args:
            message: Log message
            context: Additional context data
        """
        self.logger.info(self._format_log("INFO", message, context))
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message.
        
        Args:
            message: Log message
            context: Additional context data
        """
        self.logger.warning(self._format_log("WARNING", message, context))
    
    def error(self, message: str, error: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error message with optional exception details.
        
        Args:
            message: Log message
            error: Exception object
            context: Additional context data
        """
        log_context = context.copy() if context else {}
        
        if error:
            log_context["error"] = {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
            
        self.logger.error(self._format_log("ERROR", message, log_context))