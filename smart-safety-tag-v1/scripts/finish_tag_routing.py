#!/usr/bin/env python3
"""Close two short local connections left by the first routing session.

The chosen coordinates are checked against the footprint/pad locations so a
placement change cannot silently produce a wrong copper connection.
"""

from pathlib import Path
import pcbnew


BOARD_FILE = Path(__file__).resolve().parents[1] / "hardware" / "tag" / "smart-safety-tag.kicad_pcb"


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def pad(board, ref, number):
    fp = next(fp for fp in board.GetFootprints() if fp.GetReference() == ref)
    matches = [p for p in fp.Pads() if p.GetNumber() == number]
    if not matches:
        raise ValueError(f"Missing {ref} pad {number}")
    return matches


def add_track(board, net, start, end, width=0.2, layer=pcbnew.F_Cu):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pt(*start))
    track.SetEnd(pt(*end))
    track.SetWidth(pcbnew.FromMM(width))
    track.SetLayer(layer)
    track.SetNet(board.FindNet(net))
    board.Add(track)


def add_via(board, net, at):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pt(*at))
    via.SetWidth(pcbnew.FromMM(0.6))
    via.SetDrill(pcbnew.FromMM(0.3))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(board.FindNet(net))
    board.Add(via)


def main():
    board = pcbnew.LoadBoard(str(BOARD_FILE))
    sw = pad(board, "SW1", "1")[1]
    r23 = pad(board, "R23", "2")[0]
    if sw.GetPosition() != pt(107.05, 104.2) or r23.GetPosition() != pt(110.825, 108):
        raise ValueError("SOS placement changed; inspect the local route")
    add_track(board, "SOS_N", (107.05, 104.2), (108, 104.2))
    add_via(board, "SOS_N", (108, 104.2))
    add_track(board, "SOS_N", (108, 104.2), (110.825, 107.2), layer=pcbnew.B_Cu)
    add_via(board, "SOS_N", (110.825, 107.2))
    add_track(board, "SOS_N", (110.825, 107.2), (110.825, 108))

    mic_ground = pad(board, "U2", "2")[0]
    acoustic_ring = pad(board, "U2", "3")[0]
    if (mic_ground.GetPosition() != pt(105.45, 132.59)
            or acoustic_ring.GetPosition() != pt(106.55, 131.46)):
        raise ValueError("Microphone placement changed; inspect annular ground route")
    ring_route = [(105.45, 132.59), (105.9, 132.59),
                  (105.9, 131.46), (106.55, 131.46)]
    for start, end in zip(ring_route, ring_route[1:]):
        add_track(board, "GND", start, end, 0.16)
    pcbnew.SaveBoard(str(BOARD_FILE), board)
    print(f"Added SOS and microphone ground local routes to {BOARD_FILE}")


if __name__ == "__main__":
    main()
