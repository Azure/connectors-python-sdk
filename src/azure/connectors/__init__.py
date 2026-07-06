"""Azure Connectors package exports."""

try:
    from .github import GithubClient
except (ImportError, NameError):
    GithubClient = None  # type: ignore[assignment,misc]

try:
    from .slack import SlackClient
except (ImportError, NameError):
    SlackClient = None  # type: ignore[assignment,misc]

__all__ = ["GithubClient", "SlackClient"]
