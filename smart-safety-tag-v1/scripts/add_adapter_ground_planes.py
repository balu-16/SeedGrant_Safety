#!/usr/bin/env python3
"""Pour both adapter PCB layers to ground before final DRC."""

from pathlib import Path
import pcbnew


FILE = Path(__file__).resolve().parents[1] / "hardware" / "charging-adapter" / "charging-adapter.kicad_pcb"


def pt(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def main():
    board = pcbnew.LoadBoard(str(FILE))
    if list(board.Zones()):
        raise ValueError("Fixture already has copper zones")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(board.FindNet("GND"))
        zone.SetLocalClearance(pcbnew.FromMM(0.15))
        zone.SetMinThickness(pcbnew.FromMM(0.2))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        poly = zone.Outline()
        index = poly.NewOutline()
        for xy in ((100.3, 100.3), (131.7, 100.3),
                   (131.7, 121.7), (100.3, 121.7)):
            poly.Append(pt(*xy), index)
        board.Add(zone)
    pcbnew.SaveBoard(str(FILE), board)
    print("Added fixture F.Cu and B.Cu GND zones")


if __name__ == "__main__":
    main()
