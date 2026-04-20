"""Unit tests for SDK trigger_payload module."""

import pytest
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
        """Test that structure represents AI Gateway envelope."""
        # AI Gateway structure: {"body": {"value": [...]}}
        items = [TestTriggerItem(id="1", value="data")]
        body = TriggerCallbackBody[TestTriggerItem](value=items)
        payload = TriggerCallbackPayload[TestTriggerItem](body=body)
        
        # Verify the nested structure
        assert hasattr(payload, 'body')
        assert hasattr(payload.body, 'value')
        assert isinstance(payload.body.value, list)
