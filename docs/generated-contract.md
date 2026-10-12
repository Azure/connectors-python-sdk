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
- Root pageable operations return `ItemPaged`; aio pageable operations return
  `AsyncItemPaged`.
- Dataclasses, type aliases, enums, and `TRIGGER_OPERATIONS` are declared only
  in root and imported by aio, preserving object identity.
- Each module defines an explicit `__all__`; paired exports match except for the
  distinct client object.
- Generated clients are imported from their connector modules. Package-level
  generated-client registries and barrel exports are not part of the contract.
- Retained operations with an HTTP 202 `Location` response contract use
  `begin_*` and return `LROPoller[T]` or `AsyncLROPoller[T]`. LRO classification
  takes precedence over paging, and bare HTTP 202 responses remain ordinary.

Paging must preserve validation, connector error behavior, empty pages,
continuation links, request controls, and response hooks on every request.
Continuation links from a different origin are rebased onto the connection
runtime origin before the next request.

The shipped catalog contains exactly 44 paired LRO methods: 5 in Kusto and 39
in Plumsail. Internal Kusto retrieval helpers and superseded Plumsail revisions
remain filtered by the existing operation-retention rules.

## Regeneration evidence

Record the exact generator commit, linked generator change, source subscription
and region, capture time, and a hash of each ephemeral Swagger response in the
SDK pull request. Generate the sync/aio pair from one capture. Reviewers should
use an independent live capture; connector responses and caches are not
committed to this repository.

Before submission, verify exact root/aio catalog parity, compile every generated
module, run connector and runtime tests, validate both sample catalogs, build
the documentation, and inspect the wheel and source distribution inventories.
