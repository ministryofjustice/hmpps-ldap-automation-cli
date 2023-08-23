import logging
import cli.env


class SensitiveFormatter(logging.Formatter):
    """Formatter that removes secrets from log messages."""

    @staticmethod
    def _filter(s):
        secrets_set = set(cli.env.secrets.values())
        redacted = " ".join([s.replace(secret, "*" * len(secret)) for secret in secrets_set if secret is not None])
        return redacted

    def format(self, record):
        original = logging.Formatter.format(self, record)
        return self._filter(original)


if cli.env.vars.get("DEBUG") == 1:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
for handler in log.root.handlers:
    handler.setFormatter(SensitiveFormatter())
