"""The layout of a listen-to-meeting session directory.

Where a session's files live and how they are named, for listen.py, which
writes them, and wait.py, which reads them.

Layout::

    <session-dir>/
        chunks/chunk-NNNN.txt   finalized transcript chunks, written atomically
        transcript.md           the running full transcript
        status.json             heartbeat; `listening` is false once run exits
        stop                    created by the agent to end the capture
"""

from __future__ import annotations

import json
from pathlib import Path

CHUNK_DIRNAME = "chunks"
CHUNK_GLOB = "chunk-*.txt"
STATUS_FILENAME = "status.json"
TRANSCRIPT_FILENAME = "transcript.md"
STOP_FILENAME = "stop"


def chunk_dir(session_dir: Path) -> Path:
    return session_dir / CHUNK_DIRNAME


def status_path(session_dir: Path) -> Path:
    return session_dir / STATUS_FILENAME


def transcript_path(session_dir: Path) -> Path:
    return session_dir / TRANSCRIPT_FILENAME


def stop_path(session_dir: Path) -> Path:
    return session_dir / STOP_FILENAME


def chunk_name(index: int) -> str:
    """The filename for chunk `index`. Zero-padded so plain sorting is ordering."""
    return f"chunk-{index:04d}.txt"


def chunk_index(path: Path) -> "int | None":
    """The chunk number in a filename, or None if it isn't a chunk file."""
    _, _, digits = path.stem.partition("-")
    return int(digits) if digits.isdigit() else None


def chunks_after(session_dir: Path, after: int) -> "list[tuple[int, Path]]":
    """Chunks numbered above `after`, in order. Empty if none, or no session yet."""
    directory = chunk_dir(session_dir)
    if not directory.is_dir():
        return []
    found = []
    for path in directory.glob(CHUNK_GLOB):
        index = chunk_index(path)
        if index is not None and index > after:
            found.append((index, path))
    found.sort()
    return found


def capture_running(session_dir: Path) -> bool:
    """Whether the capture is still going.

    True while no status file is readable yet: `listen.py run` writes one only
    once the model has loaded, and a session that has not started is not one
    that has finished.
    """
    try:
        status = json.loads(status_path(session_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return bool(status.get("listening", True))
