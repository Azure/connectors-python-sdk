---
name: trigger-registration
description: 'Register Connector Gateway trigger configs for SDK-supported connectors. USE WHEN: setting up polling triggers (e.g., OnNewEmail, OnNewFile, OnUpdatedFile) that call back to an Azure Function when events occur, creating a Python Function App to receive trigger callbacks, or wiring post-deploy trigger config scripts. Covers function app scaffolding, trigger config creation, callback URL wiring, parameter discovery, and binary vs metadata payload handling. NOT FOR: connection setup (use connection-setup skill).'
---

# Connector Gateway Trigger Registration

Registers polling trigger configs on a Connector Gateway so that connector events (new email, new file, etc.) call back to your Azure Function endpoint. Also covers scaffolding a Python Function App to receive trigger callbacks.

## When to Use

- Developer needs a connector trigger (e.g., "when a new file is created in OneDrive")
- Developer has an existing Connector Gateway connection (use the `connection-setup` skill first if not)
- Developer needs to wire up the callback URL from a deployed Azure Function
- Developer needs to understand binary vs metadata trigger payload shapes

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Connector Gateway with a connected connector (see `connection-setup` skill)
- The Connector Gateway must have a **system-assigned managed identity** enabled (required for trigger callback authentication)
- Deployed Azure Function App with an HTTP trigger function to receive callbacks
- **Supported regions** for Connector Gateway: `brazilsouth`, `centraluseuap`, `eastus2euap`, `centralusstage`, `eastusstage`. Only the Connector Gateway `location` must be in a supported region; the Function App can be in any region.
- Python 3.10+ with the `azure-connectors` package installed

## Key Concepts

### Trigger Config vs Connection

Connections (managed by the `connection-setup` skill) authenticate your app to the connector API. Trigger configs tell the Connector Gateway to **poll** the connector for events and **POST callbacks** to your function when events occur.

```text
Connector Gateway
├── connections/
│   └── onedrive-test          ← auth + runtime URL (connection-setup skill)
└── triggerConfigs/
    └── onedrive-newfile       ← poll + callback config (THIS skill)
```

### Binary vs Metadata Triggers

Some connectors offer two variants of the same trigger:

| Variant | Example | Payload Shape | Body Field |
|---------|---------|---------------|------------|
| **File content (binary)** | `OnNewFileV2` | `{"body":"<base64-string>"}` | String — base64-encoded file bytes |
| **Properties only (metadata)** | `OnNewFilesV2` | `{"body":{"value":[{...}]}}` | Object — array of typed metadata items |

**Critical:** Both variants arrive with `Content-Type: application/json`. You cannot use content-type to distinguish them. Instead, parse the JSON and inspect whether `body` is a string or an object.

#### Identifying binary triggers

Binary triggers deliver raw file content as a base64-encoded string in the `body` field. Metadata triggers deliver structured data with a `body.value` array containing typed items.

Check the trigger operation name — triggers ending in a singular noun (e.g., `OnNewFile`, `OnUpdatedFile`) typically return binary content, while plural variants (e.g., `OnNewFiles`, `OnUpdatedFiles`) return metadata objects.

## Python Function App for Trigger Callbacks

### Scaffolding a New Project

Use `azd` with an HTTP trigger template to create a Python Function App that receives trigger callbacks:

1. **Initialize** with the Azure Functions Python quickstart:

   ```shell
   azd init -t functions-quickstart-python-http-azd
   ```

2. **Create an HTTP trigger function** to receive callbacks. The Connector Gateway POSTs trigger payloads to your function's HTTP endpoint.

3. **Install the SDK**:

   ```shell
   pip install azure-connectors
   ```

   Add to `requirements.txt`:

   ```text
   azure-connectors
   ```

4. **Build and deploy**:

   ```shell
   azd up
   ```

### Example: HTTP Trigger Function for Email Callbacks

Create an HTTP trigger function that receives Office 365 email trigger callbacks:

```python
import azure.functions as func
import json
import logging
from typing import Any

from azure.connectors.office365 import TriggerBatchResponseGraphClientReceiveMessage

app = func.FunctionApp()


@app.function_name(name="OnNewEmailReceived")
@app.route(route="triggers/email", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def on_new_email_received(req: func.HttpRequest) -> func.HttpResponse:
    """Handle Office 365 email trigger callbacks from Connector Gateway."""
    logging.info("Received email trigger callback")

    try:
        body = req.get_json()

        # Parse the trigger payload using the SDK's typed class
        payload = parse_trigger_payload(body, TriggerBatchResponseGraphClientReceiveMessage)

        if payload and payload.value:
            for email in payload.value:
                logging.info(f"Subject: {email.subject}, From: {email.from_}")

        return func.HttpResponse("OK", status_code=200)
    except Exception as e:
        logging.error(f"Error processing trigger callback: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)


def parse_trigger_payload(body: dict[str, Any], payload_type: type) -> Any:
    """Parse trigger callback body into typed payload."""
    if "body" in body and isinstance(body["body"], dict):
        # Metadata trigger - body contains structured data
        return payload_type(**body["body"]) if body["body"] else None
    return None
```

