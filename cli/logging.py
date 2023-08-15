import logging
from cli.env import secrets


class SensitiveFormatter(logging.Formatter):
    """Formatter that removes secrets from log messages."""

    @staticmethod
    def _filter(s):
        secrets_set = set(secrets.values())
        redacted = ' '.join([s.replace(secret, "*" * len(secret)) for secret in secrets_set])
        print("input", s)
        print("redacted", redacted)
        return redacted

    def format(self, record):
        original = logging.Formatter.format(self, record)
        return self._filter(original)


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
for handler in log.root.handlers:
    handler.setFormatter(SensitiveFormatter())
