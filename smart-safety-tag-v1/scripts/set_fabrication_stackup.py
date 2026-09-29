#!/usr/bin/env python3
"""Store the specified two-layer, 1 mm ENIG stackup in both native PCB files.

No geometry or connectivity is changed. Re-run DRC and manufacturing exports
after using this script. The dielectric value is the nominal 1 mm total less
two 35 um copper layers and two 10 um solder-mask layers.
"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BOARDS = (ROOT / "hardware/tag/smart-safety-tag.kicad_pcb",
          ROOT / "hardware/charging-adapter/charging-adapter.kicad_pcb")
STACKUP = '''\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "core") (thickness 0.91) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
'''


def balanced_end(text, start):
    depth = 0
    quoted = escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("Unbalanced PCB expression")


def main():
    for path in BOARDS:
        text = path.read_text()
        existing = text.find("(stackup")
        if existing >= 0:
            end = balanced_end(text, existing)
            text = text[:existing] + text[end:]
        text, count = re.subn(r"(\(general\s*\(thickness\s+)[0-9.]+", r"\g<1>1.0", text, count=1)
        if count != 1 or text.count("\t(setup\n") != 1:
            raise ValueError(f"Unexpected board format: {path}")
        text = text.replace("\t(setup\n", "\t(setup\n" + STACKUP, 1)
        path.write_text(text)
        print(f"Set 1 mm, 35 um copper, ENIG stackup: {path.name}")


if __name__ == "__main__":
    main()
