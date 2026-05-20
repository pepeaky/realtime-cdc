import pytest
from src.decoder import decode_wal2json


WAL_INSERT = '{"change":[{"kind":"insert","schema":"public","table":"customers","columnnames":["customer_id","name","email"],"columnvalues":[1,"Alice","alice@test.com"]}]}'
WAL_UPDATE = '{"change":[{"kind":"update","schema":"public","table":"customers","columnnames":["customer_id","name","email"],"columnvalues":[1,"Alice Updated","alice@test.com"],"oldkeys":{"keynames":["customer_id"],"keyvalues":[1]}}]}'
WAL_DELETE = '{"change":[{"kind":"delete","schema":"public","table":"customers","oldkeys":{"keynames":["customer_id"],"keyvalues":[1]}}]}'


class TestDecoder:
    def test_decode_insert(self):
        events = decode_wal2json(WAL_INSERT)
        assert len(events) == 1
        assert events[0]["operation"] == "INSERT"
        assert events[0]["table"] == "customers"
        assert events[0]["data"]["name"] == "Alice"

    def test_decode_update(self):
        events = decode_wal2json(WAL_UPDATE)
        assert events[0]["operation"] == "UPDATE"
        assert events[0]["data"]["name"] == "Alice Updated"
        assert events[0]["old_keys"]["customer_id"] == 1

    def test_decode_delete(self):
        events = decode_wal2json(WAL_DELETE)
        assert events[0]["operation"] == "DELETE"
        assert events[0]["old_keys"]["customer_id"] == 1

    def test_invalid_json_returns_empty(self):
        assert decode_wal2json("not json") == []
        assert decode_wal2json(None) == []

    def test_empty_changes(self):
        assert decode_wal2json('{"change":[]}') == []

    def test_unknown_kind_skipped(self):
        payload = '{"change":[{"kind":"truncate","schema":"public","table":"x"}]}'
        assert decode_wal2json(payload) == []

    def test_timestamp_added(self):
        events = decode_wal2json(WAL_INSERT)
        assert "timestamp" in events[0]

    def test_multiple_changes(self):
        payload = '{"change":[{"kind":"insert","schema":"public","table":"a","columnnames":["id"],"columnvalues":[1]},{"kind":"insert","schema":"public","table":"b","columnnames":["id"],"columnvalues":[2]}]}'
        events = decode_wal2json(payload)
        assert len(events) == 2
