"""CLI for the Real-Time CDC system."""

import argparse
import logging

from src.streamer import CDCStreamer


def cmd_stream(args):
    CDCStreamer().run()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Real-Time CDC: Postgres → MongoDB")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("stream", help="Start CDC streaming")

    args = parser.parse_args()
    {"stream": cmd_stream}[args.command](args)


if __name__ == "__main__":
    main()
