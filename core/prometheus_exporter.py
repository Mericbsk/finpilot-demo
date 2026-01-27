# -*- coding: utf-8 -*-
"""
FinPilot Prometheus Exporter
============================

Prometheus metrics HTTP endpoint.

Usage:
    from core.prometheus_exporter import start_metrics_server

    # Start metrics server on port 8000
    start_metrics_server(port=8000)

    # Metrics available at http://localhost:8000/metrics

Author: FinPilot Team
Version: 1.0.0
"""

from __future__ import annotations

import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

from core.monitoring import HealthStatus, health_check, metrics

# =============================================================================
# PROMETHEUS FORMAT EXPORTER
# =============================================================================


class PrometheusExporter:
    """
    Export internal metrics in Prometheus text format.

    Converts FinPilot metrics to Prometheus exposition format.
    """

    def __init__(self):
        self._metrics = metrics

    def generate_metrics_output(self) -> str:
        """Generate Prometheus-compatible metrics output."""
        lines = []

        # Add header
        lines.append("# FinPilot Metrics Export")
        lines.append(f"# Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Export all metrics from registry
        try:
            for name, metric in self._metrics._metrics.items():
                metric_type = self._get_metric_type(metric)

                # Add HELP and TYPE lines
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} {metric_type}")

                # Collect and export values
                try:
                    collected = metric.collect()
                    for value in collected:
                        # Handle both MetricValue objects and dicts
                        if hasattr(value, "labels") and hasattr(value, "value"):
                            labels_str = self._format_labels(getattr(value, "labels"))
                            metric_value = getattr(value, "value")
                        elif isinstance(value, dict):
                            labels_str = self._format_labels(value.get("labels", {}))
                            metric_value = value.get("value", 0)
                        else:
                            continue

                        if metric_type == "histogram":
                            self._export_histogram(lines, name, value)
                        else:
                            lines.append(f"{name}{labels_str} {metric_value}")
                except Exception:
                    # Skip metrics that fail to collect
                    pass

                lines.append("")
        except Exception:
            # Return basic output if metrics unavailable
            pass

        # Add health status
        lines.extend(self._export_health_metrics())

        return "\n".join(lines)

    def _get_metric_type(self, metric) -> str:
        """Get Prometheus metric type string."""
        type_name = type(metric).__name__.lower()
        return type_name

    def _format_labels(self, labels: dict) -> str:
        """Format labels for Prometheus."""
        if not labels:
            return ""

        parts = []
        for key, value in sorted(labels.items()):
            # Escape special characters in label values
            escaped_value = str(value).replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{key}="{escaped_value}"')

        return "{" + ",".join(parts) + "}"

    def _export_histogram(self, lines: list, name: str, value) -> None:
        """Export histogram in Prometheus format."""
        # Histograms are complex - we export buckets, count, sum
        # For now, export as gauge with bucket info in labels
        labels = value.labels.copy()
        lines.append(f"{name}_count{self._format_labels(labels)} {value.value}")

    def _export_health_metrics(self) -> list[str]:
        """Export health check results as metrics."""
        lines = []

        lines.append(
            "# HELP finpilot_health_status Health check status (1=healthy, 0.5=degraded, 0=unhealthy)"
        )
        lines.append("# TYPE finpilot_health_status gauge")

        try:
            health_result = health_check.run()
            checks = health_result.get("checks", [])
            for check in checks:
                check_name = check.get("name", "unknown")
                status_str = check.get("status", "unhealthy")
                if status_str == "healthy":
                    status_value = 1.0
                elif status_str == "degraded":
                    status_value = 0.5
                else:
                    status_value = 0.0
                lines.append(f'finpilot_health_status{{check="{check_name}"}} {status_value}')
        except Exception:
            lines.append('finpilot_health_status{check="error"} 0')

        return lines


# =============================================================================
# HTTP SERVER FOR METRICS
# =============================================================================


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint."""

    exporter = PrometheusExporter()

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/metrics":
            self._serve_metrics()
        elif parsed_path.path == "/health":
            self._serve_health()
        elif parsed_path.path == "/ready":
            self._serve_ready()
        else:
            self._serve_404()

    def _serve_metrics(self) -> None:
        """Serve Prometheus metrics."""
        try:
            content = self.exporter.generate_metrics_output()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except Exception as e:
            self._serve_error(str(e))

    def _serve_health(self) -> None:
        """Serve health check endpoint."""
        try:
            health_result = health_check.run()
            status_str = health_result.get("status", "unhealthy")
            all_healthy = status_str == "healthy"

            status_code = 200 if all_healthy else 503
            content = "OK" if all_healthy else "UNHEALTHY"

            self.send_response(status_code)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except Exception as e:
            self._serve_error(str(e))

    def _serve_ready(self) -> None:
        """Serve readiness check endpoint."""
        content = "READY"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _serve_404(self) -> None:
        """Serve 404 response."""
        content = "Not Found"
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _serve_error(self, message: str) -> None:
        """Serve 500 error response."""
        content = f"Error: {message}"
        self.send_response(500)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass  # Silent by default


class MetricsServer:
    """
    Background HTTP server for Prometheus metrics.

    Usage:
        server = MetricsServer(port=8000)
        server.start()

        # ... application runs ...

        server.stop()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start the metrics server in a background thread."""
        if self._running:
            return

        self._server = HTTPServer((self.host, self.port), MetricsHandler)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._running = True
        self._thread.start()

    def _run(self) -> None:
        """Run the server."""
        if self._server:
            self._server.serve_forever()

    def stop(self) -> None:
        """Stop the metrics server."""
        if not self._running:
            return

        self._running = False
        if self._server:
            self._server.shutdown()
            self._server.server_close()

        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running


# Global server instance
_metrics_server: Optional[MetricsServer] = None


def start_metrics_server(
    host: str = "0.0.0.0",
    port: Optional[int] = None,
) -> MetricsServer:
    """
    Start the metrics server.

    Args:
        host: Host to bind to.
        port: Port to bind to. If None, uses METRICS_PORT env var or 8000.

    Returns:
        MetricsServer instance.
    """
    global _metrics_server

    if port is None:
        port = int(os.getenv("METRICS_PORT", "8000"))

    if _metrics_server is None or not _metrics_server.is_running():
        _metrics_server = MetricsServer(host=host, port=port)
        _metrics_server.start()

    return _metrics_server


def stop_metrics_server() -> None:
    """Stop the metrics server."""
    global _metrics_server

    if _metrics_server:
        _metrics_server.stop()
        _metrics_server = None


def get_metrics_output() -> str:
    """Get metrics output as string without starting server."""
    exporter = PrometheusExporter()
    return exporter.generate_metrics_output()


__all__ = [
    "PrometheusExporter",
    "MetricsServer",
    "MetricsHandler",
    "start_metrics_server",
    "stop_metrics_server",
    "get_metrics_output",
]
