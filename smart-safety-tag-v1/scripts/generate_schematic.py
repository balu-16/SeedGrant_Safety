#!/usr/bin/env python3
"""Generate editable KiCad 10 hierarchical sheets from circuit_data.py.

Requires `pip install sexpdata`.  No absolute paths are embedded in the
project.  The symbol library is project-local; standard footprint geometries
are copied from KiCad's 10.0.6 library by export_footprints.py.
"""

from collections import defaultdict
from copy import deepcopy
from math import cos, radians, sin
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from sexpdata import Symbol as S, dumps, load

from circuit_data import COMPONENTS, SHEETS, Component
from parts import PARTS, Part, Pin
from release_data import RELEASE_DATE, REVISION


ROOT = Path(__file__).resolve().parents[1] / "hardware" / "tag"
PROJECT = "smart-safety-tag"
SYMBOL_LIBRARY = ROOT / "symbols" / "Safety.kicad_sym"
STANDARD_MCU_SYMBOL = ROOT / "symbols" / "upstream" / "ESP32-S3-MINI-1.kicad_sym"


def uid(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, "smart-safety-tag-v1:" + key))


def expr(name: str, *args):
    return [S(name), *args]


def effect(size: float = 1.27, hidden: bool = False):
    value = expr("effects", expr("font", expr("size", size, size)))
    if hidden:
        value.append(expr("hide", S("yes")))
    return value


def property_(name: str, value: str, x: float, y: float, hidden: bool = False):
    return expr("property", name, value, expr("at", x, y, 0), effect(hidden=hidden))


def get_child(node, name: str):
    return next((v for v in node if isinstance(v, list) and v and v[0] == S(name)), None)


def custom_symbol(part: Part):
    left = [p for p in part.pins if p.side == "L"]
    right = [p for p in part.pins if p.side == "R"]
    count = max(len(left), len(right), 2)
    half_height = ((count - 1) * 2.54 / 2) + 2.54
    half_width = 10.16
    pins = []
    for side, group in (("L", left), ("R", right)):
        for index, pin in enumerate(group):
            y = round((len(group) - 1) * 1.27 - index * 2.54, 3)
            x = -12.7 if side == "L" else 12.7
            angle = 0 if side == "L" else 180
            pins.append(
                expr(
                    "pin", S(pin.electrical), S("line"), expr("at", x, y, angle),
                    expr("length", 2.54), expr("name", pin.name, effect(1.0)),
                    expr("number", pin.number, effect(1.0)),
                )
            )
    shape = expr(
        "rectangle", expr("start", -half_width, round(half_height, 3)),
        expr("end", half_width, round(-half_height, 3)),
        expr("stroke", expr("width", 0.254), expr("type", S("default"))),
        expr("fill", expr("type", S("background"))),
    )
    name = part.name
    return expr(
        "symbol", "Safety:" + name,
        expr("pin_names", expr("offset", 0.508)),
        expr("exclude_from_sim", S("no")),
        expr("in_bom", S("yes")), expr("on_board", S("yes")),
        expr("property", "Reference", part.reference, expr("at", 0, round(half_height + 3.81, 3), 0), effect()),
        expr("property", "Value", name, expr("at", 0, round(-half_height - 3.81, 3), 0), effect()),
        expr("property", "Footprint", "Safety:" + part.footprint, expr("at", 0, 0, 0), effect(hidden=True)),
        expr("property", "Datasheet", part.datasheet, expr("at", 0, 0, 0), effect(hidden=True)),
        expr("symbol", name + "_0_1", shape),
        expr("symbol", name + "_1_1", *pins),
    )


def mcu_symbol():
    with STANDARD_MCU_SYMBOL.open() as stream:
        library = load(stream)
    symbol = deepcopy(get_child(library, "symbol"))
    symbol[1] = "Safety:ESP32-S3-MINI-1"
    get_child(symbol, "property")[2] = "U"
    for item in symbol:
        if isinstance(item, list) and len(item) > 2 and item[0] == S("property") and item[1] == "Footprint":
            item[2] = "Safety:ESP32-S2-MINI-1"
    return symbol


