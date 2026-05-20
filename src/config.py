import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_pg_config() -> dict:
    return {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", "5432")),
        "dbname": os.getenv("PG_DATABASE", "cdc_source"),
        "user": os.getenv("PG_USER", "replicator"),
        "password": os.getenv("PG_PASSWORD", ""),
    }


def get_slot_config() -> dict:
    return {
        "slot_name": os.getenv("PG_SLOT_NAME", "cdc_slot"),
        "publication": os.getenv("PG_PUBLICATION", "cdc_pub"),
    }


def get_mongo_config() -> dict:
    return {
        "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        "database": os.getenv("MONGO_DATABASE", "cdc_sink"),
    }


def get_stream_config() -> dict:
    return {
        "poll_interval": float(os.getenv("POLL_INTERVAL", "1.0")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }
