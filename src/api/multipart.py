"""Dependency-free multipart boundary validation for P10 uploads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from src.shared.errors import ApplicationError


@dataclass(frozen=True)
class UploadPart:
    field_name: str
    filename: str
    content_type: str
    content: bytes


class MultipartParser:
    def __init__(self, *, max_bytes: int = 10 * 1024 * 1024, allowed_types: frozenset[str] | None = None) -> None:
        self.max_bytes = max_bytes
        self.allowed_types = allowed_types or frozenset({"application/pdf", "text/plain", "audio/wav", "audio/mpeg", "image/jpeg", "image/png"})

    def parse(self, headers: Mapping[str, str], body: bytes) -> UploadPart:
        if len(body) > self.max_bytes:
            raise ApplicationError("UPLOAD_TOO_LARGE", "Upload exceeds the configured size limit.", details={"max_bytes": self.max_bytes})
        content_type = next((value for key, value in headers.items() if key.lower() == "content-type"), "")
        match = re.search(r"boundary=\"?([^\";]+)", content_type, flags=re.IGNORECASE)
        if not content_type.lower().startswith("multipart/form-data") or match is None:
            raise ApplicationError("UPLOAD_MULTIPART_REQUIRED", "Uploads must use multipart/form-data.")
        boundary = ("--" + match.group(1)).encode("utf-8")
        sections = [section for section in body.split(boundary) if section.strip(b"-\r\n")]
        if not sections:
            raise ApplicationError("UPLOAD_PART_REQUIRED", "A multipart file part is required.")
        raw = sections[0].strip(b"\r\n-")
        header_block, separator, content = raw.partition(b"\r\n\r\n")
        if not separator:
            raise ApplicationError("UPLOAD_PART_INVALID", "Multipart part headers are invalid.")
        part_headers: dict[str, str] = {}
        for line in header_block.decode("utf-8", errors="strict").split("\r\n"):
            name, divider, value = line.partition(":")
            if divider:
                part_headers[name.strip().lower()] = value.strip()
        disposition = part_headers.get("content-disposition", "")
        filename_match = re.search(r'filename="?([^";]+)', disposition, flags=re.IGNORECASE)
        filename = filename_match.group(1).strip() if filename_match else ""
        if not filename:
            raise ApplicationError("UPLOAD_FILENAME_REQUIRED", "Multipart file filename is required.")
        part_type = part_headers.get("content-type", "application/octet-stream").lower()
        if part_type not in self.allowed_types:
            raise ApplicationError("UPLOAD_TYPE_FORBIDDEN", "Upload content type is not allowed.", details={"content_type": part_type})
        return UploadPart(
            field_name=re.search(r'name="?([^";]+)', disposition, flags=re.IGNORECASE).group(1) if re.search(r'name="?([^";]+)', disposition, flags=re.IGNORECASE) else "file",
            filename=filename,
            content_type=part_type,
            content=content.rstrip(b"\r\n-"),
        )


__all__ = ["MultipartParser", "UploadPart"]
