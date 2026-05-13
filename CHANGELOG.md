# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
  - `TriggerCallbackPayload` — Generic types for Connector Gateway trigger integration
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
- Setup script for creating Connector Gateway connections (`Setup-Connection.ps1`)
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

[Unreleased]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.2.0b1...HEAD
[0.2.0b1]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.1.0dev2...v0.2.0b1
[0.1.0dev2]: https://github.com/Azure/Connectors-Python-SDK/compare/v0.1.0dev1...v0.1.0dev2
[0.1.0dev1]: https://github.com/Azure/Connectors-Python-SDK/releases/tag/v0.1.0dev1

