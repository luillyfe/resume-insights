import pytest
import unittest.mock as mock

from observability.metrics import MetricsCollector
from observability.config import OBSERVABILITY_CONFIG


class TestMetricsCollector:
    @pytest.fixture
    def metrics_collector(self):
        # Create a metrics collector for testing
        return MetricsCollector("test_component")
    
    @pytest.fixture
    def mock_exporter(self):
        # Create a mock exporter for testing
        exporter = mock.MagicMock()
        exporter.export = mock.MagicMock()
        return exporter
    
    def test_init(self):
        # Test initialization of metrics collector
        collector = MetricsCollector("test_component")
        assert collector.name == "test_component"
        assert isinstance(collector.metrics, dict)
        assert len(collector.metrics) == 0
    
    def test_increment_counter_new_metric(self, metrics_collector):
        # Test incrementing a new counter
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        metrics_collector.increment_counter("test_counter")
        
        assert "test_counter" in metrics_collector.metrics
        assert metrics_collector.metrics["test_counter"]["type"] == "counter"
        assert metrics_collector.metrics["test_counter"]["value"] == 1
        assert metrics_collector.metrics["test_counter"]["tags"] == {}
        
        # Verify export was called
        metrics_collector._export_metric.assert_called_once_with(
            "test_counter", metrics_collector.metrics["test_counter"]
        )
    
    def test_increment_counter_existing_metric(self, metrics_collector):
        # Test incrementing an existing counter
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        # Initialize counter
        metrics_collector.metrics["test_counter"] = {"type": "counter", "value": 5, "tags": {}}
        
        # Increment counter
        metrics_collector.increment_counter("test_counter", 3)
        
        assert metrics_collector.metrics["test_counter"]["value"] == 8
        
        # Verify export was called
        metrics_collector._export_metric.assert_called_once_with(
            "test_counter", metrics_collector.metrics["test_counter"]
        )
    
    def test_increment_counter_with_tags(self, metrics_collector):
        # Test incrementing a counter with tags
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        tags = {"env": "test", "component": "metrics"}
        metrics_collector.increment_counter("test_counter", 1, tags)
        
        assert metrics_collector.metrics["test_counter"]["tags"] == tags
    
    def test_record_gauge(self, metrics_collector):
        # Test recording a gauge metric
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        metrics_collector.record_gauge("test_gauge", 42.5)
        
        assert "test_gauge" in metrics_collector.metrics
        assert metrics_collector.metrics["test_gauge"]["type"] == "gauge"
        assert metrics_collector.metrics["test_gauge"]["value"] == 42.5
        assert metrics_collector.metrics["test_gauge"]["tags"] == {}
        
        # Verify export was called
        metrics_collector._export_metric.assert_called_once_with(
            "test_gauge", metrics_collector.metrics["test_gauge"]
        )
    
    def test_record_gauge_with_tags(self, metrics_collector):
        # Test recording a gauge metric with tags
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        tags = {"env": "test", "component": "metrics"}
        metrics_collector.record_gauge("test_gauge", 42.5, tags)
        
        assert metrics_collector.metrics["test_gauge"]["tags"] == tags
    
    def test_record_timing_new_metric(self, metrics_collector):
        # Test recording a new timing metric
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        metrics_collector.record_timing("test_timing", 100.5)
        
        assert "test_timing" in metrics_collector.metrics
        assert metrics_collector.metrics["test_timing"]["type"] == "timing"
        assert metrics_collector.metrics["test_timing"]["count"] == 1
        assert metrics_collector.metrics["test_timing"]["sum"] == 100.5
        assert metrics_collector.metrics["test_timing"]["min"] == 100.5
        assert metrics_collector.metrics["test_timing"]["max"] == 100.5
        assert metrics_collector.metrics["test_timing"]["tags"] == {}
        
        # Verify export was called
        metrics_collector._export_metric.assert_called_once_with(
            "test_timing", metrics_collector.metrics["test_timing"]
        )
    
    def test_record_timing_existing_metric(self, metrics_collector):
        # Test recording an existing timing metric
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        # Initialize timing metric
        metrics_collector.metrics["test_timing"] = {
            "type": "timing",
            "count": 1,
            "sum": 100.0,
            "min": 100.0,
            "max": 100.0,
            "tags": {}
        }
        
        # Record another timing value
        metrics_collector.record_timing("test_timing", 50.0)
        
        assert metrics_collector.metrics["test_timing"]["count"] == 2
        assert metrics_collector.metrics["test_timing"]["sum"] == 150.0
        assert metrics_collector.metrics["test_timing"]["min"] == 50.0  # New min
        assert metrics_collector.metrics["test_timing"]["max"] == 100.0  # Max unchanged
        
        # Record another timing value that's a new max
        metrics_collector.record_timing("test_timing", 200.0)
        
        assert metrics_collector.metrics["test_timing"]["count"] == 3
        assert metrics_collector.metrics["test_timing"]["sum"] == 350.0
        assert metrics_collector.metrics["test_timing"]["min"] == 50.0  # Min unchanged
        assert metrics_collector.metrics["test_timing"]["max"] == 200.0  # New max
    
    def test_record_timing_with_tags(self, metrics_collector):
        # Test recording a timing metric with tags
        metrics_collector._export_metric = mock.MagicMock()  # Mock export to isolate test
        
        tags = {"env": "test", "component": "metrics"}
        metrics_collector.record_timing("test_timing", 100.5, tags)
        
        assert metrics_collector.metrics["test_timing"]["tags"] == tags
    
    def test_export_metric(self, metrics_collector, mock_exporter):
        # Test exporting a metric to an exporter
        metrics_collector._exporters = [mock_exporter]
        
        metric_name = "test_metric"
        metric_data = {"type": "counter", "value": 1, "tags": {}}
        
        metrics_collector._export_metric(metric_name, metric_data)
        
        # Verify exporter was called with correct arguments
        mock_exporter.export.assert_called_once_with(
            metrics_collector.name, metric_name, metric_data
        )
    
    def test_export_metric_handles_exception(self, metrics_collector, mock_exporter):
        # Test that export_metric handles exceptions from exporters
        metrics_collector._exporters = [mock_exporter]
        metrics_collector.logger.error = mock.MagicMock()  # Mock logger.error
        
        # Make exporter.export raise an exception
        mock_exporter.export.side_effect = Exception("Test exception")
        
        metric_name = "test_metric"
        metric_data = {"type": "counter", "value": 1, "tags": {}}
        
        # This should not raise an exception
        metrics_collector._export_metric(metric_name, metric_data)
        
        # Verify logger.error was called
        metrics_collector.logger.error.assert_called_once()
    
    @mock.patch("observability.metrics.OBSERVABILITY_CONFIG")
    def test_setup_exporters_no_metrics_config(self, mock_config):
        # Test setup_exporters when metrics config is not present
        mock_config.get.return_value = {}
        
        # Create collector after mock is applied
        metrics_collector = MetricsCollector("test_component")
        
        assert len(metrics_collector._exporters) == 0
    
    @mock.patch("observability.metrics.OBSERVABILITY_CONFIG")
    @mock.patch("observability.exporters.console.ConsoleExporter")
    def test_setup_exporters_with_console_exporter(self, mock_console_exporter, mock_config):
        # Test setup_exporters with console exporter configured
        # Configure mock to act like a dictionary with 'metrics' key
        mock_config.__contains__.side_effect = lambda x: x == "metrics"
        mock_config.get.side_effect = lambda k, default=None: {"exporters": ["console"]} if k == "metrics" else default
        mock_console_exporter.return_value = "mock_console_exporter"
        
        # Create collector after mocks are applied
        collector = MetricsCollector("test_component") 

        assert "mock_console_exporter" in collector._exporters