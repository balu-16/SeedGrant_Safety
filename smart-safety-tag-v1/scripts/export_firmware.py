#!/usr/bin/env python3
"""Package a completed ESP-IDF hardware-test build with source/image hashes."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware" / "hardware-tests"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=FIRMWARE / "build")
    args = parser.parse_args()
    build = args.build_dir.resolve()
    description = json.loads((build / "project_description.json").read_text())
    if description["target"] != "esp32s3":
        raise ValueError("Expected an ESP32-S3 build")
    app = build / description["app_bin"]
    source = [FIRMWARE / "CMakeLists.txt", FIRMWARE / "sdkconfig.defaults",
              FIRMWARE / "sdkconfig", ROOT / "hardware/board-interface.json"]
    source += sorted((FIRMWARE / "main").glob("*"))
    source = [p for p in source if p.is_file()]
    if any(p.stat().st_mtime > app.stat().st_mtime for p in source):
        raise ValueError("A firmware source/configuration changed after the binary; rebuild first")
    output = FIRMWARE / "prebuilt"
    images = (Path("bootloader/bootloader.bin"), Path("partition_table/partition-table.bin"),
              Path(description["app_bin"]), Path("flash_args"))
    for relative in images:
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(build / relative, destination)
    commit = subprocess.check_output(
        ["git", "-C", description["idf_path"], "rev-parse", "HEAD"], text=True).strip()
    record = {
        "exported_utc": datetime.now(timezone.utc).isoformat(),
        "project_version": description["project_version"],
        "target": description["target"],
        "esp_idf_version": description["git_revision"],
        "esp_idf_commit": commit,
        "application_size_bytes": app.stat().st_size,
        "flash_size": "4 MB", "psram": "2 MB quad, 40 MHz; boot memory test enabled",
        "status": "compiled successfully; no physical-board flash or measurements performed",
        "source_sha256": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in source},
        "image_sha256": {str(p): sha256((output / p).read_bytes()).hexdigest() for p in images},
    }
    (output / "build-record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Packaged ESP-IDF {description['git_revision']} firmware: {record['application_size_bytes']} bytes")


if __name__ == "__main__":
    main()
