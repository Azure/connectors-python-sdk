# Connector Code Generation

This document describes how to generate typed Python connector clients using the `LogicAppsCompiler` CLI tool.

## Overview

The **CodefulSdkGenerator** tool generates typed Python clients from managed connector swagger definitions. The generated code provides:

- **Type-safe contracts** - Dataclass models with proper JSON field mappings
- **Paired client classes** - Root sync and `.aio` async clients with identical unsuffixed operations
- **Authentication handling** - Caller-owned Azure Core token or key credentials
- **Azure Core paging** - `ItemPaged` and `AsyncItemPaged` for collection operations

## Prerequisites

### Tools Required

1. **Azure CLI** - Provides the developer credential used by `DefaultAzureCredential`
    - Install from [Microsoft Learn](https://learn.microsoft.com/cli/azure/install-azure-cli)
    - Authenticate with `az login`
    - Select the source subscription with `az account set --subscription <subscription-id>`

2. **Azure Subscription** - Access to an Azure subscription with Logic Apps Standard
   - Required for fetching connector swagger definitions from ARM

3. **.NET 8 SDK** - For building and running the generator (code generation tool is .NET-based)

### Azure Configuration

Set environment variables (or use defaults):

| Variable | Description | Default |
|----------|-------------|---------|
| `ARMCACHE_PATH` | Temporary directory for the current live request batch | New empty directory for each run |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription whose live definitions are fetched | Set explicitly |
| `AZURE_RESOURCE_GROUP` | Resource group with Logic App | (built-in default) |
| `AZURE_LOGICAPP_SITE` | Logic App Standard site name | (built-in default) |
| `AZURE_LOCATION` | Azure region for managed APIs | `westus` |

## Building the Generator

The generator lives in the BPM repository (internal to Microsoft). To build:

```powershell
# Navigate to the BPM repository
cd <BPM-repo-root>

# Initialize the repo (first time only)
.\init.cmd

# Build the CLI tool
dotnet build .\src\tools\CodefulSdkGenerator\LogicAppsCompiler.Cli\LogicAppsCompiler.Cli.csproj -c Release
```

The compiled compiler assembly will be at:

```text
src\tools\CodefulSdkGenerator\LogicAppsCompiler.Cli\bin\Release\net8.0\LogicAppsCompiler.dll
```

## Generation Commands

Capture live definitions only when intentionally refreshing the committed
Swagger inputs. Normal regeneration uses the reviewed snapshots in this
repository.

### Generate Python Client SDK (Recommended)

Generates synchronous and asynchronous Python clients in one request:

```powershell
# Generate all connectors
dotnet LogicAppsCompiler.dll <output-directory> --pythonDirectClient

# Generate specific connectors only
dotnet LogicAppsCompiler.dll <output-directory> --pythonDirectClient --connectors=office365,sharepointonline,teams

# Example: Generate to this SDK repo's src/azure/connectors folder
dotnet LogicAppsCompiler.dll "<path-to-sdk>/src/azure/connectors" --pythonDirectClient --connectors=office365
```

**Output structure per connector:**

- `{connector}.py` - Synchronous client plus shared models, aliases, enums, and trigger metadata
- `aio/{connector}.py` - Asynchronous client importing and re-exporting shared declarations from root

The generator writes each pair atomically and removes both outputs if either
member fails. The CLI accepts one positional output directory. Use
`--pythonDirectClient` for Python generation.

### Generate C# DirectClient SDK

For the .NET SDK, use `--directClient` without `--language` (defaults to C#) or explicitly specify `--language=csharp`:

```powershell
# Generate C# clients (default language)
LogicAppsCompiler.exe <output-directory> --directClient --connectors=office365

# Or explicitly
LogicAppsCompiler.exe <output-directory> --directClient --language=csharp --connectors=office365
```

## Capture and Deterministic Regeneration

To refresh connector contracts, set the source subscription and region
explicitly, use a new empty temporary `ARMCACHE_PATH`, and capture raw responses
with `--swagger-output-directory`. Review the snapshot changes before replacing
the committed files under `swagger-cache/`.

```powershell
$env:AZURE_SUBSCRIPTION_ID = "<live-subscription-id>"
$env:AZURE_LOCATION = "<region>"
$outputDirectory = "<output-directory>"
$connectorNames = "<comma-separated-existing-api-names>"
$previousCachePath = $env:ARMCACHE_PATH
$liveCachePath = Join-Path $env:TEMP ("connector-live-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $liveCachePath, $outputDirectory -Force | Out-Null
try {
    $env:ARMCACHE_PATH = $liveCachePath
    dotnet LogicAppsCompiler.dll $outputDirectory --directClient --language=python `
        "--connectors=$connectorNames" `
        "--swagger-output-directory=<snapshot-output-directory>"
}
finally {
    $env:ARMCACHE_PATH = $previousCachePath
    Remove-Item $liveCachePath -Recurse -Force
}
```

After committing exactly one `<connector>.swagger.json` snapshot per generated
connector, regenerate the complete catalog offline:

```powershell
python scripts/regenerate_connectors.py <path-to-LogicAppsCompiler.dll> `
    --generator-revision=<full-AzureUX-BPM-commit> `
    --captured-at-utc=<UTC-capture-timestamp>
```

The helper validates exact snapshot and sync/aio inventories, generates into an
isolated directory before replacing outputs, writes the lazy client registry and
package type stubs, and updates `generation.manifest.json` with canonical hashes.
Run it a second time and require a clean diff to prove reproducibility.

### Pageable Results

Read-collection operations return Azure Core pagers, including bounded read
collections without continuation metadata. Arrays returned by mutations and
other actions remain eager payloads. Pager iteration follows continuation links
when the contract provides them and yields items directly; an empty response
yields no items. Do not await pager construction:

```python
for item in sync_client.list_items(...):
    process_item(item)

async for item in async_client.list_items(...):
    process_item(item)
```

Root clients return `ItemPaged`; aio clients return `AsyncItemPaged`. Both
support `by_page(continuation_token=...)`. Request controls and response hooks
apply to every page request.

### Long-Running Operations

Retained operations with an HTTP 202 `Location` polling contract use matching
`begin_*` methods. Root clients return `LROPoller[T]`; aio clients return
`AsyncLROPoller[T]` after the `begin_*` call is awaited. Resolve the final
payload with `poller.result()` while the connector client remains open.

The generator does not infer polling from HTTP 202 alone. Status-document
protocols, cancellation, and poller continuation tokens are not currently
generated. Request controls and response hooks apply to the initial request and
every polling request.

### Consumer Review Checks

- Capture known response collections directly in semantic names, such as
    `subscriptions`, `documents`, or `users`, rather than adding a `result` alias.
- Treat collected items as lists, not response dictionaries, and remove repeated
    conditions rather than retaining expressions such as `if documents and documents`.
- Preserve null guards for nullable non-pageable responses, such as
    `response and response.get("value")`. Test `None`, empty dictionaries, and
    populated responses separately; a repeated receiver is not a repeated condition.
- Execute migrated samples with empty and nonempty mocked results. Assert their
    output and reject caught-and-printed errors; imports and call signatures alone
    do not validate how a response is consumed.
- Pagination tests must assert the continuation request, items from later pages,
    and termination, including an empty first page that still has a next link.

## Generated Code Structure

### Python Client Output

```python
# office365.py - Auto-generated Python DirectClient SDK
# Do not edit this file directly.

from dataclasses import dataclass, field as dataclass_field
from typing import Optional, List, Dict, Any
from datetime import datetime
from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.core.pipeline.transport import HttpTransport

from azure.connectors.sdk import ConnectorClientBase

# ===== Types =====

@dataclass
class GraphCalendarEventClientReceive:
    """Response for calendar event operations."""
    
    subject: Optional[str] = dataclass_field(default=None, kw_only=True)
    """Event subject."""
    
    start: Optional[str] = dataclass_field(default=None, kw_only=True)
    """Event start time (ISO 8601)."""
    
    end: Optional[str] = dataclass_field(default=None, kw_only=True)
    """Event end time (ISO 8601)."""
    
    # ... other fields

# ===== Client =====

class Office365Client(ConnectorClientBase):
    """Typed client for Office 365 Outlook connector."""
    
    def __init__(
        self,
        connection_runtime_url: str,
        credential: TokenCredential | AzureKeyCredential,
        *,
        max_retry_attempts: int = 3,
        timeout: float = 30.0,
        transport: Optional[HttpTransport] = None,
        **kwargs: Any,
    ):
        """Initialize the Office 365 client with an Azure Core credential."""
        if not connection_runtime_url:
            raise ValueError("connection_runtime_url cannot be None or empty")

        super().__init__(
            credential,
            max_retry_attempts=max_retry_attempts,
            timeout=timeout,
            transport=transport,
            **kwargs,
        )
        self._connection_runtime_url = connection_runtime_url.rstrip("/")
    
    def send_email_v2(
        self,
        to: str,
        subject: str,
        body: str,
        *,
        from_address: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        importance: Optional[str] = None,
        is_html: bool = True,
    ) -> None:
        """
        Send an email.
        
        Args:
            to: Recipient email address(es), semicolon-separated
            subject: Email subject
            body: Email body (HTML or plain text)
            from_address: Sender address (optional, defaults to mailbox owner)
            cc: CC recipients, semicolon-separated
            bcc: BCC recipients, semicolon-separated
            importance: Email importance (Low, Normal, High)
            is_html: Whether body is HTML
        """
        # Generated implementation calls self._http_client.send(...)
        # with proper serialization and error handling
```

The paired `aio/office365.py` defines the same `Office365Client` operations
with `async def`, `AsyncTokenCredential`, and `AsyncHttpTransport`. It imports
models and other shared declarations from `azure.connectors.office365` rather
than generating duplicate definitions.

### Key Patterns in Generated Code

#### 1. Root Schema Aliases

Root schemas retain their Swagger wire shape instead of being wrapped in a dataclass:

```python
Theme = Literal["white", "blue"]
HandSignature = Literal[0, 1, 2, 3, 4]
ChatMessageList = List["ChatMessage"]
```

String and integer enums become `Literal` aliases, and array roots become typed `List` aliases. Composed `allOf` object roots remain dataclasses with referenced and inline properties flattened into the same model.

#### 2. Dataclass Models

Connector object schemas are generated as dataclasses. Swagger-required fields
are required constructor arguments; optional fields are keyword-only and
default to `None`:

```python
@dataclass
class FileMetadata:
    """Metadata for a file in SharePoint or OneDrive."""

    id: str
    name: Optional[str] = dataclass_field(default=None, kw_only=True)
    path: Optional[str] = dataclass_field(default=None, kw_only=True)
    size: Optional[int] = dataclass_field(default=None, kw_only=True)
    created_time: Optional[datetime] = dataclass_field(
        default=None,
        kw_only=True,
    )
    modified_time: Optional[datetime] = dataclass_field(
        default=None,
        kw_only=True,
    )
```

#### 3. Client Inheritance

All generated clients extend `ConnectorClientBase`:

```python
class SharepointonlineClient(ConnectorClientBase):
    """Typed client for SharePoint Online connector."""

    def __init__(
        self,
        connection_runtime_url: str,
        credential: TokenCredential | AzureKeyCredential,
    ):
        super().__init__(credential)
        self._connection_runtime_url = connection_runtime_url.rstrip("/")
```

This inheritance provides:

- HTTP client with retry logic
- Authentication through caller-owned Azure Core credentials
- Lifecycle management through matching sync or async context managers
- Error handling with `ConnectorException`

#### 4. Matching Method Signatures

Root and aio clients expose the same unsuffixed operation names and parameters.
The execution model and pager type differ:

```python
def list_items(
    self,
    dataset: str,
    table: str,
    *,
    filter_query: Optional[str] = None,
    order_by: Optional[str] = None,
    top: Optional[int] = None,
) -> ItemPaged[dict[str, Any]]:
    """
    Get items from a SharePoint list.
    
    Args:
        dataset: SharePoint site URL
        table: List name or ID
        filter_query: OData filter expression
        order_by: OData orderBy expression
        top: Maximum number of items to return
    """
    ...
```

```python
def list_items(
    self,
    dataset: str,
    table: str,
    *,
    filter_query: Optional[str] = None,
    order_by: Optional[str] = None,
    top: Optional[int] = None,
) -> AsyncItemPaged[dict[str, Any]]:
    """Return the asynchronous item pager without awaiting construction."""
    ...
```

#### 5. Type Hints and Docstrings

The generator produces:

- Full type hints for all parameters and return types
- Docstrings from connector metadata
- Optional parameter defaults
- Generic type aliases where appropriate

## Adding a Generated Client to the SDK

After generating a new connector client:

1. **Copy the generated pair** to `src/azure/connectors/`:

   ```powershell
   Copy-Item "output\office365.py" "src\azure\connectors\office365.py"
    Copy-Item "output\aio\office365.py" "src\azure\connectors\aio\office365.py"
   ```

2. **Regenerate package-level artifacts.** The helper writes the lazy client
    registry and root/aio `.pyi` files. Do not edit them manually.

3. **Create unit tests** following the pattern in `tests/`:

   ```python
   # tests/test_office365.py
   import pytest
   from azure.connectors.office365 import Office365Client
   
   class TestOffice365Client:
       def test_constructor(self, mock_token_provider):
           client = Office365Client("https://example.com", mock_token_provider)
           assert client is not None
   ```

4. **Run the test suite**:

   ```bash
   pytest
   ```

5. **Create both sample variants** under `samples/sample_connector_usage/` and
    `samples/sample_connector_usage/aio/`.

6. **Update documentation**:
   - Add connector to README.md validated connectors table
   - Update ROADMAP.md status
   - Add sample code to `samples/` directory

## Troubleshooting

### Azure Authentication

If generation fails with authentication errors:

```powershell
# Authenticate the Azure CLI credential used by DefaultAzureCredential
az login
az account set --subscription $env:AZURE_SUBSCRIPTION_ID

# Verify the active subscription and ARM token
az account show --output table
az account get-access-token --resource https://management.azure.com/ --output table
```

### Connector Not Found

If a connector name is not recognized:

1. Check available connector names in Azure Portal (Logic Apps → Connections → Built-in connectors)
2. Use lowercase connector ID (e.g., `office365` not `Office365`)
3. Try listing all available connectors in the generator help

### Generated Code Errors

If generated code has syntax errors or type issues:

1. Check the BPM repository is up to date and use `--pythonDirectClient`
2. Fix the generator, not the generated output — see [Generator File Locations](#generator-file-locations-bpm-repository)
3. Report issues to BPM team with connector name and error details (file in [BPM Azure DevOps](https://dev.azure.com/msazure/One/_workitems))
4. Add the defect to the [Known Generator Defects Registry](#known-generator-defects-registry)
5. Review swagger definition for edge cases

## Example Workflows

### Generate Office 365, SharePoint, and Teams

```powershell
# Set output directory
$outputDir = "c:\Users\victoriahall\Documents\repos\connectors-python-sdk\src\azure\connectors"

# Generate three core connectors
LogicAppsCompiler.exe $outputDir --pythonDirectClient --connectors=office365,sharepointonline,teams

# Verify output
Get-ChildItem $outputDir -Filter *.py
```

### Generate All Validated Connectors

```powershell
# Generate all currently validated connectors
$connectors = "office365,sharepointonline,teams,kusto,msgraphgroupsanduser"
LogicAppsCompiler.exe $outputDir --pythonDirectClient --connectors=$connectors
```

## Code Generation Best Practices

1. **Version control** - Do not edit generated files manually; regenerate from source
2. **Connector selection** - Generate only the connectors you need to reduce package size
3. **Updates** - Regenerate periodically to pick up connector schema updates
4. **Testing** - Always run full test suite after regeneration
5. **Documentation** - Keep README and ROADMAP in sync with available connectors

## Generated Client Acceptance Criteria

Every generated connector client MUST satisfy these invariants before merge:

### 1. Request Body Handling (Create/Update Operations)

- Every `POST`, `PUT`, or `PATCH` operation that accepts input parameters MUST construct and send a request body
- All input parameters marked as body parameters in swagger MUST be serialized into the request
- Create/update operations MUST NOT silently drop input parameters

**Validation:** Unit tests MUST assert that the outgoing request body contains expected fields for create/update operations.

### 2. Response Status Checking (All Operations)

- Every HTTP operation MUST capture the response and check the status code
- Non-2xx responses MUST raise `ConnectorException`, an Azure Core
    `HttpResponseError`, with status code and message
- Void operations (DELETE, PATCH, fire-and-forget POST) MUST NOT discard the response unchecked

**Correct pattern:**
```python
response = self.http_client.send(
    method="DELETE",
    url=request_uri,
)
if not (200 <= response.status < 300):
    raise ConnectorException(
        "DELETE",
        request_uri,
        response.status,
        response.text,
    )
```

**Note:** `ConnectorException` takes four positional arguments: `method`, `path`, `status_code`, `response_body`. The exception automatically formats these into a user-friendly message.

**Incorrect pattern (MUST NOT pass review):**
```python
self.http_client.send(  # Result discarded - silent failures!
    method="DELETE",
    url=request_uri,
)
```

The aio pattern awaits the same `send` method. **Validation:**
`test_no_unchecked_send_calls` in `tests/test_code_quality.py` scans root and aio
modules for discarded calls. Unit tests for void methods must also assert that
non-2xx responses raise `ConnectorException`.

### 3. Test Coverage

- No skipped tests without a tracked issue link in the skip reason
- Void methods MUST have explicit tests verifying non-2xx raises exception

**Coverage scope:** Test coverage is required by HTTP method category, not one test class per generated method. For each connector, the test suite MUST include:

| HTTP verb in connector | Required test coverage |
|---|---|
| GET (any) | At least 1 success test (path/query serialization) + 1 error test |
| POST with body | At least 1 test asserting body is forwarded + 1 error test |
| PUT with body | At least 1 test asserting body is forwarded + 1 error test |
| PATCH with body | At least 1 test asserting body is forwarded + 1 error test |
| DELETE | At least 1 success test + 1 error test verifying exception raised; `delete_*` resource methods must also cover HTTP 404 as success |

**Connectors with >20 public methods** are not required to have a test class per method. Representative coverage — one test group per HTTP verb type used by the connector — satisfies the acceptance criteria, provided the body-forwarding and non-2xx paths are both covered.

**Minimum per method:** The above table is the floor. For operations that are clearly distinct in behavior (e.g., two POST operations where one fires a trigger vs. one creates a resource), additional test groups are appropriate but not strictly required before merge.

### 4. Type Completeness

- All public types (dataclasses) referenced by method signatures MUST be defined
- No `# type: ignore` comments unless accompanied by a tracked issue link
- All optional parameters MUST have `Optional[T]` type hints and default values;
    Swagger-required model fields MUST remain required constructor arguments

## Generator File Locations (BPM Repository)

When fixing generator bugs (per the "fix the generator, not generated output" rule), these are the key files:

### Python Generator

| File | Purpose |
|------|--------|
| `src/tools/CodefulSdkGenerator/DirectClient/DirectClientPythonGenerator.cs` | Entry point for Python generation; orchestrates the generation pipeline |
| `src/tools/CodefulSdkGenerator/DirectClient/DirectClientPythonCodeGenerator.cs` | Core code emitter; generates Python client classes, methods, and type definitions |

### Key Differences from .NET Generator

The .NET SDK centralizes error handling in
`ConnectorClientBase.CallConnectorAsync()`. The Python emitter must explicitly
generate the status check in each root and aio method body because
`http_client.send()` does not auto-raise.

**If you find a Python generator bug:**
1. Fix it in `DirectClientPythonCodeGenerator.cs`
2. Add a test case in `CodefulSdkGenerator.Tests/`
3. Regenerate affected connectors
4. Add the defect to the Known Generator Defects Registry below

### C# Generator

| File | Purpose |
|------|--------|
| `src/tools/CodefulSdkGenerator/DirectClient/DirectClientCSharpGenerator.cs` | C# generation entry point |
| `src/tools/CodefulSdkGenerator/DirectClient/DirectClientCSharpCodeGenerator.cs` | C# code emitter |

### Shared Infrastructure

| File | Purpose |
|------|--------|
| `src/tools/CodefulSdkGenerator/ConnectorsGenerator.cs` | ARM API fetching, swagger parsing, JSON sanitization |
| `src/tools/CodefulSdkGenerator/Data/ManagedConnectorSkipList.txt` | Connectors skipped due to known issues |
| `src/tools/CodefulSdkGenerator/Data/*.txt` | Character replacement and reformatting lists |

## Known Generator Defects Registry

Track known generator issues here to prevent silent recurrence across releases.

| Defect | BPM Issue | Affected Connectors | Status | Notes |
|--------|-----------|---------------------|--------|-------|
| Teams template variable causes NameError at import | [BPM #TBD](https://dev.azure.com/msazure/One/_workitems/edit/TBD) | `teams` | Workaround (skip import test) | `DynamicValueLookup` references undefined variable; test skipped with issue link |
| Void operations not checking response status | Fixed in generator | Pre-2024 connectors | Fixed | Regenerate affected connectors: `azurequeues`, `azuretables`, `commondataservice`, `eventhubs`, `excelonlinebusiness`, `office365`, `onedrive`, `outlook`, `servicebus`, `sharepointonline`, `smtp`, `azuread` |
| api_version parameters missing default values | Fixed in generator | `azuredigitaltwins`, `azurevm`, others | Fixed | Generator now uses swagger default value for api_version/api-version parameters |
| `TimeNextVisible` emitted as `time_next_visible` | Fixed in generator | `azurequeues` | Fixed | Connector-specific public-name override emits `next_visible_time` while preserving `TimeNextVisible` as the wire name. |
| Path parameters under-encoded (missing double-encoding) | Fixed in generator | `commondataservice`, any connector with `x-ms-url-encoding: "double"` path params | Fixed | Python generator ignored `x-ms-url-encoding: "double"` and left most path params bare (`{str(param)}`), causing 404s when values contained slashes (e.g. full Dataverse dataset URLs). C# generator honored it (PR 16445892) but Python was not updated. Shared logic hoisted to `DirectClientGeneratorBase.ShouldDoubleEncodePathParameter`; Python now emits `quote(quote(str(param), safe=''), safe='')` for double-encoded params and `quote(str(param), safe='')` for all others. Regenerate affected connectors. |
| Dataverse attachment row ID emitted as an integer | Fixed in generator | `commondataservice` | Fixed | Shared Swagger preprocessing corrects the `CreateAttachment` and `CreateAttachment_V2` `id` path parameter to string before language-specific generation. Python now emits `str`, matching the existing C# `string` contract while preserving double path encoding. |
| Operation methods corrected Swagger spelling or split acronym letters | Fixed in generator | `docusign`, `github`, `googletasks`, `pdfco`, `salesforce`, `signinghub`, `slack`, `wordonlinebusiness`, `zohosign` | Fixed | Python applies deterministic acronym-aware snake_case and connector-scoped corrections for known malformed operation IDs. |
| Colliding wire names dropped after Python normalization | Fixed in generator | `teams`, `shifts`, `todo` | Fixed | Distinct generated fields preserve both `id` and `@odata.id`; serializer tests set both values together. |
| String-encoded integer enum tokens emitted as string literals | Fixed in generator | `etsy` | Fixed | Python now normalizes quoted enum tokens to the declared integer schema type. All Phase 6 and 7 clients were regenerated; only `etsy` changed. |
| Pageable item properties and bounded collection envelopes misclassified | Fixed in generator | `azuredigitaltwins`, `insightly`, `jira`, `documentdb`, `sql`, and other collection connectors | Fixed | Explicit pageable operations infer omitted item names and use recognized continuation fields present in the response schema. Bounded read envelopes select conventional primary arrays over auxiliary array metadata and emit `list_*` pagers, while mutation/action arrays remain eager. |
| Mutation arrays were lazy and primitive pagers used dictionary item types | Fixed in generator | `azuread`, `docusign`, `eventhubs`, `meetingroommap`, `mq`, `msgraphgroupsanduser`, `onedrive`, `powerbi`, `replicon`, `sendgrid`, `servicebus`, `yammer` | Fixed | Bounded mutation responses execute eagerly under action names and preserve response envelopes. Read collections retain primitive pager item types in sync and aio contracts. |
| Caller continuation URLs bypassed pagination origin normalization | Fixed in generator | All pageable connectors | Fixed | `by_page(continuation_token=...)` now routes caller tokens through the same URL resolver as service-provided next links before transport receives the request. |
| Typeless dynamic request models omitted mapping inputs | Fixed in generator | `docuware` | Fixed | Dynamic dataclass request annotations now accept either the generated model or `Mapping[str, Any]`. |
| HTTP verb used as a proxy for resource-delete semantics | Fixed in generator | `clicksendsms`, `servicebus`, `zohosign`, and other delete operations | Fixed | Generated `delete_*` methods return `None` and accept HTTP 404 even when the transport verb is PUT. DELETE-backed actions retain ordinary non-2xx failure behavior. |
| Successful response discarded when Swagger omits its schema | Fixed in generator | `orderful` | Fixed | The Python-specific `ListTransactions` override preserves the runtime JSON payload without changing other language emitters. |
| Create/update operations missing request body | [BPM #TBD](https://dev.azure.com/msazure/One/_workitems/edit/TBD) | Varies by connector | Investigation | Some POST/PATCH operations may drop body parameters |

**Adding a new defect:**
1. File an issue in BPM Azure DevOps
2. Add a row to this table with connector list
3. Add `@pytest.mark.skip(reason="Generator defect - see GENERATION.md")` to affected tests
4. Update status when fixed and connectors regenerated

### Wire-Name Collision Regeneration

The `todo` client was generated with CodefulSdkGenerator from the internal BPM repository after the wire-name collision fix. The immutable input and generated output are:

- Swagger snapshot: [`todo.swagger.json`](https://github.com/Azure/Connectors-NodeJS-SDK/blob/4123e5ac446c9226a431a46139c63158cf68ec75/swagger-cache/todo.swagger.json)
- Swagger SHA-256: `D500A1028C6E81A051A849C6A6382082363F5BCC0C74D1C132D825210670CA6A`
- Generated `todo.py` SHA-256: `4AE27DED1312DBBE98375CEDA17181D45F3E74349541C3A6B9140DC704ED9BA5` (UTF-8 with CRLF line endings as emitted on Windows)

The regeneration restores `ToDoHtml.id_2` for `@odata.id` and wire-name metadata throughout the Todo client. The generated request models are now named `CreateToDoList`, `CreateToDo`, and `UpdateToDo`; callers using the deprecated `V2`-suffixed names must update their imports. Todo polling triggers also move from callable client methods to `TRIGGER_OPERATIONS` metadata for Connector Namespace registration.

The Teams and Shifts generated clients are unchanged in this regeneration. Their existing collision fields receive serializer regression coverage that preserves both `id` and `@odata.id`.

## Related Documentation

- [README.md](README.md) - SDK overview and quick start
- [ROADMAP.md](ROADMAP.md) - Connector priorities and status
- [tests/README.md](tests/README.md) - Test suite documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
 
                           TokenCredential credential = null, 
                           HttpClient httpClient = null)
    {
        // ...
    }

    /// <summary>
    /// Send an email.
    /// </summary>
    public async Task SendEmailAsync(SendEmailInput input, 
                                     CancellationToken cancellationToken = default)
    {
        // ...
    }
}

#endregion Client
```

## Cross-Repo Architecture

The connector SDK spans 4 repositories with a strict data flow:

```text
┌──────────────────────────────────────┐
│  BPM (internal)                      │
│  CodefulSdkGenerator                 │
│  Parses swagger x-ms-dynamic-values  │
│  Emits [DynamicValues("opId")]       │
│  Includes discovery methods          │
└──────────┬───────────────────────────┘
           │ generates
           ▼
┌──────────────────────────────────────┐
│  Azure/Connectors-NET-SDK            │
│  (this repo, GitHub)                 │
│                                      │
│  src/.../DynamicValuesAttribute.cs   │  ← hand-written attribute definition
│  samples/generated/*Extensions.cs    │  ← generator output (DO NOT hand-edit)
│  src/.../Generated/                  │  ← packaged into NuGet
└──────────┬───────────┬───────────────┘
           │           │
   NuGet   │           │ NuGet
           ▼           ▼
┌────────────────┐  ┌──────────────────────────┐
│  Azure/         │  │  Azure/                  │
│  azure-         │  │  azure-connector-sdk-    │
│  connector-     │  │  samples                 │
│  sdk-lsp        │  │  (GitHub)                │
│  (GitHub)       │  │                          │
│  Roslyn reads   │  │  E2E test target         │
│  [DynamicValues]│  │  DirectConnector uses    │
│  from SDK .dll  │  │  generated client        │
│  Hover handler  │  │  SharePoint connection   │
│  fetches values │  │                          │
│  from API Hub   │  │                          │
└─────────────────┘  └──────────────────────────┘
```

### Key Rules

1. **Generated content is read-only** — files in `samples/generated/` and `src/.../Generated/` are
   produced by the BPM CodefulSdkGenerator. **Never hand-edit generated files.**
2. **Fix bugs in the generator, not in generated output** — if generated code has issues (typos,
   wrong annotations, missing methods), fix the CodefulSdkGenerator in the BPM repo, then
   regenerate. This ensures fixes survive regeneration and benefit all generation targets
   (DirectClient SDK, Codeful Workflow SDK, etc.).
3. **`DynamicValuesAttribute` is hand-written** — defined in `src/.../DynamicValuesAttribute.cs`.
   The generator emits references to it; the LSP reads it via Roslyn reflection.
4. **Merge order** — SDK (attribute) → BPM (generator) → LSP and POC (consumers). The SDK must
   define the attribute before the generator can reference it, and the generator must produce
   the annotations before consumers can use them.
5. **Regeneration** — after generator changes in BPM, re-run the generator and commit the output
   to this repo. See [Generation Commands](#generation-commands) above.
6. **Swagger text sanitization** — the generator's `SanitizeSwaggerText()` method corrects known
   typos from swagger definitions before they flow into XML documentation. Add new corrections
   there rather than patching generated files.

### Repository Links

| Repo | URL | Role |
|------|-----|------|
| BPM (CodefulSdkGenerator) | Internal (Microsoft Azure DevOps) | Generator source |
| Connector SDK (this repo) | `https://github.com/Azure/Connectors-NET-SDK` | Attribute + generated output |
| [Connector SDK LSP](https://github.com/Azure/Connectors-NET-LSP) | `https://github.com/Azure/Connectors-NET-LSP` | Design-time IntelliSense consumer |
| [Connector SDK Samples](https://github.com/Azure/Connectors-NET-Samples) | `https://github.com/Azure/Connectors-NET-Samples` | E2E validation target |

## Integration with SDK

The generated code depends on the runtime SDK for:

- `AsyncTokenCredential` or `AzureKeyCredential` authentication
- `ConnectorHttpClient` Azure Core pipeline, retry, and request controls
- Shared wire serialization and immutable response-hook contracts

Install the package with Azure Identity support:

```bash
python -m pip install azure-connectors
```

## Regeneration Schedule

Generated connectors should be regenerated periodically to incorporate:

- New connector operations
- Updated parameter schemas
- Bug fixes in swagger definitions

**Recommended schedule:**

- Monthly regeneration for active development
- Quarterly regeneration for stable projects
- Immediate regeneration when new connector features are needed

## Automation

### CI/CD Integration

Example GitHub Actions workflow for scheduled regeneration:

```yaml
name: Regenerate Connector SDKs

on:
  schedule:
    - cron: '0 0 1 * *'  # First day of each month
  workflow_dispatch:  # Allow manual trigger

jobs:
  regenerate:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      
      - name: Login to Azure
                uses: azure/login@v2
                with:
                    client-id: ${{ secrets.AZURE_CLIENT_ID }}
                    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
                    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      
      - name: Build Generator
        run: |
          dotnet build src/tools/CodefulSdkGenerator/LogicAppsCompiler.Cli -c Release
      
      - name: Generate Connectors
        env:
          AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
          AZURE_RESOURCE_GROUP: ${{ secrets.AZURE_RESOURCE_GROUP }}
                    AZURE_LOCATION: westus
                    ARMCACHE_PATH: ${{ runner.temp }}\armcache
        run: |
                    ./LogicAppsCompiler.exe ./generated --pythonDirectClient --connectors=office365,servicebus
      
      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: 'chore: Regenerate connector SDKs'
          body: 'Monthly connector SDK regeneration'
          branch: chore/regenerate-connectors
```

## Troubleshooting

### Common Issues

**Azure credential unavailable:**

```text
Run: az login, select the intended subscription, and retry.
```

**Connector not found:**

- Verify connector name is correct (use lowercase, no spaces)
- Check if connector is available in the specified Azure region

**Schema parsing errors:**

- Some connectors have malformed swagger definitions
- The generator includes built-in patches for known issues
- Problematic connectors are in the skip list

### Cache Management

ARM responses are cached to improve regeneration speed:

```powershell
# Clear cache to force fresh API calls
Remove-Item -Path "$env:TEMP\armcache" -Recurse -Force
```

## Available Connectors

To see the list of available connectors:

```powershell
# Authenticate and select the source subscription
az login
az account set --subscription "{subscriptionId}"

# List managed APIs in a region
az rest --method GET --url "https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Web/locations/westus/managedApis?api-version=2018-07-01-preview"
```

Common connectors:

- `office365` - Office 365 Outlook
- `outlook` - Outlook.com
- `servicebus` - Azure Service Bus
- `azureblob` - Azure Blob Storage
- `azuretables` - Azure Table Storage
- `azurequeues` - Azure Queue Storage
- `teams` - Microsoft Teams
- `keyvault` - Azure Key Vault
- `sql` - SQL Server
- `cosmosdb` - Azure Cosmos DB
