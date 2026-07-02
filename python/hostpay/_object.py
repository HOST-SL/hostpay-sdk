"""Lightweight attribute-access wrapper for API responses.

Responses come back as HostPayObject so you can use `wallet.id` and
`wallet["id"]` interchangeably. Unknown/new fields are preserved automatically —
strict typed models can be generated later from ../openapi.json.
"""
from __future__ import annotations

from typing import Any


class HostPayObject(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return _wrap(self[name])
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __repr__(self) -> str:
        return f"HostPayObject({dict.__repr__(self)})"


def _wrap(value: Any) -> Any:
    if isinstance(value, dict):
        return HostPayObject(value)
    if isinstance(value, list):
        return [_wrap(v) for v in value]
    return value
