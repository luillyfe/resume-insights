import time
import functools
from typing import Any, Dict, Optional, Callable, TypeVar
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