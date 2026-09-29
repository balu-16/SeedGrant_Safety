#!/usr/bin/env python3
"""Add the final local decoupling capacitors without replacing existing routes.

Run with KiCad's Python after exporting the current tag schematic as kicadxml.
Refuse a partial previous addition, and check the existing IC pad coordinates.
Always follow this operation with zone refill and a full DRC/parity check.
"""

import pcbnew

from circuit_data import COMPONENTS
from finish_tag_routing import add_track, add_via, pt
from place_tag_board import FIXED, ROTATED, FOOTPRINTS, OUTPUT, parse_netlist


LOCAL_REFS = {f"C{index}" for index in range(20, 28)}


def main():
    components, net_nodes = parse_netlist()
    board = pcbnew.LoadBoard(str(OUTPUT))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    existing = LOCAL_REFS & footprints.keys()
    if existing == LOCAL_REFS:
        print("All eight local capacitors already present; no changes")
        return
    if existing:
        raise ValueError(f"Partial local-capacitor addition: {sorted(existing)}")

    for ref, number, position in (
        ("U1", "3", (123, 104.3)), ("U2", "5", (105.45, 131.41)),
        ("U3", "1", (110.8625, 129.05)), ("U3", "5", (113.1375, 129.05)),
        ("U4", "9", (115.7625, 122.75)), ("U5", "1", (128.9, 133.2)),
        ("U9", "5", (146.1375, 112.05)),
    ):
        pad = next(p for p in footprints[ref].Pads() if p.GetNumber() == number)
        if (pad.GetPosition() - pt(*position)).EuclideanNorm() > pcbnew.FromMM(0.002):
            raise ValueError(f"{ref}.{number} moved; inspect the proposed local route")

    for component in COMPONENTS:
        ref = component.reference
        if ref not in LOCAL_REFS:
            continue
        xml = components[ref]
        nickname, name = xml.findtext("footprint").split(":", 1)
        if nickname != "Safety":
            raise ValueError(f"Unexpected capacitor library {nickname}")
        fp = pcbnew.FootprintLoad(str(FOOTPRINTS), name)
        if fp is None:
            raise ValueError(f"Missing local footprint {name}")
        board.Add(fp)
        fp.SetFPIDAsString(f"Safety:{name}")
        fp.SetReference(ref)
        fp.SetValue(component.value)
        fp.SetField("MPN", component.mpn)
        fp.SetField("Datasheet", xml.findtext("datasheet", ""))
        fp.SetPath(pcbnew.KIID_PATH(xml.find("sheetpath").attrib["tstamps"] + xml.findtext("tstamps")))
        fp.SetSheetfile(xml.find("property[@name='Sheetfile']").attrib["value"])
        fp.SetSheetname(xml.find("property[@name='Sheetname']").attrib["value"])
        fp.SetPosition(pt(*FIXED[ref]))
        fp.SetOrientationDegrees(ROTATED.get(ref, 0))
        for pad in fp.Pads():
            net = net_nodes[(ref, pad.GetNumber())]
            pad.SetNet(board.FindNet(net))
        fp.Value().SetVisible(False)

    routes = (
        ("3V3", 0.4, [(123, 104.3), (121.175, 104.3)]),
        ("3V3", 0.4, [(117.95, 104.3), (117.95, 102.6), (120, 102.6), (121.175, 103.775), (121.175, 104.3)]),
        ("GND", 0.3, [(119.625, 104.3), (119.625, 105.4)]),
        ("GND", 0.4, [(116.05, 104.3), (116.05, 105.3)]),
        ("MIC_3V0", 0.2, [(104.075, 129.5), (104.7, 129.5), (105.45, 130.25), (105.45, 131.41)]),
        ("GND", 0.3, [(102.525, 129.5), (101.5, 129.5)]),
        ("3V3", 0.2, [(115.7625, 122.75), (116.6, 122.75), (117.175, 123.325), (117.175, 124)]),
        ("GND", 0.3, [(118.725, 124), (118.725, 124.9)]),
        ("SYS", 0.25, [(128.65, 131.65), (128.9, 131.9), (128.9, 133.2)]),
        ("GND", 0.3, [(126.75, 131.65), (126.55, 132.65)]),
        ("MOTOR_3V0", 0.3, [(146.1375, 112.05), (148.125, 112.05), (148.25, 112.175)]),
        ("GND", 0.3, [(148.25, 110.625), (149, 110.625)]),
        ("MIC_3V0", 0.2, [(113.1375, 129.05), (113.175, 129.05), (113.175, 127.3)]),
        ("GND", 0.3, [(111.625, 127.3), (111.625, 126.35)]),
        ("3V3", 0.3, [(110.8625, 129.05), (109.025, 129.05)]),
        ("GND", 0.3, [(107.475, 129.05), (107.475, 128.2)]),
    )
    for net, width, vertices in routes:
        for start, end in zip(vertices, vertices[1:]):
            add_track(board, net, start, end, width)
    for position in ((119.625, 105.4), (116.05, 105.3), (101.5, 129.5),
                     (118.725, 124.9), (126.55, 132.65), (149, 110.625),
                     (111.625, 126.35), (107.475, 128.2)):
        add_via(board, "GND", position)
    pcbnew.SaveBoard(str(OUTPUT), board)
    print("Added eight local capacitors, short supply connections and ground vias")


if __name__ == "__main__":
    main()
