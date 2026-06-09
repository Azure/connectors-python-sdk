# Copyright (c) Microsoft Corporation. All rights reserved.

"""Unit tests for KeyvaultClient."""

import pytest
from unittest.mock import AsyncMock, patch
from azure.connectors.keyvault import (
    KeyvaultClient,
    KeyMetadataCollection,
    KeyMetadata,
    KeyEncryptOutput,
    KeyDecryptOutput,
    SecretMetadataCollection,
    SecretMetadata,
    Secret,
    KeyEncryptInput,
    KeyDecryptInput,
)
from azure.connectors.sdk import (
    ConnectorClientOptions,
    ManagedIdentityTokenProvider,
    ConnectorException,
)
from tests.conftest import MockResponse


class TestKeyvaultClientInitialization:
    """Tests for KeyvaultClient initialization."""

    def test_init_with_valid_url_and_defaults(self):
        """Test initialization with valid URL and default parameters."""
        client = KeyvaultClient(
            "https://example.azure.com/connections/test"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )
        assert client.connector_name == "keyvault"
        assert isinstance(
            client._http_client._token_provider, ManagedIdentityTokenProvider
        )

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = KeyvaultClient(
            "https://example.azure.com/connections/test/"
        )

        assert client._connection_runtime_url == (
            "https://example.azure.com/connections/test"
        )

    def test_init_with_custom_token_provider(self, mock_token_provider):
        """Test initialization with custom token provider."""
        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client._http_client._token_provider is mock_token_provider

    def test_init_with_custom_options(self, mock_token_provider):
        """Test initialization with custom options."""
        options = ConnectorClientOptions(
            timeout_seconds=60.0, max_retry_attempts=5
        )
        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider,
            options=options
        )

        assert client._options is options
        assert client._options.timeout_seconds == 60.0
        assert client._options.max_retry_attempts == 5

    def test_init_with_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            KeyvaultClient("")

    def test_init_with_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(
            ValueError, match="connection_runtime_url cannot be None or empty"
        ):
            KeyvaultClient(None)

    def test_connector_name_property(self, mock_token_provider):
        """Test connector_name property returns 'keyvault'."""
        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        assert client.connector_name == "keyvault"


class TestKeyvaultClientLifecycle:
    """Tests for KeyvaultClient lifecycle methods."""

    @pytest.mark.asyncio
    async def test_close(self, mock_token_provider):
        """Test close method calls http_client.close."""
        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client, 'close', new_callable=AsyncMock
        ) as mock_close:
            await client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_token_provider):
        """Test async context manager functionality."""
        with patch.object(
            KeyvaultClient, 'close', new_callable=AsyncMock
        ) as mock_close:
            async with KeyvaultClient(
                "https://example.azure.com/connections/test",
                token_provider=mock_token_provider
            ) as client:
                assert isinstance(client, KeyvaultClient)

            mock_close.assert_called_once()


class TestListKeysAsync:
    """Tests for list_keys_async method."""

    @pytest.mark.asyncio
    async def test_success_returns_keys(self, mock_token_provider):
        """Test successful request returns key list."""
        response_json = (
            '{"value": [{"name": "key1", "version": "v1"}], '
            '"continuation_token": null}'
        )
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_keys_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/keys" in call_args[0][1]
            assert result is not None
            assert "value" in result

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self, mock_token_provider):
        """Test empty response returns None."""
        mock_response = MockResponse(status=200, text='')

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await client.list_keys_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(
            status=403,
            text='{"error": {"code": "Forbidden", "message": "Access denied"}}'
        )

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_keys_async()

            assert exc_info.value.status_code == 403


class TestListKeyVersionsAsync:
    """Tests for list_key_versions_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns key versions."""
        response_json = '{"value": [{"version": "v1"}, {"version": "v2"}]}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_key_versions_async(key_name="mykey")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/keys/mykey/versions" in call_args[0][1]
            assert result is not None


class TestGetKeyMetadataAsync:
    """Tests for get_key_metadata_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns key metadata."""
        response_json = (
            '{"name": "mykey", "version": "v1", "is_enabled": true, '
            '"key_type": "RSA"}'
        )
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_key_metadata_async(key_name="mykey")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/keys/mykey/metadata" in call_args[0][1]
            assert result is not None
            assert result["name"] == "mykey"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_key_metadata_async(key_name="nonexistent")

            assert exc_info.value.status_code == 404


class TestGetKeyVersionMetadataAsync:
    """Tests for get_key_version_metadata_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns key version metadata."""
        response_json = '{"name": "mykey", "version": "v1", "is_enabled": true}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_key_version_metadata_async(
                key_name="mykey",
                key_version="v1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/keys/mykey/versions/v1/metadata" in call_args[0][1]
            assert result is not None


