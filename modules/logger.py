"""
Enterprise Logger Module for Smart Classroom Attention Analyzer.
Provides clean console logging and structured JSON logging for cloud hosting.
"""

import os
import sys
import json
import logging
import datetime

class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines for cloud log drivers (Datadog, CloudWatch, GCP)."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logger(name: str = "classroom_analyzer") -> logging.Logger:
    """Configures and returns an application logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    json_logs = os.environ.get("LOG_FORMAT", "").lower() == "json"

    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        fmt = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = setup_logger()
