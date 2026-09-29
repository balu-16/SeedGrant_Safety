#!/usr/bin/env python3
"""Create manufacturer-land-pattern footprints not in KiCad 10.0.6.

The microphone and regulator geometry follows the linked manufacturer land
patterns.  The two-contact charging interface and wired motor land pattern
are mechanical prototypes and require mating-fixture/enclosure sign-off.
"""

from math import cos, radians, sin
from pathlib import Path


OUT = Path(__file__).resolve().parents[1] / "hardware" / "tag" / "footprints" / "Safety.pretty"


def fmt(number: float) -> str:
    return f"{number:.4f}".rstrip("0").rstrip(".") if number else "0"


def common(name: str, description: str, body: str, back: bool = False) -> str:
    side = "B" if back else "F"
    return f'''(footprint "{name}"
  (version 20241229)
  (generator "pcbnew")
  (layer "{side}.Cu")
  (descr "{description}")
  (property "Reference" "REF**" (at 0 -3 0) (layer "{side}.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (property "Value" "{name}" (at 0 3 0) (layer "{side}.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (attr smd)
{body}
  (embedded_fonts no)
)\n'''


def rect(number: str, x: float, y: float, sx: float, sy: float, layer: str = "F", paste: bool = True, roundrect: bool = True) -> str:
    shape = "roundrect" if roundrect else "rect"
    layers = f'"{layer}.Cu" ' + (f'"{layer}.Paste" ' if paste else "") + f'"{layer}.Mask"'
    radius = " (roundrect_rratio 0.15)" if roundrect else ""
    return f'  (pad "{number}" smd {shape} (at {fmt(x)} {fmt(y)}) (size {fmt(sx)} {fmt(sy)}) (layers {layers}){radius})'


def line(x1, y1, x2, y2, layer="F.Fab", width=0.1):
    return f'  (fp_line (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)}) (stroke (width {fmt(width)}) (type solid)) (layer "{layer}"))'


def outline(half_x: float, half_y: float, layer: str = "F.Fab") -> list[str]:
    return [
        line(-half_x, -half_y, half_x, -half_y, layer),
        line(half_x, -half_y, half_x, half_y, layer),
        line(half_x, half_y, -half_x, half_y, layer),
        line(-half_x, half_y, -half_x, -half_y, layer),
    ]


def inductor() -> str:
    # Coilcraft XFL4015, Doc 769-2, p2: 0.98 x 3.4 mm pads, 2.37 mm pitch.
    body = [*outline(2, 2), *outline(2.25, 2.25, "F.CrtYd")]
    body += [rect("1", -1.185, 0, 0.98, 3.4), rect("2", 1.185, 0, 0.98, 3.4)]
    body.append(line(-2.1, -2.25, -1.5, -2.25, "F.SilkS", 0.12))
    return common("L_Coilcraft_XFL4015", "Coilcraft XFL4015; https://www.coilcraft.com/getmedia/84927b8b-f089-421b-a7f4-a0fa23afe908/xfl4015.pdf", "\n".join(body))


def regulator() -> str:
    # TI DLA0010A (2 x 3 mm VSON-HR), example board layout in TPS63802 p36.
    body = [*outline(1, 1.5), *outline(1.55, 1.9, "F.CrtYd")]
    for index, y in enumerate((-1.0, -0.5, 0, 0.5, 1.0), start=1):
        body.append(rect(str(index), -0.9, y, 0.6, 0.25))
    for index, y in zip((10, 9, 8, 7, 6), (-1.0, -0.5, 0, 0.5, 1.0)):
        if index == 8:
            body.append(rect("8", 0.55, y, 1.3, 0.25, paste=False))
            body.append('  (pad "" smd rect (at 0.1 0) (size 0.55 0.175) (layers "F.Paste"))')
            body.append('  (pad "" smd rect (at 0.85 0) (size 0.55 0.175) (layers "F.Paste"))')
        else:
            body.append(rect(str(index), 0.75, y, 0.9, 0.25))
    body.append(line(-1.55, -1.9, -1.1, -1.9, "F.SilkS", 0.12))
    return common("Texas_DLA0010A_VSON-10_2x3mm", "TI DLA0010A manufacturer land pattern; TPS63802 datasheet p36", "\n".join(body))


