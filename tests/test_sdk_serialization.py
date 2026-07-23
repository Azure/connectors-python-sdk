"""Unit tests for SDK wire serialization module."""

from dataclasses import dataclass, field

from azure.connectors.sdk.serialization import to_wire


@dataclass
class Leaf:
    """Leaf model with a wire-named attribute."""
    leaf_value: str = field(default=None, metadata={"wire_name": "leafValue"})


@dataclass
class Node:
    """Model with matching, wire-named, nested, and dynamic attributes."""
    name: str = None
    display_name: str = field(
        default=None, metadata={"wire_name": "displayName"}
    )
    leaf: Leaf = None
    leaves: list = None
    additional_properties: dict = None


class TestToWire:
    """Tests for the to_wire serializer."""

    def test_scalars_pass_through(self):
        """Test that scalar values are returned unchanged."""
        assert to_wire(42) == 42
        assert to_wire("text") == "text"
        assert to_wire(True) is True
        assert to_wire(None) is None

    def test_bytes_pass_through_unchanged(self):
        """Test that raw bytes are never JSON-encoded."""
        payload = b"\x00\x01\xff"
        assert to_wire(payload) is payload

    def test_bytearray_passes_through_unchanged(self):
        """Test that bytearray payloads are returned unchanged."""
        payload = bytearray(b"data")
        assert to_wire(payload) is payload

    def test_matching_attribute_uses_attribute_name(self):
        """Test that a field without metadata falls back to the attribute name."""
        result = to_wire(Node(name="value"))

        assert result == {"name": "value"}

    def test_wire_name_metadata_is_used(self):
        """Test that a field's wire_name metadata overrides the attribute name."""
        result = to_wire(Node(display_name="widget"))

        assert result == {"displayName": "widget"}

    def test_none_fields_are_omitted(self):
        """Test that None-valued dataclass fields are omitted."""
        result = to_wire(Node(name="value", display_name=None))

        assert result == {"name": "value"}

    def test_nested_dataclass_is_converted(self):
        """Test that nested dataclasses are recursively converted."""
        result = to_wire(Node(leaf=Leaf(leaf_value="deep")))

        assert result == {"leaf": {"leafValue": "deep"}}

    def test_list_of_dataclasses_is_converted(self):
        """Test that lists of dataclasses are converted element-by-element."""
        result = to_wire(Node(leaves=[Leaf(leaf_value="a"), Leaf(leaf_value="b")]))

        assert result == {"leaves": [{"leafValue": "a"}, {"leafValue": "b"}]}

    def test_additional_properties_merge_into_parent(self):
        """Test that additional_properties merge into the containing object."""
        result = to_wire(
            Node(name="value", additional_properties={"extra": "data"})
        )

        assert result == {"name": "value", "extra": "data"}
        assert "additional_properties" not in result

    def test_dict_values_are_converted_and_none_omitted(self):
        """Test that dict bodies recurse and omit None values."""
        result = to_wire({"a": Leaf(leaf_value="x"), "b": None, "c": 1})

        assert result == {"a": {"leafValue": "x"}, "c": 1}
