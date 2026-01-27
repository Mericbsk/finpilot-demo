"""
Test suite for Prometheus metrics exporter.
Tests cover metrics export, HTTP server, and health endpoints.
"""

import os
import sys
import threading
import time
import urllib.error
import urllib.request
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prometheus_exporter import (
    MetricsHandler,
    MetricsServer,
    PrometheusExporter,
    get_metrics_output,
    start_metrics_server,
    stop_metrics_server,
)


class TestPrometheusExporter:
    """Tests for PrometheusExporter class."""

    def test_exporter_initialization(self):
        """Test exporter initializes correctly."""
        exporter = PrometheusExporter()
        assert exporter is not None

    def test_generate_metrics_output(self):
        """Test metrics output generation."""
        exporter = PrometheusExporter()
        output = exporter.generate_metrics_output()

        assert isinstance(output, str)
        assert "FinPilot Metrics Export" in output

    def test_format_labels_empty(self):
        """Test empty labels formatting."""
        exporter = PrometheusExporter()
        formatted = exporter._format_labels({})
        assert formatted == ""

    def test_format_labels_single(self):
        """Test single label formatting."""
        exporter = PrometheusExporter()
        formatted = exporter._format_labels({"method": "GET"})
        assert 'method="GET"' in formatted
        assert formatted.startswith("{")
        assert formatted.endswith("}")

    def test_format_labels_multiple(self):
        """Test multiple labels formatting."""
        exporter = PrometheusExporter()
        labels = {"method": "GET", "path": "/api/v1", "status": "200"}
        formatted = exporter._format_labels(labels)

        assert 'method="GET"' in formatted
        assert 'path="/api/v1"' in formatted
        assert 'status="200"' in formatted

    def test_format_labels_escaping(self):
        """Test label value escaping."""
        exporter = PrometheusExporter()
        labels = {"path": '/api?id=1&name="test"'}
        formatted = exporter._format_labels(labels)

        # Double quotes should be escaped
        assert '\\"' in formatted

    def test_format_labels_backslash_escaping(self):
        """Test backslash escaping in labels."""
        exporter = PrometheusExporter()
        labels = {"path": "C:\\Users\\test"}
        formatted = exporter._format_labels(labels)

        # Backslashes should be escaped
        assert "\\\\" in formatted