The callback URL for this function would be:

```text
POST https://<function-app-name>.azurewebsites.net/api/triggers/email?code=<function-key>
```

## Procedure

### Step 1: Get the Callback URL

Build the callback URL using your function's HTTP endpoint and function key:

```powershell
$resourceGroup = "<resource-group>"
$functionAppName = "<function-app-name>"
$functionRoute = "triggers/email"  # Your function's route

$functionKey = az functionapp keys list -g $resourceGroup -n $functionAppName --query "functionKeys.default" -o tsv
$callbackUrl = "https://$functionAppName.azurewebsites.net/api/$functionRoute?code=$functionKey"
```

> **Important:** The route must exactly match the `route` parameter in your `@app.route()` decorator.

### Step 2: Get Trigger Parameters

Each trigger operation requires specific parameters. Use the connector's list operations to discover folder IDs and other required values:

> **Note:** Listing folders requires a data-plane call to the connection runtime URL. If you skipped access policies in the `connection-setup` skill (trigger-only flow), you must first add a local-dev access policy (`connection-setup` Step 5) to avoid 403 errors.

```powershell
$runtimeUrl = "<connection-runtime-url>"  # from connection-setup skill Step 4

# OneDrive - list folders
az rest --method GET `
    --uri "$runtimeUrl/datasets/default/folders" `
    --resource "https://apihub.azure.com" -o json

# Office 365 - list mail folders
az rest --method GET `
    --uri "$runtimeUrl/Mail/Folders" `
    --resource "https://apihub.azure.com" -o json
```

### Step 3: Create Trigger Config

```powershell
$subscriptionId = "<subscription-id>"
$resourceGroup = "<resource-group>"
$gatewayName = "<gateway-name>"
$gwId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/connectorGateways/$gatewayName"

$triggerName = "<trigger-config-name>"   # e.g., "office365-newemail"
$connectionName = "<connection-name>"    # e.g., "office365-test"
$connectorName = "<connector-name>"      # e.g., "office365"
$operationName = "<operation-name>"      # e.g., "OnNewEmailV3"
```

Build and send the PUT request. **Use `Invoke-WebRequest`** (not `az rest`) because `az rest` silently swallows error responses from this API:

```powershell
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
            @{ name = "folderId"; value = "Inbox" }
        )
    }
} | ConvertTo-Json -Depth 4

$uri = "https://management.azure.com${gwId}/triggerConfigs/${triggerName}?api-version=2026-05-01-preview"
try {
    $response = Invoke-WebRequest -Uri $uri -Method PUT -Body $body `
        -ContentType "application/json" `
        -Headers @{ Authorization = "Bearer $token" }
    Write-Output "Status: $($response.StatusCode)"
} catch {
    Write-Output "Error: $($_.Exception.Response.StatusCode) $($_.Exception.Response.ReasonPhrase)"
    $_.ErrorDetails.Message
}
```

#### Alternative: Using az rest

```powershell
$bodyFile = [System.IO.Path]::GetTempFileName()
$body | Out-File -FilePath $bodyFile -Encoding utf8

az rest --method PUT --url $uri --body "@$bodyFile" --headers "Content-Type=application/json"
Remove-Item $bodyFile -ErrorAction SilentlyContinue
```

Expected: HTTP 201 Created.

### Step 4: Verify Trigger Config

```powershell
az rest --method GET `
    --uri "https://management.azure.com${gwId}/triggerConfigs/${triggerName}?api-version=2026-05-01-preview" `
    --query "properties.{operation:operationName, state:state, hasCallback:notificationDetails.callbackUrl!=null}" `
    -o table
```

Expected: `state = Enabled`, `hasCallback = True`.

### Step 5: List All Trigger Configs

```powershell
az rest --method GET `
    --uri "https://management.azure.com${gwId}/triggerConfigs?api-version=2026-05-01-preview" `
    --query "value[].{name:name, operation:properties.operationName, state:properties.state}" `
    -o table
```

### Step 6: Fire the Trigger

Create content in the watched location to trigger the callback:

```powershell
# Example: send yourself an email to fire OnNewEmailV3
# Or upload a file to OneDrive to fire OnNewFileV2
```

The Connector Gateway polls the connector every 1-5 minutes. After polling detects the new content, it POSTs the trigger payload to your callback URL.

### Step 7: Verify Callback Received

Check function app logs:

