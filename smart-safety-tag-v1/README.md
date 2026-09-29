# Smart Safety Tag V1

Editable KiCad design and prototype fabrication package for a BLE safety tag and its protected pogo charging adapter. The tag uses an ESP32-S3-MINI-1-N4R2, PDM microphone, LIS2DW12, MAX17048, protected 400 mAh battery, physical SOS button, RGB LED and vibration motor. The phone supplies GPS and Internet access.

Both boards are routed and checked with KiCad 10.0.6. PCB DRC has no ignored rules, violations, unconnected items or schematic-parity findings. ERC reports have zero errors and warnings under KiCad's default checks; the four ERC diagnostics listed in each report remain ignored by KiCad. No individual ERC/DRC findings are excluded. The hardware-test application builds with ESP-IDF v5.5. **Physical prototype validation remains pending.** This package supports prototype manufacture; it does not establish product safety, radio/acoustic performance, enclosure fit or an ingress-protection rating.

| Deliverable | Location |
| --- | --- |
| Tag KiCad project, 8 hierarchical child sheets and 60 × 42 mm PCB | [hardware/tag/smart-safety-tag.kicad_pro](hardware/tag/smart-safety-tag.kicad_pro) |
| Charging adapter KiCad project and 32 × 22 mm PCB | [hardware/charging-adapter/charging-adapter.kicad_pro](hardware/charging-adapter/charging-adapter.kicad_pro) |
| Tag Gerbers/drills, BOM, placement CSVs and assembly/schematic PDFs | [manufacturing/tag](manufacturing/tag) |
| Adapter Gerbers/drills, BOM, placement CSVs and assembly/schematic PDFs | [manufacturing/charging-adapter](manufacturing/charging-adapter) |
| Component decisions, substitutions and manufacturer sources | [docs/design-inputs.md](docs/design-inputs.md) |
| Power architecture and calculated runtime scenarios | [docs/power-budget.md](docs/power-budget.md) |
| GPIO map and six-pad programming interface | [docs/gpio-map.md](docs/gpio-map.md) |
| Board fabrication and assembly specification | [docs/manufacturing-specification.md](docs/manufacturing-specification.md) |
| Power-on, charging, peripheral and qualification procedure | [docs/bring-up.md](docs/bring-up.md) |
| CAD/calculation/build evidence and pending measurements | [docs/verification.md](docs/verification.md) |
| Modular hardware-test source and prebuilt images | [firmware/hardware-tests](firmware/hardware-tests) |

Use KiCad 10.0.x or later and keep each project's `symbols/`, `footprints/`, `sym-lib-table` and `fp-lib-table` alongside its native files. All required symbols and land patterns are supplied locally. Optional 3D model references use KiCad's standard model libraries; external STEP models are not bundled. A PCB 3D view does not validate the proposed enclosure or cell clearances.

The main electrical substitutions are TPS63802 for TPS63031 to increase the converter current margin, TPD1E10B06 for the proposed charging ESD diode, and switched 3.0 V supplies for the microphone and motor. An analog NTC window independently inhibits charging. The charging adapter includes a USB-C power input and eFuse before its exposed spring pins. Read the design decisions and fabrication notes before purchasing or assembly.

The tag has 83 PCB footprints, including six programming pads, two bare charging contacts and a wired motor. RT1 is fitted on the rear. The battery is an off-board BOM item and must be insulated and thermally coupled to RT1 as documented. Both boards are 1.0 mm thick; the adapter's USB connector requires 1.0 ±0.10 mm. The module's antenna projects beyond the tag outline and its keepout must remain clear of the battery, clip and magnets.

Each manufacturing directory has a bare-board ZIP and `manifest.json` linking exported files to the complete editable CAD source using SHA-256 hashes. Assembly CSVs use KiCad coordinates/rotations; read the manufacturing specification before importing them. The fabrication ZIP also contains the manufacturing notes.

To regenerate checks and exports from the project root:

```sh
python3 -m pip install -r scripts/requirements.txt
python3 scripts/generate_gpio_header.py
python3 scripts/check_thermal_window.py
python3 scripts/export_manufacturing.py --cli-command kicad-cli
python3 scripts/package_release.py
```

Placement and schematic-generation scripts are construction tools. Rerunning a placement script replaces the corresponding layout, so preserve the routed board and review changes before doing that. GPIO assignments originate in `hardware/board-interface.json`; electrical components and pin/net definitions originate in `scripts/circuit_data.py`, `adapter_data.py`, `parts.py` and `passive_parts.py`.

The included firmware captures audio and checks peripherals. Keyword inference, a custom emergency BLE service, smartphone messaging and sleep/wake behavior need application firmware and physical validation. Continuous keyword detection does not operate in deep sleep in this design.
