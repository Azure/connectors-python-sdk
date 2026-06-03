[![CI](https://dev.azure.com/azfunc/public/_apis/build/status%2Fazure%2Fconnectors-python-sdk%2Fpython-connectors.public?repoName=Azure%2Fconnectors-python-sdk&branchName=main)](https://dev.azure.com/azfunc/public/_build/latest?definitionId=1724&repoName=Azure%2Fconnectors-python-sdk&branchName=main)
[![PyPI version](https://badge.fury.io/py/azure-connectors.svg)](https://badge.fury.io/py/azure-connectors)
[![Python versions](https://img.shields.io/pypi/pyversions/azure-connectors.svg)](https://pypi.org/project/azure-connectors/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Azure Connectors Python SDK

Type-safe Python clients for [Azure connectors](https://learn.microsoft.com/connectors/connector-reference/) — call Office 365, SharePoint, Teams, Dataverse, and 1,000+ connectors directly from Azure Functions and other Python apps.

> [!CAUTION]
> **Early Preview — Not for Production Use**
>
> This SDK is currently in early preview and is under active development. It is intended for evaluation, experimentation, and feedback purposes only.
>
> - **Do not use this SDK in production environments.**
> - **Breaking changes should be expected** across APIs, data models, and behavior in future releases.
> - Features may be added, modified, or removed without prior notice.
>
> We welcome feedback and contributions — please [open an issue](https://github.com/Azure/connectors-python-sdk/issues) with questions, suggestions, or bug reports.

## Why This SDK?

Azure provides a rich ecosystem of [managed connectors](https://learn.microsoft.com/connectors/connector-reference/) that bridge your code to SaaS services, PaaS resources, and on-premises systems. Originally powering Azure Logic Apps and Power Automate, these connectors are now available as **standalone, strongly-typed Python clients** for any Python application — no workflow service required.

- **Async/await native** — Built on `aiohttp` with full async support for modern Python applications
- **Type-safe operations** — Generated async methods with type hints and comprehensive docstrings
- **Built-in authentication** — Managed identity, Azure Identity, and API key token providers
- **Resilient HTTP** — Configurable retry policies with exponential backoff for transient failures
- **1,000+ connectors** — Any Azure managed connector available via API Hub can be generated

> **Note:** This is the Python SDK. A [.NET SDK](https://github.com/Azure/Connectors-NET-SDK) is also available. Node.js and Java SDKs are planned in collaboration with the Azure Functions team.

## How It Works

```text
┌─────────────────────────────────────┐
│  Your Azure Function / Python App   │
│                                     │
│  async with Office365Client(...):   │
│      await client.send_email(...)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Generated Connector Clients       │
│   (office365.py, teams.py, etc.)    │
│                                     │
│  • Typed async methods per action   │
│  • Dataclass models from Swagger    │
│  • Docstrings from connector meta   │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│   Azure Connectors Python SDK       │
│   azure.connectors.sdk              │
│                                     │
│  • ManagedIdentityTokenProvider     │
│  • ConnectorHttpClient + retry      │
│  • ConnectorClientBase              │
└─────────────────────────────────────┘
```

## Installation

Install from PyPI:

```bash
pip install azure-connectors
```

Or install with development dependencies:

```bash
pip install azure-connectors[dev]
```

## Quick Start

### Example: Send an email with Office 365

```python
import asyncio
from azure.connectors.office365 import Office365Client
from azure.connectors.sdk import ManagedIdentityTokenProvider

async def send_email_example():
    # Connection runtime URL from Azure Portal
    connection_url = "https://example.azure.com/connections/office365"
    
    # Use managed identity for authentication
    token_provider = ManagedIdentityTokenProvider()
    
    # Create client and send email
    async with Office365Client(connection_url, token_provider) as client:
        await client.send_email_v2_async(
            to="recipient@example.com",
            subject="Hello from Python SDK",
            body="<p>This email was sent using the Azure Connectors Python SDK!</p>",
            from_address="sender@example.com"
        )
    
    print("Email sent successfully!")

# Run the async function
asyncio.run(send_email_example())
```

### Example: List SharePoint items

```python
from azure.connectors.sharepointonline import SharepointonlineClient

async def list_sharepoint_items():
    connection_url = "https://example.azure.com/connections/sharepointonline"
    
    async with SharepointonlineClient(connection_url) as client:
        # Get all items from a SharePoint list
        items = await client.get_items_async(
            dataset="https://contoso.sharepoint.com/sites/MySite",
            table="MyList"
        )
        
        for item in items.get("value", []):
            print(f"Item: {item.get('Title')}")

asyncio.run(list_sharepoint_items())
```

### Example: Post a Teams message

```python
from azure.connectors.teams import TeamsClient

async def post_teams_message():
    connection_url = "https://example.azure.com/connections/teams"
    
    async with TeamsClient(connection_url) as client:
        await client.post_message_to_conversation_async(
            group_id="team-group-id",
            channel_id="19:channel-id",
            body_content="Hello from Python!",
            body_content_type="text"
        )
    
    print("Message posted to Teams!")

asyncio.run(post_teams_message())
```

## Validated Connectors

The following connectors have been generated and validated with comprehensive test coverage:

| Connector | Package | Status | Coverage | Tests |
|-----------|---------|--------|----------|-------|
| **Azure AD** | `azure.connectors.azuread` | ✅ Complete | 🔄 SDK Generated | 35 tests |
| **Azure Blob Storage** | `azure.connectors.azureblob` | ✅ Complete | ✅ E2E Validated | 52 tests |
| **Azure Cosmos DB** | `azure.connectors.documentdb` | ✅ Complete | 🔄 SDK Generated | 46 tests |
| **Azure Data Explorer** | `azure.connectors.kusto` | ✅ Complete | ✅ E2E Validated | 37 tests |
| **Azure Event Grid** | `azure.connectors.azureeventgrid` | ✅ Complete | 🔄 SDK Generated | 25 tests |
| **Azure Event Hubs** | `azure.connectors.eventhubs` | ✅ Complete | 🔄 SDK Generated | 30 tests |
| **Azure Queues** | `azure.connectors.azurequeues` | ✅ Complete | 🔄 SDK Generated | 34 tests |
| **Azure Tables** | `azure.connectors.azuretables` | ✅ Complete | 🔄 SDK Generated | 43 tests |
| **Excel Online (Business)** | `azure.connectors.excelonlinebusiness` | ✅ Complete | 🔄 SDK Generated | 37 tests |
| **IBM MQ** | `azure.connectors.mq` | ✅ Complete | ✅ E2E Validated | 30 tests |
| **Microsoft Graph** | `azure.connectors.msgraphgroupsanduser` | ✅ Complete | ✅ E2E Validated | 46 tests |
| **Microsoft Teams** | `azure.connectors.teams` | ✅ Complete | ✅ E2E Validated | 27 tests |
| **Office 365 Outlook** | `azure.connectors.office365` | ✅ Complete | ✅ E2E Validated | 41 tests |
| **Office 365 Users** | `azure.connectors.office365users` | ✅ Complete | ✅ E2E Validated | 40 tests |
| **OneDrive for Business** | `azure.connectors.onedrive` | ✅ Complete | 🔄 SDK Generated | 41 tests |
| **Outlook.com** | `azure.connectors.outlook` | ✅ Complete | 🔄 SDK Generated | 42 tests |
| **Service Bus** | `azure.connectors.servicebus` | ✅ Complete | 🔄 SDK Generated | 45 tests |
| **SharePoint Online** | `azure.connectors.sharepointonline` | ✅ Complete | ✅ E2E Validated | 44 tests |
| **SMTP** | `azure.connectors.smtp` | ✅ Complete | 🔄 SDK Generated | 27 tests |
| **Windows Defender ATP** | `azure.connectors.wdatp` | ✅ Complete | 🔄 SDK Generated | 40 tests |
| **Word Online (Business)** | `azure.connectors.wordonlinebusiness` | ✅ Complete | 🔄 SDK Generated | 30 tests |

**Total:** 716 connector tests + 110 SDK component tests

See [ROADMAP.md](ROADMAP.md) for planned connector additions and [tests/README.md](tests/README.md) for detailed test coverage.

## Authentication

The SDK supports multiple authentication methods:

### Managed Identity (Recommended for Azure)

```python
from azure.connectors.sdk import ManagedIdentityTokenProvider

# System-assigned managed identity
token_provider = ManagedIdentityTokenProvider()

# User-assigned managed identity
token_provider = ManagedIdentityTokenProvider(client_id="your-client-id")
```

### Azure Identity Credentials

```python
from azure.identity.aio import DefaultAzureCredential
from azure.connectors.office365 import Office365Client

# Use any Azure Identity credential directly
credential = DefaultAzureCredential()
client = Office365Client(connection_url, credential)
```

### Connection String / API Key

```python
from azure.connectors.sdk import ConnectionStringTokenProvider

token_provider = ConnectionStringTokenProvider("your-api-key")
```

## Configuration Options

Customize client behavior with `ConnectorClientOptions`:

```python
from azure.connectors.sdk import ConnectorClientOptions

options = ConnectorClientOptions(
    timeout_seconds=60.0,              # Request timeout
    max_retry_attempts=5,              # Max retry count
    use_exponential_backoff=True,      # Exponential backoff
    initial_retry_delay_seconds=1.0    # Initial retry delay
)

client = Office365Client(connection_url, token_provider, options)
```

## Project Structure

```text
azure-connectors/
├── src/azure/connectors/
│   ├── sdk/                    # Core SDK infrastructure
│   │   ├── authentication.py   # Token providers
│   │   ├── client_base.py      # Base connector client
│   │   ├── http_client.py      # HTTP client with retry
│   │   ├── options.py          # Configuration options
│   │   └── exceptions.py       # Exception types
│   ├── office365.py            # Office 365 generated client
│   ├── sharepointonline.py     # SharePoint generated client
│   ├── teams.py                # Teams generated client
│   ├── kusto.py                # Kusto generated client
│   └── msgraph.py              # MS Graph generated client
├── tests/                      # Comprehensive test suite
├── samples/                    # Usage examples
└── docs/                       # Additional documentation
```

## SDK-Type Bindings for Azure Functions

The SDK supports **SDK-type bindings** for Python Function apps, allowing functions to bind to and return rich, strongly-typed objects instead of raw JSON payloads. This enables cleaner code and better IDE support with type hints.

### Example: Parsing Email Messages

Use the `from_json` class method to convert JSON payloads into typed objects:

```python
from azure.connectors.office365 import ClientReceiveMessage

# Parse JSON payload into a list of typed email message objects
messages = ClientReceiveMessage.from_json(payload)

for message in messages:
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")
    print(f"Importance: {message.importance}")  # 0=Low, 1=Normal, 2=High
```

The `from_json` method handles:

- JSON string or dictionary input
- Nested `body.value` payload structure
- Field name conversion (camelCase → snake_case)
- Type conversion (e.g., importance string → int)
- Attachment parsing

> **Note:** The `from_json` method is **not auto-generated** by the SDK code generator. See [docs/sdk-type-bindings.md](docs/sdk-type-bindings.md) for implementation details and how to add support for new types.

This feature is particularly useful when building Azure Functions that process connector webhook payloads or trigger data.

## Related Projects

- **[Azure Functions Connector Extension](https://github.com/Azure/azure-functions-connector-extension)**  - An Azure Functions trigger extension for receiving webhook callbacks from Connector Namespace managed connectors
- **[Connectors .NET SDK](https://github.com/Azure/Connectors-NET-SDK)** — .NET implementation of this SDK
- **[Connectors Node.js SDK](https://github.com/Azure/connectors-nodejs-sdk)** — Node.js implementation of this SDK

## Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions provided by the bot.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Support

For issues and questions:

- 🐛 **Bug reports:** [File an issue](https://github.com/Azure/Connectors-Python-SDK/issues)
- 📚 **Documentation:** See [docs/](docs/) folder

See [SUPPORT.md](SUPPORT.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
