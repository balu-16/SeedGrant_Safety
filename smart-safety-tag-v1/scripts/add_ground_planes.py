#!/usr/bin/env python3
"""Add two-layer GND pours to the routed tag board.

KiCad's module footprint supplies the all-layer antenna copper keepout.  The
fill is done by KiCad DRC with --refill-zones --save-board, then rechecked.
"""

from pathlib import Path
import pcbnew


BOARD_FILE = Path(__file__).resolve().parents[1] / "hardware" / "tag" / "smart-safety-tag.kicad_pcb"


def pt(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def add_plane(board, layer):
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(board.FindNet("GND"))
    zone.SetLocalClearance(pcbnew.FromMM(0.15))
    zone.SetMinThickness(pcbnew.FromMM(0.2))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline = zone.Outline()
    index = outline.NewOutline()
    for x, y in ((100.3, 100.3), (159.7, 100.3), (159.7, 141.7), (100.3, 141.7)):
        outline.Append(pt(x, y), index)
    board.Add(zone)


def main():
    board = pcbnew.LoadBoard(str(BOARD_FILE))
    if list(board.Zones()):
        raise ValueError("Ground planes already present; avoid duplicate zones")
    add_plane(board, pcbnew.F_Cu)
    add_plane(board, pcbnew.B_Cu)
    pcbnew.SaveBoard(str(BOARD_FILE), board)
    print("Added F.Cu and B.Cu GND zones; refill in KiCad before DRC")


if __name__ == "__main__":
    main()
