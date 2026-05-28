# SDK-Type Bindings for Azure Functions

This document explains how to implement SDK-type bindings for the Azure Connectors Python SDK, enabling Python Function apps to work with strongly-typed objects instead of raw JSON payloads.

## Overview

SDK-type bindings allow Azure Functions to automatically deserialize connector payloads into rich, typed Python objects. Instead of manually parsing JSON and accessing dictionary keys, you can work directly with dataclass instances that have proper type hints, IDE autocomplete, and field documentation.

**Without SDK-type bindings:**

```python
import azure.functions as func

app = func.FunctionApp()

@app.connector_trigger(arg_name="payload")
def process_email(payload: str):
    data = json.loads(payload)
    subject = data.get("body", {}).get("value", [{}])[0].get("subject")
    from_address = data.get("body", {}).get("value", [{}])[0].get("from")
    # Error-prone, no type hints, no IDE support
```

**With SDK-type bindings:**

```python
import azure.functions as func
import azurefunctions.extensions.connectors.office365 as office365

app = func.FunctionApp()

@app.connector_trigger(arg_name="messages")
def process_emails(messages: List[office365.ClientReceiveMessage]):
    for message in messages:
        print(message.subject)      # IDE autocomplete works
        print(message.from_)        # Typed as Optional[str]
        print(message.importance)   # Already converted to int
```

## Important: `from_json` Is Not Auto-Generated

The `from_json` class method is **not automatically generated** by the SDK code generator. The generator creates dataclass definitions from connector Swagger/OpenAPI specifications, but the deserialization logic must be implemented manually.

This is intentional because:

1. **Payload structures vary** — Different triggers and operations return payloads in different formats
2. **Field mapping requires context** — JSON camelCase fields must be mapped to Python snake_case properties
3. **Type conversions are type-specific** — Some fields need conversion (e.g., importance strings to integers)
4. **Nested objects require custom parsing** — Attachments, sensitivity labels, and other nested types need dedicated parsing logic

## Payload Structure

Azure Functions connector triggers deliver payloads through an object with a `.value` attribute. The `from_json` method expects this structure:

```python
# The payload object (provided by Azure Functions runtime)
payload.value  # Contains either a JSON string or dict
```

The inner structure follows one of two patterns:

### Batch Response (Multiple Items)

```json
{
  "body": {
    "value": [
      { "id": "item1", "subject": "First item", ... },
      { "id": "item2", "subject": "Second item", ... }
    ]
  }
}
```

### Single Item Response

```json
{
  "body": {
    "id": "item1",
    "subject": "Single item",
    ...
  }
}
```

## Implementing `from_json` for a New Type

Follow these steps to add SDK-type binding support to a dataclass.

### Step 1: Identify the Dataclass

Find the dataclass you want to support. For example, `GraphCalendarEventClientReceive`:

```python
@dataclass
class GraphCalendarEventClientReceive:
    """Response for Get event (V3)"""
    
    subject: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    # ... other fields
```

### Step 2: Add the `from_json` Class Method

Add a `from_json` class method that:

1. Validates the payload has a `.value` attribute
2. Parses JSON if the value is a string
3. Handles both batch and single-item structures
4. Maps JSON fields to dataclass fields
5. Parses nested objects (attachments, etc.)

```python
@dataclass
class GraphCalendarEventClientReceive:
    """Response for Get event (V3)"""
    
    subject: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    # ... other fields

    @classmethod
    def from_json(cls, payload) -> List[GraphCalendarEventClientReceive]:
        """Parse a JSON payload and return a list of events.

        This method supports SDK-type bindings for Python Function apps.

        Args:
            payload: An object with a .value attribute containing a JSON 
                string or dictionary with the events.

        Returns:
            A list of GraphCalendarEventClientReceive objects.

        Raises:
            ValueError: If the payload structure is invalid.
        """
        # Step 1: Validate payload structure
        if not hasattr(payload, "value"):
            raise ValueError("Payload must have a 'value' attribute.")

        # Step 2: Parse JSON if needed
        if isinstance(payload.value, str):
            try:
                data = json.loads(payload.value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON payload: {e}.") from e
        else:
            data = payload.value

        # Step 3: Navigate to the items
        if isinstance(data, dict):
            body = data.get("body", data)
            if isinstance(body, dict):
                # Check for batch (has "value" list) or single item
                if "value" in body and isinstance(body.get("value"), list):
                    items_data = body.get("value")
                else:
                    # Single item - wrap in list
                    items_data = [body]
            else:
                items_data = []
        else:
            items_data = []

        if not isinstance(items_data, list):
            raise ValueError("Expected 'body.value' to contain a list.")

        # Step 4: Parse each item
        items: List[GraphCalendarEventClientReceive] = []
        for item in items_data:
            if not isinstance(item, dict):
                continue

            event = cls(
                subject=item.get("subject"),
                start=item.get("start"),
                end=item.get("end"),
                # Map all other fields...
            )
            items.append(event)

        return items
```

