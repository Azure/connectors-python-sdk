---
name: trigger-registration
description: 'Register Connector Namespace trigger configs for Azure connectors and scaffold Azure Functions to receive trigger callbacks. USE WHEN: setting up polling triggers (e.g., OnNewEmail, OnNewFile, OnUpdatedFile) that call back to an Azure Function, scaffolding a Function App project with ConnectorTrigger binding, wiring callback URLs, or troubleshooting trigger configs. Covers both typed SDK payloads and raw JSON generic triggers. NOT FOR: connection setup (use connection-setup skill).'
---

# Connector Namespace Trigger Registration

Registers polling trigger configs on a Connector Namespace so that connector events (new email, new file, etc.) call back to your application endpoint. Covers scaffolding a Python Function App with the ConnectorTrigger extension binding.

## When to Use

- Developer needs a connector trigger (e.g., "when a new email arrives in Office365")
- Developer has an existing Connector Namespace connection (use the `connection-setup` skill first if not)
- Developer needs to scaffold a Python Function App with ConnectorTrigger in Azure Functions
- Developer needs to wire the callback URL from a deployed or local Function App
- Developer needs to understand which typed payload to use for a given trigger operation

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Connector Namespace with a connected connector (see `connection-setup` skill)
- The Connector Namespace must have a **system-assigned managed identity** enabled
- **Supported regions** for Connector Namespace: `westcentralus`
- A [supported Python version for Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/supported-languages?tabs=isolated-process%2Cv4&pivots=programming-language-python#languages-by-runtime-version) with the `azure-connectors` package installed

## Key Concepts

### ConnectorTrigger Extension Binding

### Python Decorator and Package Rules

Use this decision logic when scaffolding a Python connector trigger function:

1. **Choose decorator by Python version:**
   - Python 3.13 → `@app.connector_trigger`
   - Python < 3.13 → `@app.generic_trigger(type="connectorTrigger")`

2. **Choose packages by trigger operation:**
   - Office 365 `OnNewEmail` → add `azurefunctions-extensions-connectors` (imports `azure-connectors` automatically)
   - Any other connector with a typed SDK model → add `azure-connectors`, use typed class as parameter type
   - No typed model available → use `str` as parameter type, no extra package needed beyond `azure-functions`

3. **Base package:** `azure-functions` (use `>=2.2.0b4` only when using `@app.connector_trigger` decorator)

### Extension Webhook Endpoint

The ConnectorTrigger extension registers a webhook route on the Function App:

```text
POST /runtime/webhooks/connector?functionName={FunctionName}&code={connector_extension_key}
```

- `functionName` must exactly match the `@app.function_name(name="...")` value
- `connector_extension` is a system key auto-generated when the extension loads
- Locally (`func start`), the system key is not enforced

### Trigger Config vs Connection

```text
Connector Namespace
├── connections/
│   └── office365-conn         ← auth + runtime URL (connection-setup skill)
└── triggerConfigs/
    └── onnewemail-trigger     ← poll + callback config (THIS skill)
```

## Scaffolding a Python Function App

### 1. Initialize with azd

```shell
azd init -t functions-quickstart-python-http-azd
```

### 2. Update host.json for preview extension bundle

```json
{
    "version": "2.0",
    "extensionBundle": {
        "id": "Microsoft.Azure.Functions.ExtensionBundle.Preview",
        "version": "[4.*, 5.0.0)"
    }
}
```

### 3. Install packages

Add to `requirements.txt` (include packages based on your approach):

```text
# >=2.2.0b4 required for @app.connector_trigger decorator (Python 3.13+ only), no pinning required for generic trigger approaches
azure-functions>=2.2.0b4

# Currently only supports Office 365 OnNewEmail operation
azurefunctions-extensions-connectors

# Required for @app.generic_trigger with typed SDK models or str payloads, don't include if using azurefunctions-extensions-connectors 
azure-connectors
```

### 4. Create a ConnectorTrigger function

#### With typed SDK payload (Office 365 email example)

```python
import azure.functions as func
import azurefunctions.extensions.connectors.office365 as office365
import logging
from typing import List

app = func.FunctionApp()


@app.function_name(name="OnNewEmail")
@app.connector_trigger(arg_name="emails")
def on_new_email(emails: List[office365.ClientReceiveMessage]) -> None:
    logging.info("OnNewEmail trigger received")

    for email in emails:
        logging.info(f"Subject: {email.subject}")
        logging.info(f"From: {email.from_}")
```

#### With connector trigger and raw JSON (when no typed SDK model exists)

```python
import azure.functions as func
import json
import logging

app = func.FunctionApp()


@app.function_name(name="OnNewFile")
@app.connector_trigger(arg_name="payload")
def on_new_file(payload: str) -> None:
    logging.info("OnNewFile trigger received")

    data = json.loads(payload)
    body = data.get("body", {})

    if isinstance(body, dict) and "value" in body:
        # Metadata trigger — batch of items
        for item in body["value"]:
            logging.info(f"File: {item.get('name')}")
    elif isinstance(body, str):
        # Binary trigger — base64-encoded file content
        import base64
        content = base64.b64decode(body)
        logging.info(f"Received file content: {len(content)} bytes")
```

#### With generic trigger (when using Python <= 3.12)

```python
import azure.functions as func
import json
import logging

app = func.FunctionApp()


@app.function_name(name="OnNewFile")
@app.generic_trigger(arg_name="payload", type="connectorTrigger")
def on_new_file(payload: str) -> None:
...
```

### 5. Run locally

Start Azurite (required for `AzureWebJobsStorage`):

```bash
npx azurite
```

Verify `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

Start the Function App:

```shell
func start
```

The extension logs the webhook endpoint at startup:

```
Connector endpoint: http://localhost:7071/runtime/webhooks/connector
```

## Registering a Trigger Config

### Step 1: Get the Callback URL

#### Deployed Function App

```powershell
$resourceGroup = "<resource-group>"
$functionAppName = "<function-app-name>"
$functionName = "<function-name>"  # must match @app.function_name(name="...")

$connectorExtensionKey = az functionapp keys list -g $resourceGroup -n $functionAppName --query "systemKeys.connector_extension" -o tsv
$callbackUrl = "https://$functionAppName.azurewebsites.net/runtime/webhooks/connector?functionName=$functionName&code=$connectorExtensionKey"
```

#### Local development (with dev tunnel)

```powershell
$tunnelUrl = "<your-tunnel-url>"  # e.g., https://<id>-7071.uks1.devtunnels.ms
$functionName = "<function-name>"
$callbackUrl = "$tunnelUrl/runtime/webhooks/connector?functionName=$functionName"
```

### Step 2: Create Trigger Config

```powershell
$subscriptionId = "<subscription-id>"
$resourceGroup = "<resource-group>"
$namespaceName = "<namespace-name>"
$nsId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/connectorGateways/$namespaceName"

$triggerName = "<trigger-config-name>"   # e.g., "onnewemail-trigger"
$connectionName = "<connection-name>"    # e.g., "office365-conn"
$connectorName = "<connector-name>"      # e.g., "office365"
$operationName = "<operation-name>"      # e.g., "OnNewEmailV3"

$token = az account get-access-token `
    --resource "https://management.core.windows.net/" `
    --query "accessToken" -o tsv

$body = @{
    properties = @{
        operationName = $operationName
        connectionDetails = @{
            connectorName = $connectorName
            connectionName = $connectionName
        }
        notificationDetails = @{
            callbackUrl = $callbackUrl
            httpMethod = "Post"
        }
        parameters = @(
            # Office 365 OnNewEmailV3:
            # @{ name = "folderPath"; value = "Inbox" }

            # OneDrive for Business OnNewFile:
            # @{ name = "folderId"; value = "root" }
        )
    }
} | ConvertTo-Json -Depth 4

$uri = "https://management.azure.com${nsId}/triggerConfigs/${triggerName}?api-version=2026-05-01-preview"
try {
    $response = Invoke-WebRequest -Uri $uri -Method PUT -Body $body `
        -ContentType "application/json" `
        -Headers @{ Authorization = "Bearer $token" }
    Write-Output "Status: $($response.StatusCode)"
} catch {
    Write-Output "Error: $($_.Exception.Response.StatusCode)"
    $_.ErrorDetails.Message
}
```

### Step 3: Verify Trigger Config

```powershell
az rest --method GET `
    --uri "https://management.azure.com${nsId}/triggerConfigs/${triggerName}?api-version=2026-05-01-preview" `
    --query "properties.{operation:operationName, state:state, callback:notificationDetails.callbackUrl}" `
    -o table
```

Expected: `state = Enabled`.

### Step 4: Test the Trigger

Trigger the connector event (e.g., send an email, upload a file). The Connector Namespace polls every 1-5 minutes.

Watch Function App logs:

```powershell
func start  # local
# or for deployed:
az functionapp log tail -g $resourceGroup -n $functionAppName
```

## Using the SDK for Actions (Beyond Triggers)

The `azure-connectors` package provides typed async clients for calling connector actions directly from any Python application — Azure Functions, Flask, FastAPI, Django, scripts, etc.

### Example: Send an email

```python
import asyncio
from azure.connectors.office365 import Office365Client
from azure.connectors.sdk import ManagedIdentityTokenProvider

async def main():
    # Connection runtime URL from Connector Namespace
    connection_url = "https://..."
    token_provider = ManagedIdentityTokenProvider()

    async with Office365Client(connection_url, token_provider) as client:
        await client.send_email_async(
            to="recipient@example.com",
            subject="Hello from Python SDK",
            body="<p>Sent from any Python app!</p>",
        )

asyncio.run(main())
```

### Example: List SharePoint items

```python
from azure.connectors.sharepointonline import SharepointonlineClient

async def list_items():
    async with SharepointonlineClient(connection_url, token_provider) as client:
        items = await client.get_items_async(
            dataset="https://contoso.sharepoint.com/sites/MySite",
            table="MyList"
        )
        for item in items.get("value", []):
            print(f"Item: {item.get('Title')}")
```

### Example: List Teams

```python
from azure.connectors.teams import TeamsClient

async def list_teams():
    async with TeamsClient(connection_url, token_provider) as client:
        teams = await client.get_all_teams_async()
        for team in teams.get("value", []):
            print(f"Team: {team.get('displayName')}")
```

### Authentication Options

```python
from azure.connectors.sdk import ManagedIdentityTokenProvider, ConnectionStringTokenProvider

# System-assigned managed identity (recommended for Azure)
token_provider = ManagedIdentityTokenProvider()

# User-assigned managed identity
token_provider = ManagedIdentityTokenProvider(client_id="your-client-id")

# Azure Identity credentials (DefaultAzureCredential, AzureCliCredential, etc.)
from azure.identity.aio import DefaultAzureCredential
credential = DefaultAzureCredential()
client = Office365Client(connection_url, credential)
```

### Validated Connectors

| Connector | Package | Status |
|-----------|---------|--------|
| Office 365 Outlook | `azure.connectors.office365` | ✅ Complete |
| SharePoint Online | `azure.connectors.sharepointonline` | ✅ Complete |
| Microsoft Teams | `azure.connectors.teams` | ✅ Complete |
| Azure Data Explorer | `azure.connectors.kusto` | ✅ Complete |
| MS Graph Groups & Users | `azure.connectors.msgraphgroupsanduser` | ✅ Complete |
| Office 365 Users | `azure.connectors.office365users` | ✅ Complete |
| Azure Blob Storage | `azure.connectors.azureblob` | ✅ Complete |
| IBM MQ | `azure.connectors.mq` | ✅ Complete |

> All SDKs support generating clients for any of the 1,000+ Azure managed connectors.

## Trigger Payload Shapes

The Connector Namespace delivers callbacks in two shapes depending on the connector's `splitOn` setting:

| Shape | JSON Structure | When |
|-------|---------------|------|
| Batch | `{"body": {"value": [...items...]}}` | splitOn disabled (default) |
| Single-item | `{"body": {...item properties...}}` | splitOn enabled |

The SDK's `TriggerCallbackPayload.from_json()` and `TriggerCallbackBody.from_dict()` methods normalize both shapes into a list, so consumers always iterate:

```python
from azure.connectors.sdk import TriggerCallbackPayload

payload = TriggerCallbackPayload.from_json(raw_json)
for item in payload.body.value:
    print(item)
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not find member 'connectionName'` | Used `connectionName` at top level | Wrap in `connectionDetails` object |
| `Could not find member 'callbackUrl'` | Put `callbackUrl` at properties level | Wrap in `notificationDetails` object |
| `Could not find member 'parameterName'` | Used `parameterName` in params array | Use `name` field instead |
| Trigger provisions but never fires | Missing `notificationDetails` or empty `callbackUrl` | Ensure `notificationDetails.callbackUrl` is set |
| `az rest` PUT returns no output | `az rest` swallows non-2xx responses | Use `Invoke-WebRequest` for PUT operations |

## Reference

For a complete mapping of trigger operations to function signatures across .NET, Python, and TypeScript, see [Operations to Functions Signature Match](https://github.com/Azure/azure-functions-connector-extension/blob/main/docs/operations-functions-match.md).
