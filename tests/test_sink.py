import pytest
from unittest.mock import MagicMock
from src.sink import MongoSink


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def sink(mock_db):
    return MongoSink(db=mock_db)


class TestMongoSink:
    def test_insert_calls_upsert(self, sink, mock_db):
        event = {"operation": "INSERT", "table": "customers", "data": {"customer_id": 1, "name": "Alice"}, "old_keys": {}, "timestamp": "2025-01-01T00:00:00"}
        result = sink.apply_event(event)
        assert result == "inserted"
        mock_db["customers"].update_one.assert_called_once()

    def test_update_calls_upsert(self, sink, mock_db):
        event = {"operation": "UPDATE", "table": "customers", "data": {"customer_id": 1, "name": "Updated"}, "old_keys": {}, "timestamp": "2025-01-01T00:00:00"}
        result = sink.apply_event(event)
        assert result == "updated"

    def test_delete_calls_delete(self, sink, mock_db):
        event = {"operation": "DELETE", "table": "customers", "data": {}, "old_keys": {"customer_id": 1}, "timestamp": "2025-01-01T00:00:00"}
        result = sink.apply_event(event)
        assert result == "deleted"
        mock_db["customers"].delete_one.assert_called_once()

    def test_batch_counts(self, sink):
        events = [
            {"operation": "INSERT", "table": "customers", "data": {"customer_id": 1}, "old_keys": {}, "timestamp": "t"},
            {"operation": "INSERT", "table": "customers", "data": {"customer_id": 2}, "old_keys": {}, "timestamp": "t"},
            {"operation": "DELETE", "table": "customers", "data": {}, "old_keys": {"customer_id": 1}, "timestamp": "t"},
        ]
        counts = sink.apply_batch(events)
        assert counts["inserted"] == 2
        assert counts["deleted"] == 1

    def test_unknown_operation(self, sink):
        event = {"operation": "TRUNCATE", "table": "x", "data": {}, "old_keys": {}, "timestamp": "t"}
        assert sink.apply_event(event) == "skipped"
