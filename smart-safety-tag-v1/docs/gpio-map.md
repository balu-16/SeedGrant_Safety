# Smart Safety Tag V1 — GPIO and Programming Map

Generated from `hardware/board-interface.json` and checked against the ESP32-S3 module symbol and schematic net definitions. Change that source and rerun `python3 scripts/generate_gpio_header.py` when changing pins.

| Function | GPIO | Module pad | Schematic net |
| --- | --- | --- | --- |
| sos n | 1 | 5 | SOS_N |
| accelerometer int1 | 2 | 6 | ACC_INT1 |
| accelerometer int2 | 4 | 8 | ACC_INT2 |
| fuel alert n | 5 | 9 | FUEL_ALERT_N |
| i2c sda | 6 | 10 | I2C_SDA |
| i2c scl | 7 | 11 | I2C_SCL |
| pdm clk | 8 | 12 | PDM_CLK |
| pdm data | 9 | 13 | PDM_DATA |
| motor gate | 10 | 14 | MOTOR_GATE |
| led red n | 11 | 15 | LED_R_N |
| led green n | 12 | 16 | LED_G_N |
| led blue n | 13 | 17 | LED_B_N |
| charger stat1 n | 14 | 18 | CHG_STAT1_N |
| charger stat2 n | 15 | 19 | CHG_STAT2_N |
| charge inhibit | 16 | 20 | CHARGE_INHIBIT |
| regulator mode | 17 | 21 | MODE_MIC |
| motor supply enable | 18 | 22 | MOTOR_EN |
| uart0 tx | 43 | 39 | UART_TX |
| uart0 rx | 44 | 40 | UART_RX |
| boot | 0 | 4 | BOOT_N |

SOS is active low; accelerometer interrupt polarity depends on its register configuration. GPIO1, GPIO2, GPIO4 and GPIO5 support RTC wake. The test application polls these inputs and does not configure deep-sleep wake.

The common-anode RGB LED is active low. MOTOR_GATE and MOTOR_EN are active high. MODE_MIC enables the microphone LDO and selects regulator PWM mode; wait for the microphone supply to settle before starting its clock. Drive PDM_CLK low before switching off the microphone. CHARGE_INHIBIT high blocks charging; the analog temperature interlock also acts independently.

GPIO0 is the boot strap. GPIO3, GPIO45 and GPIO46 are not assigned to these peripherals. GPIO26 is reserved by the N4R2 module's PSRAM and is left unconnected. UART0 uses GPIO43 TX and GPIO44 RX.

| Test pad | Signal | PCB front-view coordinate, mm |
| --- | --- | --- |
| TP1 | 3V3 | (103.00, 111.00) |
| TP2 | GND | (103.00, 114.00) |
| TP3 | TX | (103.00, 117.00) |
| TP4 | RX | (103.00, 120.00) |
| TP5 | GPIO0 | (103.00, 123.00) |
| TP6 | EN | (103.00, 126.00) |

Use a 3.3 V logic USB-UART adapter: adapter TX to TP4/RX, adapter RX to TP3/TX, and ground to TP2. Hold TP5/GPIO0 low, pulse TP6/EN low, then release EN to enter the ROM serial bootloader. Release GPIO0 after the bootloader starts. After flashing, pulse EN with GPIO0 released.

TP1 is the board's 3V3 rail. When powering through TP1, disconnect the battery and charging adapter and use a regulated 3.3 V, current-limited bench supply. Most USB-UART adapters cannot supply the MCU's peak current. Keep their power pin disconnected when the tag has another power source.

Audio uses 16000 Hz, 16-bit mono PCM with a 2.048 MHz PDM clock.