### Step 3: Handle Field Name Mapping

Map JSON camelCase field names to Python snake_case:

| JSON Field | Python Field |
|------------|--------------|
| `receivedDateTime` | `received_date_time` |
| `hasAttachments` | `has_attachments` |
| `toRecipients` | `to_recipients` |
| `bodyPreview` | `body_preview` |
| `isRead` | `is_read` |
| `from` | `from_` (reserved keyword) |

```python
message = cls(
    id=item.get("id"),
    from_=item.get("from"),              # "from" is reserved in Python
    to_recipients=item.get("toRecipients"),
    received_date_time=item.get("receivedDateTime"),
    has_attachments=item.get("hasAttachments"),
    body_preview=item.get("bodyPreview"),
    is_read=item.get("isRead"),
)
```

### Step 4: Handle Type Conversions

Some fields require conversion from JSON types to Python types:

```python
# Example: Convert importance string to integer
importance_map = {"low": 0, "normal": 1, "high": 2}

importance_value = item.get("importance")
importance_int: Optional[int] = None
if importance_value is not None:
    if isinstance(importance_value, int):
        importance_int = importance_value
    elif isinstance(importance_value, str):
        importance_int = importance_map.get(importance_value.lower())
```

### Step 5: Parse Nested Objects

For fields containing nested objects (like attachments), create instances of the nested dataclass:

```python
# Parse attachments
attachments_data = item.get("attachments")
attachments_list: Optional[List[ClientReceiveFileAttachment]] = None

if attachments_data and isinstance(attachments_data, list):
    attachments_list = []
    for attachment in attachments_data:
        if isinstance(attachment, dict):
            attachments_list.append(
                ClientReceiveFileAttachment(
                    id=attachment.get("id"),
                    name=attachment.get("name"),
                    content_bytes=attachment.get("contentBytes"),
                    content_type=attachment.get("contentType"),
                    size=attachment.get("size"),
                    is_inline=attachment.get("isInline"),
                )
            )
```

## Complete Example

Here's a complete implementation for `ClientReceiveMessage`:

