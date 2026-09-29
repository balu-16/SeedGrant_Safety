#!/usr/bin/env python3
"""Create the placement-stage tag PCB from the exported schematic netlist.

Run with KiCad's bundled Python after exporting the schematic as kicadxml.
This deliberately leaves all nets unrouted; a placement board is not a
manufacturing release.  The pack and antenna geometry is documented in
hardware/tag/placement-notes.md.
"""

from __future__ import annotations

from math import hypot
from pathlib import Path
from xml.etree import ElementTree
import json
import sys

import pcbnew

from circuit_data import COMPONENTS


PROJECT = Path(__file__).resolve().parents[1] / "hardware" / "tag"
NETLIST = PROJECT / "smart-safety-tag.xml"
OUTPUT = PROJECT / "smart-safety-tag.kicad_pcb"
FOOTPRINTS = PROJECT / "footprints" / "Safety.pretty"
OUTLINE = (100.0, 100.0, 160.0, 142.0)
PACK = (110.5, 104.0, 148.0, 135.0)

# First-pass functional placement.  The module antenna projects over the top
# edge, with its populated pins and ground pad supported by the PCB.
FIXED = {
    "U1": (130, 106), "SW1": (105, 105), "D3": (154, 104),
    "M1": (154, 114), "U2": (106, 132), "U3": (112, 130),
    "U4": (115, 123), "J1": (108, 138), "J2": (152, 138),
    "U5": (130, 134), "U6": (137, 123), "Q1": (140, 135),
    "Q2": (140, 139.5), "D1": (148, 135), "D2": (146, 140),
    "RT1": (139, 128), "U7": (152, 128), "L1": (156.5, 128.3),
    "U8": (122, 136), "U9": (145, 113), "Q3": (145, 119),
    "D4": (145, 108),
    "TP1": (103, 111), "TP2": (103, 114), "TP3": (103, 117),
    "TP4": (103, 120), "TP5": (103, 123), "TP6": (103, 126),
    "C1": (119, 112), "C2": (119, 115), "R2": (119, 118),
    "C20": (120.4, 104.3), "C21": (117.0, 104.3),
    "C22": (103.3, 129.5), "C23": (117.95, 124),
    "C24": (127.7, 131.65), "C25": (148.25, 111.4),
    "C26": (112.4, 127.3), "C27": (108.25, 129.05),
    "R3": (119, 120), "R4": (119, 122),
    "C10": (125, 128.5), "C14": (151.5, 132.2),
    "C15": (146.5, 132.2), "C13": (149.5, 124.5),
}

ROTATED = {"L1": -90, "C13": 180, "C14": 180, "C15": 180,
           "C20": 180, "C21": 180, "C22": 180,
           "C24": 180, "C25": 90, "C26": 180, "C27": 180}

ANCHORS = {
    "C3": (144, 112), "R1": (141, 112),
    "C4": (116, 129), "C5": (116, 134), "C6": (116, 132),
    "R5": (116, 136), "R6": (120, 132),
    "C7": (111, 124), "C8": (116, 127),
    "C9": (135, 135), "C11": (125, 137),
    "R7": (134, 131), "R8": (137, 131),
    "R9": (140, 116), "R10": (141, 118),
    "C12": (134, 119),
    "R11": (130, 121), "R12": (130, 123),
    "R13": (130, 125), "R14": (130, 127),
    "R15": (141, 125), "R16": (142, 128),
    "R17": (135, 139),
    "R18": (144.5, 127), "R19": (144.5, 129.2),
    "R20": (144, 125), "R21": (144, 122),
    "C16": (119, 132), "R22": (119, 134),
    "R23": (110, 108), "C17": (113, 108),
    "R24": (149, 104), "R25": (148, 106), "R26": (146, 104),
    "C18": (140, 110), "C19": (141, 114),
    "R27": (141, 119), "R28": (141, 117),
}


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def box(fp: pcbnew.FOOTPRINT):
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    shape = fp.GetCourtyard(layer)
    if shape.OutlineCount():
        bb = shape.BBox()
    else:
        bb = fp.GetBoundingBox(False, False)
    return tuple(pcbnew.ToMM(v) for v in
                 (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()))


def intersects(first, second, gap: float = 0.15) -> bool:
    return not (first[2] + gap <= second[0] or second[2] + gap <= first[0]
                or first[3] + gap <= second[1] or second[3] + gap <= first[1])


def place(fp: pcbnew.FOOTPRINT, ref: str, x: float, y: float,
          placed: dict[str, pcbnew.FOOTPRINT], fixed=False) -> bool:
    fp.SetPosition(point(x, y))
    bb = box(fp)
    if ref != "U1":
        margin = 0.45
        if (bb[0] < OUTLINE[0] + margin or bb[1] < OUTLINE[1] + margin
                or bb[2] > OUTLINE[2] - margin or bb[3] > OUTLINE[3] - margin):
            if fixed:
                raise ValueError(f"{ref}: footprint courtyard leaves the board: {bb}")
            return False
    if fp.IsFlipped() and ref != "RT1" and intersects(bb, PACK, 0.4):
        if fixed:
            raise ValueError(f"{ref}: rear footprint enters cell envelope")
        return False
    for other_ref, other in placed.items():
        if other_ref == "U1":
            # The upstream module courtyard is T-shaped.  Its rectangular
            # bounding box includes empty space on both sides of the module.
            blocked = (107.255, 81.205, 152.745, 100.755), (122.05, 100.755, 137.95, 116.545)
            collision = any(intersects(bb, region) for region in blocked)
        else:
            collision = intersects(bb, box(other))
        if fp.IsFlipped() == other.IsFlipped() and collision:
            if fixed:
                raise ValueError(f"{ref} courtyard {bb} overlaps {other_ref} {box(other)}")
            return False
    placed[ref] = fp
    return True


