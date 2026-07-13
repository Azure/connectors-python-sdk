---
name: connection-setup
description: 'Create and configure Connector Namespace connections for the Azure Connectors Python SDK. USE WHEN: setting up a new connector connection, creating a Connector Namespace, authorizing OAuth consent, adding access policies, or configuring local.settings.json / app settings. Covers Office365, SharePoint, Teams, and any Microsoft.Web/connections connector. Works with Azure Functions, Flask, FastAPI, Django, or any Python app using the SDK. NOT FOR: trigger registration (use trigger-registration skill), or code generation.'
---

# Connector Namespace Connection Setup

Automates the end-to-end connection lifecycle for SDK-supported connectors. Connections created here can be used by any Python app via the `azure-connectors` package — Azure Functions, Flask, FastAPI, Django, scripts, etc.

## When to Use

- Developer needs a new connector connection for local dev or a deployed compute host
- Developer needs to authorize (OAuth consent) a connection
- Developer needs to wire connection URLs into `local.settings.json` or deployed app settings
- Developer needs to grant access policies (CLI identity for local, managed identity for deployed)

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Target subscription and resource group known
- For deployed scenarios: compute host (e.g., Function App, App Service) with managed identity enabled
- **Supported regions** for Connector Namespace: `brazilsouth`, `centraluseuap`, `eastus2euap`, `centralusstage`, `eastusstage`. Only the Connector Namespace `location` must be in a supported region; the resource group and Function App can be in any region.

## Procedure

### Step 1: Create or Select Connector Namespace

Check for an existing Connector Namespace in the resource group:

```powershell
$subscriptionId = "<subscription-id>"
$resourceGroup = "<resource-group>"

az rest --method GET `
    --uri "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/connectorGateways?api-version=2026-05-01-preview" `
    -o json | ConvertFrom-Json | Select-Object -ExpandProperty value | Select-Object name
```

If none exists, create one:

```powershell
$connectorNamespace= "<connector-namespace>"
$location = "<azure-region>"

$gwBody = "{`"location`":`"$location`",`"identity`":{`"type`":`"SystemAssigned`"},`"properties`":{}}"
$tempFile = Join-Path $env:TEMP "gw-body.json"
[System.IO.File]::WriteAllText($tempFile, $gwBody)
az rest --method PUT `
    --uri "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/connectorGateways/$connectorNamespace?api-version=2026-05-01-preview" `
    --body "@$tempFile" --headers "Content-Type=application/json" -o json
Remove-Item $tempFile -ErrorAction SilentlyContinue
```

> **Important:** The Connector Namespace must have a managed identity enabled (`SystemAssigned`) for trigger callback authentication. If the Connector Namespace was created without an identity, update it:
>
> ```powershell
> $gwBody = "{`"location`":`"$location`",`"identity`":{`"type`":`"SystemAssigned`"},`"properties`":{}}"
> $tempFile = Join-Path $env:TEMP "gw-identity.json"
> [System.IO.File]::WriteAllText($tempFile, $gwBody)
> az rest --method PUT `
>     --uri "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/connectorGateways/$connectorNamespace?api-version=2026-05-01-preview" `
>     --body "@$tempFile" --headers "Content-Type=application/json" -o json
> Remove-Item $tempFile -ErrorAction SilentlyContinue
> ```

### Step 2: Create Connection

Supported SDK connector names: `arm`, `azureautomation`, `azuredatafactory`, `azuredigitaltwins`, `azuremonitorlogs`, `azuread`, `azureblob`, `box`, `azurequeues`, `azuretables`, `azurevm`, `commondataservice`, `documentdb`, `dropbox`, `docusign`, `eventhubs`, `excelonline`, `excelonlinebusiness`, `ftp`, `github`, `googlecalendar`, `googledrive`, `googletasks`, `jira`, `keyvault`, `kusto`, `microsoftbookings`, `microsoftforms`, `mq`, `msgraphgroupsanduser`, `office365`, `office365groups`, `office365groupsmail`, `office365users`, `onedrive`, `onedriveforbusiness`, `onenote`, `outlook`, `planner`, `powerbi`, `rss`, `salesforce`, `servicebus`, `sharepointonline`, `shifts`, `slack`, `smtp`, `teams`, `todo`, `wdatp`, `wordonlinebusiness`, `yammer` (and any `Microsoft.Web/connections` connector name).

