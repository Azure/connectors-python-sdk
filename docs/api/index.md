# API reference

The API reference is generated from the current Python source on every documentation build.

## Async core SDK

Root core modules provide asynchronous client lifecycle, HTTP behavior,
serialization, exceptions, and trigger payload types. The root runtime is async-only.

## Connector clients

Each shipped connector has an asynchronous root module containing its client and
the shared request and response declarations reachable from that connector's
contract. No separate aio catalog or synchronous mirror is provided. Import
clients and models from `azure.connectors.<connector>`.

Pageable operations return `AsyncItemPaged` without awaiting construction.
Location-backed long-running operations return `AsyncLROPoller` from awaited
`begin_*` methods.

Both API sections are discovered automatically, so new connector modules
appear without a separate documentation allow-list.

Generated connector source is read-only. Corrections to generated signatures or docstrings must be made in the CodefulSdkGenerator and regenerated into this repository.

!!! note
    Python module names follow managed connector API names. Public class names preserve the generated contract naming used by the installed package.
