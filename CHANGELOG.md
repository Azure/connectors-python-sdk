# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking Changes

- Generated Python operation names now preserve the exact Swagger `operationId` spelling while grouping acronym runs in snake_case. This renames methods in DocuSign, Google Tasks, PDF.co, SigningHub, Slack, Word Online (Business), and Zoho Sign.
- Regenerated Office 365 Groups Mail, Planner, SMTP, and Yammer now expose current request and response model names instead of deprecated version-family sibling names. Their polling triggers are available through `TRIGGER_OPERATIONS`, not callable client methods.
- `UploadDocument.document_id` now represents the natural `document_id` wire field. Callers that used it for `documentId` must use `document_id_2` instead.
- Regenerated Azure Queues, DocuSign, Event Hubs, Microsoft Forms, SharePoint Online, and Microsoft Teams from the current managed connector contracts. Trigger routes are now exposed through `TRIGGER_OPERATIONS` instead of callable client methods, and deprecated DocuSign operations are no longer generated.
- Azure Event Hubs batch sends now require `partition_key`. Word Online (Business) template and PDF operations now require `source`, `drive`, and `file` identifiers.
- Regenerated contracts move trigger routes from callable methods to `TRIGGER_OPERATIONS` for GitHub, Jira, Office 365 Outlook, Office 365 Groups, Power BI, Service Bus, and Shifts. Microsoft Bookings no longer exposes the deprecated `create_appointment_async`, `update_appointment_async`, or `cancel_appointment_async` methods.
- Azure Digital Twins now supplies API version `2020-10-31` internally instead of accepting `api_version` on its public methods. Azure IoT Central schema methods now accept template and module identifiers; Azure Tables entity listing no longer accepts continuation-key parameters; Jira issue listing now accepts JQL and a next-page token; Office 365 Outlook and OneNote signatures now follow their current managed connector contracts.

### Changed

- Regenerated Office 365 Outlook, Office 365 Groups Mail, Pipedrive, Planner, Plumsail Documents, SharePoint Online, SMTP, and Yammer from pinned managed connector contracts using the current CodefulSdkGenerator.
- Regenerated Azure Queues, Azure Cosmos DB, DocuSign, DocuWare, Azure Event Hubs, Microsoft Forms, SharePoint Online, SigningHub, Microsoft Teams, and Word Online (Business) from the merged CodefulSdkGenerator contract updates.
- Binary request bodies for SharePoint file and attachment uploads, SigningHub document uploads, and Microsoft Teams HTTP requests are forwarded as raw bytes with `application/octet-stream`.
- Regenerated Azure AD, Azure Digital Twins, Azure Event Grid, Azure IoT Central, Azure Monitor Logs, Azure Queues, Azure Tables, Azure Cosmos DB, DocuSign, DocuWare, Azure Event Hubs, GitHub, Jira, Azure Data Explorer, Microsoft Bookings, Microsoft Forms, Office 365 Outlook, Office 365 Groups, OneNote, Pipedrive, Power BI, Service Bus, Shifts, SigningHub, Microsoft Teams, and Word Online (Business) with corrected root-schema handling.

### Fixed

- Current routes now bind to their exact current request definitions instead of deprecated version-family siblings. SharePoint Online also preserves both `/copyFile` and `/copyFileAsync` as distinct callable methods.
- Regenerated SigningHub so properties whose wire names normalize to the same Python identifier are preserved with distinct serializable fields.

### Added

