#!/usr/bin/env python3
"""Generate the editable single-sheet KiCad charging fixture schematic."""

from pathlib import Path
from sexpdata import Symbol as S, dumps

from adapter_data import COMPONENTS, PARTS
from generate_schematic import custom_symbol, expr, header, instance, uid


ROOT = Path(__file__).resolve().parents[1] / "hardware" / "charging-adapter"
PROJECT = "charging-adapter"


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    symbols = {name: custom_symbol(part) for name, part in PARTS.items()}
    library = expr("kicad_symbol_lib", expr("version", 20251024),
                   expr("generator", "smart-safety-tag"), *symbols.values())
    (ROOT / "symbols").mkdir(exist_ok=True)
    (ROOT / "symbols" / "Safety.kicad_sym").write_text(dumps(library) + "\n")
    (ROOT / "sym-lib-table").write_text(
        '(sym_lib_table (lib (name "Safety")(type "KiCad")'
        '(uri "${KIPRJMOD}/symbols/Safety.kicad_sym")(options "")(descr "Local adapter symbols")))\n'
    )
    (ROOT / "fp-lib-table").write_text(
        '(fp_lib_table (lib (name "Safety")(type "KiCad")'
        '(uri "${KIPRJMOD}/footprints/Safety.pretty")(options "")(descr "Local adapter footprints")))\n'
    )
    project_file = ROOT / f"{PROJECT}.kicad_pro"
    if not project_file.exists():
        project_file.write_text("{}\n")
    root_uuid = uid("adapter:root")
    root = header(root_uuid, "Smart Safety Tag 5V Charging Fixture")
    root.append(expr("lib_symbols", *symbols.values()))
    for index, component in enumerate(COMPONENTS):
        x, y = 55.88 + (index // 4) * 83.82, 46.99 + (index % 4) * 58.42
        body, wiring = instance(component, symbols[component.part], x, y,
                                "/" + root_uuid, parts=PARTS,
                                project=PROJECT, key_prefix="adapter:")
        root.extend(wiring)
        root.append(body)
    root.append(expr("sheet_instances", expr("path", "/", expr("page", "1"))))
    root.append(expr("embedded_fonts", S("no")))
    (ROOT / f"{PROJECT}.kicad_sch").write_text(dumps(root) + "\n")
    print(f"Generated {len(COMPONENTS)} charging adapter components: {ROOT}")


if __name__ == "__main__":
    main()
