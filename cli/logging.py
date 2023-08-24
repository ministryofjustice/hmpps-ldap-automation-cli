import logging
import cli.env


class SensitiveFormatter(logging.Formatter):
    """Formatter that removes secrets from log messages."""

    def __init__(self, format_str=None, datefmt_str=None):
        super().__init__(fmt=format_str, datefmt=datefmt_str)
        self._secrets_set = set(cli.env.secrets.values())  # Retrieve secrets set here

    def _filter(self, s):
        redacted = " ".join(
            [s.replace(secret, "*" * len(secret)) for secret in self._secrets_set if secret is not None]
        )
        return redacted

    def format(self, record):
        original = super().format(record)
        return self._filter(original)


def configure_logging():
    print("configure_logging")
    """Configure logging based on environment variables."""
    format = cli.env.vars.get("LOG_FORMAT") or "%(asctime)s - %(levelname)s - %(module)s - %(message)s\n"
    datefmt = cli.env.vars.get("LOG_DATE_FORMAT") or "%Y-%m-%d %H:%M:%S"

    log = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(SensitiveFormatter(format_str=format, datefmt_str=datefmt))
    log.addHandler(handler)
    if cli.env.vars.get("DEBUG") == 1:
        print("DEBUG")
        log.setLevel(logging.DEBUG)
    else:
        print("INFO")
        log.setLevel(level=logging.INFO)
    return log


log = configure_logging()