```python
@dataclass
class ClientReceiveMessage:
    """Definition: ClientReceiveMessage"""

    from_: Optional[str] = None
    to: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    reply_to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    importance: Optional[int] = None
    body_preview: Optional[str] = None
    has_attachment: Optional[bool] = None
    id: Optional[str] = None
    internet_message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    date_time_received: Optional[str] = None
    is_read: Optional[bool] = None
    attachments: Optional[List[ClientReceiveFileAttachment]] = None
    is_html: Optional[bool] = None

    @classmethod
    def from_json(cls, payload) -> List[ClientReceiveMessage]:
        """Parse a JSON payload and return a list of ClientReceiveMessage objects.

        This method supports SDK-type bindings for Python Function apps, allowing
        functions to bind to and return rich ClientReceiveMessage objects instead
        of raw JSON payloads.

        Args:
            payload: An object with a .value attribute containing a JSON string 
                or dictionary with the email messages.
                Expected structure: {"body": {"value": [...messages...]}}

        Returns:
            A list of ClientReceiveMessage objects parsed from the payload.

        Raises:
            ValueError: If the payload structure is invalid or cannot be parsed.
        """
        importance_map = {"low": 0, "normal": 1, "high": 2}
        
        if not hasattr(payload, "value"):
            raise ValueError("Payload must have a 'value' attribute.")

        if isinstance(payload.value, str):
            try:
                data = json.loads(payload.value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON payload: {e}.") from e
        else:
            data = payload.value

        # Navigate to body.value to extract the list of messages
        if isinstance(data, dict):
            body = data.get("body", data)
            if isinstance(body, dict):
                if "value" in body and isinstance(body.get("value"), list):
                    messages_data = body.get("value")
                else:
                    messages_data = [body]
            else:
                messages_data = []
        else:
            messages_data = []

        if not isinstance(messages_data, list):
            raise ValueError("Expected 'body.value' to contain a list of messages.")

        messages: List[ClientReceiveMessage] = []
        for item in messages_data:
            if not isinstance(item, dict):
                continue

            # Parse attachments
            attachments_data = item.get("attachments")
            attachments_list: Optional[List[ClientReceiveFileAttachment]] = None
            if attachments_data and isinstance(attachments_data, list):
                attachments_list = []
                for attachment in attachments_data:
                    if isinstance(attachment, dict):
                        attachments_list.append(
                            ClientReceiveFileAttachment(
                                id=attachment.get("id"),
                                name=attachment.get("name"),
                                content_bytes=attachment.get("contentBytes"),
                                content_type=attachment.get("contentType"),
                                size=attachment.get("size"),
                                is_inline=attachment.get("isInline"),
                                last_modified_date_time=attachment.get(
                                    "lastModifiedDateTime"
                                ),
                                content_id=attachment.get("contentId"),
                            )
                        )

            # Convert importance string to int
            importance_value = item.get("importance")
            importance_int: Optional[int] = None
            if importance_value is not None:
                if isinstance(importance_value, int):
                    importance_int = importance_value
                elif isinstance(importance_value, str):
                    importance_int = importance_map.get(importance_value.lower())

            message = cls(
                id=item.get("id"),
                from_=item.get("from"),
                to=item.get("toRecipients"),
                cc=item.get("ccRecipients"),
                bcc=item.get("bccRecipients"),
                reply_to=item.get("replyTo"),
                subject=item.get("subject"),
                body=item.get("body"),
                importance=importance_int,
                body_preview=item.get("bodyPreview"),
                has_attachment=item.get("hasAttachments"),
                internet_message_id=item.get("internetMessageId"),
                conversation_id=item.get("conversationId"),
                date_time_received=item.get("receivedDateTime"),
                is_read=item.get("isRead"),
                attachments=attachments_list,
                is_html=item.get("isHtml"),
            )
            messages.append(message)

        return messages
```

## Writing Tests

Always add unit tests for your `from_json` implementation:

```python
class TestMyTypeFromJson:
    """Tests for MyType.from_json method."""

    def _make_payload(self, value):
        """Create a payload object with a .value attribute for testing."""
        from types import SimpleNamespace
        return SimpleNamespace(value=value)

    def test_from_json_parses_batch(self):
        """Test parsing batch messages."""
        payload = self._make_payload({
            "body": {
                "value": [
                    {"id": "1", "subject": "First"},
                    {"id": "2", "subject": "Second"},
                ]
            }
        })

        items = MyType.from_json(payload)

        assert len(items) == 2
        assert items[0].id == "1"
        assert items[1].subject == "Second"

    def test_from_json_parses_single_item(self):
        """Test parsing single item."""
        payload = self._make_payload({
            "body": {"id": "single", "subject": "Single Item"}
        })

        items = MyType.from_json(payload)

        assert len(items) == 1
        assert items[0].id == "single"

    def test_from_json_missing_value_raises_error(self):
        """Test that missing .value attribute raises ValueError."""
        payload = {"body": {"value": []}}  # Plain dict, no .value attr

        with pytest.raises(ValueError, match="Payload must have a 'value' attribute"):
            MyType.from_json(payload)
```

## Supported Types

The following types currently have `from_json` implementations:

| Type | Description |
|------|-------------|
| `ClientReceiveMessage` | Email messages (with integer importance) |
| `GraphClientReceiveMessage` | Graph API email messages (with string importance) |
| `GraphCalendarEventClientReceive` | Calendar events (Get event V3) |
| `GraphCalendarEventListWithActionType` | Calendar events with action type |

## Contributing New Types

When adding `from_json` to a new type:

