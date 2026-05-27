# Python SDK Roadmap

## Overview

This document tracks the development roadmap for the Azure Connectors Python SDK, including connector support, PyPI publication, samples, and planned features.

## Current Status (v0.1.0dev2)

| Component | Status | Notes |
|-----------|--------|-------|
| Core SDK | ✅ Complete | Token providers, HTTP client, retry logic, async/await |
| Office 365 | ✅ Complete | 53 methods, 41 tests, 79% coverage |
| SharePoint | ✅ Complete | 45 methods, 44 tests, 57% coverage |
| Teams | ✅ Complete | 49 methods, 27 tests passing, 73% coverage (18 skipped) |
| Kusto | ✅ Complete | 6 methods, 37 tests, 98% coverage |
| MS Graph | ✅ Complete | 7 methods, 46 tests |
| CI/CD | ✅ Complete | GitHub Actions for pytest, flake8, build |
| PyPI Publishing | ✅ Complete | Release workflow ready |
| Documentation | ✅ Complete | README, samples, test docs |

---

## Phase 1: Core Infrastructure & Initial Connectors ✅

**Status:** Complete (v0.1.0dev1 - v0.1.0dev2)

### Completed

- [x] Core SDK abstractions (`ConnectorClientBase`, `TokenProvider`, `ConnectorHttpClient`)
- [x] Authentication providers (Managed Identity, Azure Identity, Connection String)
- [x] HTTP client with retry logic and exponential backoff
- [x] Async/await support throughout
- [x] Type hints and dataclass models
- [x] Office 365 Outlook connector
- [x] SharePoint Online connector
- [x] Microsoft Teams connector
- [x] Azure Data Explorer (Kusto) connector
- [x] Microsoft Graph connector
- [x] Comprehensive test suite (305 tests, 75% coverage)
- [x] Sample code for all connectors
- [x] Connection setup PowerShell script
- [x] GitHub Actions CI/CD
- [x] PyPI publishing workflow
- [x] Documentation (README, guides, API docs)

---

## Phase 2: PyPI Publication & Ecosystem

**Target:** Q2 2026

### Goals

- [ ] Publish `azure-connectors` to PyPI
  - [x] Package metadata and classifiers
  - [x] Version management workflow
  - [x] PyPI authentication setup
  - [ ] First stable release (v0.1.0)
- [ ] Package distribution
  - [x] Wheel and source distribution builds
  - [x] GitHub Releases with artifacts
  - [ ] TestPyPI validation
  - [ ] PyPI publication
- [ ] Documentation enhancements
  - [ ] Sphinx documentation site
  - [ ] API reference auto-generation
  - [ ] Tutorial series
  - [ ] Migration guide from Logic Apps

### Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| v0.1.0dev2 published to TestPyPI | April 2026 | ⏳ In Progress |
| Documentation site launched | May 2026 | 📋 Planned |
| v0.1.0 stable release to PyPI | May 2026 | 📋 Planned |

---

## Phase 3: Additional High-Priority Connectors

**Target:** Q3 2026

### M365 Expansion

| Priority | Connector | Use Cases | Status |
|----------|-----------|-----------|--------|
| 3.1 | **OneDrive for Business** | File operations, knowledge base | 📋 Planned |
| 3.2 | **Office 365 Users** | User directory, profile data | 📋 Planned |
| 3.3 | **Office 365 Groups** | Group management | 📋 Planned |
| 3.4 | **Planner** | Task management | 📋 Planned |

### Data & Integration

| Priority | Connector | Use Cases | Status |
|----------|-----------|-----------|--------|
| 3.5 | **Excel Online** | Spreadsheet operations | 📋 Planned |
| 3.6 | **Dataverse** | Power Platform integration | 📋 Planned |
| 3.7 | **SQL Server** | Database operations | 📋 Planned |

### Azure Services

