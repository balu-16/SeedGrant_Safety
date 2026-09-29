#!/usr/bin/env python3
"""Place the protected charging fixture and enforce schematic/pad parity."""

import json
from pathlib import Path
from xml.etree import ElementTree
import pcbnew

from adapter_data import COMPONENTS


ROOT = Path(__file__).resolve().parents[1] / "hardware" / "charging-adapter"
XML = ROOT / "charging-adapter.xml"
OUTPUT = ROOT / "charging-adapter.kicad_pcb"
LIB = ROOT / "footprints" / "Safety.pretty"
RECT = (100, 100, 132, 122)
POSITION = {
    "J1": (108, 103.4), "R1": (104, 111), "R2": (108, 111),
    "D1": (120, 104.5), "C1": (116, 105), "U1": (120, 109),
    "C2": (116, 109), "R3": (125, 104.5), "R4": (125, 107),
    "R5": (125, 110), "C3": (115, 112.5), "D2": (111, 117),
    "P1": (117, 117), "P2": (124.5, 117),
    "TP1": (129, 111), "TP2": (129, 115),
}


def pt(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def bbox(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return [pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom())]


def overlap(a, b, gap=0.15):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0]
                or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def main():
    tree = ElementTree.parse(XML)
    xml_parts = {e.attrib["ref"]: e for e in tree.findall("./components/comp")}
    nets_by_pad = {(n.attrib["ref"], n.attrib["pin"]): net.attrib["name"]
                   for net in tree.findall("./nets/net") for n in net.findall("node")}
    if set(xml_parts) != {c.reference for c in COMPONENTS}:
        raise ValueError("Adapter schematic does not match adapter_data")
    for c in COMPONENTS:
        for pin, net in c.nets.items():
            if nets_by_pad.get((c.reference, pin)) != net:
                raise ValueError(f"{c.reference} pad {pin}: netlist differs")
    extras = set(nets_by_pad) - {(c.reference, p) for c in COMPONENTS for p in c.nets}
    if any(not nets_by_pad[key].startswith("unconnected-") for key in extras):
        raise ValueError("Unexpected connected schematic pads")
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.0))
    corners = [(RECT[0], RECT[1]), (RECT[2], RECT[1]),
               (RECT[2], RECT[3]), (RECT[0], RECT[3])]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(pt(x1, y1))
        edge.SetEnd(pt(x2, y2))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(0.05))
        board.Add(edge)
    nets = {}
    for name in nets_by_pad.values():
        if name not in nets:
            info = pcbnew.NETINFO_ITEM(board, name)
            board.Add(info)
            nets[name] = info
    placed = {}
    for c in COMPONENTS:
        ref = c.reference
        e = xml_parts[ref]
        nickname, name = e.findtext("footprint").split(":")
        if nickname != "Safety":
            raise ValueError(f"Unexpected library for {ref}")
        fp = pcbnew.FootprintLoad(str(LIB), name)
        if fp is None:
            raise ValueError(f"Missing adapter footprint {name}")
        board.Add(fp)
        fp.SetFPIDAsString(f"Safety:{name}")
        fp.SetReference(ref)
        fp.SetValue(e.findtext("value"))
        fp.SetPath(pcbnew.KIID_PATH(e.find("sheetpath").attrib["tstamps"] + e.findtext("tstamps")))
        fp.SetSheetfile("charging-adapter.kicad_sch")
        fp.SetSheetname("")
        fp.SetField("MPN", c.mpn)
        fp.SetField("Datasheet", e.findtext("datasheet", ""))
        fp.GetField("MPN").SetVisible(False)
        fp.GetField("MPN").SetLayer(pcbnew.F_Fab)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        if ref == "J1":
            # The KiCad footprint's PCB-edge marker is at local y=+3.4.
            # Rotating the connector puts its mouth at the top board edge.
            fp.SetOrientationDegrees(180)
        x, y = POSITION[ref]
        fp.SetPosition(pt(x, y))
        bb = bbox(fp)
        if ref != "J1" and (bb[0] < RECT[0] + 0.4 or bb[1] < RECT[1] + 0.4
                            or bb[2] > RECT[2] - 0.4 or bb[3] > RECT[3] - 0.4):
            raise ValueError(f"{ref} courtyard outside board: {bb}")
        for other_ref, other in placed.items():
            if overlap(bb, bbox(other)):
                raise ValueError(f"{ref} overlaps {other_ref}")
        placed[ref] = fp
        if not set(c.nets) <= {p.GetNumber() for p in fp.Pads()}:
            raise ValueError(f"{ref} symbol/land-pattern pins differ")
        for pad in fp.Pads():
            net = nets_by_pad.get((ref, pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
    pcbnew.SaveBoard(str(OUTPUT), board)
    project = ROOT / "charging-adapter.kicad_pro"
    data = json.loads(project.read_text())
    rules = data["board"]["design_settings"]["rules"]
    rules.update(min_clearance=0.13, min_hole_clearance=0.15,
                 min_track_width=0.13)
    data["net_settings"]["classes"][0]["clearance"] = 0.13
    project.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"Placed {len(placed)} adapter components on 32 x 22 mm board")


if __name__ == "__main__":
    main()