class TestEncryptDataAsync:
    """Tests for encrypt_data_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful encryption."""
        response_json = '{"encrypted_data": "base64encodeddata=="}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        encrypt_input = KeyEncryptInput(
            algorithm="RSA-OAEP",
            raw_data="Hello, World!"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.encrypt_data_async(
                input=encrypt_input,
                key_name="mykey"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/keys/mykey/encrypt" in call_args[0][1]
            assert result is not None
            assert result["encrypted_data"] == "base64encodeddata=="

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(
            status=400,
            text='{"error": "Invalid algorithm"}'
        )

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        encrypt_input = KeyEncryptInput(
            algorithm="INVALID",
            raw_data="data"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.encrypt_data_async(
                    input=encrypt_input,
                    key_name="mykey"
                )

            assert exc_info.value.status_code == 400


class TestEncryptDataWithVersionAsync:
    """Tests for encrypt_data_with_version_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful encryption with specific version."""
        response_json = '{"encrypted_data": "encryptedwithv1=="}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        encrypt_input = KeyEncryptInput(
            algorithm="RSA-OAEP",
            raw_data="Hello, World!"
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.encrypt_data_with_version_async(
                input=encrypt_input,
                key_name="mykey",
                key_version="v1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/keys/mykey/versions/v1/encrypt" in call_args[0][1]
            assert result is not None


class TestDecryptDataAsync:
    """Tests for decrypt_data_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful decryption."""
        response_json = '{"raw_data": "Hello, World!"}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        decrypt_input = KeyDecryptInput(
            algorithm="RSA-OAEP",
            encrypted_data="base64encodeddata=="
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.decrypt_data_async(
                input=decrypt_input,
                key_name="mykey"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/keys/mykey/decrypt" in call_args[0][1]
            assert result is not None
            assert result["raw_data"] == "Hello, World!"


class TestDecryptDataWithVersionAsync:
    """Tests for decrypt_data_with_version_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful decryption with specific version."""
        response_json = '{"raw_data": "Decrypted data"}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        decrypt_input = KeyDecryptInput(
            algorithm="RSA-OAEP",
            encrypted_data="encryptedwithv1=="
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.decrypt_data_with_version_async(
                input=decrypt_input,
                key_name="mykey",
                key_version="v1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "POST"
            assert "/keys/mykey/versions/v1/decrypt" in call_args[0][1]
            assert result is not None


class TestListSecretsAsync:
    """Tests for list_secrets_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns secret list."""
        response_json = '{"value": [{"name": "secret1"}, {"name": "secret2"}]}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_secrets_async()

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/secrets" in call_args[0][1]
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(status=403, text='{"error": "Forbidden"}')

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.list_secrets_async()

            assert exc_info.value.status_code == 403


class TestListSecretVersionsAsync:
    """Tests for list_secret_versions_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns secret versions."""
        response_json = '{"value": [{"version": "v1"}, {"version": "v2"}]}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.list_secret_versions_async(
                secret_name="mysecret"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/secrets/mysecret/versions" in call_args[0][1]
            assert result is not None


class TestGetSecretMetadataAsync:
    """Tests for get_secret_metadata_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns secret metadata."""
        response_json = (
            '{"name": "mysecret", "version": "v1", "is_enabled": true, '
            '"content_type": "application/json"}'
        )
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_secret_metadata_async(
                secret_name="mysecret"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/secrets/mysecret/metadata" in call_args[0][1]
            assert result is not None
            assert result["name"] == "mysecret"


class TestGetSecretVersionMetadataAsync:
    """Tests for get_secret_version_metadata_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns secret version metadata."""
        response_json = '{"name": "mysecret", "version": "v1", "is_enabled": true}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_secret_version_metadata_async(
                secret_name="mysecret",
                secret_version="v1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/secrets/mysecret/versions/v1/metadata" in call_args[0][1]
            assert result is not None


class TestGetSecretAsync:
    """Tests for get_secret_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns secret value."""
        response_json = (
            '{"value": "supersecretvalue", "name": "mysecret", '
            '"is_enabled": true}'
        )
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_secret_async(secret_name="mysecret")

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/secrets/mysecret/value" in call_args[0][1]
            assert result is not None
            assert result["value"] == "supersecretvalue"

    @pytest.mark.asyncio
    async def test_error_response_raises_exception(self, mock_token_provider):
        """Test that error response raises ConnectorException."""
        mock_response = MockResponse(status=404, text='{"error": "Not found"}')

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_secret_async(secret_name="nonexistent")

            assert exc_info.value.status_code == 404


class TestGetSecretVersionAsync:
    """Tests for get_secret_version_async method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_token_provider):
        """Test successful request returns secret version value."""
        response_json = '{"value": "secretvaluev1", "name": "mysecret"}'
        mock_response = MockResponse(status=200, text=response_json)

        client = KeyvaultClient(
            "https://example.azure.com/connections/test",
            token_provider=mock_token_provider
        )

        with patch.object(
            client._http_client,
            'send_async',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_send:
            result = await client.get_secret_version_async(
                secret_name="mysecret",
                secret_version="v1"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "GET"
            assert "/secrets/mysecret/versions/v1/value" in call_args[0][1]
            assert result is not None
            assert result["value"] == "secretvaluev1"


class TestDataClasses:
    """Tests for dataclass definitions."""

    def test_key_metadata_defaults(self):
        """Test KeyMetadata dataclass with defaults."""
        key = KeyMetadata()
        assert key.name is None
        assert key.version is None
        assert key.is_enabled is None
        assert key.key_type is None
        assert key.allowed_operations is None

    def test_key_metadata_with_values(self):
        """Test KeyMetadata dataclass with values."""
        key = KeyMetadata(
            name="mykey",
            version="v1",
            is_enabled=True,
            key_type="RSA",
            allowed_operations=["encrypt", "decrypt"]
        )
        assert key.name == "mykey"
        assert key.version == "v1"
        assert key.is_enabled is True
        assert key.key_type == "RSA"
        assert len(key.allowed_operations) == 2

    def test_key_metadata_collection_defaults(self):
        """Test KeyMetadataCollection dataclass with defaults."""
        collection = KeyMetadataCollection()
        assert collection.value is None
        assert collection.continuation_token is None

    def test_key_encrypt_input_defaults(self):
        """Test KeyEncryptInput dataclass with defaults."""
        input_obj = KeyEncryptInput()
        assert input_obj.algorithm is None
        assert input_obj.raw_data is None

    def test_key_encrypt_input_with_values(self):
        """Test KeyEncryptInput dataclass with values."""
        input_obj = KeyEncryptInput(
            algorithm="RSA-OAEP",
            raw_data="data to encrypt"
        )
        assert input_obj.algorithm == "RSA-OAEP"
        assert input_obj.raw_data == "data to encrypt"

    def test_key_decrypt_input_defaults(self):
        """Test KeyDecryptInput dataclass with defaults."""
        input_obj = KeyDecryptInput()
        assert input_obj.algorithm is None
        assert input_obj.encrypted_data is None

    def test_key_encrypt_output_defaults(self):
        """Test KeyEncryptOutput dataclass with defaults."""
        output = KeyEncryptOutput()
        assert output.encrypted_data is None

    def test_key_decrypt_output_defaults(self):
        """Test KeyDecryptOutput dataclass with defaults."""
        output = KeyDecryptOutput()
        assert output.raw_data is None

    def test_secret_metadata_defaults(self):
        """Test SecretMetadata dataclass with defaults."""
        secret = SecretMetadata()
        assert secret.name is None
        assert secret.version is None
        assert secret.content_type is None
        assert secret.is_enabled is None

    def test_secret_metadata_with_values(self):
        """Test SecretMetadata dataclass with values."""
        secret = SecretMetadata(
            name="mysecret",
            version="v1",
            content_type="text/plain",
            is_enabled=True
        )
        assert secret.name == "mysecret"
        assert secret.version == "v1"
        assert secret.content_type == "text/plain"
        assert secret.is_enabled is True

    def test_secret_metadata_collection_defaults(self):
        """Test SecretMetadataCollection dataclass with defaults."""
        collection = SecretMetadataCollection()
        assert collection.value is None
        assert collection.continuation_token is None

    def test_secret_defaults(self):
        """Test Secret dataclass with defaults."""
        secret = Secret()
        assert secret.value is None
        assert secret.name is None
        assert secret.version is None
        assert secret.content_type is None
        assert secret.is_enabled is None

    def test_secret_with_values(self):
        """Test Secret dataclass with values."""
        secret = Secret(
            value="supersecretvalue",
            name="mysecret",
            version="v1",
            content_type="text/plain",
            is_enabled=True
        )
        assert secret.value == "supersecretvalue"
        assert secret.name == "mysecret"
        assert secret.version == "v1"
        assert secret.content_type == "text/plain"
        assert secret.is_enabled is True
