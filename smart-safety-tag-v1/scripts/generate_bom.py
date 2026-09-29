#!/usr/bin/env python3
"""Generate exact-MPN procurement BOMs from the authoritative circuit data."""

from collections import defaultdict
import csv
from pathlib import Path

from adapter_data import COMPONENTS as ADAPTER, PARTS as ADAPTER_PARTS
from circuit_data import COMPONENTS as TAG
from parts import PARTS as TAG_PARTS


ROOT = Path(__file__).resolve().parents[1] / "manufacturing"

MANUFACTURERS = {
    "MCU": "Espressif", "MIC": "Infineon", "LDO3V0": "Texas Instruments",
    "ACCEL": "STMicroelectronics", "BATCONN": "Molex", "ESD": "Texas Instruments",
    "REVDIODE": "Nexperia", "CHARGER": "Texas Instruments", "NTC": "TDK",
    "WINDOW": "Texas Instruments", "BSS138": "Nexperia",
    "BUCKBOOST": "Texas Instruments", "L": "Coilcraft", "GAUGE": "Analog Devices",
    "SW": "C&K", "RGB": "Kingbright", "MOTOR": "Vybronics",
    "NMOS": "Alpha & Omega Semiconductor", "DIODE": "Nexperia",
    "USBC": "GCT", "EFUSE": "Texas Instruments", "POGO": "Mill-Max",
    "R": "Yageo", "C": "TDK",
}


def datasheet(component, part):
    if component.part == "R":
        return "https://www.yageogroup.com/component-documentation/download/specsheet/" + component.mpn
    if component.part == "C":
        return "https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=" + component.mpn
    return part.datasheet


def bom_rows(components, parts, tag=False):
    groups = defaultdict(list)
    for component in components:
        if component.part in ("TP", "CHGCONN"):
            continue
        if not component.mpn:
            raise ValueError(f"{component.reference}: missing orderable manufacturer part number")
        footprint = component.footprint or ("ESP32-S2-MINI-1" if component.part == "MCU"
                                            else parts[component.part].footprint)
        key = (component.mpn, component.value, footprint, component.part)
        groups[key].append(component)
    rows = []
    for (mpn, value, footprint, part_key), group in groups.items():
        group.sort(key=lambda item: (item.reference.rstrip("0123456789"),
                                     int(item.reference.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))))
        rows.append({
            "References": " ".join(c.reference for c in group),
            "Quantity": len(group),
            "Manufacturer": MANUFACTURERS[part_key],
            "Manufacturer Part Number": mpn,
            "Value / Description": value,
            "Package / PCB Footprint": "Safety:" + footprint,
            "Assembly": "Wire to PCB pads" if part_key == "MOTOR" else "PCB placement",
            "Manufacturer Source": (
                "https://documentation.espressif.com/esp32-s3-mini-1_mini-1u_datasheet_en.pdf"
                if part_key == "MCU" else datasheet(group[0], parts[part_key])
            ),
        })
    if tag:
        rows.append({
            "References": "BAT1", "Quantity": 1, "Manufacturer": "Akyga",
            "Manufacturer Part Number": "AKY1604",
            "Value / Description": "Protected 400 mAh Li-polymer pack; Molex 51021-0200 lead",
            "Package / PCB Footprint": "LP403035, cell 4.0 x 30 x 37 mm; assembled 4.5 x 31 x 37.5 mm",
            "Assembly": "Attach to J1 after PCB electrical checks",
            "Manufacturer Source": "https://elektronik.ropla.eu/pdf/stock/aky/aky1604.pdf",
        })
    return sorted(rows, key=lambda row: row["References"].split()[0])


def write(name, components, parts, tag=False):
    dest = ROOT / name / "bom"
    dest.mkdir(parents=True, exist_ok=True)
    rows = bom_rows(components, parts, tag=tag)
    path = dest / (name + "-bom.csv")
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{path}: {len(rows)} procurement lines")


if __name__ == "__main__":
    write("tag", TAG, TAG_PARTS, tag=True)
    write("charging-adapter", ADAPTER, ADAPTER_PARTS)
