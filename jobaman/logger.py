import logging
import sys

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def configure(
    level=logging.INFO,
    log_format=None,
    name=None,
):

    log_format = log_format or LOG_FORMAT

    root = logging.getLogger(name)
    root.handlers.clear()
    root.setLevel(level)

    formatter = logging.Formatter(log_format, datefmt=DATE_FORMAT)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setFormatter(formatter)
    error_handler.setLevel(level)
    error_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    root.addHandler(error_handler)

    info_handler = logging.StreamHandler(sys.stdout)
    info_handler.setFormatter(formatter)
    info_handler.setLevel(level)
    info_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    root.addHandler(info_handler)


def get_logger(name=None):
    return logging.getLogger(name)
