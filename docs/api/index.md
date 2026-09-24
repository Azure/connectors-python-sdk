# API reference

The API reference is generated from the current Python source on every documentation build.

## Core SDK

Core modules provide authentication, client lifecycle, HTTP behavior, serialization, options, exceptions, and trigger payload types. These modules are maintained by the SDK team.

## Connector modules

Each shipped connector has its own generated module containing an asynchronous client and the request and response models reachable from that connector's contract. Connector pages are discovered automatically, so newly generated modules appear without a separate documentation allow-list.

Generated connector source is read-only. Corrections to generated signatures or docstrings must be made in the CodefulSdkGenerator and regenerated into this repository.

!!! note
    Python module names follow managed connector API names. Public class names preserve the generated contract naming used by the installed package.
