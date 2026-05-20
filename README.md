# Real-Time CDC

Change Data Capture pipeline that streams PostgreSQL WAL changes to MongoDB in real-time using logical replication, wal2json decoding, and upsert-based sink operations.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│              PostgreSQL (Source)               │
│  ┌──────────┐  ┌──────────┐                  │
│  │ customers │  │  orders   │  ← WAL-logged   │
│  └──────────┘  └──────────┘                  │
│         │ logical replication (wal_level=logical)
│  ┌──────▼──────────────────┐                  │
│  │  Replication Slot        │                  │
│  │  (wal2json output)       │                  │
│  └──────────┬──────────────┘                  │
└─────────────┼────────────────────────────────┘
              │ JSON change events
              ▼
     ┌─────────────────┐
     │     Decoder       │  Parse wal2json → normalized events
     │  src/decoder.py   │  {operation, table, data, old_keys}
     └────────┬────────┘
              │
     ┌────────▼────────┐
     │    Mongo Sink     │  Upsert on INSERT/UPDATE, delete on DELETE
     │   src/sink.py     │  Tracks _pg_pk for idempotent writes
     └─────────────────┘
              │
              ▼
     ┌─────────────────┐
     │    MongoDB        │  Mirrored collections: customers, orders
     │    (Sink)         │
     └─────────────────┘
```

## Features

- **Logical replication** — uses Postgres replication slots (no polling, no triggers)
- **wal2json decoding** — structured JSON change events
- **Idempotent sink** — upserts with `_pg_pk` field, safe for replays
- **Graceful shutdown** — SIGINT/SIGTERM handling with LSN feedback
- **Docker Compose** — full setup with Postgres (wal_level=logical) + MongoDB

## Quick Start

```bash
git clone <repo-url> && cd 08-realtime-cdc
cp .env.example .env

# start infrastructure + CDC
docker compose up --build

# in another terminal, insert test data:
docker compose exec postgres psql -U replicator -d cdc_source \
    -c "INSERT INTO customers (name, email) VALUES ('Alice', 'alice@test.com')"

# verify in MongoDB:
docker compose exec mongo mongosh cdc_sink --eval "db.customers.find()"
```

## Testing

```bash
pip install -r requirements.txt
pytest -v
```

**13 tests** — WAL decoding (8 tests) and MongoDB sink operations (5 tests). No Postgres/Mongo required.

## Project Structure

```
├── docker-compose.yml    # Postgres + MongoDB + CDC service
├── Dockerfile
├── sql/
│   └── source_schema.sql # Source tables + triggers + publication
├── src/
│   ├── config.py         # .env loader
│   ├── decoder.py        # wal2json payload parser
│   ├── sink.py           # MongoDB upsert/delete operations
│   └── streamer.py       # CDC loop (replication slot consumer)
├── main.py               # CLI: stream
└── tests/
    ├── test_decoder.py   # 8 tests — WAL message parsing
    └── test_sink.py      # 5 tests — MongoDB operations (mocked)
```
