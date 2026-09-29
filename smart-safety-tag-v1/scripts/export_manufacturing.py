#!/usr/bin/env python3
"""Check and export revision-matched prototype fabrication files.

Usage: python3 scripts/export_manufacturing.py --cli-command 'kicad-cli'
The `--cli-command` also accepts an AppImage launcher followed by kicad-cli.
No machine-specific tool path is stored in the project.
"""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shlex
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

from adapter_data import COMPONENTS as ADAPTER, PARTS as ADAPTER_PARTS
from circuit_data import COMPONENTS as TAG
from generate_bom import write as write_bom
from parts import PARTS as TAG_PARTS
from release_data import REVISION


ROOT = Path(__file__).resolve().parents[1]
FAB_LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts"


def run(cli, *args):
    command = [*cli, *map(str, args)]
    print("+", " ".join(shlex.quote(word) for word in command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def project(cli, kind, name, components, parts):
    board = ROOT / "hardware" / kind / (name + ".kicad_pcb")
    schematic = ROOT / "hardware" / kind / (name + ".kicad_sch")
    hardware = board.parent
    output = ROOT / "manufacturing" / kind
    gerbers, drills, pnp, assembly = (
        output / sub for sub in ("gerbers", "drill_files", "pick_and_place", "assembly")
    )
    for folder in (gerbers, drills, pnp, assembly):
        folder.mkdir(parents=True, exist_ok=True)

    # Both checks must pass before any manufacturing output is refreshed.
    run(cli, "sch", "erc", "--severity-all", "--exit-code-violations",
        "--output", hardware / "erc-report.txt", schematic)
    run(cli, "pcb", "drc", "--severity-all", "--schematic-parity",
        "--refill-zones", "--save-board", "--format", "json",
        "--exit-code-violations", "--output", hardware / "routed-drc.json", board)
    drc = json.loads((hardware / "routed-drc.json").read_text())
    if any(drc.get(key) for key in ("violations", "unconnected_items", "schematic_parity")):
        raise RuntimeError(f"{kind} DRC report contains findings")

    write_bom(kind, components, parts, tag=kind == "tag")
    run(cli, "pcb", "export", "gerbers", "--layers", FAB_LAYERS,
        "--check-zones", "--output", gerbers, board)
    run(cli, "pcb", "export", "drill", "--format", "excellon",
        "--excellon-units", "mm", "--generate-report",
        "--report-path", drills / (name + "-drill-report.txt"),
        "--output", drills, board)
    for side in ("front", "back"):
        run(cli, "pcb", "export", "pos", "--side", side,
            "--format", "csv", "--units", "mm", "--exclude-dnp",
            "--output", pnp / (name + f"-{side}-pos.csv"), board)
    drawing_scale = "3" if kind == "tag" else "4"
    run(cli, "pcb", "export", "pdf", "--mode-single", "--black-and-white",
        "--scale", drawing_scale,
        "--layers", "F.Fab,Edge.Cuts",
        "--output", assembly / (name + "-front-assembly.pdf"), board)
    run(cli, "pcb", "export", "pdf", "--mode-single", "--black-and-white",
        "--scale", drawing_scale,
        "--mirror", "--layers", "B.Fab,Edge.Cuts",
        "--output", assembly / (name + "-back-assembly.pdf"), board)
    run(cli, "sch", "export", "pdf", "--black-and-white",
        "--output", assembly / (name + "-schematic.pdf"), schematic)

    notes = output / "fabrication-notes.md"
    specification = ROOT / "docs/manufacturing-specification.md"
    shutil.copy2(specification, notes)

    # A compact archive is convenient for a prototype fabricator.  The
    # manifest outside it ties the exported set to the editable source.
    archive = output / (name + "-prototype-fab.zip")
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        zip_file.write(notes, notes.name)
        for folder in (gerbers, drills):
            for file in sorted(folder.iterdir()):
                if file.is_file():
                    zip_file.write(file, file.relative_to(output))
    # Hash the complete editable project, including every hierarchical sheet,
    # project-local symbol and land pattern, rule settings and library tables.
    paths = [p for p in hardware.rglob("*") if p.is_file() and
             (p.suffix in (".kicad_pcb", ".kicad_sch", ".kicad_pro", ".kicad_sym", ".kicad_mod")
              or p.name in ("sym-lib-table", "fp-lib-table", "erc-report.txt", "routed-drc.json"))]
    paths += [ROOT / "hardware/board-interface.json", specification]
    paths += [p for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"]
    manifest = {
        "project": name,
        "revision": REVISION,
        "exported_utc": datetime.now(timezone.utc).isoformat(),
        "status": "prototype fabrication package; physical validation pending",
        "files_sha256": {
            str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Exported {kind}: {archive} ({len(manifest['files_sha256'])} hashed files)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli-command", default="kicad-cli")
    parser.add_argument("--project", choices=("both", "tag", "charging-adapter"),
                        default="both")
    args = parser.parse_args()
    cli = shlex.split(args.cli_command)
    if args.project in ("both", "tag"):
        project(cli, "tag", "smart-safety-tag", TAG, TAG_PARTS)
    if args.project in ("both", "charging-adapter"):
        project(cli, "charging-adapter", "charging-adapter", ADAPTER, ADAPTER_PARTS)
