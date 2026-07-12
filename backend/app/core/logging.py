"""
Structured JSON logging via structlog.
Logs are emitted as JSON to stdout — compatible with Grafana Loki, CloudWatch, etc.
"""
import logging
import sys

try:
    import structlog

    def setup_logging(log_level: str = "INFO"):
        """Configure structlog for JSON output."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level.upper(), logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        # Also configure stdlib logging so libraries emit structured output
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper(), logging.INFO),
        )

except ImportError:
    # Fallback if structlog is not installed
    def setup_logging(log_level: str = "INFO"):
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper(), logging.INFO),
        )
