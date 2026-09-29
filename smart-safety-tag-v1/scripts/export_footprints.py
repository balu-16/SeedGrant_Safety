#!/usr/bin/env python3
"""Vendor exact KiCad 10 standard footprints needed by the tag project."""

from argparse import ArgumentParser
from pathlib import Path
from shutil import copy2
from sexpdata import Symbol, dumps, loads

from circuit_data import COMPONENTS
from parts import PARTS


OUT = Path(__file__).resolve().parents[1] / "hardware" / "tag" / "footprints" / "Safety.pretty"


def adapt_overhanging_module(path: Path) -> None:
    """Omit outline silk that would be clipped by the antenna overhang."""
    footprint = loads(path.read_text())
    graphic_types = {"fp_line", "fp_arc", "fp_circle", "fp_poly", "fp_rect"}
    kept = [footprint[0]]
    for item in footprint[1:]:
        if (isinstance(item, list) and item and str(item[0]) in graphic_types
                and any(isinstance(child, list) and child and child[0] == Symbol("layer")
                        and len(child) > 1 and child[1] == "F.SilkS" for child in item)):
            continue
        kept.append(item)
    path.write_text(dumps(kept) + "\n")


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path, required=True, help="KiCad 10 kicad-footprints checkout")
    args = parser.parse_args()
    if not args.source.is_dir():
        parser.error("--source must be a directory")
    requested = {
        component.footprint or ("ESP32-S2-MINI-1" if component.part == "MCU" else PARTS[component.part].footprint)
        for component in COMPONENTS
    }
    OUT.mkdir(parents=True, exist_ok=True)
    copied = []
    pending = []
    for name in sorted(requested):
        matches = list(args.source.glob(f"*.pretty/{name}.kicad_mod"))
        if len(matches) == 1:
            copy2(matches[0], OUT / matches[0].name)
            if name == "ESP32-S2-MINI-1":
                adapt_overhanging_module(OUT / matches[0].name)
            copied.append(name)
        elif len(matches) == 0:
            pending.append(name)
        else:
            raise RuntimeError(f"Ambiguous footprint {name}: {matches}")
    print(f"Vendored {len(copied)} KiCad 10 footprints into {OUT}")
    if pending:
        print("Require manufacturer-land-pattern implementation:")
        for name in pending:
            print(f"  {name}")


if __name__ == "__main__":
    main()
