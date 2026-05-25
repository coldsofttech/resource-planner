import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DESTINATION = os.getenv("LOG_DESTINATION", "local")
LOG_NAME = os.getenv("LOG_NAME", "application")
LOG_PATH = os.getenv("LOG_PATH", "") or str(BASE_DIR / "logs")
LOG_ROTATION = os.getenv("LOG_ROTATION", "none")
LOG_ROTATION_SIZE_MB = int(os.getenv("LOG_ROTATION_SIZE_MB", "10"))
LOG_CLEANUP_KEEP_FILES = int(os.getenv("LOG_CLEANUP_KEEP_FILES", "5"))
LOG_CLEANUP_KEEP_DAYS = int(os.getenv("LOG_CLEANUP_KEEP_DAYS", "0"))
LOG_S3_BUCKET = os.getenv("LOG_S3_BUCKET", "")
AWS_REGION = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-1"))
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

COMMON_FORMAT = (
    "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d] — %(message)s"
)
COMMON_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOGGERS = ["django", "apps", "jobs", "packages"]


def _file_handler_config(log_file: Path) -> dict:
    """Return the appropriate file handler config based on rotation policy."""
    if LOG_ROTATION == "size":
        return {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_file),
            "maxBytes": LOG_ROTATION_SIZE_MB * 1024 * 1024,
            "backupCount": LOG_CLEANUP_KEEP_FILES,
            "formatter": "verbose",
            "encoding": "utf-8",
            "delay": True,
        }
    if LOG_ROTATION in ("daily", "weekly", "monthly"):
        # TimedRotatingFileHandler: midnight=daily, W0=weekly,
        # monthly=midnight+interval=30.
        when_map = {"daily": "midnight", "weekly": "W0", "monthly": "midnight"}
        interval_map = {"daily": 1, "weekly": 1, "monthly": 30}
        return {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_file),
            "when": when_map[LOG_ROTATION],
            "interval": interval_map[LOG_ROTATION],
            "backupCount": LOG_CLEANUP_KEEP_FILES,
            "formatter": "verbose",
            "encoding": "utf-8",
            "delay": True,
        }
    # none
    return {
        "class": "logging.FileHandler",
        "filename": str(log_file),
        "formatter": "verbose",
        "encoding": "utf-8",
        "delay": True,
    }


def _build_handlers() -> dict:
    handlers: dict = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    }

    try:
        if LOG_DESTINATION == "local":
            log_dir = Path(LOG_PATH)
            log_dir.mkdir(parents=True, exist_ok=True)
            handlers["destination"] = _file_handler_config(log_dir / f"{LOG_NAME}.log")

        elif LOG_DESTINATION == "s3":
            handlers["destination"] = {
                "class": "awscore.logging.S3LogHandler",
                "bucket": LOG_S3_BUCKET,
                "key_prefix": LOG_NAME,
                "region": AWS_REGION,
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "formatter": "verbose",
            }

        elif LOG_DESTINATION == "cloudwatch":
            handlers["destination"] = {
                "class": "watchtower.CloudWatchLogHandler",
                "log_group_name": LOG_NAME,
                "boto3_client": None,
                "formatter": "verbose",
            }
    except OSError:
        # Fall back to console-only if the log directory/file cannot be prepared
        # (e.g. a management script runs alongside a live server that holds the file).
        pass

    return handlers


def _active_handlers(handlers: dict) -> list[str]:
    names = ["console"]
    if "destination" in handlers:
        names.append("destination")
    return names


_handlers = _build_handlers()
_handler_names = _active_handlers(_handlers)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": COMMON_FORMAT,
            "datefmt": COMMON_DATE_FORMAT,
        },
        "simple": {
            "format": "[%(levelname)s] %(message)s",
        },
    },
    "handlers": _handlers,
    "root": {
        "handlers": _handler_names,
        "level": LOG_LEVEL,
    },
    "loggers": {
        name: {
            "handlers": _handler_names,
            "level": LOG_LEVEL,
            "propagate": False,
        }
        for name in LOGGERS
    },
}
