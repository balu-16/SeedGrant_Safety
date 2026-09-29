# Smart Safety Tag Hardware Tests

Modular bring-up application for the ESP32-S3-MINI-1-N4R2. It builds with ESP-IDF **v5.5**, targets `esp32s3`, configures 4 MB flash and 2 MB quad PSRAM, and enables the PSRAM boot memory test. The GPIO header is generated from the hardware interface and audited against the schematic's module pin map.

From the project root:

```sh
python3 -m pip install -r scripts/requirements.txt
python3 scripts/generate_gpio_header.py
cd firmware/hardware-tests
# Activate your installed ESP-IDF v5.5 environment before these commands.
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

Replace the serial port for your system. Enter the ROM bootloader manually using GPIO0 and EN as described in [gpio-map.md](../../docs/gpio-map.md); the six-pad interface does not include automatic DTR/RTS circuitry. Use 3.3 V UART logic and a supply capable of MCU current peaks. For battery/rail checks, follow [bring-up.md](../../docs/bring-up.md) first.

The build completed with ESP-IDF v5.5 (`8c750b088c7cd857d079c0eeb495da199b359461`) and GCC 14.2.0. Prebuilt bootloader, partition table and application images plus hashes are in `prebuilt/`. These images have **not been flashed to a physical tag**. To use the images with the ESP-IDF environment active, enter `prebuilt/` and run:

```sh
python -m esptool --chip esp32s3 --port /dev/ttyUSB0 --baud 460800 write_flash @flash_args
```

After flashing, release GPIO0 and pulse EN to boot. The UART monitor is 115200 baud.

| Module | Behavior |
| --- | --- |
| `board_main.c` | Initializes outputs/buses, reports test status and periodically logs inputs. |
| `i2c_bus.c` | 400 kHz I²C master with external 4.7 kΩ pull-ups. |
| `accelerometer_test.c` | Checks LIS2DW12 identity, enables 50 Hz low-power data and logs raw XYZ. |
| `fuel_gauge_test.c` | Reads MAX17048 battery voltage and estimated SOC. |
| `feedback_test.c` | Brief RGB sequence and approximately 120 ms motor pulse. |
| `sos_test.c` | Polls the filtered active-low SOS input and logs transitions/feedback. |
| `microphone_test.c` | Enables the mic supply/PWM mode, captures four 16 kHz mono PCM windows, logs amplitude statistics and switches the microphone off. |
| `ble_test.c` | Advertises `SafetyTag-HW`, accepts a BLE connection and resumes advertising after disconnect. |

The GPIO map and PCM/PDM clock settings are in `main/board_pins.h`; regenerate it from `hardware/board-interface.json` when changing the schematic. A logged PASS means the corresponding API/read check completed. Inspect readings and perform the physical observations in the bring-up procedure to establish sensor/audio/radio function.

This application provides peripheral checks. Keyword inference, a custom emergency BLE service, phone/GPS messaging, charging policy, calibrated battery alerts and sleep/wake firmware remain application work. Continuous keyword detection is not implemented, and no physical board, wake, RF, runtime or acoustic measurement is implied by the successful compilation.
