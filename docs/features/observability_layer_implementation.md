# Observability Layer Phase 1: Core Logging Infrastructure

## Overview

This document outlines the implementation plan for adding an observability layer to the Resume Insights application, with a primary focus on core logging infrastructure. The observability layer will enhance the application's reliability, maintainability, and performance by providing structured logging capabilities across all components.

## Goals

- Implement structured logging across all application components
- Provide consistent logging patterns for error handling and operation tracking
- Enable configurable log levels for different environments
- Maintain low overhead on application performance

## Implementation Strategy

### Phase 1: Core Logging Infrastructure

#### 1. Create Observability Package

We will create a new package structure within the application:

```
observability/
    __init__.py
    config.py         # Observability configuration
    logging.py        # Structured logging utilities
```

#### 2. Implement Structured JSON Logging

The `logging.py` module will provide a wrapper around Python's built-in logging module with enhanced functionality:

```python
# Example implementation of logging.py
import json
import logging
import datetime
import traceback
from typing import Any, Dict, Optional

class Logger:
    """Wrapper around Python's logging module with structured JSON logging."""
    
    def __init__(self, name: str, level: str = "INFO"):
        """Initialize logger with name and level.
        
        Args:
            name: The name of the logger, typically the module name
            level: The logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        self.name = name
        
        # Add handlers if not already configured
        if not self.logger.handlers:
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
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
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
        log_context = context or {}
        
        if error:
            log_context["error"] = {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
            
        self.logger.error(self._format_log("ERROR", message, log_context))
```

#### 3. Implement Configuration Management

The `config.py` module will extend the existing configuration system to include observability settings:

```python
# Example implementation of config.py
from typing import Dict, Any
import os

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
OBSERVABILITY_CONFIG: Dict[str, Any] = DEFAULT_OBSERVABILITY_CONFIG

def configure_observability(config: Dict[str, Any] = None) -> None:
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
    import logging
    log_level = OBSERVABILITY_CONFIG["logging"]["level"]
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Configure file logging if enabled
    if "file" in OBSERVABILITY_CONFIG["logging"]["output"]:
        file_path = OBSERVABILITY_CONFIG["logging"]["file_path"]
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(getattr(logging, log_level))
        logging.getLogger().addHandler(file_handler)
```

#### 4. Integration with Core Components

We will integrate the logging framework into the core components of the application, starting with the `ResumeInsights` class in `core.py`:

```python
# Example integration in core.py
from resume_insights.observability.logging import Logger

class ResumeInsights:
    """Main class for extracting insights from resumes."""
    
    def __init__(self, ...):
        # Initialize logger
        self.logger = Logger("ResumeInsights")
        self.logger.info("Initializing ResumeInsights")
        
        # Existing initialization code...
        
    def extract_candidate_data(self) -> Candidate:
        """Extracts candidate data from the resume."""
        self.logger.info("Extracting candidate data from resume")
        
        try:
            # Extract work history first to use for skill analysis
            self.logger.debug("Extracting work history")
            work_history = self.work_history_analyzer.extract_work_history()

            # Extract resume text
            self.logger.debug("Extracting resume text")
            resume_text = self.work_history_analyzer.extract_resume_text()

            # Extract detailed skills
            self.logger.debug("Extracting skills with details")
            skills_with_details = self.skill_analyzer.extract_skills_with_details(
                resume_text, work_history
            )

            # Parse candidate data from the resume
            self.logger.debug("Parsing candidate data")
            candidate = self._parse_candidate_data()

            # Update the candidate with detailed skills
            candidate.skills = skills_with_details
            
            self.logger.info("Successfully extracted candidate data", {
                "skills_count": len(skills_with_details) if skills_with_details else 0
            })

            return candidate
        except Exception as e:
            self.logger.error("Failed to extract candidate data", e)
            raise Exception(f"Failed to extract candidate data: {str(e)}")
```

Similar integration will be done for other core components:
- `SkillAnalyzer`
- `WorkHistoryAnalyzer`
- `JobMatcher`

#### 5. Integration with Application Entry Point

We will also integrate logging into the Streamlit application entry point in `app.py`:

```python
# Example integration in app.py
from resume_insights.observability.logging import Logger
from resume_insights.observability.config import configure_observability

# Initialize observability
configure_observability()
logger = Logger("app")

def main():
    st.set_page_config(page_title="Resume Insights", page_icon="📄")
    logger.info("Application started")

    # Existing code...
    
    if uploaded_file is not None:
        if st.button("Get Insights"):
            logger.info("Processing resume", {"filename": uploaded_file.name})
            with st.spinner("Parsing resume... This may take a moment."):
                try:
                    # Temporary file handling
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_file_path = temp_file.name

                    # Extract the candidate data from the resume
                    logger.debug("Creating ResumeInsights instance")
                    st.session_state.resumeInsights = create_resume_insights(temp_file_path)
                    
                    logger.debug("Extracting candidate data")
                    st.session_state.insights = (
                        st.session_state.resumeInsights.extract_candidate_data()
                    )
                    
                    logger.info("Successfully processed resume")

                except Exception as e:
                    logger.error("Failed to extract insights", e)
                    st.error(f"Failed to extract insights: {str(e)}")
```

## Testing Strategy

1. **Unit Tests**: Create unit tests for the Logger class to ensure proper formatting and behavior
2. **Integration Tests**: Test the integration of logging in core components
3. **Manual Testing**: Verify log output in different scenarios (success, error, etc.)

## Dependencies

The observability layer will use the following dependencies:
- Python's built-in `logging` module
- Python's built-in `json` module

No additional external dependencies are required for the core logging infrastructure.

## Performance Considerations

- JSON formatting adds minimal overhead to logging operations
- Log levels will be used to control verbosity in different environments
- Debug logging will be disabled in production environments by default

## Future Enhancements

While this implementation focuses on core logging infrastructure, future enhancements could include:

1. **Metrics Collection**: Add performance metrics for critical operations
2. **Distributed Tracing**: Implement request flow tracking
3. **Log Aggregation**: Integration with external log aggregation services
4. **Alerting**: Notification system for error conditions

## Conclusion

The proposed observability layer implementation provides a solid foundation for monitoring and debugging the Resume Insights application. By focusing on core logging infrastructure, we can gain valuable insights into application behavior without adding significant complexity or overhead.