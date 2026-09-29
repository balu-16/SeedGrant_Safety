# Smart Safety Tag V1 — Prototype Manufacturing Specification

Fabricate from the current `manufacturing/tag/` and `manufacturing/charging-adapter/` exports. Each directory contains Gerbers, Excellon drills, an exact-MPN BOM, placement CSVs, assembly/schematic PDFs and a SHA-256 manifest. The ZIP in each directory contains the bare-board fabrication files. CAD checks do not establish product safety, enclosure fit or physical performance.

| Requirement | Tag | Charging adapter |
| --- | --- | --- |
| Finished outline, excluding stroke width | 60.0 × 42.0 mm | 32.0 × 22.0 mm |
| Layers | Two, F.Cu/B.Cu | Two, F.Cu/B.Cu |
| Finished thickness | 1.0 mm | **1.0 ±0.10 mm**; required by the USB4125 drawing |
| Material and copper | FR-4; 35 µm nominal copper each side | FR-4; 35 µm nominal copper each side |
| Surface finish | ENIG; exposed charging/test pads remain open | ENIG |
| Mask and legend | Both sides; preserve the supplied pad openings | Both sides |
| Minimum design clearance | 0.13 mm copper; 0.15 mm copper-to-hole | 0.13 mm copper; 0.15 mm copper-to-hole |
| Standard vias | 0.60 mm pad / 0.30 mm finished drill | 0.60 mm pad / 0.30 mm finished drill |
| Other holes | Two 0.80 mm plated motor-lead holes; one **0.40 mm unplated acoustic hole** | USB connector plated slots, as supplied in the drill file |
| Assembly | Front SMT; RT1 on rear; wired motor and battery attached after checks | Front SMT, including two spring pins |

The tag's actual minimum track width is 0.16 mm at the microphone ground connection and dense signal fanouts. The fabricator must support the 0.13 mm clearances used around small packages. Confirm plated-slot processing on the adapter and correct plated/unplated handling in the merged Excellon files. The Gerber job's size includes the 0.05 mm Edge.Cuts stroke, which can appear as 60.05 × 42.05 mm or 32.05 × 22.05 mm; route on the outline centerline. The USB connector thickness requirement comes from the [GCT drawing](https://gct.co/files/drawings/usb4125.pdf).

Use the supplied paste geometry for the exposed-pad packages, microphone ground ring and pogo bases. Select a stencil/reflow process compatible with the exact component datasheets, including the right-angle RGB LED. Keep flux, cleaning fluid, adhesive and solder out of the microphone's acoustic hole. Do not fill or tent the acoustic hole. The 0.30 mm vias use the board's tenting settings; no via filling or copper capping is requested.

Placement CSVs use KiCad's Cartesian millimetre coordinates with origin (0,0): **PosY is negative**. Rotations use KiCad's convention. The back assembly PDF is mirrored for viewing the rear face. Align the CSVs, PCB and drawings in the assembler's CAM system before placing polarized parts. Test pads and J2 are bare PCB features and have no purchasing line. M1 is excluded from placement files because its leads are soldered manually. BAT1 is included in the procurement BOM but has no PCB footprint.

Inspect pin 1, polarity and solder joints for U1–U9, the microphone, diodes, MOSFETs, RGB LED and battery connector. Use inspection appropriate to hidden exposed-pad joints. Measure the battery lead polarity before plugging it into J1. Retain the 8 mm motor mechanically and strain-relieve both leads. Insulate the cell from the board and provide an insulating thermal bond to RT1 without concentrating pressure on the pouch cell.

The tag's rear charging contacts are 2.8 mm diameter at 7.5 mm pitch. In the PCB's front-view coordinates, J2.1 (+5 V raw) is at (148.25, 138.00) mm and J2.2 (GND) is at (155.75, 138.00) mm. Adapter P1 (+5 V protected) is at (117.00, 117.00) mm and P2 (GND) at (124.50, 117.00) mm. Verify the physical mating polarity; rear-view mirroring changes the apparent left/right order.

The spring pins require a retained, keyed fixture with controlled compression. Magnets, keying, mechanical retention and contact wear are not defined by the PCB pads. ENIG is suitable for prototype evaluation; establish the contact-finish life requirement before production. The clip-on enclosure, acoustic seal, cell support, magnet placement and button actuator need a fitted mechanical prototype. There are no board mounting holes; retention must support board edges without damaging components or the antenna. No ingress-protection rating is claimed.

Before quantity assembly, complete the power, charging, thermal, contact-fault, RF, acoustic and mechanical tests in [bring-up.md](bring-up.md) and record the results in [verification.md](verification.md). The current package is for prototype fabrication and validation.
