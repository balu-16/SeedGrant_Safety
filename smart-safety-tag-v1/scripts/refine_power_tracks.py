#!/usr/bin/env python3
"""Widen routed supply traces where the actual pad/track clearances permit it.

Run with KiCad's Python and supply its CLI command. All-severity DRC, zone
connectivity and schematic parity must pass before and after refinement.
Existing widths are the lower bound; genuine findings are never excluded.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import shlex
import subprocess
import tempfile

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
TARGET_MM = {
    "3V3": 0.6, "SYS": 0.6, "BAT": 0.6,
    "CHG_RAW": 0.5, "CHG_IN": 0.5,
    "MOTOR_3V0": 0.5, "MOTOR_LOW": 0.5,
    "SW_L1": 0.6, "SW_L2": 0.6,
    "USB_5V": 0.6, "PROTECTED_5V": 0.6,
}
BOARDS = {"tag": ROOT / "hardware/tag/smart-safety-tag.kicad_pcb",
          "charging-adapter": ROOT / "hardware/charging-adapter/charging-adapter.kicad_pcb"}


def drc(cli, board_path, report):
    subprocess.run([*cli, "pcb", "drc", "--severity-all", "--schematic-parity",
                    "--refill-zones", "--save-board", "--format", "json",
                    "--output", str(report), str(board_path)], check=True, cwd=ROOT,
                   stdout=subprocess.DEVNULL)
    return json.loads(report.read_text())


def findings(report):
    return report["violations"] + report["unconnected_items"] + report["schematic_parity"]


def refine(cli, name, report):
    path = BOARDS[name]
    baseline = drc(cli, path, report)
    if findings(baseline):
        raise ValueError(f"{name}: resolve all DRC/connectivity/parity findings first")
    original = path.read_bytes()
    board = pcbnew.LoadBoard(str(path))
    widths = {}
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA) or item.GetNetname() not in TARGET_MM:
            continue
        widths[item.m_Uuid.AsString()] = item.GetWidth()
        item.SetWidth(max(item.GetWidth(), pcbnew.FromMM(TARGET_MM[item.GetNetname()])))
    pcbnew.SaveBoard(str(path), board)

    try:
        for attempt in range(10):
            check = drc(cli, path, report)
            remaining = findings(check)
            print(f"{name}: width check {attempt + 1}, {len(remaining)} findings", flush=True)
            if not remaining:
                break
            board = pcbnew.LoadBoard(str(path))
            tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()
                      if not isinstance(t, pcbnew.PCB_VIA) and t.m_Uuid.AsString() in widths}
            offending = {item["uuid"] for finding in remaining for item in finding.get("items", [])
                         if item["uuid"] in tracks and tracks[item["uuid"]].GetWidth() > widths[item["uuid"]]}
            if not offending:
                # A wider route can isolate a zone without naming that track.
                # Reduce the remaining widened items and recheck connectivity.
                offending = {uuid for uuid, t in tracks.items() if t.GetWidth() > widths[uuid]}
            if not offending:
                raise ValueError(f"{name}: width changes could not resolve {len(remaining)} findings")
            for uuid in offending:
                t = tracks[uuid]
                t.SetWidth(max(widths[uuid], t.GetWidth() - pcbnew.FromMM(0.1)))
            pcbnew.SaveBoard(str(path), board)
        else:
            raise ValueError(f"{name}: refinement did not converge")
    except BaseException:
        path.write_bytes(original)
        raise

    board = pcbnew.LoadBoard(str(path))
    stats = defaultdict(lambda: defaultdict(lambda: {"segments": 0, "length_mm": 0.0}))
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() not in TARGET_MM:
            continue
        width = f"{pcbnew.ToMM(t.GetWidth()):.3f}"
        group = stats[t.GetNetname()][width]
        group["segments"] += 1
        group["length_mm"] += pcbnew.ToMM(t.GetLength())
    return {net: {width: {**group, "length_mm": round(group["length_mm"], 3)}
                   for width, group in sorted(widths.items())} for net, widths in sorted(stats.items())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli-command", default="kicad-cli")
    parser.add_argument("--project", choices=("both", *BOARDS), default="both")
    args = parser.parse_args()
    output = ROOT / "docs/power-routing.json"
    record = json.loads(output.read_text()) if output.exists() else {}
    with tempfile.TemporaryDirectory(prefix="safety-tag-width-") as folder:
        for name in BOARDS:
            if args.project in ("both", name):
                record[name] = refine(shlex.split(args.cli_command), name, Path(folder) / "drc.json")
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(f"Verified power-route widths recorded in {output.name}")


if __name__ == "__main__":
    main()
