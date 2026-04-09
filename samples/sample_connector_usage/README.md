# Sample Connector Usage

This directory contains samples demonstrating how to use the Azure Workflows Connector SDK for Python with generated connector clients.

## Samples

### 1. Office 365 Connector (`sample_connector_usage_office365.py`)
Demonstrates Office 365 Outlook operations:
- Sending emails
- Managing calendar categories
- SDK runtime components
- Token provider usage
- Azure Functions integration
- Error handling patterns

**Run:**
```bash
python sample_connector_usage_office365.py
```

### 2. SharePoint Online Connector (`sample_connector_usage_sharepoint.py`)
Demonstrates SharePoint Online operations:
- List management (create, read, update, delete items)
- File operations (upload, download, metadata)
- OData query filtering
- Batch operations
- Common use cases (task management, document archiving)

**Run:**
```bash
python sample_sharepoint_usage_sharepoint.py
```

### 3. Kusto (Azure Data Explorer) Connector (`sample_connector_usage_kusto.py`)
Demonstrates Kusto/Azure Data Explorer operations:
- Running KQL queries (time-based, aggregations, joins)
- Control commands (schema inspection, admin tasks)
- Query visualization (charts, timecharts)
- Async command execution (long-running operations)
- Real-world use cases (monitoring, reporting, anomaly detection)
- KQL query patterns and best practices

**Run:**
```bash
python sample_connector_usage_kusto.py
```

## Overview

This sample shows:
- SDK runtime components (authentication, HTTP, base classes)
- Token provider usage patterns
- Generated client usage examples
- Integration with Azure Functions
- Async context manager patterns
- Error handling

## Prerequisites

1. **Python 3.10+** - Async/await support required
2. **Azure Workflows Connector SDK** - Install via pip:
   ```bash
   pip install <TBD>
   ```
3. **Generated connector code** - Use LogicAppsCompiler CLI (see below)

## Running the Sample

```bash
# From this directory
python sample_connector_usage_office365.py
```

The sample is informational - it prints usage patterns and examples without making actual API calls.

## Generating Connector Code

To use real connectors, generate client code using the LogicAppsCompiler CLI:

```bash
# Navigate to the BPM repository
cd c:\Users\victoriahall\Documents\repos\AzureUX-BPM

# Build the generator
dotnet build .\src\tools\CodefulSdkGenerator\LogicAppsCompiler.Cli -c Release

# Generate Python clients (e.g., Office365)
cd src\tools\CodefulSdkGenerator\LogicAppsCompiler.Cli\bin\Release
.\LogicAppsCompiler.exe "..\..\..\..\..\..\PythonSDK\src\azure_workflows_connectors_sdk\generated" --pythonDirectClient --connectors=office365,sharepointonline
```

See [PythonSDK/GENERATION.md](../../GENERATION.md) for complete documentation.

## Usage Pattern

After generating connector code:

```python
from azure_workflows_connectors_sdk.generated.office365_client import (
    Office365Client,
    ClientSendHtmlMessage,
)
from azure_workflows_connectors_sdk import ManagedIdentityTokenProvider

async def send_email():
    # Get connection runtime URL from Azure Portal
    connection_url = "https://..."
    token_provider = ManagedIdentityTokenProvider()
    
    async with Office365Client(connection_url, token_provider) as client:
        email = ClientSendHtmlMessage(
            to="recipient@example.com",
            subject="Hello from SDK",
            body="<p>Email body</p>",
        )
        await client.send_email_v2_async(email)
```

## Azure Functions Integration

Generated clients work seamlessly with Azure Functions:

```python
import azure.functions as func
from azure_workflows_connectors_sdk.generated.office365_client import (
    Office365Client,
    ClientSendHtmlMessage,
)
from azure_workflows_connectors_sdk import ManagedIdentityTokenProvider

app = func.FunctionApp()

@app.route(route='send-email', auth_level=func.AuthLevel.FUNCTION)
async def send_email(req: func.HttpRequest) -> func.HttpResponse:
    connection_url = os.environ['CONNECTION_RUNTIME_URL']
    token_provider = ManagedIdentityTokenProvider()
    
    async with Office365Client(connection_url, token_provider) as client:
        email = ClientSendHtmlMessage(
            to=req.params.get('to'),
            subject='Hello',
            body='<p>Sent from Azure Function!</p>',
        )
        await client.send_email_v2_async(email)
    
    return func.HttpResponse('Email sent!', status_code=200)
```

## Error Handling

The SDK provides structured error handling:

```python
from azure_workflows_connectors_sdk import ConnectorException
from azure_workflows_connectors_sdk.generated.office365_client import (
    Office365Client,
    ClientSendHtmlMessage,
)

try:
    async with Office365Client(url, token_provider) as client:
        email = ClientSendHtmlMessage(
            to="recipient@example.com",
            subject="Test",
            body="<p>Test email</p>",
        )
        await client.send_email_v2_async(email)
except ConnectorException as ex:
    print(f"Connector error: {ex.message}")
    print(f"Status code: {ex.status_code}")
    print(f"Error body: {ex.error_body}")
```

## Available Connectors

The generator supports ~1,500 Azure managed connectors. Popular ones include:

**Microsoft 365 & Office:**
- `office365` - Office 365 Outlook
- `teams` - Microsoft Teams
- `sharepointonline` - SharePoint Online
- `onedriveforbusiness` - OneDrive for Business

**Cloud Storage:**
- `azureblob` - Azure Blob Storage
- `googledrive` - Google Drive
- `dropbox` - Dropbox

**Databases:**
- `sql` - SQL Server
- `dataverse` - Microsoft Dataverse
- `cosmosdb` - Azure Cosmos DB

See [GENERATION.md](../../GENERATION.md) for the complete list.

## Next Steps

1. Generate connector code for your needed connectors
2. Install the SDK: `pip install <TBD>`
3. Get connection runtime URL from Azure Portal
4. Use typed clients in your application
5. Deploy to Azure Functions or run locally

## Reference

- Python SDK: [PythonSDK/src/azure_workflows_connectors_sdk](../../src/azure_workflows_connectors_sdk)
- Generation Guide: [GENERATION.md](../../GENERATION.md)
- .NET Sample: [DotnetSDK/samples/SampleConnectorUsage](../../../DotnetSDK/samples/SampleConnectorUsage)