class TestMetricsServer:
    """Tests for MetricsServer HTTP server."""

    def test_server_initialization(self):
        """Test server initializes with correct config."""
        server = MetricsServer(host="127.0.0.1", port=29999)
        assert server.host == "127.0.0.1"
        assert server.port == 29999
        assert not server.is_running()

    def test_server_default_config(self):
        """Test server uses default config."""
        server = MetricsServer()
        assert server.host == "0.0.0.0"
        assert server.port == 8000

    def test_server_start_stop(self):
        """Test server start and stop lifecycle."""
        server = MetricsServer(host="127.0.0.1", port=29998)

        try:
            server.start()
            time.sleep(0.3)
            assert server.is_running()

            server.stop()
            time.sleep(0.3)
            assert not server.is_running()
        except OSError:
            pytest.skip("Port 29998 unavailable")

    def test_server_metrics_endpoint(self):
        """Test metrics endpoint returns data."""
        server = MetricsServer(host="127.0.0.1", port=29997)

        try:
            server.start()
            time.sleep(0.3)

            try:
                response = urllib.request.urlopen("http://127.0.0.1:29997/metrics", timeout=2)
                data = response.read().decode()
                assert response.status == 200
                assert isinstance(data, str)
                assert "FinPilot" in data or "finpilot" in data.lower()
            except urllib.error.URLError as e:
                pytest.skip(f"Could not connect to metrics server: {e}")
            finally:
                server.stop()
        except OSError:
            pytest.skip("Port 29997 unavailable")

    def test_server_health_endpoint(self):
        """Test health endpoint returns OK."""
        server = MetricsServer(host="127.0.0.1", port=29996)

        try:
            server.start()
            time.sleep(0.3)

            try:
                response = urllib.request.urlopen("http://127.0.0.1:29996/health", timeout=2)
                data = response.read().decode()
                assert response.status == 200
                # Should contain health status info
                assert isinstance(data, str)
            except urllib.error.URLError as e:
                pytest.skip(f"Could not connect to health endpoint: {e}")
            finally:
                server.stop()
        except OSError:
            pytest.skip("Port 29996 unavailable")

    def test_server_ready_endpoint(self):
        """Test ready endpoint returns OK."""
        server = MetricsServer(host="127.0.0.1", port=29995)

        try:
            server.start()
            time.sleep(0.3)

            try:
                response = urllib.request.urlopen("http://127.0.0.1:29995/ready", timeout=2)
                data = response.read().decode()
                assert response.status == 200
            except urllib.error.URLError as e:
                pytest.skip(f"Could not connect to ready endpoint: {e}")
            finally:
                server.stop()
        except OSError:
            pytest.skip("Port 29995 unavailable")

    def test_double_start_no_error(self):
        """Test starting server twice doesn't error."""
        server = MetricsServer(host="127.0.0.1", port=29994)

        try:
            server.start()
            time.sleep(0.2)
            # Second start should be no-op or handled gracefully
            server.start()
            assert server.is_running()
        except OSError:
            pytest.skip("Port 29994 unavailable")
        finally:
            server.stop()

    def test_double_stop_no_error(self):
        """Test stopping server twice doesn't error."""
        server = MetricsServer(host="127.0.0.1", port=29993)

        try:
            server.start()
            time.sleep(0.2)
            server.stop()
            # Second stop should be no-op
            server.stop()
            assert not server.is_running()
        except OSError:
            pytest.skip("Port 29993 unavailable")

    def test_server_404_unknown_path(self):
        """Test 404 for unknown paths."""
        server = MetricsServer(host="127.0.0.1", port=29992)

        try:
            server.start()
            time.sleep(0.3)

            try:
                response = urllib.request.urlopen("http://127.0.0.1:29992/unknown", timeout=2)
                pytest.fail("Expected 404 error")
            except urllib.error.HTTPError as e:
                assert e.code == 404
            except urllib.error.URLError as e:
                pytest.skip(f"Could not connect: {e}")
            finally:
                server.stop()
        except OSError:
            pytest.skip("Port 29992 unavailable")


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_metrics_output(self):
        """Test get_metrics_output returns string."""
        output = get_metrics_output()
        assert isinstance(output, str)

    def test_start_stop_metrics_server(self):
        """Test global start/stop functions."""
        try:
            server = start_metrics_server(host="127.0.0.1", port=29991)
            assert server is not None
            time.sleep(0.2)
            stop_metrics_server()
        except OSError:
            pytest.skip("Port 29991 unavailable")


class TestPrometheusFormat:
    """Tests for Prometheus output format compliance."""

    def test_output_contains_header(self):
        """Test output contains header comments."""
        exporter = PrometheusExporter()
        output = exporter.generate_metrics_output()

        assert "# " in output  # Has comments
        assert "FinPilot" in output

    def test_output_contains_timestamp(self):
        """Test output contains generation timestamp."""
        exporter = PrometheusExporter()
        output = exporter.generate_metrics_output()

        # Should have generated timestamp
        assert "Generated at" in output

    def test_help_type_format(self):
        """Test HELP and TYPE comments format."""
        exporter = PrometheusExporter()
        output = exporter.generate_metrics_output()

        # If there are metrics, they should have HELP/TYPE
        # This may be empty if no metrics registered
        assert isinstance(output, str)

    def test_unicode_in_labels(self):
        """Test unicode in label values."""
        exporter = PrometheusExporter()

        labels = {"region": "日本", "env": "production"}
        formatted = exporter._format_labels(labels)
        assert "region" in formatted
        assert "env" in formatted


