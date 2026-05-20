"""MongoDB sink — applies CDC events as upserts/deletes."""

from __future__ import annotations
import logging
from pymongo import MongoClient
from pymongo.database import Database

from src.config import get_mongo_config

logger = logging.getLogger("cdc.sink")


class MongoSink:
    def __init__(self, db: Database | None = None):
        if db is not None:
            self.db = db
        else:
            cfg = get_mongo_config()
            client = MongoClient(cfg["uri"])
            self.db = client[cfg["database"]]

    def apply_event(self, event: dict) -> str:
        table = event["table"]
        op = event["operation"]
        data = event.get("data", {})
        old_keys = event.get("old_keys", {})
        collection = self.db[table]

        if op == "INSERT":
            pk = self._extract_pk(data, table)
            doc = {**data, "_pg_pk": pk, "_cdc_op": "INSERT", "_cdc_ts": event["timestamp"]}
            collection.update_one({"_pg_pk": pk}, {"$set": doc}, upsert=True)
            logger.debug("INSERT %s pk=%s", table, pk)
            return "inserted"

        elif op == "UPDATE":
            pk = self._extract_pk(data, table)
            doc = {**data, "_pg_pk": pk, "_cdc_op": "UPDATE", "_cdc_ts": event["timestamp"]}
            collection.update_one({"_pg_pk": pk}, {"$set": doc}, upsert=True)
            logger.debug("UPDATE %s pk=%s", table, pk)
            return "updated"

        elif op == "DELETE":
            pk = self._extract_pk(old_keys, table)
            collection.delete_one({"_pg_pk": pk})
            logger.debug("DELETE %s pk=%s", table, pk)
            return "deleted"

        return "skipped"

    def apply_batch(self, events: list[dict]) -> dict:
        counts = {"inserted": 0, "updated": 0, "deleted": 0, "skipped": 0}
        for event in events:
            result = self.apply_event(event)
            counts[result] = counts.get(result, 0) + 1
        return counts

    def _extract_pk(self, data: dict, table: str) -> str:
        pk_map = {"customers": "customer_id", "orders": "order_id"}
        pk_col = pk_map.get(table, "id")
        return str(data.get(pk_col, "unknown"))
