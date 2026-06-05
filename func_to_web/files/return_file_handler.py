import shutil
import time
import uuid
from pathlib import Path


# Marker file used to throttle opportunistic cleanup. Its name has no "___"
# separators, so _decode_filename() returns None for it and cleanup_returned_files
# never treats it as a returned file (never deletes it).
CLEANUP_MARKER = ".last_cleanup"


def _encode_filename(file_id: str, timestamp: int, filename: str) -> str:
    safe = filename.replace("___", "_")
    return f"{file_id}___{timestamp}___{safe}"


def _decode_filename(name: str) -> dict | None:
    parts = name.split("___")
    if len(parts) != 3:
        return None
    try:
        return {"file_id": parts[0], "timestamp": int(parts[1]), "filename": parts[2]}
    except ValueError:
        return None


def save_returned_file(
    file_response, returns_dir: Path, returns_lifetime: int
) -> tuple[str, str]:
    """Save a FileResponse to disk.

    Runs opportunistic cleanup first (throttled, cheap when recent).

    Returns:
        (file_id, file_path)
    """
    maybe_cleanup(returns_dir, returns_lifetime)

    file_id = uuid.uuid4().hex
    timestamp = int(time.time())
    encoded = _encode_filename(file_id, timestamp, file_response.filename)
    file_path = returns_dir / encoded

    returns_dir.mkdir(parents=True, exist_ok=True)

    if file_response.path is not None:
        # Stream-copy so large files never load fully into RAM.
        with open(file_response.path, "rb") as src, open(file_path, "wb") as dst:
            shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
    else:
        file_path.write_bytes(file_response.data)

    return file_id, str(file_path)


def get_returned_file(file_id: str, returns_dir: Path) -> dict | None:
    """Find a returned file by file_id.

    Returns:
        {"path": str, "filename": str} or None if not found.
    """
    if not returns_dir.exists():
        return None

    for p in returns_dir.iterdir():
        if not p.is_file():
            continue
        meta = _decode_filename(p.name)
        if meta and meta["file_id"] == file_id:
            return {"path": str(p), "filename": meta["filename"]}

    return None


def cleanup_returned_files(returns_dir: Path, returns_lifetime: int) -> int:
    """Delete returned files older than `returns_lifetime` seconds.

    Returns:
        Number of files deleted.
    """
    if not returns_dir.exists():
        return 0

    now = int(time.time())
    count = 0

    for p in returns_dir.iterdir():
        if not p.is_file():
            continue
        # _decode_filename returns None for the .last_cleanup marker (no "___"),
        # so the marker is skipped here and never deleted.
        meta = _decode_filename(p.name)
        if meta and (now - meta["timestamp"]) > returns_lifetime:
            try:
                p.unlink()
                count += 1
            except OSError:
                pass

    return count


def maybe_cleanup(returns_dir: Path, returns_lifetime: int) -> None:
    """Opportunistically clean up expired returned files, throttled by a marker.

    A `.last_cleanup` marker file in `returns_dir` records (via its mtime) when
    cleanup last ran. If it is younger than `returns_lifetime` seconds, this is a
    cheap no-op (a single stat). Otherwise the marker is refreshed and
    `cleanup_returned_files` runs.

    Multi-process safe by being harmless: there are no locks on purpose. If two
    processes pass the freshness check at the same time, both run cleanup — the
    duplicate `unlink()` calls are already swallowed as OSError in
    `cleanup_returned_files`.
    """
    marker = returns_dir / CLEANUP_MARKER

    try:
        if (time.time() - marker.stat().st_mtime) < returns_lifetime:
            return
    except OSError:
        # Marker missing or unreadable — fall through and run cleanup.
        pass

    returns_dir.mkdir(parents=True, exist_ok=True)
    marker.touch()
    cleanup_returned_files(returns_dir, returns_lifetime)
