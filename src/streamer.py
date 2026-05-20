"""CDC streamer — consumes WAL changes and feeds them to the sink."""

from __future__ import annotations
import logging
import signal
import time

import psycopg2
from psycopg2.extras import LogicalReplicationConnection

from src.config import get_pg_config, get_slot_config, get_stream_config
from src.decoder import decode_wal2json
from src.sink import MongoSink

logger = logging.getLogger("cdc.streamer")


class CDCStreamer:
    def __init__(self):
        self._running = False
        self._pg_cfg = get_pg_config()
        self._slot_cfg = get_slot_config()
        self._stream_cfg = get_stream_config()
        self._sink = MongoSink()
        self._conn = None

    def _connect(self):
        self._conn = psycopg2.connect(
            **self._pg_cfg,
            connection_factory=LogicalReplicationConnection,
        )
        cur = self._conn.cursor()

        try:
            cur.create_replication_slot(self._slot_cfg["slot_name"], output_plugin="wal2json")
            logger.info("Created replication slot: %s", self._slot_cfg["slot_name"])
        except psycopg2.errors.DuplicateObject:
            logger.info("Replication slot already exists: %s", self._slot_cfg["slot_name"])

        cur.start_replication(
            slot_name=self._slot_cfg["slot_name"],
            decode=True,
            options={"publication_names": self._slot_cfg["publication"], "include-pk": "true"},
        )
        return cur

    def _handle_signal(self, signum, frame):
        logger.info("Received signal %d — stopping", signum)
        self._running = False

    def run(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        cur = self._connect()
        self._running = True
        logger.info("CDC streaming started — slot=%s", self._slot_cfg["slot_name"])

        while self._running:
            msg = cur.read_message()
            if msg:
                events = decode_wal2json(msg.payload)
                if events:
                    counts = self._sink.apply_batch(events)
                    logger.info("Applied %d events: %s", len(events), counts)
                msg.cursor.send_feedback(flush_lsn=msg.data_start)
            else:
                time.sleep(self._stream_cfg["poll_interval"])

        if self._conn:
            self._conn.close()
        logger.info("CDC streaming stopped")