- Added current managed connector discovery operations for Azure IoT Central device templates, Azure Monitor Logs time ranges, Azure Tables storage accounts, Azure Data Explorer query schemas, and Service Bus entities, system properties, queues, session options, topics, subscriptions, and subscription filters.
- **Zoho Sign** (`zohosign.py`) connector client with unit tests and a sample
- Discovery and schema operations from the latest Azure Event Hubs, SharePoint Online, Microsoft Teams, and Word Online (Business) contracts
- **DocuWare** (`docuware.py`) connector client with unit tests and samples
- **SigningHub** (`signinghub.py`) connector client with unit tests and samples
- **Pipedrive** (`pipedrive.py`) connector client with unit tests and samples
- **Zendesk** (`zendesk.py`) connector client with unit tests and samples
- **SQL Server** (`sql.py`) connector client with unit tests and samples
- **Plumsail Documents** (`plumsail.py`) connector client with unit tests and samples
- **PDF.co** (`pdfco.py`) connector client with unit tests and samples
- **Fin & Ops Apps (Dynamics 365)** (`dynamicsax.py`) connector client with unit tests and samples
- **Cloudmersive Document Conversion** (`cloudmersiveconvert.py`) connector client with unit tests and samples
- **Azure IoT Central** (`azureiotcentral.py`) connector client with unit tests and samples
- **Azure Event Grid** (`azureeventgrid.py`) connector client with unit tests and samples
- **Universal Print** (`universalprint.py`) connector client with unit tests and samples
- **GitHub** (`github.py`) connector client with unit tests and samples
- **Slack** (`slack.py`) connector client with unit tests and samples
- **Jira** (`jira.py`) connector client with unit tests and samples
- **Power BI** (`powerbi.py`) connector client with unit tests and samples
- **Microsoft Forms** (`microsoftforms.py`) connector client with unit tests and samples
- **Microsoft To Do** (`todo.py`) connector client with unit tests and samples
- **Shifts** (`shifts.py`) connector client with unit tests and samples
- **DocuSign** (`docusign.py`) connector client with unit tests and samples
- **Salesforce** (`salesforce.py`) connector client with unit tests and samples
- **Yammer** (`yammer.py`) connector client with unit tests and samples
- **Planner** (`planner.py`) connector client with unit tests and samples
- **OneNote** (`onenote.py`) connector client with unit tests and samples
- **Office 365 Groups** (`office365groups.py`) connector client with unit tests and samples
- **Microsoft Bookings** (`microsoftbookings.py`) connector client with unit tests and samples
- **Azure Key Vault** (`keyvault.py`) connector client with unit tests and samples
- **Azure VM** (`azurevm.py`) connector client with unit tests and samples
- **Azure Digital Twins** (`azuredigitaltwins.py`) connector client with unit tests and samples
- **Azure Data Factory** (`azuredatafactory.py`) connector client with unit tests and samples
- **Azure Automation** (`azureautomation.py`) connector client with unit tests and samples
- **Azure Monitor Logs** (`azuremonitorlogs.py`) connector client with unit tests and samples
- **Box** (`box.py`) connector client with unit tests and samples
- **Dropbox** (`dropbox.py`) connector client with unit tests and samples
- **Google Calendar** (`googlecalendar.py`) connector client with unit tests and samples
- **Google Drive** (`googledrive.py`) connector client with unit tests and samples
- **Google Tasks** (`googletasks.py`) connector client with unit tests and samples
- **Excel Online** (`excelonline.py`) connector client with unit tests and samples
- **OneDrive for Business** (`onedriveforbusiness.py`) connector client with unit tests and samples
- **FTP** (`ftp.py`) connector client with unit tests and samples
- **RSS** (`rss.py`) connector client with unit tests and samples
- **Office 365 Groups Mail** (`office365groupsmail.py`) connector client with unit tests and samples

### Fixed

- Generated string enums, integer enums, arrays, and `allOf` definitions now retain their Swagger JSON wire shapes instead of being emitted as dynamic object wrappers.
- **Azure Queues** (`azurequeues.py`): corrected the public `QueueMessage.next_visible_time` property while preserving the `TimeNextVisible` wire name, and added `dequeue_count` plus the nested queue-message response models.
- **Microsoft Dataverse** (`commondataservice.py`): path parameters are now double URL-encoded so values containing reserved characters (for example the `://` in an environment/organization URL used as the `dataset` segment) survive apihub gateway routing. Previously these segments were single-encoded and could be mis-routed. Fix applied in the CodefulSdkGenerator and regenerated; added regression tests covering encoding of the `dataset`, `table`, and `id` segments.
- **Microsoft Dataverse** (`commondataservice.py`): regenerated with the corrected CodefulSdkGenerator so curated internal operations are retained. The client now exposes all 22 operations at parity with the .NET SDK (previously 11), adding attachment, association/disassociation, collection-relationship, option-set/multi-select metadata, delete, and pagination methods. Added unit tests covering the new operations.
- **Microsoft Dataverse** (`commondataservice.py`): `get_next_page_async` now returns the page payload (`dict[str, Any] | None`) instead of discarding it as `None`, so pagination via `nextLink` is usable and at parity with the .NET `GetNextPageAsync`. Operations whose swagger omits a response schema now honor the per-operation response-type override in the Python generator path. Fix applied in the CodefulSdkGenerator and regenerated; added tests covering the returned payload and the trigger-operation registry.

## [0.3.0b2]

### Added

- **13 new connector clients** with unit tests and samples:
  - ARM (Azure Resource Manager), Azure AD, Azure Cosmos DB, Azure Event Hubs, Azure Queues, Azure Tables, Excel Online (Business), Microsoft Dataverse, Microsoft Defender ATP, Outlook, Service Bus, SMTP, Word Online (Business)

### Changed

- **Comprehensive error handling improvements** across 14 connector clients:
  - Added error handling tests for all HTTP operations (4xx/5xx responses)
  - Fixed variable shadowing in `outlook.py` and `office365.py` (`respond_to_event_async`)
  - Fixed incorrect `ConnectorException` signature in `teams.py` (2 methods)

## [0.2.0b2] - 2026-05-13

### Added

- **OneDrive for Business** (`onedrive.py`) connector client with 30+ methods for file operations, sharing, tags, and triggers
- **Office 365 SDK type bindings**: Added 3 new typed response classes for improved deserialization
  - `ClientReceiveMessage.from_json()` — Parse email messages from trigger callbacks
  - `GraphClientReceiveMessage.from_json()` — Parse Graph API email responses
  - `GraphCalendarEventListWithActionType.from_json()` — Parse calendar event responses

