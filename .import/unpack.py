"""Verify and expand the fixed, author-reviewed project source snapshot."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "41c78dbdff9ff40bda4a98fa5e4a2b13535e57fa394cd27eb9708d98796c0fee"
EXPECTED_BYTES = 124856
EXPECTED_FILES = 106


def main() -> None:
    parts = ROOT / ".import" / "parts"
    raw = b"".join((parts / f"{i:03d}").read_bytes() for i in range(11))
    if len(raw) != EXPECTED_BYTES or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise SystemExit("Source snapshot checksum mismatch; nothing extracted.")
    payload: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:xz") as archive:
        members = archive.getmembers()
        if len(members) != EXPECTED_FILES or sum(m.size for m in members) > 2_000_000:
            raise SystemExit("Unexpected archive size or member count.")
        for member in members:
            path = PurePosixPath(member.name)
            allowed = member.name == "artifact_inventory.json" or path.parts[0] in {"engineering", "marketing", "reviews"}
            if not member.isfile() or path.is_absolute() or ".." in path.parts or not allowed:
                raise SystemExit(f"Unsafe member: {member.name!r}")
            if member.name in payload:
                raise SystemExit(f"Duplicate member: {member.name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise SystemExit(f"Unreadable member: {member.name}")
            data = stream.read()
            if len(data) != member.size:
                raise SystemExit(f"Truncated member: {member.name}")
            payload[member.name] = data
    inventory = json.loads(payload["artifact_inventory.json"])
    expected = {item["path"]: item for item in inventory["files"] if item["remote_import"]}
    if set(payload) != set(expected) | {"artifact_inventory.json"}:
        raise SystemExit("Archive and file inventory disagree.")
    for name, data in payload.items():
        if name in expected:
            item = expected[name]
            if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise SystemExit(f"File checksum mismatch: {name}")
        destination = ROOT / name
        if ROOT not in destination.resolve().parents:
            raise SystemExit(f"Path escapes checkout: {name}")
        if destination.is_symlink() or (destination.exists() and destination.read_bytes() != data):
            raise SystemExit(f"Refusing to overwrite changed file: {name}")
    for name, data in payload.items():
        destination = ROOT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    print(f"Verified and expanded {len(payload)} files; archive SHA256 {EXPECTED_SHA256}.")


if __name__ == "__main__":
    main()
