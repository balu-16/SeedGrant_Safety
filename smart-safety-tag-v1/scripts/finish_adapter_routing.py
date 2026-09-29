#!/usr/bin/env python3
"""Complete the two short pogo-pin fanouts after the adapter routing session."""

from pathlib import Path
import pcbnew


BOARD_FILE = Path(__file__).resolve().parents[1] / "hardware" / "charging-adapter" / "charging-adapter.kicad_pcb"


def pt(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def track(board, net, start, end, layer=pcbnew.F_Cu, width=0.2):
    item = pcbnew.PCB_TRACK(board)
    item.SetStart(pt(*start))
    item.SetEnd(pt(*end))
    item.SetLayer(layer)
    item.SetWidth(pcbnew.FromMM(width))
    item.SetNet(board.FindNet(net))
    board.Add(item)


def via(board, net, at):
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(pt(*at))
    item.SetWidth(pcbnew.FromMM(0.6))
    item.SetDrill(pcbnew.FromMM(0.3))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(board.FindNet(net))
    board.Add(item)


def main():
    board = pcbnew.LoadBoard(str(BOARD_FILE))
    by_ref = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, at in (("P1", (117, 117)), ("P2", (124.5, 117))):
        pad = next(p for p in by_ref[ref].Pads() if p.GetNumber() == "1")
        if pad.GetPosition() != pt(*at):
            raise ValueError(f"{ref} moved; inspect routing before updating")
    track(board, "GND", (124.5, 117), (124.5, 115))
    track(board, "PROTECTED_5V", (117, 117), (117, 119))
    via(board, "PROTECTED_5V", (117, 119))
    track(board, "PROTECTED_5V", (117, 119), (117.489, 113.211), pcbnew.B_Cu)
    via(board, "PROTECTED_5V", (117.489, 113.211))
    pcbnew.SaveBoard(str(BOARD_FILE), board)
    print("Completed both fixture pogo-pin fanouts")


if __name__ == "__main__":
    main()