def automatic_place(fp, ref, placed):
    target = ANCHORS.get(ref)
    if target is None:
        raise ValueError(f"No placement anchor for {ref}")
    candidates = []
    for xi in range(202, 318):  # 101..158.5, in 0.5 mm increments
        x = xi / 2
        for yi in range(202, 282):  # 101..140.5
            y = yi / 2
            distance = hypot(x - target[0], y - target[1])
            if distance <= 14:
                candidates.append((distance, x, y))
    for _, x, y in sorted(candidates):
        if place(fp, ref, x, y, placed):
            return
    raise ValueError(f"No open placement for {ref} near {target}")


def parse_netlist():
    tree = ElementTree.parse(NETLIST)
    components = {item.attrib["ref"]: item for item in tree.findall("./components/comp")}
    net_nodes = {}
    for net in tree.findall("./nets/net"):
        for node in net.findall("node"):
            key = (node.attrib["ref"], node.attrib["pin"])
            if key in net_nodes:
                raise ValueError(f"Duplicate schematic net assignment: {key}")
            net_nodes[key] = net.attrib["name"]
    references = {component.reference for component in COMPONENTS}
    if set(components) != references:
        raise ValueError(f"Schematic components differ from circuit_data: {set(components) ^ references}")
    for component in COMPONENTS:
        for number, net in component.nets.items():
            actual = net_nodes.get((component.reference, number))
            if actual != net:
                raise ValueError(f"{component.reference} pad {number}: source {net}, netlist {actual}")
    extra = set(net_nodes) - {(c.reference, n) for c in COMPONENTS for n in c.nets}
    if any(not net_nodes[key].startswith("unconnected-") for key in extra):
        raise ValueError("Schematic netlist has unexpected connected pads")
    return components, net_nodes


def add_outline(board):
    x1, y1, x2, y2 = OUTLINE
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(point(ax, ay))
        edge.SetEnd(point(bx, by))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(mm(0.05))
        board.Add(edge)


def add_pack_envelope(board):
    x1, y1, x2, y2 = PACK
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(point(ax, ay))
        edge.SetEnd(point(bx, by))
        edge.SetLayer(pcbnew.B_Fab)
        edge.SetWidth(mm(0.1))
        board.Add(edge)


def main():
    xml_components, net_nodes = parse_netlist()
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.0))
    add_outline(board)
    add_pack_envelope(board)
    nets = {}
    for name in net_nodes.values():
        if name not in nets:
            net = pcbnew.NETINFO_ITEM(board, name)
            board.Add(net)
            nets[name] = net

    footprints = {}
    for component in COMPONENTS:
        ref = component.reference
        xml = xml_components[ref]
        nickname, name = xml.findtext("footprint").split(":", 1)
        if nickname != "Safety":
            raise ValueError(f"Unexpected footprint library {nickname}")
        fp = pcbnew.FootprintLoad(str(FOOTPRINTS), name)
        if fp is None:
            raise ValueError(f"Missing footprint: {name}")
        fp.SetFPIDAsString(f"Safety:{name}")
        fp.SetReference(ref)
        fp.SetValue(xml.findtext("value"))
        sheet = xml.find("sheetpath")
        fp.SetPath(pcbnew.KIID_PATH(sheet.attrib["tstamps"] + xml.findtext("tstamps")))
        fp.SetSheetfile(xml.find("property[@name='Sheetfile']").attrib["value"])
        fp.SetSheetname(xml.find("property[@name='Sheetname']").attrib["value"])
        board.Add(fp)
        fp.SetField("MPN", component.mpn)
        fp.SetField("Datasheet", xml.findtext("datasheet", ""))
        fp.GetField("MPN").SetVisible(False)
        fp.GetField("MPN").SetLayer(pcbnew.F_Fab)
        if ref == "RT1":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            fp.GetField("MPN").SetLayer(pcbnew.B_Fab)
        if ref in ROTATED:
            fp.SetOrientationDegrees(ROTATED[ref])
        pad_numbers = {pad.GetNumber() for pad in fp.Pads()}
        if not set(component.nets) <= pad_numbers:
            raise ValueError(f"{ref}: symbol pads absent from footprint {set(component.nets) - pad_numbers}")
        for pad in fp.Pads():
            name = net_nodes.get((ref, pad.GetNumber()))
            if name:
                pad.SetNet(nets[name])
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        footprints[ref] = fp

    placed = {}
    for ref, (x, y) in FIXED.items():
        place(footprints[ref], ref, x, y, placed, fixed=True)
    for component in COMPONENTS:
        ref = component.reference
        if ref not in placed:
            automatic_place(footprints[ref], ref, placed)
    pcbnew.SaveBoard(str(OUTPUT), board)
    # SaveBoard initializes a default .kicad_pro for a new board.  Override
    # its generic 0.2 mm clearance with rules matching the 0.5 mm-pitch LGA
    # and the manufacturer's acoustic-port copper-to-hole geometry.
    project_file = PROJECT / "smart-safety-tag.kicad_pro"
    project = json.loads(project_file.read_text())
    rules = project["board"]["design_settings"]["rules"]
    rules.update(min_clearance=0.13, min_hole_clearance=0.15,
                 min_track_width=0.13)
    default_class = next(item for item in project["net_settings"]["classes"]
                         if item["name"] == "Default")
    default_class["clearance"] = 0.13
    project_file.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n")
    print(f"Placed {len(placed)} components, {len(nets)} nets on {OUTLINE[2]-OUTLINE[0]:.0f} x {OUTLINE[3]-OUTLINE[1]:.0f} mm board")
    print(f"Placement-stage PCB: {OUTPUT}")


if __name__ == "__main__":
    main()
