"""Unit tests for SDK trigger_payload module."""

from dataclasses import dataclass

from azure.connectors.sdk.trigger_payload import TriggerCallbackBody, TriggerCallbackPayload


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
        """Test that structure represents Connector Namespace envelope."""
        # Connector Namespace structure: {"body": {"value": [...]}}
        items = [TestTriggerItem(id="1", value="data")]
        body = TriggerCallbackBody[TestTriggerItem](value=items)
        payload = TriggerCallbackPayload[TestTriggerItem](body=body)

        # Verify the nested structure
        assert hasattr(payload, 'body')
        assert hasattr(payload.body, 'value')
        assert isinstance(payload.body.value, list)


class TestTriggerCallbackBodyFromDict:
    """Tests for TriggerCallbackBody.from_dict — batch and single-item shapes."""

    def test_batch_shape_with_items(self):
        """Test batch shape: {"value": [...items...]}."""
        data = {"value": [{"id": "1", "value": "first"}, {"id": "2", "value": "second"}]}
        body = TriggerCallbackBody.from_dict(data)

        assert body.value is not None
        assert len(body.value) == 2
        assert body.value[0] == {"id": "1", "value": "first"}
        assert body.value[1] == {"id": "2", "value": "second"}

    def test_batch_shape_with_empty_list(self):
        """Test batch shape with empty value list: {"value": []}."""
        data = {"value": []}
        body = TriggerCallbackBody.from_dict(data)

        assert body.value is not None
        assert body.value == []

    def test_batch_shape_with_null_value(self):
        """Test batch shape with null value: {"value": null}."""
        data = {"value": None}
        body = TriggerCallbackBody.from_dict(data)

        assert body.value is None

    def test_single_item_shape(self):
        """Test single-item shape: {...item properties...} wraps into list."""
        data = {"id": "msg-1", "subject": "Hello", "from": "user@example.com"}
        body = TriggerCallbackBody.from_dict(data)

        assert body.value is not None
        assert len(body.value) == 1
        assert body.value[0] == {"id": "msg-1", "subject": "Hello", "from": "user@example.com"}

    def test_single_item_shape_with_value_property_not_list(self):
        """Test item with 'value' property that is not a list is treated as single-item."""
        data = {"id": "1", "value": "some-string-not-a-list", "other": "field"}
        body = TriggerCallbackBody.from_dict(data)

        # Has multiple properties and value is not a list, so single-item shape
        assert body.value is not None
        assert len(body.value) == 1
        assert body.value[0] == data

    def test_single_item_shape_with_multiple_properties_including_value_list(self):
        """Test that a dict with 'value' list but multiple properties is single-item."""
        data = {"value": ["a", "b"], "extra": "field"}
        body = TriggerCallbackBody.from_dict(data)

        # Has 2 properties, so NOT batch shape — treat as single-item
        assert body.value is not None
        assert len(body.value) == 1
        assert body.value[0] == data

    def test_none_data(self):
        """Test None input returns body with None value."""
        body = TriggerCallbackBody.from_dict(None)

        assert body.value is None

    def test_batch_shape_with_item_factory(self):
        """Test batch shape with item_factory converts items."""
        data = {"value": [{"id": "1", "value": "first"}, {"id": "2", "value": "second"}]}

        def factory(d):
            return TestTriggerItem(id=d["id"], value=d["value"])

        body = TriggerCallbackBody.from_dict(data, item_factory=factory)

        assert body.value is not None
        assert len(body.value) == 2
        assert isinstance(body.value[0], TestTriggerItem)
        assert body.value[0].id == "1"
        assert body.value[1].value == "second"

    def test_single_item_shape_with_item_factory(self):
        """Test single-item shape with item_factory converts the item."""
        data = {"id": "msg-1", "value": "hello"}

        def factory(d):
            return TestTriggerItem(id=d["id"], value=d["value"])

        body = TriggerCallbackBody.from_dict(data, item_factory=factory)

        assert body.value is not None
        assert len(body.value) == 1
        assert isinstance(body.value[0], TestTriggerItem)
        assert body.value[0].id == "msg-1"