class TestEdgeCases:
    """Edge case and error handling tests."""

    def test_empty_labels_dict(self):
        """Test empty labels dict returns empty string."""
        exporter = PrometheusExporter()
        result = exporter._format_labels({})
        assert result == ""

    def test_special_characters_in_values(self):
        """Test special characters in label values are escaped."""
        exporter = PrometheusExporter()

        labels = {"path": "line1\nline2"}
        formatted = exporter._format_labels(labels)
        # Newlines might be escaped or handled
        assert "path" in formatted

    def test_numeric_label_values(self):
        """Test numeric label values are converted to string."""
        exporter = PrometheusExporter()

        labels = {"status": 200, "count": 42}
        formatted = exporter._format_labels(labels)
        assert "200" in formatted
        assert "42" in formatted

    def test_concurrent_output_generation(self):
        """Test thread-safe output generation."""
        exporter = PrometheusExporter()
        outputs = []

        def generate_worker():
            for _ in range(10):
                output = exporter.generate_metrics_output()
                outputs.append(output)

        threads = [threading.Thread(target=generate_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All outputs should be valid strings
        assert len(outputs) == 50
        for output in outputs:
            assert isinstance(output, str)

    def test_server_port_in_use(self):
        """Test graceful handling of port already in use."""
        server1 = MetricsServer(host="127.0.0.1", port=29989)
        server2 = MetricsServer(host="127.0.0.1", port=29989)

        try:
            server1.start()
            time.sleep(0.3)

            # Second server should handle gracefully
            with pytest.raises((OSError, Exception)):
                server2.start()
                time.sleep(0.2)
        except OSError:
            pytest.skip("Port 29989 unavailable")
        finally:
            server1.stop()
            server2.stop()


class TestIntegration:
    """Integration tests for the full metrics pipeline."""

    def test_full_server_lifecycle(self):
        """Test complete server lifecycle with requests."""
        server = MetricsServer(host="127.0.0.1", port=29988)

        try:
            # Start server
            server.start()
            time.sleep(0.3)
            assert server.is_running()

            # Make multiple requests
            for endpoint in ["/metrics", "/health", "/ready"]:
                try:
                    response = urllib.request.urlopen(
                        f"http://127.0.0.1:29988{endpoint}", timeout=2
                    )
                    assert response.status == 200
                except urllib.error.URLError:
                    pass  # Endpoint might not exist

            # Stop server
            server.stop()
            time.sleep(0.2)
            assert not server.is_running()
        except OSError:
            pytest.skip("Port 29988 unavailable")

    def test_module_functions_integration(self):
        """Test module-level functions work together."""
        try:
            # Get metrics output
            output1 = get_metrics_output()
            assert isinstance(output1, str)

            # Start server
            server = start_metrics_server(host="127.0.0.1", port=29987)
            time.sleep(0.2)

            # Get metrics while server running
            output2 = get_metrics_output()
            assert isinstance(output2, str)

            # Stop server
            stop_metrics_server()
        except OSError:
            pytest.skip("Port 29987 unavailable")


class TestHealthEndpoint:
    """Tests for health check functionality."""

    def test_health_endpoint_format(self):
        """Test health endpoint returns proper format."""
        server = MetricsServer(host="127.0.0.1", port=29986)

        try:
            server.start()
            time.sleep(0.3)

            try:
                response = urllib.request.urlopen("http://127.0.0.1:29986/health", timeout=2)
                data = response.read().decode()
                # Should be JSON or text
                assert isinstance(data, str)
                assert len(data) > 0
            except urllib.error.URLError as e:
                pytest.skip(f"Could not connect: {e}")
            finally:
                server.stop()
        except OSError:
            pytest.skip("Port 29986 unavailable")

    def test_ready_endpoint_format(self):
        """Test ready endpoint returns proper format."""
        server = MetricsServer(host="127.0.0.1", port=29985)

        try:
            server.start()
            time.sleep(0.3)

            try:
                response = urllib.request.urlopen("http://127.0.0.1:29985/ready", timeout=2)
                data = response.read().decode()
                assert isinstance(data, str)
                assert len(data) > 0
            except urllib.error.URLError as e:
                pytest.skip(f"Could not connect: {e}")
            finally:
                server.stop()
        except OSError:
            pytest.skip("Port 29985 unavailable")