```powershell
az webapp log download -g $resourceGroup -n $functionAppName --log-file "$env:TEMP/func-logs.zip"
Expand-Archive -Path "$env:TEMP/func-logs.zip" -DestinationPath "$env:TEMP/func-logs" -Force
Get-ChildItem "$env:TEMP/func-logs" -Recurse -Filter "*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 3 |
    ForEach-Object { Select-String -Path $_.FullName -Pattern "trigger callback" }
```

## API Schema Reference

### TriggerConfig PUT Body

```json
{
  "properties": {
    "operationName": "OnNewEmailV3",
    "connectionDetails": {
      "connectorName": "office365",
      "connectionName": "office365-test"
    },
    "notificationDetails": {
      "callbackUrl": "https://my-func.azurewebsites.net/api/triggers/email?code=<function-key>",
      "httpMethod": "Post"
    },
    "parameters": [
      { "name": "folderId", "value": "Inbox" }
    ]
  }
}
```

### Property Names (Validated)

| Property | Notes |
|----------|-------|
| `properties.connectionDetails` | **Not** `connectionName` at top level |
| `properties.connectionDetails.connectorName` | Required — the API connector name |
| `properties.connectionDetails.connectionName` | Required — the connection resource name |
| `properties.notificationDetails.callbackUrl` | **Missing = trigger has no target** — trigger provisions but never calls back |
| `properties.notificationDetails.httpMethod` | `"Post"` |
| `parameters[].name` | **Not** `parameterName` |
| `parameters[].value` | String value |

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not find member 'connectionName'` | Used `connectionName` instead of `connectionDetails` | Use `connectionDetails` with nested `connectorName` + `connectionName` |
| `Could not find member 'callbackUrl'` | Put `callbackUrl` at properties level | Wrap in `notificationDetails` |
| `Could not find member 'parameterName'` | Used `parameterName` in parameter array | Use `name` |
| `Cannot deserialize... into ConnectorGatewayOperationsParameter[]` | Parameters as object, not array | Use `[{"name":"...","value":"..."}]` array |
| `missing required property 'folderId'` | Required trigger parameter not provided | Add to parameters array |
| Trigger provisions but never fires callback | Missing `notificationDetails` or empty `notificationDetails.callbackUrl` | Add `notificationDetails` with a non-empty `callbackUrl` and `httpMethod` |
| `az rest` PUT returns no output/error | `az rest` swallows non-2xx responses silently | Use `Invoke-WebRequest` instead for PUT operations |

## Handling Trigger Payloads in Python

### Binary Content Triggers (e.g., OnNewFileV2)

```python
import base64
import json
from typing import Any


def handle_binary_trigger(body: dict[str, Any]) -> bytes | None:
    """Handle binary trigger payload (e.g., OnNewFileV2)."""
    if "body" not in body:
        return None

    body_value = body["body"]

    if isinstance(body_value, str):
        # Binary trigger — body is base64-encoded file content.
        # NOTE: The base64 string may be wrapped in extra quotes
        # from the Logic Apps expression engine. Strip them.
        base64_content = body_value.strip('"')

        if base64_content:
            try:
                return base64.b64decode(base64_content)
            except Exception:
                # Invalid base64 payload
                return None

    return None
```

### Metadata Triggers (e.g., OnNewFilesV2, OnNewEmailV3)

```python
from dataclasses import dataclass
from typing import Any

from azure.connectors.office365 import TriggerBatchResponseGraphClientReceiveMessage


def handle_metadata_trigger(body: dict[str, Any]) -> list[Any]:
    """Handle metadata trigger payload (e.g., OnNewEmailV3)."""
    # Callback JSON shape: {"body":{"value":[{...item...}]}}
    if "body" not in body:
        return []

    body_value = body["body"]

    if isinstance(body_value, dict) and "value" in body_value:
        return body_value["value"]

    return []


# Using SDK typed payload classes
def handle_email_trigger(body: dict[str, Any]) -> TriggerBatchResponseGraphClientReceiveMessage | None:
    """Handle Office 365 email trigger with typed payload."""
    if "body" in body and isinstance(body["body"], dict):
        return TriggerBatchResponseGraphClientReceiveMessage(**body["body"])
    return None
```

### Detecting the Variant at Runtime

```python
from typing import Any


def detect_trigger_variant(body: dict[str, Any]) -> str:
    """Detect whether this is a binary or metadata trigger payload."""
    if "body" not in body:
        return "unknown"

    body_value = body["body"]

    if isinstance(body_value, str):
        # Binary content trigger (OnNewFileV2, OnUpdatedFileV2)
        return "binary"
    elif isinstance(body_value, dict):
        # Metadata trigger (OnNewFilesV2, OnUpdatedFilesV2, OnNewEmailV3)
        return "metadata"

    return "unknown"
```
```