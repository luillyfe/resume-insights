# Metrics Collection Extension Plan

## Overview

This document outlines the implementation plan for extending the Resume Insights observability module with metrics collection capabilities. Building upon the existing logging infrastructure, this extension will enable performance monitoring, timing of critical operations, and exporting metrics to a backend system for analysis.

## Goals

- Implement a metrics collector class for tracking application performance metrics
- Add timing decorators to measure execution time of performance-critical methods
- Set up metrics export to a configurable backend system
- Maintain low overhead on application performance

## Implementation Strategy

### 1. Extend Observability Package Structure

We will extend the existing observability package with new modules:

```
observability/
    __init__.py
    config.py         # Updated with metrics configuration
    logging.py        # Existing structured logging utilities
    metrics.py        # New metrics collection utilities
    exporters/        # New directory for metrics exporters
        __init__.py
        console.py    # Console metrics exporter
        prometheus.py # Prometheus metrics exporter (optional)
```

### 2. Implement Metrics Collector Class

The `metrics.py` module will provide a `MetricsCollector` class for tracking various types of metrics:

```python
# Example implementation of metrics.py
import time
import functools
from typing import Any, Dict, List, Optional, Callable, Type, Union, TypeVar
from observability.config import OBSERVABILITY_CONFIG
from observability.logging import Logger

# Type variables for decorator
F = TypeVar('F', bound=Callable[..., Any])

class MetricsCollector:
    """Collector for application metrics."""
    
    def __init__(self, name: str):
        """Initialize metrics collector with component name.
        
        Args:
            name: The name of the component being measured
        """
        self.name = name
        self.logger = Logger(f"{name}.metrics")
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self._exporters = []
        
        # Initialize exporters based on configuration
        self._setup_exporters()
    
    def _setup_exporters(self) -> None:
        """Set up metrics exporters based on configuration."""
        if "metrics" not in OBSERVABILITY_CONFIG:
            return
            
        exporters_config = OBSERVABILITY_CONFIG.get("metrics", {}).get("exporters", [])
        
        for exporter_name in exporters_config:
            if exporter_name == "console":
                from observability.exporters.console import ConsoleExporter
                self._exporters.append(ConsoleExporter())
            elif exporter_name == "prometheus" and "prometheus" in OBSERVABILITY_CONFIG.get("metrics", {}):
                from observability.exporters.prometheus import PrometheusExporter
                prometheus_config = OBSERVABILITY_CONFIG["metrics"]["prometheus"]
                self._exporters.append(PrometheusExporter(prometheus_config))
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            tags: Optional tags for the metric
        """
        if name not in self.metrics:
            self.metrics[name] = {"type": "counter", "value": 0, "tags": tags or {}}
        
        self.metrics[name]["value"] += value
        self._export_metric(name, self.metrics[name])
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric.
        
        Args:
            name: Metric name
            value: Current value
            tags: Optional tags for the metric
        """
        self.metrics[name] = {"type": "gauge", "value": value, "tags": tags or {}}
        self._export_metric(name, self.metrics[name])
    
    def record_timing(self, name: str, value_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric in milliseconds.
        
        Args:
            name: Metric name
            value_ms: Timing value in milliseconds
            tags: Optional tags for the metric
        """
        if name not in self.metrics:
            self.metrics[name] = {
                "type": "timing", 
                "count": 0, 
                "sum": 0.0, 
                "min": float('inf'),
                "max": 0.0,
                "tags": tags or {}
            }
        
        metric = self.metrics[name]
        metric["count"] += 1
        metric["sum"] += value_ms
        metric["min"] = min(metric["min"], value_ms)
        metric["max"] = max(metric["max"], value_ms)
        
        self._export_metric(name, metric)
    
    def _export_metric(self, name: str, metric: Dict[str, Any]) -> None:
        """Export a metric to all configured exporters.
        
        Args:
            name: Metric name
            metric: Metric data
        """
        for exporter in self._exporters:
            try:
                exporter.export(self.name, name, metric)
            except Exception as e:
                self.logger.error(f"Failed to export metric {name}", error=e)

# Decorator for timing functions
def timed(metric_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None) -> Callable[[F], F]:
    """Decorator to time function execution and record as a metric.
    
    Args:
        metric_name: Optional custom metric name (defaults to function name)
        tags: Optional tags for the metric
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get component name from first arg if it's a method (self)
            component = args[0].__class__.__name__ if args and hasattr(args[0], '__class__') else 'global'
            
            # Create metrics collector
            collector = MetricsCollector(component)
            
            # Start timing
            start_time = time.time()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            finally:
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Use provided metric name or generate from function
                name = metric_name or f"{func.__name__}.execution_time"
                
                # Record timing metric
                collector.record_timing(name, execution_time_ms, tags)
        
        return wrapper  # type: ignore
    
    return decorator
```

### 3. Implement Metrics Exporters

Create exporters for different backends, starting with a simple console exporter:

```python
# Example implementation of exporters/console.py
import json
from typing import Dict, Any
from observability.logging import Logger

class ConsoleExporter:
    """Exports metrics to console via logger."""
    
    def __init__(self):
        """Initialize console exporter."""
        self.logger = Logger("metrics.exporter.console")
    
    def export(self, component: str, metric_name: str, metric_data: Dict[str, Any]) -> None:
        """Export a metric to console.
        
        Args:
            component: Component name
            metric_name: Metric name
            metric_data: Metric data
        """
        self.logger.info(
            f"METRIC: {component}.{metric_name}", 
            context={"metric": metric_data}
        )
```