| Priority | Connector | Use Cases | Status |
|----------|-----------|-----------|--------|
| 3.8 | **Azure Blob Storage** | File storage (if not using Functions binding) | 📋 Planned |
| 3.9 | **Azure Log Analytics** | Query/ingest operations | 📋 Planned |
| 3.10 | **Event Hubs** | Event streaming (if not using Functions binding) | 📋 Planned |

---

## Phase 4: Python Samples & Best Practices

**Target:** Q3 2026

### Sample Projects

- [ ] **Azure Functions samples**
  - [ ] HTTP trigger with Office 365 email
  - [ ] Timer trigger with SharePoint list sync
  - [ ] Blob trigger with Teams notification
  - [ ] Durable Functions orchestration
- [ ] **FastAPI integration**
  - [ ] REST API with connector clients
  - [ ] Webhook receivers for triggers
  - [ ] OpenAPI documentation
- [ ] **Django/Flask examples**
  - [ ] Web app with connector integration
  - [ ] Background tasks with celery
- [ ] **Data processing pipelines**
  - [ ] Kusto query to DataFrame
  - [ ] SharePoint to data lake
  - [ ] Teams bot integration

### Best Practices Documentation

- [ ] Error handling patterns
- [ ] Retry and timeout configuration
- [ ] Authentication in production
- [ ] Performance optimization
- [ ] Testing strategies
- [ ] Logging and monitoring

---

## Phase 5: Advanced Features

**Target:** Q4 2026

### SDK Enhancements

- [ ] **Trigger support**
  - [ ] Polling triggers (webhooks where supported)
  - [ ] Connector Namespace integration
  - [ ] Event Grid integration
- [ ] **Batch operations**
  - [ ] Bulk send for email
  - [ ] Batch SharePoint operations
- [ ] **Streaming support**
  - [ ] Large file uploads/downloads
  - [ ] Chunked data transfer
- [ ] **Caching layer**
  - [ ] Token caching
  - [ ] Response caching
  - [ ] Cache invalidation

### Developer Experience

- [ ] **Code generation CLI**
  - [ ] Python CLI tool for generating clients
  - [ ] Custom connector support
  - [ ] Swagger-to-Python pipeline
- [ ] **VS Code extension**
  - [ ] IntelliSense for connector operations
  - [ ] Code snippets
  - [ ] Connection manager
- [ ] **Type stub generation**
  - [ ] PEP 561 compliance
  - [ ] Mypy compatibility

---

## Phase 6: Enterprise & Ecosystem

**Target:** 2027

### Enterprise Features

- [ ] **Multi-region support**
  - [ ] Region affinity configuration
  - [ ] Cross-region failover
- [ ] **Compliance & security**
  - [ ] Private endpoints
  - [ ] CMK support
  - [ ] Audit logging
- [ ] **Performance & scale**
  - [ ] Connection pooling
  - [ ] Rate limiting
  - [ ] Circuit breakers

### Ecosystem Integration

- [ ] **Azure SDK integration**
  - [ ] Unified configuration
  - [ ] Shared credential chain
  - [ ] Consistent logging
- [ ] **Observability**
  - [ ] OpenTelemetry support
  - [ ] Application Insights integration
  - [ ] Custom metrics
- [ ] **Language parity**
  - [ ] Feature alignment with .NET SDK
  - [ ] Shared test cases
  - [ ] Cross-language samples

---

## Connector Priority Matrix

Based on usage data, agentic solution value, and community requests:

| Tier | Connectors | Priority |
|------|------------|----------|
| **Tier 1** (Complete) | Office 365, SharePoint, Teams, Kusto, MS Graph | ✅ |
| **Tier 2** (Next) | OneDrive, Excel, Dataverse, SQL | 📋 Q3 2026 |
| **Tier 3** (Future) | Dynamics 365, Salesforce, Blob Storage, Log Analytics | 📋 Q4 2026 |
| **Tier 4** (Backlog) | SMTP, SFTP, ServiceNow, Snowflake | 📋 2027 |

---

## Code Generation Status