class TestTriggerCallbackPayloadFromJson:
    """Tests for TriggerCallbackPayload.from_json — batch and single-item shapes."""

    def test_batch_json_string(self):
        """Test parsing batch JSON string: {"body": {"value": [...]}}."""
        import json
        payload_str = json.dumps({
            "body": {
                "value": [
                    {"id": "1", "subject": "Email 1"},
                    {"id": "2", "subject": "Email 2"},
                ]
            }
        })

        result = TriggerCallbackPayload.from_json(payload_str)

        assert result.body is not None
        assert result.body.value is not None
        assert len(result.body.value) == 2
        assert result.body.value[0]["subject"] == "Email 1"
        assert result.body.value[1]["subject"] == "Email 2"

    def test_single_item_json_string(self):
        """Test parsing single-item JSON string: {"body": {...item...}}."""
        import json
        payload_str = json.dumps({
            "body": {
                "id": "msg-1",
                "subject": "Single Email",
                "from": "user@example.com",
            }
        })

        result = TriggerCallbackPayload.from_json(payload_str)

        assert result.body is not None
        assert result.body.value is not None
        assert len(result.body.value) == 1
        assert result.body.value[0]["subject"] == "Single Email"
        assert result.body.value[0]["from"] == "user@example.com"

    def test_batch_dict(self):
        """Test parsing batch dict payload."""
        data = {
            "body": {
                "value": [{"id": "1"}, {"id": "2"}, {"id": "3"}]
            }
        }

        result = TriggerCallbackPayload.from_json(data)

        assert result.body is not None
        assert len(result.body.value) == 3

    def test_single_item_dict(self):
        """Test parsing single-item dict payload."""
        data = {
            "body": {"id": "item-1", "name": "test", "status": "active"}
        }

        result = TriggerCallbackPayload.from_json(data)

        assert result.body is not None
        assert len(result.body.value) == 1
        assert result.body.value[0]["name"] == "test"

    def test_null_body(self):
        """Test payload with null body."""
        data = {"body": None}

        result = TriggerCallbackPayload.from_json(data)

        assert result.body is None

    def test_missing_body(self):
        """Test payload with missing body key."""
        data = {"other": "field"}

        result = TriggerCallbackPayload.from_json(data)

        assert result.body is None

    def test_none_payload(self):
        """Test None payload via from_dict."""
        result = TriggerCallbackPayload.from_dict(None)

        assert result.body is None

    def test_invalid_json_string(self):
        """Test that invalid JSON string raises ValueError."""
        import pytest
        with pytest.raises(ValueError, match="Invalid JSON payload"):
            TriggerCallbackPayload.from_json("not valid json {{{")

    def test_with_item_factory(self):
        """Test from_json with item_factory for typed conversion."""
        import json
        payload_str = json.dumps({
            "body": {
                "value": [
                    {"id": "1", "value": "first"},
                    {"id": "2", "value": "second"},
                ]
            }
        })

        def factory(d):
            return TestTriggerItem(id=d["id"], value=d["value"])

        result = TriggerCallbackPayload.from_json(payload_str, item_factory=factory)

        assert result.body is not None
        assert len(result.body.value) == 2
        assert isinstance(result.body.value[0], TestTriggerItem)
        assert result.body.value[0].id == "1"

    def test_single_item_with_item_factory(self):
        """Test single-item shape with item_factory."""
        data = {
            "body": {"id": "msg-1", "value": "hello"}
        }

        def factory(d):
            return TestTriggerItem(id=d["id"], value=d["value"])

        result = TriggerCallbackPayload.from_json(data, item_factory=factory)

        assert result.body is not None
        assert len(result.body.value) == 1
        assert isinstance(result.body.value[0], TestTriggerItem)
        assert result.body.value[0].id == "msg-1"

    def test_batch_empty_value(self):
        """Test batch shape with empty value list."""
        data = {"body": {"value": []}}

        result = TriggerCallbackPayload.from_json(data)

        assert result.body is not None
        assert result.body.value == []

    def test_batch_null_value(self):
        """Test batch shape with null value."""
        data = {"body": {"value": None}}

        result = TriggerCallbackPayload.from_json(data)

        assert result.body is not None
        assert result.body.value is None