def symbol_pins(symbol):
    result = {}
    for unit in symbol:
        if not isinstance(unit, list) or unit[0] != S("symbol"):
            continue
        for pin in unit:
            if not isinstance(pin, list) or pin[0] != S("pin"):
                continue
            number = str(get_child(pin, "number")[1])
            x, y, angle = get_child(pin, "at")[1:4]
            result[number] = (float(x), float(y), float(angle), str(pin[1]))
    return result


def component_position(sheet: str, index: int) -> tuple[float, float]:
    if sheet == "mcu_ble":
        return (101.6, 148.59) if index == 0 else (254.0 + ((index - 1) // 7) * 81.28,
                                                  43.18 + ((index - 1) % 7) * 30.48)
    return (50.8 + (index // 10) * 139.7, 40.64 + (index % 10) * 22.86)


def global_label(net: str, x: float, y: float, angle: int, key: str):
    effects = effect(0.9)
    effects.append(expr("justify", S("right" if angle in (0, 90) else "left")))
    return expr(
        "global_label", net, expr("shape", S("bidirectional")),
        expr("at", round(x, 3), round(y, 3), angle), effects,
        expr("uuid", uid("label:" + key)),
    )


def no_connect(x: float, y: float, key: str):
    return expr("no_connect", expr("at", round(x, 3), round(y, 3)), expr("uuid", uid("nc:" + key)))


def wire(x1: float, y1: float, x2: float, y2: float, key: str):
    return expr(
        "wire", expr("pts", expr("xy", round(x1, 3), round(y1, 3)),
                    expr("xy", round(x2, 3), round(y2, 3))),
        expr("stroke", expr("width", 0), expr("type", S("default"))),
        expr("uuid", uid("wire:" + key)),
    )


def instance(component: Component, symbol, x: float, y: float, path: str,
             parts: dict[str, Part] = PARTS, project: str = PROJECT,
             key_prefix: str = ""):
    pins = symbol_pins(symbol)
    unknown = set(component.nets) - set(pins)
    if unknown:
        raise ValueError(f"{component.reference}: unknown package pins {sorted(unknown)}")
    footprint = component.footprint or ("ESP32-S2-MINI-1" if component.part == "MCU" else parts[component.part].footprint)
    lib_name = "ESP32-S3-MINI-1" if component.part == "MCU" else parts[component.part].name
    maximum_y = max(abs(item[1]) for item in pins.values())
    body = expr(
        "symbol", expr("lib_id", "Safety:" + lib_name), expr("at", x, y, 0),
        expr("unit", 1), expr("exclude_from_sim", S("no")),
        expr("in_bom", S("no" if component.part in ("TP", "CHGCONN") else "yes")),
        expr("on_board", S("yes")), expr("dnp", S("no")),
        expr("uuid", uid(key_prefix + "symbol:" + component.reference)),
        property_("Reference", component.reference, x - (20.32 if component.part == "MCU" else 0), round(y - maximum_y - 5.08, 3)),
        property_("Value", component.value, x + (25.4 if component.part == "MCU" else 0), round(y + maximum_y + 5.08, 3)),
        property_("Footprint", "Safety:" + footprint, x, y, True),
        property_("Datasheet", "" if component.part == "MCU" else parts[component.part].datasheet, x, y, True),
        property_("MPN", component.mpn, x, y, True),
    )
    for number in pins:
        body.append(expr("pin", number, expr("uuid", uid(key_prefix + "pin:" + component.reference + ":" + number))))
    body.append(
        expr("instances", expr("project", project, expr("path", path,
            expr("reference", component.reference), expr("unit", 1))))
    )
    extra = []
    occupied = {}
    for number, (px, py, pin_angle, electrical) in pins.items():
        net = component.nets.get(number)
        at = (round(x + px, 3), round(y - py, 3))
        if at in occupied:
            if net and occupied[at] != net:
                raise ValueError(f"{component.reference}: stacked pins at {at} have distinct nets")
            continue
        occupied[at] = net
        if net:
            dx = round(-5.08 * cos(radians(pin_angle)), 3)
            dy = round(5.08 * sin(radians(pin_angle)), 3)
            label_x, label_y = round(at[0] + dx, 3), round(at[1] + dy, 3)
            if abs(dx) > abs(dy):
                label_angle = 0 if dx < 0 else 180
            else:
                label_angle = 270 if dy < 0 else 90
            extra.append(wire(*at, label_x, label_y, key_prefix + component.reference + ":" + number))
            extra.append(global_label(net, label_x, label_y, label_angle, key_prefix + component.reference + ":" + number))
        elif electrical != "no_connect":
            extra.append(no_connect(*at, key_prefix + component.reference + ":" + number))
    return body, extra


def header(root_uuid: str, title: str):
    return [
        S("kicad_sch"), expr("version", 20250114), expr("generator", "eeschema"),
        expr("generator_version", "10.0"), expr("uuid", root_uuid),
        expr("paper", "A3"), expr("title_block", expr("title", title),
            expr("date", RELEASE_DATE), expr("rev", REVISION),
            expr("comment", 1, "Prototype; physical validation pending")),
    ]


def sheet_block(name: str, sheet_uuid: str, root_uuid: str, page: int, x: float, y: float):
    return expr(
        "sheet", expr("at", x, y), expr("size", 88.9, 25.4),
        expr("exclude_from_sim", S("no")), expr("in_bom", S("yes")),
        expr("on_board", S("yes")), expr("dnp", S("no")),
        expr("stroke", expr("width", 0.1524), expr("type", S("solid"))),
        expr("fill", expr("color", 0, 0, 0, 0)), expr("uuid", sheet_uuid),
        property_("Sheetname", name.replace("_", " ").title(), x, y - 1.27),
        property_("Sheetfile", f"schematic/{name}/{name}.kicad_sch", x, y + 26.67),
        expr("instances", expr("project", PROJECT,
            expr("path", "/" + root_uuid, expr("page", str(page))))),
    )


def write_project():
    ROOT.mkdir(parents=True, exist_ok=True)
    root_uuid = uid("root")
    symbols = {key: custom_symbol(value) for key, value in PARTS.items()}
    symbols["MCU"] = mcu_symbol()

    SYMBOL_LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    library = expr("kicad_symbol_lib", expr("version", 20251024),
                   expr("generator", "smart-safety-tag"), *symbols.values())
    SYMBOL_LIBRARY.write_text(dumps(library) + "\n")
    (ROOT / "sym-lib-table").write_text(
        '(sym_lib_table (lib (name "Safety")(type "KiCad")'
        '(uri "${KIPRJMOD}/symbols/Safety.kicad_sym")(options "")(descr "Local verified pin maps")))\n'
    )
    (ROOT / "fp-lib-table").write_text(
        '(fp_lib_table (lib (name "Safety")(type "KiCad")'
        '(uri "${KIPRJMOD}/footprints/Safety.pretty")(options "")(descr "Local footprints")))\n'
    )
    project_file = ROOT / f"{PROJECT}.kicad_pro"
    if not project_file.exists():
        project_file.write_text("{}\n")

    grouped = defaultdict(list)
    for item in COMPONENTS:
        grouped[item.sheet].append(item)
    root = header(root_uuid, "Smart Safety Tag V1")
    root.append(expr("lib_symbols"))
    for index, name in enumerate(SHEETS, start=2):
        sheet_uuid = uid("sheet:" + name)
        x = 35.56 + ((index - 2) % 2) * 177.8
        y = 35.56 + ((index - 2) // 2) * 55.88
        root.append(sheet_block(name, sheet_uuid, root_uuid, index, x, y))
        child = header(uid("child:" + name), name.replace("_", " ").title())
        types = {item.part for item in grouped[name]}
        child.append(expr("lib_symbols", *(symbols[key] for key in sorted(types))))
        path = "/" + root_uuid + "/" + sheet_uuid
        for comp_index, component in enumerate(grouped[name]):
            x, y = component_position(name, comp_index)
            body, extra = instance(component, symbols[component.part], x, y, path)
            child.extend(extra)
            child.append(body)
        child.append(expr("sheet_instances", expr("path", "/", expr("page", str(index)))))
        child.append(expr("embedded_fonts", S("no")))
        folder = ROOT / "schematic" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{name}.kicad_sch").write_text(dumps(child) + "\n")
    root.append(expr("sheet_instances", expr("path", "/", expr("page", "1"))))
    root.append(expr("embedded_fonts", S("no")))
    (ROOT / f"{PROJECT}.kicad_sch").write_text(dumps(root) + "\n")
    print(f"Generated {len(COMPONENTS)} tag components in {len(SHEETS)} native sheets: {ROOT}")


if __name__ == "__main__":
    write_project()