| Component | Status | Notes |
|-----------|--------|-------|
| LogicAppsCompiler with `--python` flag | ✅ Available | BPM PR 15456622 |
| Python output templates | ✅ Complete | Dataclasses, async methods |
| Type hint generation | ✅ Complete | Full Python 3.10+ typing |
| Docstring generation | ✅ Complete | From connector metadata |
| Test generation | 📋 Planned | Auto-generate unit tests |

See [GENERATION.md](GENERATION.md) for code generation documentation.

---

## Community Feedback & Requests

We track community requests in [GitHub Issues](https://github.com/Azure/Connectors-Python-SDK/issues). Top requests:

1. **More connectors** — OneDrive, Excel, Dataverse
2. **Trigger support** — Polling triggers for Office 365, SharePoint
3. **Code generation CLI** — Standalone tool for custom connectors
4. **Better documentation** — More examples, tutorials
5. **Azure Functions integration** — Native Functions bindings

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Requesting new connectors
- Reporting bugs
- Submitting pull requests
- Code generation contributions

For questions and discussions, visit [GitHub Discussions](https://github.com/Azure/LogicApps/discussions).


1. **Function app registers** a callback URL with the connector service at deployment time (cloud) or F5 time (local)
2. **Connector service monitors** for events on its own compute (Logic Apps multi-tenant infrastructure)
3. **Events push to the function** via HTTP callback — the function wakes up and processes the event
4. **No scale controller work** needed on Functions side (HTTP push triggers scaling naturally)

This means connector triggers do **not** run on Functions compute. The connector infrastructure handles all polling/monitoring (including any fallback polling if webhook subscribe fails) and only delivers an HTTP push when an event occurs; Azure Functions never performs polling on its own compute.

**Webhook expiry/refresh:** The connector infrastructure owns webhook lifecycle management, including automatic refresh of expiring webhook subscriptions. The Functions extension does **not** need to handle webhook renewal. (Settled 2026-03-10.)

#### Implementation Approach: Worker Library → Extension

| Phase | Approach | Scope | Languages |
|-------|----------|-------|-----------|
| **5a** | Worker library (C# NuGet) | Quick POC, end-to-end proof | C# only |
| **5b** | Host extension | Production, cross-language | All Functions languages |

> **Naming:** `5a`/`5b` refer to the two implementation phases (worker library → host extension). Within Phase 5a, the trigger support plan groups tasks into sub-phases `5A`–`5D`.

**Rationale**: Worker library is a 1-2 day POC effort. Host extension (like Durable Functions, MCP) requires deeper Functions runtime integration but works across all languages. Start with worker library, prove the model, then build the extension.

**Reference implementations**:

- Azure Functions Event Grid extension — similar webhook registration + callback pattern.
- [azure-functions-connectors-python](https://github.com/anthonychu/azure-functions-connectors-python) — Python sample showing connector trigger + action usage in Functions, including a Teams reply example. Must be studied in detail (see [Execution Plan](#execution-plan)).

#### Local Development (F5 Experience)

Local webhook triggers require:

1. **Dev tunnels / ngrok** to expose a local port as a public endpoint
2. **Webhook registration** at F5 time with the connector service pointing to the tunnel URL
3. **Separate dev/prod connectors** — configured via `local.settings.json` (dev) vs app settings (prod)

The Functions team is already improving local CLI tooling for tunnel integration.

#### Design Decisions from Brainstorm

| Decision | Rationale |
|----------|-----------|
| **No output bindings** | Use SDK action clients directly. Wait for customer feedback on whether input bindings (DI-injected clients) are needed. |
| **Strongly typed trigger payloads** | SDK code generation extends to triggers — each connector produces typed trigger output models. |
| **Generic + typed trigger attributes** | `[ConnectorTrigger(type, operation)]` for broad coverage + per-connector typed attributes (e.g., `[Office365OutlookTrigger]`) for popular connectors. |
| **Event notification, not content push** | For large files (SharePoint, Outlook attachments), trigger delivers metadata; user code fetches content separately via action client. |
| **No streaming initially** | Extension route has gRPC limitation for large payloads. Start with notification model; add streaming later. |
| **Deployment-time registration (cloud)** | Webhook relationships set up at deploy/provision time, not runtime. Locally, at F5 startup time. |
| **Webhook refresh owned by connector infra** | The connector platform handles webhook expiry and automatic re-registration. The Functions extension does not manage webhook lifecycle. |

#### Open Questions (as of 2026-03-13)

| Question | Owner | Context |
|----------|-------|---------|
| **VNet-locked Function Apps** — Pure webhooks break when inbound traffic is restricted (Private Endpoints, IP restrictions). Do we need pull delivery / polling from Functions side? | Functions + Connectors | Event Grid hybrid model (webhook + pull) suggested. May need Trigger Monitor / Scale Controller outbound polling as alternative. |
| **Local F5 tunnel setup** — How to automatically configure dev tunnels for webhook triggers across all languages? | Functions | Functions team improving local CLI tooling. We need to ensure our webhook registration works with tunnel URLs. |
| **RBAC for connector resources** — What Azure role(s) does the Function App identity need? New role required? | Connectors | Need to document minimum RBAC for `Microsoft.Web/connections`. |
| **Multi-language trigger data types** — Python decorators, Java annotations, Node.js methods for trigger payloads | Connectors + Functions | Our C# SDK generates typed trigger models. Need equivalent type generation strategy for Python/Node/Java. |

#### Known Risks

| Risk | Source | Impact | Mitigation |
|------|--------|--------|------------|
| **Webhook trigger 404 on subscribe** | [M365 Agent POC](https://github.com/coreai-microsoft/m365-agent-poc) found that `ApiConnectionNotification` (webhook-style) triggers return 404 on subscribe in LA Standard. Had to fall back to polling. | If this is a connector infrastructure issue (not LA-specific), our webhook model may not work for all connectors. | Validate webhook registration works from Functions extension using a different code path than LA's `ApiConnectionNotification` handler. If connector-level, design polling fallback. |
| **Teams connector gaps in LA Standard** | Same POC. LA Standard uses a different APIM gateway that restricts Graph API endpoints — chat/DM paths return 404. | Teams trigger feasibility may be limited to channel-level events. | Evaluate Graph API direct calls as alternative. Prioritize Office 365 email trigger (confirmed working) for Phase 5a POC. |
| **Catch-up storm on polling fallback** | If connector is down during polling, queued events process all at once on restart, potentially overwhelming the function. | Relevant only if we need polling fallback for connectors where webhook subscribe fails. | Batch-size limits in the connector service's polling loop; backpressure handling in the Functions extension. User function code should not need to throttle. |
| **VNet inbound restrictions** | Webhook-only model fails for Function Apps with locked-down inbound. | Enterprise customers with Private Endpoints cannot receive webhook callbacks. | Design a polling fallback where Functions Trigger Monitor performs outbound calls to connector service. Similar to Event Grid pull delivery model. |

#### Priority Triggers

| Connector | Trigger Type | 90-Day Executions | Status |
|-----------|--------------|-------------------|--------|
| Office 365 | Email arrival | 25.7B | ⬜ Design |
| SharePoint Online | File/list changes | 22.9B | ⬜ Design |
| Service Bus | Message trigger | 10.3B | ⬜ Evaluate overlap with native Functions binding |
| OneDrive for Business | File trigger | 5.3B | ⬜ Design |
| SQL | Row trigger | 2.6B | ⬜ Design |

**Most popular SaaS connectors for triggers**: Outlook and Teams for SaaS; Service Bus for PaaS.

---

## Execution Plan

### Immediate Next Steps

1. ~~**Generate SharePoint Online connector** (Priority 1.1)~~ ✅ Complete
   - [x] Run generator: `--directClient --connectors=sharepointonline`
   - [x] Add generated code to SDK repo
   - [x] Verify compilation (fixed 2 generator bugs)
   - [x] Create PR
   - [x] Validate end-to-end with POC (GetSharePointLists)

1. ~~**Study Python connector reference implementations**~~ ✅ Complete
   - [x] Clone [azure-functions-connectors-python](https://github.com/anthonychu/azure-functions-connectors-python) locally
   - [x] Analyze the Teams, Office 365, and SharePoint samples — trigger registration, callback handling, payload shapes
   - [x] Analyze [m365-agent-poc](https://github.com/coreai-microsoft/m365-agent-poc) — Brain-and-Nerves pattern, Logic App triggers
   - [x] Analyze Codeful Workflows SDK (`logicapps-sdk`) — code-to-workflow compiler approach, generated trigger classes, trigger type distinctions
   - [x] Document how trigger attributes are defined (Python decorators vs .NET attributes vs C# builder API)
   - [x] Identify patterns applicable to our C# worker library POC (Phase 5a)
   - [x] Identify gaps or differences from our current design assumptions
   - [x] Write up findings (internal analysis document)

1. **Generate Microsoft Graph connector** (Priority 1.2)
   - [ ] Run generator: `--directClient --connectors=graph` (or similar)
   - [ ] Add generated code to SDK repo
   - [ ] Verify compilation
   - [ ] Create PR

1. **SDK documentation**
   - [x] Add README with usage examples
   - [x] Document connection setup process ([docs/connection-setup.md](docs/connection-setup.md))
   - [ ] Add NuGet package instructions (future)

### Per-Connector Validation Checklist

For each new connector, complete these steps:

#### Code Generation

- [ ] Generate DirectClient code: `--directClient --connectors={connectorName}`
- [ ] Add to SDK repo as `Generated/{Connector}Extensions.cs`
- [ ] Fix any compilation errors (document generator bugs found)
- [ ] Create PR

#### Connection Setup (see [docs/connection-setup.md](docs/connection-setup.md))

- [ ] Create connection from Logic Apps Standard app
- [ ] Get connection runtime URL: `az resource show ... --query "properties.connectionRuntimeUrl"`
- [ ] Add access policy for your identity
- [ ] Wait for ACL propagation (1-5 minutes)
- [ ] Test via CLI: `az rest --method GET --uri "{runtimeUrl}/{path}" --resource "https://apihub.azure.com"`

#### POC Validation

- [ ] Add runtime URL to `local.settings.json`
- [ ] Create test endpoint in POC
- [ ] Validate end-to-end request

---

## Related Analysis

- **Azure Functions + Logic Apps Connector Integration** — Idea proposal from the Azure Functions team for bringing Logic Apps connectors into Functions as first-class triggers and action clients. Our SDK is the implementation of the "action clients" portion; the proposal validates our architecture and identifies future work (triggers, OBO, Python SDK).
- **Connector Trigger Support for Azure Functions (2026-02-20)** — Cross-team brainstorm establishing the webhook/Event Grid pattern for triggers, worker library → extension phased approach, and local dev requirements.
- **[Python connector samples](https://github.com/anthonychu/azure-functions-connectors-python)** — Reference implementation showing connector trigger + action usage in Functions (Python). Timer+Blob+Queue architecture with cursor-based polling. Analyzed internally.
- **[M365 Agent POC](https://github.com/coreai-microsoft/m365-agent-poc)** — Working POC using today's GA connectors with Functions (LA Connector as trigger layer, Functions as code runner). Found v1/v2/v3 connector version surprises and webhook subscribe 404 issues. Analyzed internally.
- **[Codeful Workflows SDK](https://github.com/AzureAD/logicapps-sdk)** (`logicapps-sdk`) — C# code-to-workflow compiler. Generates typed trigger classes for all 1000+ managed connectors. Compiles to workflow.json and delegates trigger lifecycle to Logic Apps runtime. Different approach from our direct-invocation SDK but shares swagger-to-trigger-model generation. Analyzed internally.
- **BPM Runtime Trigger Architecture** — Analyzed the Logic Apps runtime trigger implementation: three trigger strategies (polling, pure webhook, notification hybrid), dual-job provisioning, class hierarchy, coordination protocol. Extraction plan and trigger taxonomy documentation available internally.
- **Connector Namespace API Design** — Control plane API design for `Microsoft.Web/connectorGateways` (internal document).

### Backlog

1. **Transition to Connector Namespace API** (`Microsoft.Web/connectorGateways`)
   - The Connector Namespace resource exposes connections and triggers as data-plane resources without requiring Logic Apps. Available in First Release / TIP regions (as of 2026-03-05) but not yet GA.
   - **Blocked on:** Connector Namespace reaching GA with stable API surface.
   - [ ] Monitor Connector Namespace API availability and documentation
   - [ ] Evaluate migration path from `Microsoft.Web/connections` direct access
   - [ ] Update SDK connection setup to support Connector Namespace resource type
   - [ ] Update POC to validate Connector Namespace–based connection flow
   - [ ] Update `docs/connection-setup.md` with Connector Namespace instructions

1. **Multi-language trigger SDK** (Python, Node.js, Java)

1. **Connection setup automation** (VS Code extension / LSP)
   - AI agents can already automate the full connection lifecycle via the `connection-setup` skill (`.github/skills/connection-setup/SKILL.md`): Connector Namespace creation, connection creation, OAuth consent link, access policies, and settings injection.
   - **Next:** Build native VS Code extension support (or LSP ConnectionsService) for in-editor connection creation with UI, following the building blocks documented in the skill file.
   - [ ] LSP ConnectionsService: detect existing connections, guided creation flow
   - [ ] VS Code command palette: "Add Connector Connection" with connector picker
   - [ ] Auto-inject connection settings into `local.settings.json` per connection settings schema
   - [ ] Auto-detect Function App MSI and offer one-click access policy grant
   - [ ] Support both Format A (`__aiGatewayName` + `__connectionName`) and Format B (`__connectionRuntimeUrl`)
   - The Functions team needs trigger data type definitions for Python decorators, Node.js methods, and Java annotations.
   - **Depends on:** Phase 5a C# POC proving the trigger model.
   - [ ] Design cross-language type generation strategy
   - [ ] Evaluate whether CodefulSdkGenerator can emit Python/TypeScript/Java models
   - [ ] Coordinate with Functions team on integration points

## Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| BPM generator PR merged to master | ⏳ Awaiting review | Can work from feature branch, but need master for stability |
| OAuth connections for testing | ✅ Office365 works | Need connection setup for each new connector |
| Connector Namespace GA | ⬜ Not yet GA | Using `Microsoft.Web/connections` direct access until then |
| Functions extension for triggers | ⬜ Functions team owns | We provide SDK + connector-side delivery; they build the extension |
| MWF sync cadence | ✅ Established 2026-03-13 | Cross-team alignment on Connectors for Functions |

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Connectors with Actions | 10+ | 2 (Office365, SharePoint) |
| POC operations validated | 5+ | 3 (SendEmail, GetCategories, GetSharePointLists) |
| Partner adoption | 1+ team | 0 |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-04-03 | Initial public release with Office365, SharePoint, and Teams connector clients. Trigger support in active design. |

---

## Lessons Learned

### Generator Issues Discovered

| Issue | Connector | Fix | BPM Commit |
|-------|-----------|-----|------------|
| Multi-line descriptions break XML doc syntax | SharePoint | `EscapeXml` now replaces `\r\n`, `\n`, `\r` with spaces | `5eb6bf0` |
| Property name same as class name (CS0542) | SharePoint | Append `Value` suffix when property name matches type name | `5eb6bf0` |
| `null` properties sent to APIs that reject them | Office365 | Added `JsonIgnoreCondition.WhenWritingNull` to JsonOptions | Earlier commit |

### Per-Connector Notes

| Connector | File Size | Operations | Issues Found | Notes |
|-----------|-----------|------------|--------------|-------|
| Office365 | ~170KB | ~50 | WhenWritingNull | Clean generation after fix |
| SharePoint | ~100KB | ~110 | 2 (newlines, property collision) | Validated with GetAllTablesAsync listing 8 libraries |
