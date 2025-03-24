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