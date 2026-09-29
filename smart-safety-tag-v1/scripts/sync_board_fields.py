#!/usr/bin/env python3
"""Update purchasing fields on already routed PCBs without touching geometry.

Run with KiCad's bundled Python.  Refuse missing/extra footprints so a stale
board cannot silently receive a current BOM.
"""

from pathlib import Path
import re
import sys

import pcbnew

from adapter_data import COMPONENTS as ADAPTER, PARTS as ADAPTER_PARTS
from circuit_data import COMPONENTS as TAG
from parts import PARTS as TAG_PARTS
from set_fabrication_stackup import balanced_end
from release_data import RELEASE_DATE, REVISION


ROOT = Path(__file__).resolve().parents[1] / "hardware"


def sync(kind: str, name: str, components, parts):
    path = ROOT / kind / (name + ".kicad_pcb")
    board = pcbnew.LoadBoard(str(path))
    title = board.GetTitleBlock()
    title.SetTitle("Smart Safety Tag V1" if kind == "tag" else "Smart Safety Tag Charging Adapter")
    title.SetRevision(REVISION)
    title.SetDate(RELEASE_DATE)
    title.SetComment(0, "Prototype; physical validation pending")
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    expected = {component.reference: component for component in components}
    if footprints.keys() != expected.keys():
        raise ValueError(f"{kind} footprint mismatch: {footprints.keys() ^ expected.keys()}")
    for ref, component in expected.items():
        fp = footprints[ref]
        fp.SetValue(component.value)
        fp.SetField("MPN", component.mpn)
        fp.SetField("Datasheet", "" if component.part == "MCU" else parts[component.part].datasheet)
        field = fp.GetField("MPN")
        field.SetVisible(False)
        field.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
        fp.Reference().SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
        fp.Reference().SetVisible(True)
        fp.Reference().SetMirrored(fp.IsFlipped())
        fp.Reference().SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
        # The tag has 75 populated positions in 60 x 42 mm.  Smaller Fab
        # references remain legible at the 3:1 assembly drawing scale and
        # reduce collisions among the closely spaced passive parts.
        text_size = 0.55 if kind == "tag" else 0.7
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(text_size), pcbnew.FromMM(text_size)))
        fp.Reference().SetTextThickness(pcbnew.FromMM(0.10 if kind == "tag" else 0.12))
        if kind == "tag" and ref == "C15":
            center = fp.GetPosition()
            fp.Reference().SetPosition(pcbnew.VECTOR2I(
                center.x - pcbnew.FromMM(0.25),
                center.y + pcbnew.FromMM(1.85),
            ))
        attributes = fp.GetAttributes()
        if component.part in ("TP", "CHGCONN"):
            attributes |= pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        if component.part == "MOTOR":
            attributes |= pcbnew.FP_EXCLUDE_FROM_POS_FILES
        fp.SetAttributes(attributes)
    pcbnew.SaveBoard(str(path), board)
    # PCB_TEXT visibility is not serialized for arbitrary footprint graphics.
    # Remove the redundant Fab placeholder as a balanced expression instead
    # of deleting C++ objects while SWIG holds references to the footprint.
    sources = [path, *sorted((path.parent / "footprints/Safety.pretty").glob("*.kicad_mod"))]
    for source in sources:
        text = source.read_text()
        matches = list(re.finditer(r'\(fp_text\s+user\s+"\$\{REFERENCE\}"', text))
        for match in reversed(matches):
            end = balanced_end(text, match.start())
            text = text[:match.start()] + text[end:]
        if matches:
            source.write_text(text)
    print(f"Updated {len(footprints)} {kind} PCB footprints")


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["tag"], ["charging-adapter"]):
        raise SystemExit("usage: sync_board_fields.py [tag|charging-adapter]")
    if not sys.argv[1:] or sys.argv[1] == "tag":
        sync("tag", "smart-safety-tag", TAG, TAG_PARTS)
    if not sys.argv[1:] or sys.argv[1] == "charging-adapter":
        sync("charging-adapter", "charging-adapter", ADAPTER, ADAPTER_PARTS)
