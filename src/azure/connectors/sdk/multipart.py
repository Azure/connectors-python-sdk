# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Encode multipart connector requests without JSON-encoding file content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from aiohttp import MultipartWriter
from aiohttp.abc import AbstractStreamWriter


@dataclass(frozen=True)
class MultipartFile:
    """A buffered upload with a filename and media type.

    Args:
        content: The unencoded file bytes.
        file_name: The filename sent in the part's Content-Disposition header.
        content_type: The file's media type.
    """

    content: bytes
    file_name: str = "blob"
    content_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        """Validate file content and headers before building a request."""
        if not isinstance(self.content, bytes):
            raise TypeError("Parameter 'content' must contain bytes.")
        if not self.file_name or any(
            character in self.file_name for character in "\r\n"
        ):
            raise ValueError("Parameter 'file_name' must be a nonempty single line.")
        if "/" not in self.content_type or any(
            character in self.content_type for character in "\r\n"
        ):
            raise ValueError("Parameter 'content_type' must be a single-line media type.")


class _MultipartBuffer(AbstractStreamWriter):
    """Collect the native multipart writer's output for replay-safe requests."""

    def __init__(self) -> None:
        self.content = bytearray()

    async def write(self, content: bytes | bytearray | memoryview) -> None:
        """Append bytes emitted by the multipart writer."""
        self.content.extend(content)

    async def write_eof(self, chunk: bytes = b"") -> None:
        """Append a final chunk to the in-memory body."""
        await self.write(chunk)

    async def drain(self) -> None:
        """Buffer writes need no network drain."""

    def enable_compression(
        self, encoding: str = "deflate", strategy: int | None = None
    ) -> None:
        """Reject HTTP compression in a MIME-body-only buffer."""
        raise NotImplementedError("Multipart buffers do not encode HTTP compression.")

    def enable_chunking(self) -> None:
        """Reject HTTP chunk framing in a MIME-body-only buffer."""
        raise NotImplementedError("Multipart buffers do not encode HTTP chunks.")

    async def write_headers(
        self, status_line: str, headers: Mapping[str, str]
    ) -> None:
        """Reject HTTP headers in a MIME-body-only buffer."""
        raise NotImplementedError("Multipart buffers encode only the MIME body.")


async def encode_multipart_form_data(
    fields: Iterable[tuple[str, str | bytes | MultipartFile]],
) -> tuple[bytes, str]:
    """Encode ordered fields, including repeated names and empty forms.

    Args:
        fields: Wire field names and text or binary values. Plain bytes use
            the default filename and media type from MultipartFile.

    Returns:
        The complete body bytes and their boundary-bearing content type.

    Raises:
        TypeError: If a field is neither text nor a supported binary value.
    """
    buffer = _MultipartBuffer()
    with MultipartWriter("form-data") as multipart:
        for name, value in fields:
            if isinstance(value, bytes):
                value = MultipartFile(value)
            if isinstance(value, MultipartFile):
                part = multipart.append(
                    value.content,
                    {"Content-Type": value.content_type},
                )
                part.set_content_disposition(
                    "form-data",
                    quote_fields=False,
                    name=name,
                    filename=value.file_name,
                )
            elif isinstance(value, str):
                part = multipart.append(value)
                part.set_content_disposition("form-data", name=name)
            else:
                raise TypeError(f"Multipart field '{name}' must contain text or file bytes.")

        await multipart.write(buffer)
        return bytes(buffer.content), multipart.content_type
