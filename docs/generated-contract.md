# Generated connector contract

Generated connector clients are committed artifacts produced by the BPM
CodefulSdkGenerator. Do not hand-edit files under `src/azure/connectors/` or
`src/azure/connectors/aio/`.

## Paired output

One Python generation request must emit an atomic pair for every connector:

```text
src/azure/connectors/<connector>.py       # sync client and shared declarations
src/azure/connectors/aio/<connector>.py   # async client, imports shared declarations
```

If either member fails, the generator must not leave a partial pair. Both files
must come from the same generator revision and the same captured connector
contract.

## Public invariants

- Root operations are synchronous; aio operations are asynchronous except that
  pageable methods construct and return their pager without being awaited.
- Paired clients have the same class name, unsuffixed operation names,
  parameters, request controls, and non-paging return payload types.
- Root read-collection operations return `ItemPaged`; aio read-collection
  operations return `AsyncItemPaged`. This includes bounded read collections
  without a continuation-link contract. Arrays returned by mutations and other
  actions remain eager operation payloads.
- Dataclasses, type aliases, enums, and `TRIGGER_OPERATIONS` are declared only
  in root and imported by aio, preserving object identity.
- Swagger-required dataclass properties are required constructor arguments;
  only optional properties default to `None`.
- Each module defines an explicit `__all__`; paired exports match except for the
  distinct client object.
- Generated clients are available from their connector modules and as lazy
  package-root exports. The generated registry and `.pyi` files keep runtime
  discovery and static typing synchronized without eagerly importing every
  connector module.
- Retained operations with an HTTP 202 `Location` response contract use
  `begin_*` and return `LROPoller[T]` or `AsyncLROPoller[T]`. LRO classification
  takes precedence over paging, and bare HTTP 202 responses remain ordinary.
- `ConnectorException` derives from Azure Core `HttpResponseError` while
  retaining connector operation, path, status, and response-body details.

Paging must preserve validation, connector error behavior, empty pages,
continuation links, request controls, and response hooks on every request.
Service links and caller-provided continuation tokens pass through the same URL
resolver. Links from a different origin are rebased onto the connection runtime
origin before the next request.

The shipped catalog contains exactly 44 paired LRO methods: 5 in Kusto and 39
in Plumsail. Internal Kusto retrieval helpers and superseded Plumsail revisions
remain filtered by the existing operation-retention rules.

## Regeneration evidence

The `generation.manifest.json` file records the exact generator commit and
compiler hash, source subscription and region, capture time, and hashes for
every generated module, registry, and package type stub. Source Swagger files
used during generation are not committed to this repository.

Use the pinned generator revision and the live-metadata workflow in
`GENERATION.md` to refresh the complete sync/aio catalog. Review source metadata
changes and generated output together before updating the manifest.

Before submission, verify exact root/aio catalog parity, compile every generated
module, run connector and runtime tests, validate both sample catalogs, build
the documentation, and inspect the wheel and source distribution inventories.