Optionally, implement a Prometheus exporter if needed:

```python
# Example implementation of exporters/prometheus.py
from typing import Dict, Any, Optional
from observability.logging import Logger

# Note: This would require the prometheus_client package
try:
    import prometheus_client as prom
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

class PrometheusExporter:
    """Exports metrics to Prometheus."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Prometheus exporter.
        
        Args:
            config: Prometheus configuration
        """
        self.logger = Logger("metrics.exporter.prometheus")
        self.metrics: Dict[str, Any] = {}
        
        if not PROMETHEUS_AVAILABLE:
            self.logger.warning("Prometheus client not available. Install with 'pip install prometheus-client'")
            return
            
        # Start Prometheus HTTP server if configured
        if config.get("start_http_server", False):
            port = config.get("port", 8000)
            prom.start_http_server(port)
            self.logger.info(f"Started Prometheus metrics server on port {port}")
    
    def export(self, component: str, metric_name: str, metric_data: Dict[str, Any]) -> None:
        """Export a metric to Prometheus.
        
        Args:
            component: Component name
            metric_name: Metric name
            metric_data: Metric data
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        # Create full metric name
        full_name = f"{component}_{metric_name}".replace(".", "_")
        metric_type = metric_data.get("type")
        labels = metric_data.get("tags", {})
        
        # Create or get metric
        if full_name not in self.metrics:
            if metric_type == "counter":
                self.metrics[full_name] = prom.Counter(full_name, f"{component} {metric_name} counter", labels.keys())
            elif metric_type == "gauge":
                self.metrics[full_name] = prom.Gauge(full_name, f"{component} {metric_name} gauge", labels.keys())
            elif metric_type == "timing":
                self.metrics[full_name] = prom.Histogram(full_name, f"{component} {metric_name} timing", labels.keys())
        
        # Update metric value
        if metric_type == "counter":
            self.metrics[full_name].labels(**labels).inc(metric_data.get("value", 1))
        elif metric_type == "gauge":
            self.metrics[full_name].labels(**labels).set(metric_data.get("value", 0))
        elif metric_type == "timing":
            self.metrics[full_name].labels(**labels).observe(metric_data.get("value", 0))
```

### 4. Update Configuration Module

Extend the existing configuration module to support metrics settings:

```python
# Updated config.py with metrics configuration
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
    },
    "metrics": {
        "enabled": True,
        "exporters": ["console"],
        "prometheus": {
            "start_http_server": False,
            "port": 8000
        }
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
            if section in OBSERVABILITY_CONFIG and isinstance(OBSERVABILITY_CONFIG[section], dict):
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
```

### 5. Update Package Exports

Update the `__init__.py` file to expose the new metrics functionality:

```python
# Updated __init__.py
from observability.logging import Logger
from observability.metrics import MetricsCollector, timed
from observability.config import configure_observability, OBSERVABILITY_CONFIG

__all__ = ["Logger", "MetricsCollector", "timed", "configure_observability", "OBSERVABILITY_CONFIG"]
```

## Implementation Plan

### Phase 1: Core Metrics Infrastructure

1. **Create metrics.py module**
   - Implement `MetricsCollector` class
   - Implement timing decorator

2. **Create exporters package**
   - Implement console exporter
   - Define exporter interface

3. **Update configuration**
   - Extend config.py with metrics settings
   - Update package exports

### Phase 2: Application Integration

1. **Identify performance-critical methods**
   - Core resume parsing operations
   - LLM query operations
   - Skill extraction and analysis

2. **Apply timing decorators**
   - Add `@timed` decorator to identified methods
   - Example:
     ```python
     from observability import timed
     
     class ResumeInsights:
         @timed(metric_name="extract_candidate_data.time", tags={"source": "resume"})
         def extract_candidate_data(self) -> Candidate:
             # Existing implementation
     ```

3. **Add custom metrics**
   - Track resume processing counts
   - Track skill extraction success rates
   - Track LLM API usage

### Phase 3: Advanced Metrics (Optional)

1. **Implement Prometheus exporter**
   - Add prometheus_client dependency
   - Implement PrometheusExporter class

2. **Set up dashboards**
   - Create Grafana dashboards for metrics visualization
   - Set up alerts for performance degradation

## Performance Considerations

- Metrics collection adds some overhead, but should be minimal with proper implementation
- Use sampling for high-volume operations if needed
- Disable detailed metrics in production if performance impact is significant

## Dependencies

- No additional dependencies for basic metrics (console exporter)
- Optional: prometheus_client for Prometheus integration

## Testing Strategy

1. **Unit tests**
   - Test MetricsCollector functionality
   - Test timing decorator accuracy
   - Test exporters

2. **Integration tests**
   - Verify metrics are collected during application operation
   - Verify metrics are exported correctly

## Conclusion

The proposed metrics collection extension builds upon the existing observability infrastructure to provide valuable performance insights. By implementing timing decorators and a flexible metrics collection system, we can monitor critical operations, identify performance bottlenecks, and ensure the application meets performance requirements.