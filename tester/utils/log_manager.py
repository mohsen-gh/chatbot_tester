import logging
import logging.config

APP_NAME = "chatbot_tester"

def setup_logging(
    app_name: str = APP_NAME,
    app_level: str = "DEBUG",
    root_level: str = "INFO",
):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "DEBUG",
            },
        },

        # Root logger → controls third-party libs
        "root": {
            "handlers": ["console"],
            "level": root_level,
        },

        # Your application namespace
        "loggers": {
            app_name: {
                "handlers": ["console"],
                "level": app_level,
                "propagate": False,  # important!
            },
        },
    }

    logging.config.dictConfig(logging_config)

def get_logger(name:str) -> logging.Logger:
    return logging.getLogger(f"{APP_NAME}.{name}")