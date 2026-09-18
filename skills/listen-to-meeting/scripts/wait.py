#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Wait for new transcript chunks in a running listen-to-meeting session.

    wait.py --session-dir DIR [--after N] [--timeout SECONDS]

Blocks until the first of: a chunk numbered above --after appears, the capture
stops, or --timeout elapses (default 10s). Prints the new chunk paths to
stdout, one per line, and the outcome — `new`, `stopped` or `timeout` — to
stderr. Always exits 0; a timeout is a normal result.

The capture itself is listen.py; this only reads the directory.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import session

POLL = 0.2  # how often to look
DEFAULT_TIMEOUT = 10.0  # ceiling on one wait; the agent is blocked for it, so keep it short


def wait(session_dir: Path, after: int, timeout: float) -> int:
    deadline = time.monotonic() + timeout
    while True:
        new = session.chunks_after(session_dir, after)
        if new:
            for _, path in new:
                print(path)
            print(f"new: {len(new)} chunk(s)", file=sys.stderr)
            return 0

        # Checked after the scan: `run` writes its final chunks before marking
        # itself stopped, so this order never drops the last one.
        if not session.capture_running(session_dir):
            print("stopped: capture is no longer running", file=sys.stderr)
            return 0

        if time.monotonic() >= deadline:
            print("timeout: no new chunks", file=sys.stderr)
            return 0
        time.sleep(POLL)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--session-dir", required=True, help="the running session's directory")
    parser.add_argument("--after", type=int, default=0, help="highest chunk number already processed")
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT,
        help=f"return after this many seconds even with nothing new (default: {DEFAULT_TIMEOUT:g})",
    )
    args = parser.parse_args()
    return wait(Path(args.session_dir).resolve(), args.after, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
