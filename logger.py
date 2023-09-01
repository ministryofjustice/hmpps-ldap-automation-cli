import logging
import env


def configure_logging():
    class SensitiveFormatter(logging.Formatter):
        """Formatter that removes secrets from log messages."""

        def __init__(self, format_str=None, datefmt_str=None):
            super().__init__(fmt=format_str, datefmt=datefmt_str)
            self._secrets_set = set(env.secrets.values())  # Retrieve secrets set here
            self.default_msec_format = "%s.%03d"

        def _filter(self, s):
            redacted = " ".join(
                ["*" * len(string) if string in self._secrets_set else string for string in s.split(" ")]
            )

            return redacted

        def format(self, record):
            original = super().format(record)
            return self._filter(original)

    print("configure_logging")
    """Configure logging based on environment variables."""
    format = env.vars.get("LOG_FORMAT") or "%(asctime)s.%(msecs)03d - %(levelname)s: %(message)s"
    datefmt = env.vars.get("LOG_DATE_FORMAT") or "%Y-%m-%d %H:%M:%S"

    log = logging.getLogger(__name__)

    if logging.root.hasHandlers():
        logging.root.handlers = []

    handler = logging.StreamHandler()
    handler.setFormatter(SensitiveFormatter(format_str=format, datefmt_str=datefmt))
    logging.root.addHandler(handler)
    if env.vars.get("LOG_LEVEL") == "DEBUG":
        print("DEBUG")
        log.setLevel(logging.DEBUG)
    elif env.vars.get("LOG_LEVEL") == "WARNING":
        print("WARNING")
        log.setLevel(logging.WARNING)
    elif env.vars.get("LOG_LEVEL") == "ERROR":
        print("ERROR")
        log.setLevel(logging.ERROR)
    elif env.vars.get("LOG_LEVEL") == "INFO":
        print("INFO")
        log.setLevel(logging.INFO)
    return True


log = logging.getLogger(__name__)
