#!/usr/bin/env python3
"""Vendor fixed KiCad 10 land patterns and generate the Mill-Max pogo pad."""

from argparse import ArgumentParser
from pathlib import Path
from shutil import copy2

from adapter_data import COMPONENTS, PARTS


ROOT = Path(__file__).resolve().parents[1] / "hardware" / "charging-adapter"
OUT = ROOT / "footprints" / "Safety.pretty"
POGO_NAME = "PogoPin_MillMax_0900-1"


def pogo_footprint() -> str:
    # Mill-Max 0900-1 base Ø1.83 mm; 2.6 mm copper pad exceeds the catalog's
    # Ø2.21 mm minimum.  Reduced paste prevents a tall solder fillet.
    return f'''(footprint "{POGO_NAME}"
  (version 20241229) (generator "pcbnew") (layer "F.Cu")
  (descr "Mill-Max 0900-1-15-20-75-14-11-0 SMT spring pin; base diameter 1.83 mm")
  (property "Reference" "REF**" (at 0 -2.5 0) (layer "F.SilkS")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (property "Value" "{POGO_NAME}" (at 0 2.5 0) (layer "F.Fab")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (attr smd)
  (fp_circle (center 0 0) (end 0.915 0) (stroke (width 0.1) (type solid))
    (fill no) (layer "F.Fab"))
  (fp_circle (center 0 0) (end 1.7 0) (stroke (width 0.05) (type solid))
    (fill no) (layer "F.CrtYd"))
  (pad "1" smd circle (at 0 0) (size 2.6 2.6) (layers "F.Cu" "F.Mask"))
  (pad "" smd circle (at 0 0) (size 1.8 1.8) (layers "F.Paste"))
  (embedded_fonts no)
)\n'''


def main():
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path, required=True,
                        help="KiCad 10 kicad-footprints checkout")
    source = parser.parse_args().source
    if not source.is_dir():
        parser.error("--source must be a directory")
    OUT.mkdir(parents=True, exist_ok=True)
    names = {c.footprint or PARTS[c.part].footprint for c in COMPONENTS}
    for name in sorted(names - {POGO_NAME}):
        matches = list(source.glob(f"*.pretty/{name}.kicad_mod"))
        if len(matches) != 1:
            raise ValueError(f"Expected one KiCad 10 footprint for {name}, found {matches}")
        copy2(matches[0], OUT / f"{name}.kicad_mod")
    (OUT / f"{POGO_NAME}.kicad_mod").write_text(pogo_footprint())
    print(f"Vendored {len(names)} fixture footprints")


if __name__ == "__main__":
    main()
