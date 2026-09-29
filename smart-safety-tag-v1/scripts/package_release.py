#!/usr/bin/env python3
"""Verify source/export hashes and package the complete prototype release.

Run after export_manufacturing.py.  The archive contains editable CAD,
manufacturing files, firmware source and prebuilt hardware-test images.
Generated build caches and KiCad UI state are intentionally omitted.
"""

from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from release_data import RELEASE_DATE, REVISION


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT.parent / f"smart-safety-tag-v1-{REVISION}-complete.zip"
EXCLUDED_DIRS = {"__pycache__", "build", ".git"}
EXCLUDED_SUFFIXES = {".pyc", ".kicad_prl", ".xml"}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_hashes(entries: dict[str, str], *, base: Path = ROOT) -> None:
    for name, expected in entries.items():
        path = base / name
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f"Missing or modified release input: {path}")


def verify() -> None:
    for kind, name in (("tag", "smart-safety-tag"),
                       ("charging-adapter", "charging-adapter")):
        directory = ROOT / "hardware" / kind
        report = json.loads((directory / "routed-drc.json").read_text())
        for key in ("violations", "unconnected_items", "schematic_parity", "ignored_checks"):
            if report[key]:
                raise ValueError(f"{kind} DRC still has {key}")
        erc = (directory / "erc-report.txt").read_text()
        if "ERC messages: 0  Errors 0  Warnings 0" not in erc:
            raise ValueError(f"{kind} ERC is not clear")
        manifest = json.loads((ROOT / "manufacturing" / kind / "manifest.json").read_text())
        if manifest["project"] != name or manifest["revision"] != REVISION:
            raise ValueError(f"{kind} manifest does not match this revision")
        verify_hashes(manifest["files_sha256"])

    record = json.loads((ROOT / "firmware/hardware-tests/prebuilt/build-record.json").read_text())
    verify_hashes(record["source_sha256"])
    verify_hashes(record["image_sha256"],
                  base=ROOT / "firmware/hardware-tests/prebuilt")


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return (not any(part in EXCLUDED_DIRS or part.endswith("-backups")
                    for part in relative.parts)
            and path.suffix not in EXCLUDED_SUFFIXES)


def package() -> None:
    verify()
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and included(path))
    if not files:
        raise ValueError("No release files found")
    year, month, day = map(int, RELEASE_DATE.split("-"))
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = f"{ROOT.name}/{path.relative_to(ROOT).as_posix()}"
            info = ZipInfo(name, date_time=(year, month, day, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED,
                             compresslevel=9)
    checksum = ARCHIVE.with_name(ARCHIVE.name + ".sha256")
    checksum.write_text(f"{digest(ARCHIVE)}  {ARCHIVE.name}\n")
    print(f"Verified both CAD/export manifests and firmware build record")
    print(f"Created {ARCHIVE} ({len(files)} files, {ARCHIVE.stat().st_size} bytes)")
    print(f"SHA-256: {digest(ARCHIVE)}")


if __name__ == "__main__":
    package()
