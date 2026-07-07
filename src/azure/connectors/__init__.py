"""Azure Connectors package exports."""

try:
    from .azuremonitorlogs import AzuremonitorlogsClient
except (ImportError, NameError):
    AzuremonitorlogsClient = None  # type: ignore[assignment,misc]

try:
    from .docusign import DocusignClient
except (ImportError, NameError):
    DocusignClient = None  # type: ignore[assignment,misc]

try:
    from .github import GithubClient
except (ImportError, NameError):
    GithubClient = None  # type: ignore[assignment,misc]

try:
    from .jira import JiraClient
except (ImportError, NameError):
    JiraClient = None  # type: ignore[assignment,misc]

try:
    from .microsoftforms import MicrosoftformsClient
except (ImportError, NameError):
    MicrosoftformsClient = None  # type: ignore[assignment,misc]

try:
    from .powerbi import PowerbiClient
except (ImportError, NameError):
    PowerbiClient = None  # type: ignore[assignment,misc]

try:
    from .salesforce import SalesforceClient
except (ImportError, NameError):
    SalesforceClient = None  # type: ignore[assignment,misc]

try:
    from .shifts import ShiftsClient
except (ImportError, NameError):
    ShiftsClient = None  # type: ignore[assignment,misc]

try:
    from .slack import SlackClient
except (ImportError, NameError):
    SlackClient = None  # type: ignore[assignment,misc]

try:
    from .todo import TodoClient
except (ImportError, NameError):
    TodoClient = None  # type: ignore[assignment,misc]

__all__ = [
    "AzuremonitorlogsClient",
    "DocusignClient",
    "GithubClient",
    "JiraClient",
    "MicrosoftformsClient",
    "PowerbiClient",
    "SalesforceClient",
    "ShiftsClient",
    "SlackClient",
    "TodoClient",
]
