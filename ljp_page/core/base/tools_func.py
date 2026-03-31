from typing import Any, Mapping


def _safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, (list, tuple)):
        return list(value)
    return str(value)