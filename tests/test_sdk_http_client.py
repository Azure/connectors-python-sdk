"""Unit tests for SDK http_client module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

from azure.connectors.sdk.http_client import ConnectorHttpClient, ConnectorResponse
from azure.connectors.sdk.options import ConnectorClientOptions
from azure.connectors.sdk.exceptions import ConnectorException


@dataclass
class TestDataClass:
    """Test dataclass for body serialization."""
    name: str
    value: int
    optional: str = None


@dataclass
class TestDynamicDataClass:
    """Test dataclass with additional_properties for dynamic schemas."""
    required_field: str
    additional_properties: dict = None


@dataclass
class WireNamedDataClass:
    """Dataclass whose Swagger wire names differ from snake_case attributes."""
    print_background: bool = field(
        default=None, metadata={"wire_name": "printBackground"}
    )
    paper_size: str = field(default=None, metadata={"wire_name": "paperSize"})
    html: str = None


@dataclass
class WireNamedChild:
    """Nested child dataclass with a wire-named attribute."""
    child_value: str = field(default=None, metadata={"wire_name": "childValue"})


@dataclass
class WireNamedParent:
    """Parent dataclass with nested dataclasses and lists of dataclasses."""
    parent_name: str = field(default=None, metadata={"wire_name": "parentName"})
    child: WireNamedChild = None
    children: list = None


@dataclass
class WireNamedDynamicDataClass:
    """Dataclass combining a wire-named field with additional_properties."""
    display_name: str = field(default=None, metadata={"wire_name": "displayName"})
    additional_properties: dict = None


class TestConnectorResponse:
    """Tests for ConnectorResponse."""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        headers = {"Content-Type": "application/json"}
        response = ConnectorResponse[dict](
            status_code=200,
            headers=headers,
            value={"key": "value"}
        )

        assert response.status_code == 200
        assert response.headers == headers
        assert response.value == {"key": "value"}

    def test_init_with_none_value(self):
        """Test initialization with None value."""
        response = ConnectorResponse[str](
            status_code=204,
            headers={},
            value=None
        )

        assert response.value is None

    def test_is_success_status_code_200(self):
        """Test is_success_status_code for 200."""
        response = ConnectorResponse[str](200, {}, "OK")

        assert response.is_success_status_code is True

    def test_is_success_status_code_299(self):
        """Test is_success_status_code for 299."""
        response = ConnectorResponse[str](299, {}, "Custom Success")

        assert response.is_success_status_code is True

    def test_is_success_status_code_199(self):
        """Test is_success_status_code for 199 (not success)."""
        response = ConnectorResponse[str](199, {}, "Not Success")

        assert response.is_success_status_code is False

    def test_is_success_status_code_300(self):
        """Test is_success_status_code for 300 (not success)."""
        response = ConnectorResponse[str](300, {}, "Redirect")

        assert response.is_success_status_code is False

    def test_is_success_status_code_400(self):
        """Test is_success_status_code for 400."""
        response = ConnectorResponse[str](400, {}, "Bad Request")

        assert response.is_success_status_code is False

    def test_is_success_status_code_500(self):
        """Test is_success_status_code for 500."""
        response = ConnectorResponse[str](500, {}, "Server Error")

        assert response.is_success_status_code is False

    def test_generic_type_parameter(self):
        """Test generic type parameter works."""
        response = ConnectorResponse[list](200, {}, [1, 2, 3])

        assert response.value == [1, 2, 3]


class TestConnectorHttpClient:
    """Tests for ConnectorHttpClient."""

    def test_init(self, mock_token_provider):
        """Test initialization."""
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        assert client._token_provider is mock_token_provider
        assert client._options is options
        assert client._session is None

    def test_api_hub_scopes_constant(self):
        """Test API_HUB_SCOPES constant."""
        assert ConnectorHttpClient.API_HUB_SCOPES == ["https://apihub.azure.com/.default"]

    @pytest.mark.asyncio
    async def test_ensure_session_creates_session(self, mock_token_provider):
        """Test that _ensure_session creates a session."""
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        assert client._session is None

        session = await client._ensure_session()

        assert session is not None
        assert client._session is session

    @pytest.mark.asyncio
    async def test_ensure_session_reuses_existing_session(self, mock_token_provider):
        """Test that _ensure_session reuses existing session."""
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        session1 = await client._ensure_session()
        session2 = await client._ensure_session()

        assert session1 is session2

    @pytest.mark.asyncio
    async def test_close_closes_session(self, mock_token_provider):
        """Test that close closes the session."""
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        session = await client._ensure_session()
        assert not session.closed

        await client.close()

        assert session.closed
        assert client._session is None

    @pytest.mark.asyncio
    async def test_close_closes_token_provider(self, mock_token_provider):
        """Test that close closes the token provider."""
        mock_token_provider.close = AsyncMock()
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        await client.close()

        mock_token_provider.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_session(self, mock_token_provider):
        """Test close when no session exists."""
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_send_async_with_default_scopes(self, mock_token_provider):
        """Test send_async with default scopes."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="test_token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{"result": "ok"}')

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ):
            await client.send_async("GET", "https://api.example.com/data")

            mock_token_provider.get_access_token_async.assert_called_once_with(
                ["https://apihub.azure.com/.default"]
            )

    @pytest.mark.asyncio
    async def test_send_async_with_custom_scopes(self, mock_token_provider):
        """Test send_async with custom scopes."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="custom_token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='')

        custom_scopes = ["https://custom.api.com/.default"]

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ):
            await client.send_async("POST", "https://api.example.com/data", scopes=custom_scopes)

            mock_token_provider.get_access_token_async.assert_called_once_with(custom_scopes)

    @pytest.mark.asyncio
    async def test_send_async_with_dataclass_body(self, mock_token_provider):
        """Test send_async with dataclass body."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{"id": "123"}')

        body = TestDataClass(name="test", value=42)

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/items", body=body)

            # Verify body was serialized correctly
            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            assert sent_body["name"] == "test"
            assert sent_body["value"] == 42

    @pytest.mark.asyncio
    async def test_send_async_filters_none_values(self, mock_token_provider):
        """Test that None values are filtered from body."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = TestDataClass(name="test", value=42, optional=None)

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/items", body=body)

            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            assert "optional" not in sent_body

    @pytest.mark.asyncio
    async def test_send_async_with_dynamic_schema(self, mock_token_provider):
        """Test send_async with dynamic schema (additional_properties)."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = TestDynamicDataClass(
            required_field="value",
            additional_properties={"dynamic1": "data1", "dynamic2": "data2"}
        )

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/dynamic", body=body)

            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            assert sent_body["required_field"] == "value"
            assert sent_body["dynamic1"] == "data1"
            assert sent_body["dynamic2"] == "data2"
            assert "additional_properties" not in sent_body

    @pytest.mark.asyncio
    async def test_send_async_with_dict_body(self, mock_token_provider):
        """Test send_async with dictionary body."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = {"key": "value", "count": 10}

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/data", body=body)

            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            assert sent_body == body

    @pytest.mark.asyncio
    async def test_send_async_with_none_body(self, mock_token_provider):
        """Test send_async with None body."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("GET", "https://api.example.com/data", body=None)

            call_args = mock_send.call_args
            assert call_args[0][4] is None

    @pytest.mark.asyncio
    async def test_send_async_uses_wire_names_for_dataclass_body(self, mock_token_provider):
        """Test that dataclass fields are serialized under their Swagger wire names."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = WireNamedDataClass(
            print_background=True, paper_size="A4", html="<p>hi</p>"
        )

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/pdf", body=body)

            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            # NOTE(victoriahall): Snake_case attributes must be emitted under the
            # Swagger camelCase wire names, never the Python attribute names.
            assert sent_body["printBackground"] is True
            assert sent_body["paperSize"] == "A4"
            assert sent_body["html"] == "<p>hi</p>"
            assert "print_background" not in sent_body
            assert "paper_size" not in sent_body

    @pytest.mark.asyncio
    async def test_send_async_uses_wire_names_for_nested_and_list_bodies(self, mock_token_provider):
        """Test wire-name serialization through nested dataclasses and lists of dataclasses."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = WireNamedParent(
            parent_name="root",
            child=WireNamedChild(child_value="c"),
            children=[WireNamedChild(child_value="a"), WireNamedChild(child_value="b")],
        )

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/tree", body=body)

            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            assert sent_body["parentName"] == "root"
            assert sent_body["child"] == {"childValue": "c"}
            assert sent_body["children"] == [
                {"childValue": "a"},
                {"childValue": "b"},
            ]

    @pytest.mark.asyncio
    async def test_send_async_merges_additional_properties_with_wire_names(
        self, mock_token_provider
    ):
        """Test that additional_properties merge alongside wire-named fields."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = WireNamedDynamicDataClass(
            display_name="widget",
            additional_properties={"dynamic1": "data1", "dynamic2": "data2"},
        )

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/dynamic", body=body)

            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            assert sent_body["displayName"] == "widget"
            assert sent_body["dynamic1"] == "data1"
            assert sent_body["dynamic2"] == "data2"
            assert "display_name" not in sent_body
            assert "additional_properties" not in sent_body

    @pytest.mark.asyncio
    async def test_send_async_omits_none_wire_named_fields(self, mock_token_provider):
        """Test that None-valued wire-named fields are omitted from the payload."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = WireNamedDataClass(print_background=True, paper_size=None, html=None)

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/pdf", body=body)

            call_args = mock_send.call_args
            import json
            sent_body = json.loads(call_args[0][4])
            assert sent_body == {"printBackground": True}
            assert "paperSize" not in sent_body
            assert "html" not in sent_body

    @pytest.mark.asyncio
    async def test_send_async_sends_binary_body_verbatim(self, mock_token_provider):
        """Test that raw binary bodies are sent as bytes without JSON encoding."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = b"\x00\x01raw-binary\xff"

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("POST", "https://api.example.com/upload", body=body)

            call_args = mock_send.call_args
            sent_body = call_args[0][4]
            # NOTE(victoriahall): Binary payloads must never be JSON-encoded; the
            # exact bytes must reach the transport unchanged.
            assert isinstance(sent_body, bytes)
            assert sent_body == b"\x00\x01raw-binary\xff"

    @pytest.mark.asyncio
    async def test_send_async_sets_authorization_header(self, mock_token_provider):
        """Test that authorization header is set correctly."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="bearer_token_123")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async("GET", "https://api.example.com/data")

            call_args = mock_send.call_args
            headers = call_args[0][3]
            assert headers["Authorization"] == "Bearer bearer_token_123"

    @pytest.mark.asyncio
    async def test_send_async_sets_content_type_header(self, mock_token_provider):
        """Test that content-type header is set correctly."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async(
                "POST", "https://api.example.com/data", body={"test": "data"}
            )

            call_args = mock_send.call_args
            headers = call_args[0][3]
            assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_send_async_with_bytes_body_sends_raw_octet_stream(self, mock_token_provider):
        """Test send_async sends raw bytes as application/octet-stream."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = b"\x00\x01raw-binary\xff"

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async(
                "POST", "https://api.example.com/upload", body=body
            )

            call_args = mock_send.call_args
            headers = call_args[0][3]
            sent_body = call_args[0][4]
            assert headers["Content-Type"] == "application/octet-stream"
            assert sent_body == body
            assert isinstance(sent_body, bytes)

    @pytest.mark.asyncio
    async def test_send_async_with_bytes_body_honors_explicit_content_type(
        self, mock_token_provider
    ):
        """Test send_async honors an explicit content_type for a bytes body."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')

        body = b"%PDF-1.4 binary"

        with patch.object(
            client, '_send_with_retry', new_callable=AsyncMock, return_value=mock_response
        ) as mock_send:
            await client.send_async(
                "POST",
                "https://api.example.com/upload",
                body=body,
                content_type="application/pdf",
            )

            call_args = mock_send.call_args
            headers = call_args[0][3]
            sent_body = call_args[0][4]
            assert headers["Content-Type"] == "application/pdf"
            assert sent_body == body

    @pytest.mark.asyncio
    async def test_delay_retry_with_exponential_backoff(self, mock_token_provider):
        """Test retry delay with exponential backoff."""
        options = ConnectorClientOptions(
            use_exponential_backoff=True,
            initial_retry_delay_seconds=1.0
        )
        client = ConnectorHttpClient(mock_token_provider, options)

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await client._delay_retry(0)
            mock_sleep.assert_called_once_with(1.0)

            mock_sleep.reset_mock()
            await client._delay_retry(1)
            mock_sleep.assert_called_once_with(2.0)

            mock_sleep.reset_mock()
            await client._delay_retry(2)
            mock_sleep.assert_called_once_with(4.0)

    @pytest.mark.asyncio
    async def test_delay_retry_without_exponential_backoff(self, mock_token_provider):
        """Test retry delay without exponential backoff."""
        options = ConnectorClientOptions(
            use_exponential_backoff=False,
            initial_retry_delay_seconds=0.5
        )
        client = ConnectorHttpClient(mock_token_provider, options)

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await client._delay_retry(0)
            mock_sleep.assert_called_with(0.5)

            mock_sleep.reset_mock()
            await client._delay_retry(5)
            mock_sleep.assert_called_with(0.5)

    @pytest.mark.asyncio
    async def test_get_async_success(self, mock_token_provider):
        """Test get_async with successful response."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = '{"data": "value"}'

        with patch.object(client, 'send_async', new_callable=AsyncMock, return_value=mock_response):
            result = await client.get_async("https://api.example.com/resource")

            assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_async_error_raises_exception(self, mock_token_provider):
        """Test get_async with error response raises ConnectorException."""
        mock_token_provider.get_access_token_async = AsyncMock(return_value="token")
        options = ConnectorClientOptions()
        client = ConnectorHttpClient(mock_token_provider, options)

        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.text = '{"error": "Not Found"}'

        with patch.object(client, 'send_async', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(ConnectorException) as exc_info:
                await client.get_async("https://api.example.com/missing")

            assert exc_info.value.status_code == 404
