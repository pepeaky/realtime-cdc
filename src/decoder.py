"""Decodes PostgreSQL logical replication messages (pgoutput / wal2json)."""

from __future__ import annotations
import json
from datetime import datetime, timezone


def decode_wal2json(payload: str) -> list[dict]:
    try:
        msg = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return []

    events = []
    for change in msg.get("change", []):
        event = _normalize_change(change)
        if event:
            events.append(event)
    return events


def _normalize_change(change: dict) -> dict | None:
    kind = change.get("kind")
    if kind not in ("insert", "update", "delete"):
        return None

    table = change.get("table")
    schema = change.get("schema", "public")

    columns = change.get("columnnames", [])
    values = change.get("columnvalues", [])
    data = dict(zip(columns, values)) if columns and values else {}

    old_columns = change.get("oldkeys", {}).get("keynames", [])
    old_values = change.get("oldkeys", {}).get("keyvalues", [])
    old_data = dict(zip(old_columns, old_values)) if old_columns else {}

    return {
        "operation": kind.upper(),
        "schema": schema,
        "table": table,
        "data": data,
        "old_keys": old_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
