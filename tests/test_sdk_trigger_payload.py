"""Unit tests for SDK trigger_payload module."""

import json
from dataclasses import dataclass

from azure.connectors.sdk.trigger_payload import (
    TriggerCallbackBody,
    TriggerCallbackPayload,
    _is_batch_shape,
)


@dataclass
class TestTriggerItem:
    """Test trigger item type."""
    id: str
    value: str


class TestTriggerCallbackBody:
    """Tests for TriggerCallbackBody."""

    def test_init_with_no_value(self):
        """Test initialization with no value."""
        body = TriggerCallbackBody[TestTriggerItem]()

        assert body.value is None

    def test_init_with_empty_list(self):
        """Test initialization with empty list."""
        body = TriggerCallbackBody[TestTriggerItem](value=[])

        assert body.value == []

    def test_init_with_items(self):
        """Test initialization with trigger items."""
        items = [
            TestTriggerItem(id="1", value="first"),
            TestTriggerItem(id="2", value="second"),
        ]
        body = TriggerCallbackBody[TestTriggerItem](value=items)

        assert body.value == items
        assert len(body.value) == 2

    def test_is_dataclass(self):
        """Test that TriggerCallbackBody is a dataclass."""
        from dataclasses import is_dataclass

        body = TriggerCallbackBody[TestTriggerItem]()
        assert is_dataclass(body)

    def test_generic_type_parameter(self):
        """Test generic type parameter works."""
        @dataclass
        class CustomItem:
            name: str

        body = TriggerCallbackBody[CustomItem](value=[CustomItem(name="test")])

        assert body.value[0].name == "test"

    def test_value_can_be_modified(self):
        """Test that value list can be modified."""
        body = TriggerCallbackBody[TestTriggerItem](value=[])
        body.value.append(TestTriggerItem(id="3", value="third"))

        assert len(body.value) == 1

    def test_with_dict_items(self):
        """Test with dictionary trigger items."""
        items = [{"id": "1", "data": "value"}]
        body = TriggerCallbackBody[dict](value=items)

        assert body.value[0]["id"] == "1"


