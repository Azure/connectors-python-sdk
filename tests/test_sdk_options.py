"""Unit tests for SDK options module."""

import pytest

from azure.connectors.sdk.options import ConnectorClientOptions


class TestConnectorClientOptions:
    """Tests for ConnectorClientOptions."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        options = ConnectorClientOptions()
        
        assert options.base_uri is None
        assert options.max_retry_attempts == 3
        assert options.timeout_seconds == 30.0
        assert options.use_exponential_backoff is True
        assert options.initial_retry_delay_seconds == 0.5

    def test_custom_base_uri(self):
        """Test setting custom base URI."""
        options = ConnectorClientOptions(base_uri="https://api.example.com")
        
        assert options.base_uri == "https://api.example.com"

    def test_custom_max_retry_attempts(self):
        """Test setting custom max retry attempts."""
        options = ConnectorClientOptions(max_retry_attempts=5)
        
        assert options.max_retry_attempts == 5

    def test_custom_timeout_seconds(self):
        """Test setting custom timeout."""
        options = ConnectorClientOptions(timeout_seconds=60.0)
        
        assert options.timeout_seconds == 60.0

    def test_disable_exponential_backoff(self):
        """Test disabling exponential backoff."""
        options = ConnectorClientOptions(use_exponential_backoff=False)
        
        assert options.use_exponential_backoff is False

    def test_custom_initial_retry_delay(self):
        """Test setting custom initial retry delay."""
        options = ConnectorClientOptions(initial_retry_delay_seconds=1.0)
        
        assert options.initial_retry_delay_seconds == 1.0

    def test_all_custom_parameters(self):
        """Test setting all parameters to custom values."""
        options = ConnectorClientOptions(
            base_uri="https://custom.api.com",
            max_retry_attempts=10,
            timeout_seconds=120.0,
            use_exponential_backoff=False,
            initial_retry_delay_seconds=2.0
        )
        
        assert options.base_uri == "https://custom.api.com"
        assert options.max_retry_attempts == 10
        assert options.timeout_seconds == 120.0
        assert options.use_exponential_backoff is False
        assert options.initial_retry_delay_seconds == 2.0

    def test_zero_retry_attempts(self):
        """Test setting zero retry attempts."""
        options = ConnectorClientOptions(max_retry_attempts=0)
        
        assert options.max_retry_attempts == 0

    def test_fractional_timeout(self):
        """Test setting fractional timeout."""
        options = ConnectorClientOptions(timeout_seconds=2.5)
        
        assert options.timeout_seconds == 2.5

    def test_very_small_retry_delay(self):
        """Test setting very small retry delay."""
        options = ConnectorClientOptions(initial_retry_delay_seconds=0.1)
        
        assert options.initial_retry_delay_seconds == 0.1

    def test_is_dataclass(self):
        """Test that ConnectorClientOptions is a dataclass."""
        from dataclasses import is_dataclass
        
        assert is_dataclass(ConnectorClientOptions)

    def test_options_equality(self):
        """Test equality comparison of options."""
        options1 = ConnectorClientOptions(max_retry_attempts=5)
        options2 = ConnectorClientOptions(max_retry_attempts=5)
        options3 = ConnectorClientOptions(max_retry_attempts=3)
        
        assert options1 == options2
        assert options1 != options3

    def test_options_repr(self):
        """Test string representation of options."""
        options = ConnectorClientOptions(timeout_seconds=45.0)
        repr_str = repr(options)
        
        assert "ConnectorClientOptions" in repr_str
        assert "timeout_seconds=45.0" in repr_str

    def test_field_types(self):
        """Test that field types are correct."""
        options = ConnectorClientOptions()
        
        assert isinstance(options.max_retry_attempts, int)
        assert isinstance(options.timeout_seconds, float)
        assert isinstance(options.use_exponential_backoff, bool)
        assert isinstance(options.initial_retry_delay_seconds, float)
