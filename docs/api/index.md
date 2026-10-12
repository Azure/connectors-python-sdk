# API reference

The API reference is generated from the current Python source on every documentation build.

## Synchronous core SDK

Root core modules provide synchronous client lifecycle, HTTP behavior,
serialization, exceptions, and trigger payload types. The aio core section
documents asynchronous runtime counterparts.

## Connector clients

Each shipped connector has a synchronous root module containing its client and
the shared request and response declarations reachable from that connector's
contract. The matching aio module contains the asynchronous client and
re-exports the exact root-owned declarations. Both clients expose identical
unsuffixed operation names.

Root pageable operations return `ItemPaged`; aio pageable operations return
`AsyncItemPaged`. Long-running operation pollers are not generated in this
release.

All four API sections are discovered automatically, so new paired modules
appear without a separate documentation allow-list.

Generated connector source is read-only. Corrections to generated signatures or docstrings must be made in the CodefulSdkGenerator and regenerated into this repository.

!!! note
    Python module names follow managed connector API names. Public class names preserve the generated contract naming used by the installed package.