class TestTriggerCallbackPayload:
    """Tests for TriggerCallbackPayload."""

    def test_init_with_no_body(self):
        """Test initialization with no body."""
        payload = TriggerCallbackPayload[TestTriggerItem]()

        assert payload.body is None

    def test_init_with_body(self):
        """Test initialization with body."""
        items = [TestTriggerItem(id="1", value="test")]
        body = TriggerCallbackBody[TestTriggerItem](value=items)
        payload = TriggerCallbackPayload[TestTriggerItem](body=body)

        assert payload.body is body
        assert payload.body.value == items

    def test_is_dataclass(self):
        """Test that TriggerCallbackPayload is a dataclass."""
        from dataclasses import is_dataclass

        payload = TriggerCallbackPayload[TestTriggerItem]()
        assert is_dataclass(payload)

    def test_nested_structure(self):
        """Test nested structure with items."""
        items = [
            TestTriggerItem(id="1", value="first"),
            TestTriggerItem(id="2", value="second"),
            TestTriggerItem(id="3", value="third"),
        ]
        body = TriggerCallbackBody[TestTriggerItem](value=items)
        payload = TriggerCallbackPayload[TestTriggerItem](body=body)

        assert payload.body is not None
        assert payload.body.value is not None
        assert len(payload.body.value) == 3
        assert payload.body.value[1].id == "2"

    def test_generic_type_parameter(self):
        """Test generic type parameter works."""
        @dataclass
        class EmailMessage:
            subject: str
            from_address: str

        message = EmailMessage(subject="Test", from_address="user@example.com")
        body = TriggerCallbackBody[EmailMessage](value=[message])
        payload = TriggerCallbackPayload[EmailMessage](body=body)

        assert payload.body.value[0].subject == "Test"

    def test_empty_payload_structure(self):
        """Test empty payload structure."""
        body = TriggerCallbackBody[TestTriggerItem](value=[])
        payload = TriggerCallbackPayload[TestTriggerItem](body=body)

        assert payload.body.value == []

    def test_accessing_nested_items(self):
        """Test accessing items through nested structure."""
        items = [TestTriggerItem(id=str(i), value=f"item_{i}") for i in range(5)]
        body = TriggerCallbackBody[TestTriggerItem](value=items)
        payload = TriggerCallbackPayload[TestTriggerItem](body=body)

        for i, item in enumerate(payload.body.value):
            assert item.id == str(i)
            assert item.value == f"item_{i}"

    def test_payload_equality(self):
        """Test payload equality comparison."""
        items1 = [TestTriggerItem(id="1", value="test")]
        body1 = TriggerCallbackBody[TestTriggerItem](value=items1)
        payload1 = TriggerCallbackPayload[TestTriggerItem](body=body1)

        items2 = [TestTriggerItem(id="1", value="test")]
        body2 = TriggerCallbackBody[TestTriggerItem](value=items2)
        payload2 = TriggerCallbackPayload[TestTriggerItem](body=body2)

        assert payload1.body.value == payload2.body.value

    def test_none_body_payload(self):
        """Test payload with None body."""
        payload = TriggerCallbackPayload[TestTriggerItem](body=None)

        assert payload.body is None

    def test_with_complex_nested_types(self):
        """Test with complex nested data types."""
        @dataclass
        class ComplexItem:
            id: str
            metadata: dict
            tags: list

        items = [
            ComplexItem(
                id="item1",
                metadata={"key": "value"},
                tags=["tag1", "tag2"]
            )
        ]
        body = TriggerCallbackBody[ComplexItem](value=items)
        payload = TriggerCallbackPayload[ComplexItem](body=body)

        assert payload.body.value[0].metadata["key"] == "value"
        assert payload.body.value[0].tags == ["tag1", "tag2"]

    def test_represents_ai_gateway_structure(self):
        """Test that structure represents Connector Gateway envelope."""
        # Connector Gateway structure: {"body": {"value": [...]}}
        items = [TestTriggerItem(id="1", value="data")]
        body = TriggerCallbackBody[TestTriggerItem](value=items)
        payload = TriggerCallbackPayload[TestTriggerItem](body=body)

        # Verify the nested structure
        assert hasattr(payload, 'body')
        assert hasattr(payload.body, 'value')
        assert isinstance(payload.body.value, list)


class TestIsBatchShape:
    """Tests for the _is_batch_shape discriminator function."""

    def test_batch_shape_with_list(self):
        """Test batch shape with value as list."""
        data = {"value": [{"id": "1"}, {"id": "2"}]}
        assert _is_batch_shape(data) is True

    def test_batch_shape_with_empty_list(self):
        """Test batch shape with empty list."""
        data = {"value": []}
        assert _is_batch_shape(data) is True

    def test_batch_shape_with_null(self):
        """Test batch shape with null value."""
        data = {"value": None}
        assert _is_batch_shape(data) is True

    def test_single_item_with_multiple_properties(self):
        """Test single-item shape with multiple properties."""
        data = {"id": "1", "subject": "Test", "value": ["extra"]}
        assert _is_batch_shape(data) is False

    def test_single_item_with_scalar_value(self):
        """Test single-item shape where value is a scalar."""
        data = {"value": "not-a-list"}
        assert _is_batch_shape(data) is False

    def test_single_item_without_value_property(self):
        """Test single-item shape without value property."""
        data = {"id": "1", "subject": "Test"}
        assert _is_batch_shape(data) is False

    def test_empty_dict_is_not_batch(self):
        """Test empty dict is not batch shape."""
        data = {}
        assert _is_batch_shape(data) is False


