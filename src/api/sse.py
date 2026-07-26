"""SSE event schema and deterministic serialization for P10."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable


EVENT_TYPES = frozenset({"plan", "tool", "evidence", "token", "citation", "error", "done"})


@dataclass(frozen=True)
class SSEEvent:
    event: str
    data: dict[str, Any]
    event_id: str | None = None

    def __post_init__(self) -> None:
        if self.event not in EVENT_TYPES:
            raise ValueError(f"unsupported SSE event: {self.event}")

    def encode(self) -> bytes:
        lines: list[str] = []
        if self.event_id:
            lines.append(f"id: {self.event_id}")
        lines.append(f"event: {self.event}")
        payload = json.dumps(self.data, sort_keys=True, default=str, separators=(",", ":"))
        lines.extend(f"data: {line}" for line in payload.splitlines() or [""])
        return ("\n".join(lines) + "\n\n").encode("utf-8")


@dataclass(frozen=True)
class SSEStream:
    events: tuple[SSEEvent, ...]

    @property
    def body(self) -> bytes:
        return b"".join(event.encode() for event in self.events)

    @classmethod
    def from_events(cls, events: Iterable[SSEEvent]) -> "SSEStream":
        return cls(tuple(events))


__all__ = ["EVENT_TYPES", "SSEEvent", "SSEStream"]
