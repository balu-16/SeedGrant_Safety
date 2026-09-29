"""Electrical connectivity for the tag schematic; pin keys are package pads."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Component:
    reference: str
    part: str
    value: str
    sheet: str
    nets: dict[str, str]
    mpn: str = ""
    footprint: str = ""
    notes: str = ""


COMPONENTS: list[Component] = []


def add(sheet: str, ref: str, part: str, value: str, nets: dict[int | str, str], mpn: str = "", footprint: str = "", notes: str = "") -> None:
    COMPONENTS.append(Component(ref, part, value, sheet, {str(k): v for k, v in nets.items()}, mpn, footprint, notes))


def two(sheet: str, ref: str, part: str, value: str, one: str, two: str, mpn: str = "", footprint: str = "") -> None:
    add(sheet, ref, part, value, {1: one, 2: two}, mpn, footprint)


# The RF module pin map comes from Espressif ESP32-S3-MINI-1 v1.7.  GPIO26 is
# internally committed to PSRAM on the -N4R2 ordering option and stays NC.
MCU_NETS = {
    3: "3V3", 4: "BOOT_N", 5: "SOS_N", 6: "ACC_INT1", 8: "ACC_INT2",
    9: "FUEL_ALERT_N", 10: "I2C_SDA", 11: "I2C_SCL", 12: "PDM_CLK",
    13: "PDM_DATA", 14: "MOTOR_GATE", 15: "LED_R_N", 16: "LED_G_N",
    17: "LED_B_N", 18: "CHG_STAT1_N", 19: "CHG_STAT2_N",
    20: "CHARGE_INHIBIT", 21: "MODE_MIC", 22: "MOTOR_EN",
    39: "UART_TX", 40: "UART_RX", 45: "EN",
}
for ground_pin in (1, 2, 42, 43, *range(46, 66)):
    MCU_NETS[ground_pin] = "GND"
add("mcu_ble", "U1", "MCU", "ESP32-S3-MINI-1-N4R2", MCU_NETS, "ESP32-S3-MINI-1-N4R2")
two("mcu_ble", "C1", "C", "22uF 16V X5R", "3V3", "GND", "C3216X5R1C226M160AB", "C_1206_3216Metric")
two("mcu_ble", "C2", "C", "100nF 16V X7R", "3V3", "GND")
two("mcu_ble", "C20", "C", "100nF 16V X7R", "3V3", "GND")
two("mcu_ble", "C21", "C", "10uF 10V X5R", "3V3", "GND", footprint="C_0805_2012Metric")
two("mcu_ble", "R1", "R", "10k 1%", "3V3", "EN")
two("mcu_ble", "C3", "C", "1uF 10V X7R", "EN", "GND")
two("mcu_ble", "R2", "R", "10k 1%", "3V3", "BOOT_N")
two("mcu_ble", "R3", "R", "4.7k 1%", "3V3", "I2C_SDA")
two("mcu_ble", "R4", "R", "4.7k 1%", "3V3", "I2C_SCL")

# The microphone has its own quiet 3.0 V LDO.  The divider keeps a 3.3 V
# PDM clock within the microphone supply domain.  MODE_MIC first switches
# TPS63802 to fixed PWM and then enables this LDO; firmware waits for settling.
add("microphone", "U2", "MIC", "IM67D128BV01", {1: "PDM_DATA", 2: "GND", 3: "GND", 4: "PDM_CLK_3V0", 5: "MIC_3V0"}, "IM67D128BV01")
add("microphone", "U3", "LDO3V0", "TPS7A2030PDBVR", {1: "3V3", 2: "GND", 3: "MODE_MIC", 5: "MIC_3V0"}, "TPS7A2030PDBVR")
two("microphone", "C4", "C", "1uF 10V X7R", "3V3", "GND")
two("microphone", "C5", "C", "1uF 10V X7R", "MIC_3V0", "GND")
two("microphone", "C6", "C", "1uF 10V X7R", "MIC_3V0", "GND")
two("microphone", "C22", "C", "1uF 10V X7R", "MIC_3V0", "GND")
two("microphone", "C26", "C", "1uF 10V X7R", "MIC_3V0", "GND")
two("microphone", "C27", "C", "1uF 10V X7R", "3V3", "GND")
two("microphone", "R5", "R", "1k 1%", "PDM_CLK", "PDM_CLK_3V0")
two("microphone", "R6", "R", "10k 1%", "PDM_CLK_3V0", "GND")

add("accelerometer", "U4", "ACCEL", "LIS2DW12", {1: "I2C_SCL", 2: "3V3", 3: "GND", 4: "I2C_SDA", 6: "GND", 7: "GND", 8: "GND", 9: "3V3", 10: "3V3", 11: "ACC_INT2", 12: "ACC_INT1"}, "LIS2DW12TR")
two("accelerometer", "C7", "C", "100nF 16V X7R", "3V3", "GND")
two("accelerometer", "C23", "C", "100nF 16V X7R", "3V3", "GND")
two("accelerometer", "C8", "C", "10uF 10V X5R", "3V3", "GND", footprint="C_0805_2012Metric")

# Protected 400 mAh pack on Molex PicoBlade; RT1 is mounted on the back of the
# PCB and must be mechanically bonded to the cell surface, then validated.
add("battery_charging", "J1", "BATCONN", "AKY1604 protected pack", {1: "BAT", 2: "GND"}, "53261-0271")
add("battery_charging", "J2", "CHGCONN", "5V magnetic pogo contact pair", {1: "CHG_RAW", 2: "GND"}, footprint="Pogo_Charge_2Pin")
two("battery_charging", "D1", "ESD", "TPD1E10B06DYAR", "CHG_RAW", "GND", "TPD1E10B06DYAR")
add("battery_charging", "D2", "REVDIODE", "PMEG6010CEH", {1: "CHG_IN", 2: "CHG_RAW"}, "PMEG6010CEH,115")
add("battery_charging", "U5", "CHARGER", "BQ25185DLHR", {1: "SYS", 2: "BAT", 3: "CHG_STAT2_N", 4: "CHG_CE_N", 5: "GND", 6: "TS_MR", 7: "ILIM_SET", 8: "ICHG_SET", 9: "CHG_STAT1_N", 10: "CHG_IN", 11: "GND"}, "BQ25185DLHR")
two("battery_charging", "C9", "C", "1uF 25V X7R", "CHG_IN", "GND")
two("battery_charging", "C10", "C", "22uF 16V X5R", "SYS", "GND", "C3216X5R1C226M160AB", "C_1206_3216Metric")
two("battery_charging", "C24", "C", "10uF 10V X5R", "SYS", "GND", footprint="C_0805_2012Metric")
two("battery_charging", "C11", "C", "1uF 10V X7R", "BAT", "GND")
two("battery_charging", "R7", "R", "18k 1%", "ILIM_SET", "GND")
two("battery_charging", "R8", "R", "2k 1%", "ICHG_SET", "GND")
two("battery_charging", "RT1", "NTC", "10k B3435 1%", "TS_MR", "GND", "B57332V5103A260")
two("battery_charging", "R9", "R", "10k 1%", "3V3", "CHG_STAT1_N")
two("battery_charging", "R10", "R", "10k 1%", "3V3", "CHG_STAT2_N")

# Independent analog temperature interlock.  The charger TS/MR's 38 uA source
# biases RT1.  Window comparator outputs are tied together; either fault
# pulls CHG_OK low, turning Q1 off, then R16 drives /CE high (charge off).
add("battery_charging", "U6", "WINDOW", "TLV7042DDFR", {1: "CHG_OK", 2: "HOT_REF", 3: "TS_MR", 4: "GND", 5: "COLD_REF", 6: "TS_MR", 7: "CHG_OK", 8: "CHG_IN"}, "TLV7042DDFR")
two("battery_charging", "C12", "C", "100nF 16V X7R", "CHG_IN", "GND")
two("battery_charging", "R11", "R", "432k 1%", "CHG_IN", "HOT_REF")
two("battery_charging", "R12", "R", "24.9k 1%", "HOT_REF", "GND")
two("battery_charging", "R13", "R", "365k 1%", "CHG_IN", "COLD_REF")
two("battery_charging", "R14", "R", "49.9k 1%", "COLD_REF", "GND")
two("battery_charging", "R15", "R", "100k 1%", "CHG_IN", "CHG_OK")
two("battery_charging", "R16", "R", "47k 1%", "CHG_IN", "CHG_CE_N")
add("battery_charging", "Q1", "BSS138", "BSS138P", {1: "CHG_OK", 2: "GND", 3: "CHG_CE_N"}, "BSS138P,215")
add("battery_charging", "Q2", "BSS138", "BSS138P", {1: "CHARGE_INHIBIT", 2: "GND", 3: "CHG_OK"}, "BSS138P,215")
two("battery_charging", "R17", "R", "100k 1%", "CHARGE_INHIBIT", "GND")

add("power_regulation", "U7", "BUCKBOOST", "TPS63802DLAR", {1: "SYS", 2: "MODE_MIC", 3: "GND", 4: "FB", 5: "PWR_GOOD_N", 6: "3V3", 7: "SW_L2", 8: "GND", 9: "SW_L1", 10: "SYS"}, "TPS63802DLAR")
two("power_regulation", "L1", "L", "0.47uH 5.4A at 20% drop", "SW_L1", "SW_L2", "XFL4015-471MEC")
two("power_regulation", "C13", "C", "22uF 16V X5R", "SYS", "GND", "C3216X5R1C226M160AB", "C_1206_3216Metric")
two("power_regulation", "C14", "C", "22uF 16V X5R", "3V3", "GND", "C3216X5R1C226M160AB", "C_1206_3216Metric")
two("power_regulation", "C15", "C", "22uF 16V X5R", "3V3", "GND", "C3216X5R1C226M160AB", "C_1206_3216Metric")
two("power_regulation", "R18", "R", "511k 1%", "3V3", "FB")
two("power_regulation", "R19", "R", "91k 1%", "FB", "GND")
two("power_regulation", "R20", "R", "100k 1%", "MODE_MIC", "GND")
two("power_regulation", "R21", "R", "10k 1%", "3V3", "PWR_GOOD_N")

add("battery_monitoring", "U8", "GAUGE", "MAX17048G+T10", {1: "GND", 3: "BAT", 4: "GND", 5: "FUEL_ALERT_N", 6: "GND", 7: "I2C_SCL", 8: "I2C_SDA", 9: "GND"}, "MAX17048G+T10")
two("battery_monitoring", "C16", "C", "100nF 16V X7R", "BAT", "GND")
two("battery_monitoring", "R22", "R", "10k 1%", "3V3", "FUEL_ALERT_N")

add("sos_feedback", "SW1", "SW", "SOS", {1: "SOS_N", 2: "GND", "SH": "GND"}, "KMR231GLFS")
two("sos_feedback", "R23", "R", "100k 1%", "3V3", "SOS_N")
two("sos_feedback", "C17", "C", "10nF 16V X7R", "SOS_N", "GND")
add("sos_feedback", "D3", "RGB", "APFA3010LSEEZGKQBKC", {1: "LED_R_K", 2: "3V3", 3: "LED_G_K", 4: "LED_B_K"}, "APFA3010LSEEZGKQBKC")
two("sos_feedback", "R24", "R", "1k 1%", "LED_R_K", "LED_R_N")
two("sos_feedback", "R25", "R", "330R 1%", "LED_G_K", "LED_G_N")
two("sos_feedback", "R26", "R", "330R 1%", "LED_B_K", "LED_B_N")
add("sos_feedback", "U9", "LDO3V0", "TPS7A2030PDBVR", {1: "SYS", 2: "GND", 3: "MOTOR_EN", 5: "MOTOR_3V0"}, "TPS7A2030PDBVR")
two("sos_feedback", "C18", "C", "1uF 10V X7R", "SYS", "GND")
two("sos_feedback", "C19", "C", "4.7uF 10V X7R", "MOTOR_3V0", "GND")
two("sos_feedback", "C25", "C", "1uF 10V X7R", "MOTOR_3V0", "GND")
add("sos_feedback", "M1", "MOTOR", "VC0825B002F", {1: "MOTOR_3V0", 2: "MOTOR_LOW"}, "VC0825B002F")
add("sos_feedback", "Q3", "NMOS", "AO3400A", {1: "MOTOR_GATE_R", 2: "GND", 3: "MOTOR_LOW"}, "AO3400A")
two("sos_feedback", "R27", "R", "100R 1%", "MOTOR_GATE", "MOTOR_GATE_R")
two("sos_feedback", "R28", "R", "100k 1%", "MOTOR_GATE_R", "GND")
add("sos_feedback", "D4", "DIODE", "PMEG2010EA", {1: "MOTOR_3V0", 2: "MOTOR_LOW"}, "PMEG2010EA,115")

for ref, net in (
    ("TP1", "3V3"), ("TP2", "GND"), ("TP3", "UART_TX"),
    ("TP4", "UART_RX"), ("TP5", "BOOT_N"), ("TP6", "EN"),
):
    add("programming_protection", ref, "TP", net, {1: net}, footprint="TestPoint_Pad_D1.0mm")


SHEETS = (
    "mcu_ble", "microphone", "accelerometer", "battery_charging",
    "power_regulation", "battery_monitoring", "sos_feedback", "programming_protection",
)


# Keep the exact purchasing code and the schematic/board value in sync.
from passive_parts import resolve_passives
COMPONENTS[:] = resolve_passives(COMPONENTS)
