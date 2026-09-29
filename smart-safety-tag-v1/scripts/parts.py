"""Datasheet checked symbol pin tables for the Smart Safety Tag circuits.

The generator uses these pin numbers as the single source of truth for its
schematic, symbol library and exported connection audit.  Footprint geometry
is handled separately, and must be checked before PCB release.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    electrical: str = "passive"
    side: str = "L"


@dataclass(frozen=True)
class Part:
    name: str
    reference: str
    pins: tuple[Pin, ...]
    footprint: str
    datasheet: str = ""


def p(number: int | str, name: str, electrical: str = "passive", side: str = "L") -> Pin:
    return Pin(str(number), name, electrical, side)


PARTS: dict[str, Part] = {
    "R": Part("R", "R", (p(1, "1"), p(2, "2", side="R")), "R_0603_1608Metric"),
    "C": Part("C", "C", (p(1, "1"), p(2, "2", side="R")), "C_0603_1608Metric"),
    "L": Part("L", "L", (p(1, "1"), p(2, "2", side="R")), "L_Coilcraft_XFL4015",
              "https://www.coilcraft.com/getmedia/84927b8b-f089-421b-a7f4-a0fa23afe908/xfl4015.pdf"),
    "NTC": Part("NTC", "RT", (p(1, "1"), p(2, "2", side="R")), "R_0603_1608Metric", "https://www.tdk-electronics.tdk.com/en/530404/products/product-catalog/sensors-and-sensor-systems/smd-ntc-thermistors"),
    "DIODE": Part("DIODE", "D", (p(1, "K"), p(2, "A", side="R")), "D_SOD-323",
                   "https://assets.nexperia.com/documents/data-sheet/PMEG2010EA.pdf"),
    "REVDIODE": Part("REVDIODE", "D", (p(1, "K", "power_out"), p(2, "A", side="R")), "D_SOD-123F",
                      "https://assets.nexperia.com/documents/data-sheet/PMEG6010CEH.pdf"),
    "ESD": Part("ESD", "D", (p(1, "IO"), p(2, "GND", side="R")), "D_SOD-523", "https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf"),
    "NMOS": Part("NMOS", "Q", (p(1, "G"), p(2, "S"), p(3, "D", side="R")), "SOT-23", "https://aosmd.com/res/data_sheets/AO3400A.pdf"),
    "BSS138": Part("BSS138", "Q", (p(1, "G"), p(2, "S"), p(3, "D", side="R")), "SOT-23",
                    "https://assets.nexperia.com/documents/data-sheet/BSS138P.pdf"),
    "SW": Part("SW", "SW", (p(1, "A"), p(2, "B", side="R"), p("SH", "SHIELD")), "SW_Push_1P1T-SH_NO_CK_KMR2xxG", "https://www.ckswitches.com/media/1479/kmr2.pdf"),
    "CONN2": Part("CONN2", "J", (p(1, "1"), p(2, "2")), "Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal"),
    "BATCONN": Part("BATCONN", "J", (p(1, "PACK+", "power_out"), p(2, "PACK-", "power_out")), "Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal",
                     "https://www.molex.com/en-us/products/part-detail/532610271"),
    "CHGCONN": Part("CHGCONN", "J", (p(1, "PROTECTED_5V", "power_out"), p(2, "RETURN")), "Pogo_Charge_2Pin"),
    "TP": Part("TP", "TP", (p(1, "TP"),), "TestPoint_Pad_D1.0mm"),
    "MOTOR": Part("MOTOR", "M", (p(1, "+"), p(2, "-", side="R")), "Motor_VC0825B002F",
                  "https://www.vybronics.com/wp-content/uploads/datasheet-files/Vybronics-VC0825B002F-datasheet.pdf"),
    "RGB": Part("RGB", "D", (p(1, "RED_K", side="R"), p(2, "COMMON_A"), p(3, "GREEN_K", side="R"), p(4, "BLUE_K", side="R")), "LED_Kingbright_APFA3010_3x1.5mm_Horizontal", "https://www.kingbrightusa.com/images/catalog/spec/apfa3010lseezgkqbkc.pdf"),
    "MIC": Part("IM67D128BV01", "U", (p(1, "DATA", "output", "R"), p(2, "LR"), p(3, "GND", "power_in"), p(4, "CLOCK", "input"), p(5, "VDD", "power_in")), "Infineon_IM67D128BV01", "https://www.infineon.com/assets/row/public/documents/24/49/infineon-im67d128b-datasheet-en.pdf"),
    "ACCEL": Part("LIS2DW12", "U", (p(1, "SCL", "input"), p(2, "CS", "input"), p(3, "SA0", "input"), p(4, "SDA", "bidirectional"), p(5, "NC", "no_connect"), p(6, "GND", "power_in"), p(7, "RES"), p(8, "GND", "power_in"), p(9, "VDD", "power_in"), p(10, "VDDIO", "power_in"), p(11, "INT2", "output", "R"), p(12, "INT1", "output", "R")), "LGA-12_2x2mm_P0.5mm", "https://www.st.com/resource/en/datasheet/lis2dw12.pdf"),
    "CHARGER": Part("BQ25185", "U", (p(1, "SYS", "power_out", "R"), p(2, "BAT", "passive", "R"), p(3, "STAT2", "open_collector", "R"), p(4, "CE", "input"), p(5, "GND", "power_in"), p(6, "TS/MR", "input"), p(7, "ILIM/VSET", "input"), p(8, "ISET", "input"), p(9, "STAT1", "open_collector", "R"), p(10, "IN", "power_in"), p(11, "EP", "power_in")), "Texas_DLH0010A_WSON-10-1EP_2.2x2mm_P0.4mm_EP0.9x1.5mm", "https://www.ti.com/lit/ds/symlink/bq25185.pdf"),
    "WINDOW": Part("TLV7042", "U", (p(1, "OUTA", "open_collector", "R"), p(2, "INA-", "input"), p(3, "INA+", "input"), p(4, "VEE", "power_in"), p(5, "INB+", "input"), p(6, "INB-", "input"), p(7, "OUTB", "open_collector", "R"), p(8, "VCC", "power_in")), "SOT-23-8", "https://www.ti.com/lit/ds/symlink/tlv7032.pdf"),
    "BUCKBOOST": Part("TPS63802", "U", (p(1, "EN", "input"), p(2, "MODE", "input"), p(3, "AGND", "power_in"), p(4, "FB", "input"), p(5, "PG", "open_collector", "R"), p(6, "VOUT", "power_out", "R"), p(7, "L2", "passive", "R"), p(8, "GND", "power_in"), p(9, "L1"), p(10, "VIN", "power_in")), "Texas_DLA0010A_VSON-10_2x3mm", "https://www.ti.com/lit/ds/symlink/tps63802.pdf"),
    "GAUGE": Part("MAX17048", "U", (p(1, "CTG", "power_in"), p(2, "CELL", "no_connect"), p(3, "VDD", "power_in"), p(4, "GND", "power_in"), p(5, "ALRT", "open_collector", "R"), p(6, "QSTRT", "input"), p(7, "SCL", "input"), p(8, "SDA", "bidirectional"), p(9, "EP", "power_in")), "TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm", "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf"),
    "LDO3V0": Part("TPS7A2030PDBVR", "U", (p(1, "IN", "power_in"), p(2, "GND", "power_in"), p(3, "EN", "input"), p(4, "NC", "no_connect"), p(5, "OUT", "power_out", "R")), "SOT-23-5", "https://www.ti.com/lit/ds/symlink/tps7a20.pdf"),
}
