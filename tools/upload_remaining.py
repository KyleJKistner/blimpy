"""Add the full-package assets to Blimpy using your normal authenticated Git.

Run from the extracted FULL project package, not a source-only GitHub clone.
Nothing is pushed unless --push is provided. No tokens are accepted or stored.
An existing different file is never overwritten; pushes never use --force.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/KyleJKistner/blimpy.git"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str, cwd: Path, capture: bool = False) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True,
                            text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--push", action="store_true", help="Commit and push verified assets to the public Blimpy repository")
    args = parser.parse_args()
    records = [item for item in json.loads((ROOT / "artifact_inventory.json").read_text())["files"]
               if not item["remote_import"]]
    for item in records:
        rel = PurePosixPath(item["path"])
        if rel.is_absolute() or ".." in rel.parts or rel.parts[0] not in {"engineering", "marketing", "reviews"}:
            raise SystemExit(f"Unsafe inventory path: {rel}")
        source = ROOT / rel
        if source.is_symlink() or ROOT not in source.resolve().parents:
            raise SystemExit(f"Unsafe source path: {source}")
        if not source.is_file() or source.stat().st_size != item["bytes"] or digest(source) != item["sha256"]:
            raise SystemExit(f"Missing/changed asset: {rel}. Use the original full project ZIP.")
    print(f"Verified {len(records)} remaining files ({sum(x['bytes'] for x in records):,} bytes).")
    if not args.push:
        print("No Git writes performed. Add --push to commit these assets to the public repository.")
        return
    if shutil.which("git") is None:
        raise SystemExit("Install Git and configure your normal GitHub authentication first.")
    work = Path(tempfile.mkdtemp(prefix="blimpy-assets-"))
    checkout = work / "blimpy"
    print(f"Working checkout (retained on completion or failure): {checkout}")
    git("clone", "--branch", "main", "--single-branch", REPO, str(checkout), cwd=work)
    for key in ("user.name", "user.email"):
        if not git("config", "--get", key, cwd=checkout, capture=True):
            raise SystemExit(f"Set your Git {key} before retrying; no commit created.")
    pending = []
    for item in records:
        destination = checkout / item["path"]
        if checkout not in destination.resolve().parents or destination.is_symlink():
            raise SystemExit(f"Unsafe remote path: {item['path']}")
        if destination.exists():
            if not destination.is_file() or digest(destination) != item["sha256"]:
                raise SystemExit(f"Remote file differs; refusing overwrite: {item['path']}")
        else:
            pending.append(item)
    if not pending:
        print("All assets already exist with matching checksums; nothing to commit.")
        return
    for item in pending:
        destination = checkout / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / item["path"], destination)
    for offset in range(0, len(pending), 50):
        git("--literal-pathspecs", "add", "--", *[x["path"] for x in pending[offset:offset + 50]], cwd=checkout)
    git("commit", "-m", "Add full-resolution concept films, audio, models and review evidence", cwd=checkout)
    git("push", "origin", "HEAD:main", cwd=checkout)
    print("Published commit:", git("rev-parse", "HEAD", cwd=checkout, capture=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Stopped without force-pushing: {error}") from error
