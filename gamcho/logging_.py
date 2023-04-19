def make_base_config():
    return {
        "version": 1,
        "formatters": {
            "tlnm": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "message_only": {
                "format": "%(message)s"
            },
        },
        "handlers": {
            "console": {
                "formatter": "message_only",
                "class": "logging.StreamHandler",
            },
            "file": {
                "formatter": "tlnm",
                "class": "logging.FileHandler",
                "mode": "w",
                # "filename" better be specified
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": "INFO",
            },
        }
    }