```powershell
$connectorName = "<connector-name>"      # e.g., "azureblob", "kusto", "mq", "msgraphgroupsanduser", "office365", "office365users", "sharepointonline", "teams"
$connectionName = "<connection-name>"    # e.g., "office365-test", "sharepoint-test"

$gwId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Web/connectorGateways/$connectorNamespace"
$connBody = "{`"properties`":{`"connectorName`":`"$connectorName`"}}"
$tempFile = Join-Path $env:TEMP "conn-body.json"
[System.IO.File]::WriteAllText($tempFile, $connBody)
az rest --method PUT `
    --uri "https://management.azure.com${gwId}/connections/${connectionName}?api-version=2026-05-01-preview" `
    --body "@$tempFile" --headers "Content-Type=application/json" -o json | ConvertFrom-Json | Select-Object name, @{n='status';e={$_.properties.statuses[0].status}}
Remove-Item $tempFile -ErrorAction SilentlyContinue
```

The connection starts in **Error** state (unauthenticated). Proceed to Step 3.

### Step 3: OAuth Consent (In-Browser)

Retrieve the consent link and open it in the default browser — no portal needed:

```powershell
$consentBody = '{"parameters":[{"redirectUrl":"https://portal.azure.com","parameterName":"token"}]}'
$tempFile = Join-Path $env:TEMP "consent-body.json"
[System.IO.File]::WriteAllText($tempFile, $consentBody)
$result = az rest --method POST `
    --uri "https://management.azure.com${gwId}/connections/${connectionName}/listConsentLinks?api-version=2026-05-01-preview" `
    --body "@$tempFile" --headers "Content-Type=application/json" -o json | ConvertFrom-Json
Remove-Item $tempFile -ErrorAction SilentlyContinue

$link = $result.value[0].link
Start-Process $link
```

The user completes OAuth in the browser. After consent, verify:

```powershell
az rest --method GET `
    --uri "https://management.azure.com${gwId}/connections/${connectionName}?api-version=2026-05-01-preview" `
    -o json | ConvertFrom-Json | Select-Object @{n='status';e={$_.properties.statuses[0].status}}
```

Expected: `Connected`.

### Step 4: Get Connection Runtime URL

```powershell
$conn = az rest --method GET `
    --uri "https://management.azure.com${gwId}/connections/${connectionName}?api-version=2026-05-01-preview" `
    -o json | ConvertFrom-Json
$runtimeUrl = $conn.properties.connectionRuntimeUrl
Write-Output "Runtime URL: $runtimeUrl"
```

### Step 5: Add Access Policies

> **Note:** Access policies control which identities can call the connection's runtime URL for connector **actions** (e.g., send email, list files). For **trigger-only** scenarios, the Connector Namespace polls server-side and does not need an access policy on the connection. Skip this step if your function only receives trigger callbacks and does not call connector actions at runtime.

#### For local development (Azure CLI identity)

```powershell
$userObjectId = az ad signed-in-user show --query "id" -o tsv
$tenantId = az account show --query "tenantId" -o tsv

$policyBody = "{`"properties`":{`"principal`":{`"type`":`"ActiveDirectory`",`"identity`":{`"objectId`":`"$userObjectId`",`"tenantId`":`"$tenantId`"}}}}"
$tempFile = Join-Path $env:TEMP "policy-body.json"
[System.IO.File]::WriteAllText($tempFile, $policyBody)
az rest --method PUT `
    --uri "https://management.azure.com${gwId}/connections/${connectionName}/accessPolicies/local-dev?api-version=2026-05-01-preview" `
    --body "@$tempFile" --headers "Content-Type=application/json" -o json | ConvertFrom-Json | Select-Object name
Remove-Item $tempFile -ErrorAction SilentlyContinue
```

#### For deployed compute host (e.g., Function App with system-assigned MSI)

```powershell
$functionAppName = "<function-app-name>"
$msiObjectId = az functionapp identity show -g $resourceGroup -n $functionAppName --query "principalId" -o tsv
$tenantId = az account show --query "tenantId" -o tsv

$policyBody = "{`"properties`":{`"principal`":{`"type`":`"ActiveDirectory`",`"identity`":{`"objectId`":`"$msiObjectId`",`"tenantId`":`"$tenantId`"}}}}"
$tempFile = Join-Path $env:TEMP "msi-policy-body.json"
[System.IO.File]::WriteAllText($tempFile, $policyBody)
az rest --method PUT `
    --uri "https://management.azure.com${gwId}/connections/${connectionName}/accessPolicies/functionapp-msi?api-version=2026-05-01-preview" `
    --body "@$tempFile" --headers "Content-Type=application/json" -o json | ConvertFrom-Json | Select-Object name
Remove-Item $tempFile -ErrorAction SilentlyContinue
```

> ACL propagation takes 1-5 minutes. If you get 403 errors immediately after adding, wait and retry.


### Step 6: Verify Connection

Test the connection works end-to-end:

```powershell
# Office365
az rest --method GET --uri "$runtimeUrl/Categories" --resource "https://apihub.azure.com" -o json

# SharePoint
az rest --method GET --uri "$runtimeUrl/datasets" --resource "https://apihub.azure.com" -o json

# Teams — list joined teams to verify Teams connection
az rest --method GET --uri "$runtimeUrl/beta/me/joinedTeams" --resource "https://apihub.azure.com" -o json

# Azure Blob — list datasets
az rest --method GET --uri "$runtimeUrl/v2/datasets" --resource "https://apihub.azure.com" -o json
```

## Next Steps

- **SDK usage:** Use the connection runtime URL with the SDK's typed async clients:
  ```python
  from azure.connectors.office365 import Office365Client
  from azure.connectors.sdk import ManagedIdentityTokenProvider

  async with Office365Client(runtime_url, ManagedIdentityTokenProvider()) as client:
      await client.send_email_async(to="...", subject="...", body="...")
  ```
- **Azure Functions triggers:** To register connector triggers (e.g., OnNewEmail, OnNewFile) for Azure Functions, use the [trigger-registration skill](../trigger-registration/SKILL.md).
- **Azure Functions signatures:** For a complete mapping of trigger operations to Azure Functions signatures, see [Operations to Functions Signature Match](https://github.com/Azure/azure-functions-connector-extension/blob/main/docs/operations-functions-match.md).