class TestTriggerCallbackBodyFromDict:
    """Tests for TriggerCallbackBody.from_dict factory method."""

    def test_from_dict_none(self):
        """Test from_dict with None returns None."""
        result = TriggerCallbackBody.from_dict(None)
        assert result is None

    def test_from_dict_batch_shape(self):
        """Test from_dict with batch shape."""
        data = {"value": [{"id": "1"}, {"id": "2"}]}
        result = TriggerCallbackBody.from_dict(data)

        assert result is not None
        assert len(result.value) == 2
        assert result.value[0]["id"] == "1"
        assert result.value[1]["id"] == "2"

    def test_from_dict_batch_shape_empty_list(self):
        """Test from_dict with batch shape containing empty list."""
        data = {"value": []}
        result = TriggerCallbackBody.from_dict(data)

        assert result is not None
        assert result.value == []

    def test_from_dict_batch_shape_null_value(self):
        """Test from_dict with batch shape containing null value."""
        data = {"value": None}
        result = TriggerCallbackBody.from_dict(data)

        assert result is not None
        assert result.value is None

    def test_from_dict_single_item_shape(self):
        """Test from_dict with single-item shape."""
        data = {"id": "1", "subject": "Test email", "from": "sender@test.com"}
        result = TriggerCallbackBody.from_dict(data)

        assert result is not None
        assert len(result.value) == 1
        assert result.value[0]["id"] == "1"
        assert result.value[0]["subject"] == "Test email"

    def test_from_dict_single_item_with_item_parser(self):
        """Test from_dict with single-item shape and item parser."""
        data = {"id": "1", "value": "test"}

        def parser(d: dict) -> TestTriggerItem:
            return TestTriggerItem(id=d["id"], value=d["value"])

        result = TriggerCallbackBody.from_dict(data, item_parser=parser)

        assert result is not None
        assert len(result.value) == 1
        assert isinstance(result.value[0], TestTriggerItem)
        assert result.value[0].id == "1"

    def test_from_dict_batch_shape_with_item_parser(self):
        """Test from_dict with batch shape and item parser."""
        data = {"value": [{"id": "1", "value": "first"}, {"id": "2", "value": "second"}]}

        def parser(d: dict) -> TestTriggerItem:
            return TestTriggerItem(id=d["id"], value=d["value"])

        result = TriggerCallbackBody.from_dict(data, item_parser=parser)

        assert result is not None
        assert len(result.value) == 2
        assert isinstance(result.value[0], TestTriggerItem)
        assert result.value[0].id == "1"
        assert result.value[1].id == "2"

    def test_from_dict_single_item_with_value_array_property(self):
        """Test that single-item T with a value array plus other fields is not batch."""
        # This mirrors the .NET test: a single-item that has a "value" array field
        # plus other fields should NOT be misclassified as batch.
        data = {
            "subject": "Item with value field",
            "from": "sender@test.com",
            "value": ["extra", "data"],
        }
        result = TriggerCallbackBody.from_dict(data)

        assert result is not None
        assert len(result.value) == 1
        assert result.value[0]["subject"] == "Item with value field"
        assert result.value[0]["value"] == ["extra", "data"]


