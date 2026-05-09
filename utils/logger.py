# ============================================================
# UltraAgent — utils/logger.py
# ============================================================

import os
import structlog

def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer() if os.getenv("ENVIRONMENT") != "production"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}.get(level, 20)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
