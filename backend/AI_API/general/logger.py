import logging
import os
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode

LOG_NAME = "apartment_manager"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
LOG_FILE = os.path.join(BASE_DIR, "data", "app.log")

_TRACE_ID: ContextVar[str] = ContextVar("trace_id", default="-")

class TraceIdOptionalFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = _ensure_trace_id()
        if not hasattr(record, "error_code"):
            record.error_code = "-"
        if not hasattr(record, "error_message"):
            record.error_message = "-"
        return True

def get_trace_id() -> str:
    return _TRACE_ID.get()

def _ensure_trace_id() -> str:
    """
    Ensures that a trace ID is set. Generates and sets a new trace ID if none is found or if the current trace ID is invalid.

    If the current trace ID is either missing or set to "-", the function generates a new UUID-based trace ID,
    assigns it to the trace context, and then returns the trace ID. This function is primarily used to ensure
    uniqueness and consistency in trace identification.

    :return: The ensured or newly generated trace ID
    :rtype: str
    """
    trace_id = _TRACE_ID.get()
    if not trace_id or trace_id == "-":
        import uuid
        trace_id = str(uuid.uuid4())
        _TRACE_ID.set(trace_id)
    return trace_id

def set_trace_id(value: str) -> None:
    _TRACE_ID.set(value)

def clear_trace_id() -> None:
    _TRACE_ID.set("-")


def _extend_log(error_description: ErrorCode, trace_id: str) -> dict:
    """
    Constructs a dictionary with error details and trace information.

    This function takes an error description and trace identifier as arguments,
    then creates a dictionary including the error code, error message,
    and trace ID. If the error code or error message is not provided,
    default values of "-" are used.

    :param error_description: A tuple containing error code and error message.
    :type error_description: ErrorCode
    :param trace_id: Unique identifier for the trace.
    :type trace_id: str
    :return: A dictionary with keys "trace_id", "error_code", and "error_message",
             containing the respective given or default values.
    :rtype: dict
    """
    error_code, error_message = None, None

    if error_description:
        error_code, error_message = error_description.value
    return {
        "trace_id": trace_id,
        "error_code": error_code if error_code is not None else "-",
        "error_message": error_message if error_message is not None else "-",
    }


def init_logging() -> logging.Logger:
    """
    Initializes and sets up logging for the application. This function ensures that
    a logger is created with the specified log level and attaches handlers for
    console output and log file rotation. The logs are formatted with timestamps,
    log levels, logger names, trace_id, and messages for better readability. If the logger
    already has handlers attached, it does not add duplicate handlers.
    The trace_id is part of the log format by default and is auto-generated when missing
    by the helper functions do_log / log_*.

    :type level: str
    :return: A configured logger instance.
    :rtype: logging.Logger
    """
    level = "INFO"
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    logger = logging.getLogger(LOG_NAME)
    if isinstance(level, str):
        numeric_level = logging.getLevelName(level.upper())
        if not isinstance(numeric_level, int):
            numeric_level = logging.INFO
    else:
        numeric_level = level
    logger.setLevel(numeric_level)

    # This check prevents adding duplicate handlers to an already configured logger
    if logger.handlers:
        return logger

    # What should be written to the log
    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] trace_id=%(trace_id)s "
            "error_code=%(error_code)s error_message=%(error_message)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    # Log for console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # Files rotate after reaching ~5MB with 3 backup files kept
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addFilter(TraceIdOptionalFilter())

    # It prevents log messages from being passed up to parent loggers
    # Without this, duplicate log messages in the output
    logger.propagate = False

    logger.info("Logging initialized")
    return logger


def get_logger() -> logging.Logger:
    """
    Retrieves and returns a logger instance configured with the specified
    logger name. This function simplifies obtaining a logger for logging
    messages consistently across the application.

    :return: A logger instance corresponding to the specified logger name.
    :rtype: logging.Logger
    """
    return logging.getLogger(LOG_NAME)

def log_info(message: str) -> None:
    logger = get_logger()
    extra = {"trace_id": _ensure_trace_id(), "error_code": "-", "error_message": "-"}
    logger.info(message, extra=extra)


def log_warning(warning_details: ErrorCode) -> None:
    logger = get_logger()
    extra = _extend_log(warning_details, _ensure_trace_id())
    logger.warning(
        msg=f"Error code: {extra['error_code']}, Error message: {extra['error_message']}",
        extra=extra
    )

def log_error(error_details: ErrorCode, exception: Exception=None) -> str:
    trace_id = _ensure_trace_id()
    logger = get_logger()

    extra = _extend_log(error_details, trace_id)
    message = f"Error code: {extra.get('error_code')}, Error message: {extra.get('error_message')}"

    if exception:
        exc_info_tuple = (exception.__class__, exception, exception.__traceback__)
    else:
        exc_info_tuple = None

    logger.error(message, exc_info=exc_info_tuple, extra=extra)

    return trace_id
