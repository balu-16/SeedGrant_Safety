#!/usr/bin/env python3
"""Audit MCU pad/GPIO assignments and generate the firmware's single pin map."""

import json
from pathlib import Path

from sexpdata import Symbol as S

from circuit_data import MCU_NETS
from generate_schematic import get_child, mcu_symbol


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "hardware" / "board-interface.json"
OUTPUT = ROOT / "firmware" / "hardware-tests" / "main" / "board_pins.h"
DOCUMENT = ROOT / "docs" / "gpio-map.md"

NET_NAMES = {
    "sos_n": "SOS_N", "accelerometer_int1": "ACC_INT1",
    "accelerometer_int2": "ACC_INT2", "fuel_alert_n": "FUEL_ALERT_N",
    "i2c_sda": "I2C_SDA", "i2c_scl": "I2C_SCL",
    "pdm_clk": "PDM_CLK", "pdm_data": "PDM_DATA",
    "motor_gate": "MOTOR_GATE", "led_red_n": "LED_R_N",
    "led_green_n": "LED_G_N", "led_blue_n": "LED_B_N",
    "charger_stat1_n": "CHG_STAT1_N", "charger_stat2_n": "CHG_STAT2_N",
    "charge_inhibit": "CHARGE_INHIBIT", "regulator_mode": "MODE_MIC",
    "motor_supply_enable": "MOTOR_EN", "uart0_tx": "UART_TX",
    "uart0_rx": "UART_RX", "boot": "BOOT_N",
}


def pin_names():
    result = {}
    for unit in mcu_symbol():
        if not isinstance(unit, list) or unit[0] != S("symbol"):
            continue
        for pin in unit:
            if isinstance(pin, list) and pin[0] == S("pin"):
                result[str(get_child(pin, "number")[1])] = str(get_child(pin, "name")[1])
    return result


def main():
    interface = json.loads(INPUT.read_text())
    names = pin_names()
    if set(interface["gpio"]) != set(NET_NAMES):
        raise ValueError(f"GPIO list mismatch: {set(interface['gpio']) ^ set(NET_NAMES)}")
    for key, gpio in interface["gpio"].items():
        matching = [pad for pad, net in MCU_NETS.items() if net == NET_NAMES[key]]
        expected_pin_name = {"uart0_tx": "TXD0", "uart0_rx": "RXD0"}.get(key, f"IO{gpio}")
        if len(matching) != 1 or names[str(matching[0])] != expected_pin_name:
            raise ValueError(f"{key}: JSON GPIO{gpio}, schematic pad {matching}")
    lines = [
        "/* Generated from hardware/board-interface.json and audited against the MCU symbol. */",
        "#pragma once", "",
    ]
    for key, gpio in interface["gpio"].items():
        lines.append(f"#define PIN_{key.upper()} {gpio}")
    lines += [
        "", f"#define AUDIO_PCM_RATE_HZ {interface['audio']['pcm_sample_rate_hz']}",
        f"#define AUDIO_PDM_CLOCK_HZ {interface['audio']['pdm_clock_hz']}", "",
    ]
    if interface["audio"]["pcm_sample_rate_hz"] * 128 != interface["audio"]["pdm_clock_hz"]:
        raise ValueError("PDM clock requires the 128x I2S decimation setting")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines))
    document = [
        "# Smart Safety Tag V1 — GPIO and Programming Map", "",
        "Generated from `hardware/board-interface.json` and checked against the "
        "ESP32-S3 module symbol and schematic net definitions. Change that source "
        "and rerun `python3 scripts/generate_gpio_header.py` when changing pins.", "",
        "| Function | GPIO | Module pad | Schematic net |",
        "| --- | --- | --- | --- |",
    ]
    for key, gpio in interface["gpio"].items():
        module_pad = next(pad for pad, net in MCU_NETS.items() if net == NET_NAMES[key])
        document.append(f"| {key.replace('_', ' ')} | {gpio} | {module_pad} | {NET_NAMES[key]} |")
    document += [
        "", "SOS is active low; accelerometer interrupt polarity depends on its register "
        "configuration. GPIO1, GPIO2, GPIO4 and GPIO5 support RTC wake. The test "
        "application polls these inputs and does not configure deep-sleep wake.", "",
        "The common-anode RGB LED is active low. MOTOR_GATE and MOTOR_EN are active "
        "high. MODE_MIC enables the microphone LDO and selects regulator PWM mode; "
        "wait for the microphone supply to settle before starting its clock. Drive "
        "PDM_CLK low before switching off the microphone. CHARGE_INHIBIT high blocks "
        "charging; the analog temperature interlock also acts independently.", "",
        "GPIO0 is the boot strap. GPIO3, GPIO45 and GPIO46 are not assigned to these "
        "peripherals. GPIO26 is reserved by the N4R2 module's PSRAM and is left "
        "unconnected. UART0 uses GPIO43 TX and GPIO44 RX.", "",
        "| Test pad | Signal | PCB front-view coordinate, mm |",
        "| --- | --- | --- |",
    ]
    for index, signal in enumerate(interface["programming_pads"], start=1):
        document.append(f"| TP{index} | {signal} | (103.00, {108 + 3 * index:.2f}) |")
    document += [
        "", "Use a 3.3 V logic USB-UART adapter: adapter TX to TP4/RX, adapter RX to "
        "TP3/TX, and ground to TP2. Hold TP5/GPIO0 low, pulse TP6/EN low, then "
        "release EN to enter the ROM serial bootloader. Release GPIO0 after the "
        "bootloader starts. After flashing, pulse EN with GPIO0 released.", "",
        "TP1 is the board's 3V3 rail. When powering through TP1, disconnect the "
        "battery and charging adapter and use a regulated 3.3 V, current-limited "
        "bench supply. Most USB-UART adapters cannot supply the MCU's peak current. "
        "Keep their power pin disconnected when the tag has another power source.", "",
        f"Audio uses {interface['audio']['pcm_sample_rate_hz']} Hz, "
        f"{interface['audio']['pcm_bits']}-bit mono PCM with a "
        f"{interface['audio']['pdm_clock_hz'] / 1e6:.3f} MHz PDM clock.", "",
    ]
    DOCUMENT.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENT.write_text("\n".join(document))
    print(f"Audited {len(NET_NAMES)} GPIO assignments; generated firmware header and GPIO document")


if __name__ == "__main__":
    main()