def paste_arc(center_x: float, center_y: float, start_angle: float, end_angle: float) -> str:
    mid_angle = (start_angle + end_angle) / 2
    def point(angle: float) -> str:
        return f"{fmt(center_x + 0.54 * cos(radians(angle)))} {fmt(center_y + 0.54 * sin(radians(angle)))}"
    return (f'  (fp_arc (start {point(start_angle)}) (mid {point(mid_angle)}) '
            f'(end {point(end_angle)}) (stroke (width 0.22) (type solid)) (layer "F.Paste"))')


def microphone() -> str:
    # IM67D128BV01, datasheet Figure 15.  The 0.4 mm NPTH is the acoustic port.
    body = [*outline(1.5, 1.1), *outline(1.8, 1.4, "F.CrtYd")]
    for number, x, y in ((1, -1.15, 0.59), (2, -0.55, 0.59), (4, -1.15, -0.59), (5, -0.55, -0.59)):
        body.append(rect(str(number), x, y, 0.42, 0.625))
    body.append('''  (pad "3" smd custom (at 0.55 -0.54) (size 0.3 0.3) (layers "F.Cu" "F.Mask")
    (options (clearance outline) (anchor circle))
    (primitives (gr_circle (center 0 0.54) (end 0.54 0.54) (width 0.32) (fill no))))''')
    body.append('  (pad "" np_thru_hole circle (at 0.55 0) (size 0.4 0.4) (drill 0.4) (layers "*.Cu" "*.Mask"))')
    for start, end in ((5, 115), (125, 235), (245, 355)):
        body.append(paste_arc(0.55, 0, start, end))
    body.append(line(-1.7, 0.8, -1.7, 1.3, "F.SilkS", 0.12))
    return common("Infineon_IM67D128BV01", "Infineon IM67D128BV01 manufacturer Figure 15; acoustic port 0.4mm NPTH", "\n".join(body))


def motor() -> str:
    # Solder termination for a wired 8 x 2.5 mm coin motor.  The motor body is
    # retained by the enclosure, not by its two lead solder joints.
    body = [
        '  (fp_circle (center 0 0) (end 4 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
        *outline(4.5, 6.5, "F.CrtYd"),
        '  (pad "1" thru_hole circle (at -2.5 5.4) (size 1.6 1.6) (drill 0.8) (layers "*.Cu" "*.Mask"))',
        '  (pad "2" thru_hole circle (at 2.5 5.4) (size 1.6 1.6) (drill 0.8) (layers "*.Cu" "*.Mask"))',
        '  (fp_text user "MOTOR +" (at -2.5 7.1) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.1))))',
    ]
    footprint = common("Motor_VC0825B002F", "Wired 8mm coin motor solder terminations; enclosure must retain motor", "\n".join(body))
    return footprint.replace("  (attr smd)", "  (attr through_hole exclude_from_pos_files)")


def pogo() -> str:
    # Mechanically provisional 7.5 mm pitch, 2.8 mm ENIG pads on rear face.
    body = [
        '  (pad "1" smd circle (at -3.75 0) (size 2.8 2.8) (layers "B.Cu" "B.Mask"))',
        '  (pad "2" smd circle (at 3.75 0) (size 2.8 2.8) (layers "B.Cu" "B.Mask"))',
        '  (fp_text user "+" (at -3.75 2.7) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.12)) (justify mirror)))',
        '  (fp_text user "-" (at 3.75 2.7) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.12)) (justify mirror)))',
        *outline(6, 2.2, "B.CrtYd"),
    ]
    return common("Pogo_Charge_2Pin", "Provisional 2.8mm ENIG contacts at 7.5mm pitch; verify fixture", "\n".join(body), back=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, maker in (
        ("L_Coilcraft_XFL4015", inductor),
        ("Texas_DLA0010A_VSON-10_2x3mm", regulator),
        ("Infineon_IM67D128BV01", microphone),
        ("Motor_VC0825B002F", motor),
        ("Pogo_Charge_2Pin", pogo),
    ):
        (OUT / (name + ".kicad_mod")).write_text(maker())
        print(name)


if __name__ == "__main__":
    main()