### Changed

- **Regenerated connector clients** based on latest contract changes
  - Updated binary content methods to use `response.text.encode('latin-1')` pattern
  - Removed deprecated SharePoint methods no longer in contract

### Fixed
- **Rename Package Metadata**: renamed package metadata from Logic Apps to Azure Connectors branding, removed logic-apps keyword.
- **`TriggerCallbackBody[T]` now handles both batch and single-item callback shapes** — Connector Namespace delivers trigger callbacks in two shapes depending on the trigger configuration's splitOn setting: batch `{"body":{"value":[...]}}` and single-item `{"body":{...item...}}`. The new `from_dict()` factory methods on `TriggerCallbackPayload` and `TriggerCallbackBody` transparently normalize both shapes into `body.value` as a list, preventing silent zero-item processing when splitOn is enabled. Use `TriggerCallbackPayload.from_dict(data)` to parse callback payloads that may arrive in either shape.

## [0.2.0b1] - 2026-05-13

### Added

- **Azure Blob Storage** (`azureblob.py`) connector client and samples
- **IBM MQ** (`mq.py`) connector client and samples
- **Office 365 Users** (`office365users.py`) connector client and samples
- Microsoft Graph Groups and Users samples (`sample_connector_usage_msgraphgroupsanduser.py`)

### Changed

- Renamed `msgraph` to `msgraphgroupsanduser` to match the official connector API name

## [0.1.0dev2] - 2026-04-23

### Added

- Microsoft Graph (msgraphgroupsanduser) generated typed client with 46 tests
- Comprehensive unit tests for SDK core components (110 tests)
  - Token provider tests (AzureIdentityTokenProvider, ManagedIdentityTokenProvider, ConnectionStringTokenProvider)
  - HTTP client tests with retry logic and exponential backoff
  - Client base, exceptions, options, and trigger payload tests
- GitHub Actions CI/CD workflows for Python (pytest, flake8, build)
- PyPI release workflow with version management

### Changed

- Fixed all flake8 linting errors across SDK codebase
- Updated package exports to include all connector clients
- Improved test coverage to 75% overall (305 tests total)

## [0.1.0dev1] - 2026-04-20

### Added

- Initial Python SDK release with core abstractions
  - `ConnectorClientBase` — Abstract base for all connector clients
  - `TokenProvider` interface with three implementations:
    - `ManagedIdentityTokenProvider` — Azure managed identity support
    - `AzureIdentityTokenProvider` — Wraps Azure Identity credentials
    - `ConnectionStringTokenProvider` — API key / connection string support
  - `ConnectorHttpClient` — HTTP pipeline with configurable retry, exponential backoff
  - `ConnectorClientOptions` — Configuration for timeouts, retries, backoff
  - `ConnectorException` — Typed exceptions with response body truncation
  - `TriggerCallbackPayload` — Generic types for Connector Namespace trigger integration
- Generated connector clients (auto-generated from Logic Apps swagger):
  - **Office 365 Outlook** (`office365.py`) — 53 methods, 41 tests, 79% coverage
  - **SharePoint Online** (`sharepointonline.py`) — 45 methods, 44 tests, 57% coverage
  - **Microsoft Teams** (`teams.py`) — 49 methods, 27 tests passing, 73% coverage
  - **Azure Data Explorer** (`kusto.py`) — 6 methods, 37 tests, 98% coverage
- Async/await support throughout (built on `aiohttp`)
- Type hints and dataclass models for all API operations
- Comprehensive test suite:
  - Connector tests: 149 tests (131 passing, 18 skipped)
  - SDK component tests: 110 tests (all passing)
  - Test fixtures and mocking infrastructure
- Sample code for Office 365, SharePoint, Teams, and Kusto
- Setup script for creating Connector Namespace connections (`Setup-Connection.ps1`)
- Documentation:
  - README with quick start examples
  - Connection setup guide (`docs/connection-setup.md`)
  - Test documentation (`tests/README.md`)
  - Contributing guidelines

### Development Infrastructure

- Python 3.10+ support (tested on 3.10, 3.11, 3.12, 3.13)
- pytest with async support and coverage reporting
- flake8 linting with 79-character line limit
- Type checking configuration
- EditorConfig and VSCode settings
- Pyproject.toml packaging configuration

[Unreleased]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.3.0b2...HEAD
[0.3.0b2]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.2.0b2...v0.3.0b2
[0.2.0b2]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.1.0b1...v0.2.0b2
[0.2.0b1]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.1.0dev2...v0.2.0b1
[0.1.0dev2]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.1.0dev1...v0.1.0dev2
[0.1.0dev1]: https://github.com/Azure/Connectors-Python-SDK/releases/tag/v0.1.0dev1

