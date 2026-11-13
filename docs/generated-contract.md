# Generated connector contract

Generated connector clients are committed artifacts produced by the BPM
CodefulSdkGenerator. Do not hand-edit generated files under `src/azure/connectors/`.

## Async-only output

One Python generation request emits one root module for every connector:

```text
src/azure/connectors/<connector>.py       # async client, models, and metadata
```

Each module must come from the recorded generator revision and connector
contract. There is no synchronous mirror or separate aio catalog.

## Public invariants

- Root operations are asynchronous except that
  pageable methods construct and return their pager without being awaited.
- Clients expose unsuffixed operation names and keyword-only optional parameters
  and request controls.
- Read-collection operations return `AsyncItemPaged`. This includes bounded read collections
  without a continuation-link contract. Arrays returned by mutations and other
  actions remain eager operation payloads.
  ServiceNow knowledge search yields the `articles` array through
  `list_knowledge_articles`; the `meta` object is not an item. Its Swagger
  declares no continuation link, so iteration makes one request.
- Dataclasses, type aliases, enums, and `TRIGGER_OPERATIONS` are declared in
  the root connector module alongside the async client.
- Swagger-required dataclass properties are required constructor arguments;
  only optional properties default to `None`.
- Each module defines an explicit `__all__`.
- Generated clients are available from their connector modules and as lazy
  package-root exports. The generated registry and `.pyi` files keep runtime
  discovery and static typing synchronized without eagerly importing every
  connector module.
- Retained operations with an HTTP 202 `Location` response contract use
  `begin_*` and return `AsyncLROPoller[T]` after awaiting the call. LRO classification
  takes precedence over paging, and bare HTTP 202 responses remain ordinary.
- `ConnectorException` derives from Azure Core `HttpResponseError` while
  retaining connector operation, path, status, and response-body details.

Paging must preserve validation, connector error behavior, empty pages,
continuation links, request controls, and response hooks on every request.
Service links and caller-provided continuation tokens pass through the same URL
resolver. Links from a different origin are rebased onto the connection runtime
origin before the next request.

The shipped catalog contains exactly 44 LRO methods: 5 in Kusto and 39
in Plumsail. Internal Kusto retrieval helpers and superseded Plumsail revisions
remain filtered by the existing operation-retention rules.

## Multipart form-data

Swagger 2.0 `formData` parameters become typed operation arguments, not JSON
model properties. File fields accept bytes or `MultipartFile`; optional fields
remain keyword-only and disappear from the request when omitted. Internal
defaults stay on the wire without becoming public arguments.

The shared encoder uses a native multipart writer and forwards its complete
boundary-bearing content type with the buffered body through Azure Core.
Files retain their original bytes, filename, and media type. Scalar fields,
empty strings, and repeated names remain separate MIME parts. Arrays use their
declared `csv`, `ssv`, `tsv`, `pipes`, or `multi` collection format.
File disposition parameters use quoted-string escaping rather than percent
encoding, preserving spaces, Unicode, percent signs, and embedded quotes without
requiring the receiver to URL-decode filenames.

Bodyless operations remain callable when only their `consumes` metadata says
multipart. File arrays, unknown collection formats, mixed body/form-data
declarations, and `multipart/mixed` request payloads remain unsupported.

## Regeneration evidence

Source Swagger files used during generation are not committed to this
repository. Record the exact generator commit and source metadata in the pull
request, then use the live-metadata workflow in `GENERATION.md` to refresh the
complete 101-connector async catalog. Review source metadata changes and generated output
together before committing regenerated clients.

Before submission, verify the root catalog inventory, compile every generated
module, run connector and runtime tests, validate all 101 async samples, build
the documentation, and inspect the wheel and source distribution inventories.
