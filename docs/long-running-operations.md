# Long-running operations

Kusto and Plumsail operations that declare an HTTP 202 `Location` polling
contract use Azure Core pollers. Their generated method names begin with
`begin_`.

## Asynchronous clients

```python
from azure.connectors.kusto import KustoClient


async with KustoClient(connection_url, credential) as client:
    poller = await client.begin_list_kusto_results(input=query)
    result = await poller.result()
```

`AsyncLROPoller` starts polling when it is awaited through `result()`, `wait()`,
or the poller itself.

## Polling behavior

- HTTP 202 responses must provide a `Location` header.
- Polling requests use GET and honor numeric or HTTP-date `Retry-After` values.
- Relative and connector-backend polling URLs are routed through the
  authenticated connection runtime origin.
- `timeout`, `headers`, `client_request_id`, and `response_hook` are forwarded
  to the initial request and every poll request. `timeout` applies to each
  network request, not the lifetime of the long-running operation.
- A non-202 success response completes the poller. Terminal non-success
  responses raise `ConnectorException`.

Keep the connector client open until polling completes. Poller continuation
tokens, cancellation, `Azure-AsyncOperation` status documents, and
`Operation-Location` final-resource protocols are not currently supported.