class TestTriggerCallbackPayloadFromDict:
    """Tests for TriggerCallbackPayload.from_dict factory method."""

    def test_from_dict_none(self):
        """Test from_dict with None returns None."""
        result = TriggerCallbackPayload.from_dict(None)
        assert result is None

    def test_from_dict_batch_shape(self):
        """Test from_dict with batch shape payload."""
        data = {"body": {"value": [{"id": "1"}, {"id": "2"}]}}
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert result.body is not None
        assert len(result.body.value) == 2

    def test_from_dict_single_item_shape(self):
        """Test from_dict with single-item shape payload."""
        data = {"body": {"id": "1", "subject": "Test email"}}
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert result.body is not None
        assert len(result.body.value) == 1
        assert result.body.value[0]["id"] == "1"

    def test_from_dict_no_body(self):
        """Test from_dict with no body field."""
        data = {}
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert result.body is None

    def test_from_dict_null_body(self):
        """Test from_dict with null body."""
        data = {"body": None}
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert result.body is None

    def test_from_dict_with_item_parser(self):
        """Test from_dict with item parser."""
        data = {"body": {"id": "1", "value": "test"}}

        def parser(d: dict) -> TestTriggerItem:
            return TestTriggerItem(id=d["id"], value=d["value"])

        result = TriggerCallbackPayload.from_dict(data, item_parser=parser)

        assert result is not None
        assert len(result.body.value) == 1
        assert isinstance(result.body.value[0], TestTriggerItem)

    def test_from_dict_json_roundtrip_batch(self):
        """Test JSON parsing with batch shape."""
        json_str = '{"body": {"value": [{"id": "1", "subject": "Test"}]}}'
        data = json.loads(json_str)
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert len(result.body.value) == 1
        assert result.body.value[0]["id"] == "1"

    def test_from_dict_json_roundtrip_single_item(self):
        """Test JSON parsing with single-item shape."""
        json_str = '{"body": {"id": "1", "subject": "Test email"}}'
        data = json.loads(json_str)
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert len(result.body.value) == 1
        assert result.body.value[0]["subject"] == "Test email"

    def test_from_dict_both_shapes_produce_identical_count(self):
        """Test that both shapes produce identical item counts."""
        batch_data = {"body": {"value": [{"subject": "Test", "from": "sender@test.com"}]}}
        single_data = {"body": {"subject": "Test", "from": "sender@test.com"}}

        batch_result = TriggerCallbackPayload.from_dict(batch_data)
        single_result = TriggerCallbackPayload.from_dict(single_data)

        assert batch_result.body.value is not None
        assert single_result.body.value is not None
        assert len(batch_result.body.value) == len(single_result.body.value)
        assert batch_result.body.value[0]["subject"] == single_result.body.value[0]["subject"]


class TestSingleItemShapeIntegration:
    """Integration tests for single-item shape (splitOn enabled) scenarios."""

    # Captured single-item callback similar to production when splitOn is enabled.
    SINGLE_ITEM_PAYLOAD = {
        "body": {
            "id": "AAMkADlmOTA3NWNm",
            "receivedDateTime": "2026-05-14T16:06:00+00:00",
            "hasAttachments": False,
            "subject": "Single-item callback test",
            "bodyPreview": "This is a single-item callback.",
            "importance": "normal",
            "isRead": False,
            "isHtml": True,
            "body": "<html><body>Single item</body></html>",
            "from": "sender@microsoft.com",
            "toRecipients": "recipient@microsoft.com",
            "ccRecipients": None,
            "bccRecipients": None,
            "replyTo": None,
            "attachments": [],
        }
    }

    def test_single_item_wraps_in_list(self):
        """Test single-item shape is wrapped in a one-element list."""
        result = TriggerCallbackPayload.from_dict(self.SINGLE_ITEM_PAYLOAD)

        assert result is not None
        assert result.body is not None
        assert result.body.value is not None
        assert len(result.body.value) == 1

    def test_single_item_parses_fields(self):
        """Test single-item shape fields are parsed correctly."""
        result = TriggerCallbackPayload.from_dict(self.SINGLE_ITEM_PAYLOAD)
        email = result.body.value[0]

        assert email["id"] == "AAMkADlmOTA3NWNm"
        assert email["subject"] == "Single-item callback test"
        assert email["from"] == "sender@microsoft.com"
        assert email["toRecipients"] == "recipient@microsoft.com"
        assert email["importance"] == "normal"
        assert email["hasAttachments"] is False

    def test_null_value_roundtrip_preserves_null(self):
        """Test that {"value": null} is recognized as batch with null list."""
        data = {"body": {"value": None}}
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert result.body is not None
        assert result.body.value is None

    def test_sole_value_scalar_treated_as_single_item(self):
        """Test single-item T whose only property is 'value' with a scalar."""
        data = {"body": {"value": "not-a-list"}}
        result = TriggerCallbackPayload.from_dict(data)

        assert result is not None
        assert len(result.body.value) == 1
        assert result.body.value[0]["value"] == "not-a-list"