1. **Follow the pattern** — Use the existing implementations as templates
2. **Handle all fields** — Map every field from the JSON to the dataclass
3. **Document the method** — Include docstring with Args, Returns, and Raises
4. **Add tests** — Cover batch, single item, missing fields, and error cases
5. **Update this doc** — Add your type to the "Supported Types" table
6. **Update the extensions repo** — See the next section for required changes

## Step 6: Update Azure Functions Python Extensions

After implementing `from_json` in this SDK, you must also update the [azure-functions-python-extensions](https://github.com/Azure/azure-functions-python-extensions) repository to register the new type with the Azure Functions runtime.

### Checklist: Adding a New Connector Type

Use these variables when following the checklist:

| Variable | Description | Example |
|----------|-------------|---------|
| `{ConnectorName}` | Connector directory name | `office365`, `sharepoint`, `teams` |
| `{NewTypeName}` | SDK type class name | `ClientReceiveMessage`, `GraphCalendarEventListWithActionType` |
| `{action_name}` | Action name for samples folder | `on_new_email`, `on_flagged_email` |
| `{Action Description}` | Human-readable action | "On New Email", "When an event is added" |

---

### 1. Create the SDK Type Wrapper

**File:** `azurefunctions-extensions-connectors/azurefunctions/extensions/connectors/{ConnectorName}/{newTypeName}.py`

Create a wrapper class that imports and re-exports the SDK type from `azure.connectors`.
```python
#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT License.

from typing import List

from azure.connectors.{ConnectorName} import {NewTypeName} as Azure{NewTypeName}
from azurefunctions.extensions.base import Datum, SdkType


class {NewTypeName}(SdkType, Azure{NewTypeName}):
    def __init__(self, *, data: Datum) -> None:
        self._json_payload = data

    @classmethod
    def supports_deferred_binding(cls) -> bool:
        """{ConnectorName} connector does not support deferred binding."""
        return False

    def get_sdk_type(self) -> List[Azure{NewTypeName}]:
        if not self._json_payload:
            raise ValueError(
                f"Unable to create {self.__class__.__name__} SDK type. "
                f"No data provided."
            )
        try:
            messages = Azure{NewTypeName}.from_json(self._json_payload)
            return messages
        except Exception as e:
            raise ValueError(
                f"Unable to create {self.__class__.__name__} SDK type. "
                f"Exception: {e}"
            ) from e
```

---

### 2. Update the Converter

**File:** `connectorConverter.py`

- Add import: `from .{ConnectorName}.{newTypeName} import {NewTypeName}`
- Add to `SUPPORTED_SDK_TYPES` tuple
- Add `elif` branch in `decode()` method

---

### 3. Update Package Exports

**File:** `azurefunctions-extensions-connectors/azurefunctions/extensions/connectors/{ConnectorName}/__init__.py`

- Add import: `from .{newTypeName} import {NewTypeName}`
- Add `"{NewTypeName}"` to `__all__` list

---

### 4. Add Unit Tests

**File:** `test_clientreceivemessage.py`

- Add `{NewTypeName}` to imports
- Add tests:
  - `test_{newtype}_input_type_single` — single type annotation accepted
  - `test_{newtype}_input_type_list` — `List[{NewTypeName}]` accepted
  - `test_{newtype}_input_none` — `None` data returns `None`
- Add test class:
  - `Test{NewTypeName}.test_supports_deferred_binding_false`

---

### 5. Create Sample Folder

**Folder:** `azurefunctions-extensions-connectors/samples/{ConnectorName}_samples_{action_name}/`

Create these files:

| File | Description |
|------|-------------|
| `function_app.py` | Single and batch trigger functions using `azurefunctions.extensions.connectors.{ConnectorName}` |
| `host.json` | Copy from existing sample |
| `local.settings.json` | Copy from existing sample |
| `requirements.txt` | Copy from existing sample |

---

### 6. Update Samples README

**File:** `README.md`

Add a new section documenting the sample folder and action.

---

### Summary

| Category | Count |
|----------|-------|
| Files Modified | 4 (`connectorConverter.py`, `{ConnectorName}/__init__.py`, `tests/test_clientreceivemessage.py`, `samples/README.md`) |
| Files Created | 5 (1 SDK type wrapper + 4 sample files) |

After completing these changes, create a PR to [azure-functions-python-extensions](https://github.com/Azure/azure-functions-python-extensions) and coordinate a new release.
