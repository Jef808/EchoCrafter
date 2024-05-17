"""Logging module for the Echo Crafter application."""

import logging
import json
import time
import os
from pathlib import Path

LOG_FILE = Path(os.environ.get('EC_LOG_DIR', '')) / "transcripts.jsonl"
ONLY_TRUE_ONCE = True


class CustomRecord(logging.LogRecord):
    """Custom LogRecord class with a timestamp attribute."""

    def __init__(self, name, level, pathname, lineno, msg, args,
                 exc_info, func=None, sinfo=None):
        """Initialize a CustomRecord instance."""
        super().__init__(name, level, pathname, lineno, msg, args,
                         exc_info, func=func, sinfo=sinfo)
        self.timestamp = time.time()


class JsonFormatter(logging.Formatter):
    """JSON formatter for log records."""

    def format(self, record):
        """Format a log record as a JSON string."""
        log_dict = record.__dict__.copy()
        log_dict['msg'] = record.getMessage()
        return json.dumps(log_dict)


def setup_logger(name, level=logging.INFO):
    """Set up a logger with a JSON formatter."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logging.setLogRecordFactory(CustomRecord)
    handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
