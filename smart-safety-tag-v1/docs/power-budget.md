# Smart Safety Tag V1 — Power Budget

These are calculations and planning estimates. No prototype current, runtime, ripple or temperature measurement has been recorded.

The power path is `5 V adapter → protected pogo output → tag reverse diode → BQ25185 IN/SYS → TPS63802 → 3V3`. The protected battery connects to BAT. The microphone takes 3.0 V from 3V3 through its switched LDO. The motor takes 3.0 V from SYS through a separate switched LDO.

The regulator's nominal output is `0.5 × (1 + 511/91) = 3.308 V`. With 1% divider resistors and 1% PWM reference accuracy, the unloaded arithmetic limits are approximately 3.220–3.398 V. This calculation excludes feedback input bias, routing loss, ripple and load steps. Measure 3V3 at U1, including during BLE transmission and motor startup. [TPS63802 datasheet](https://www.ti.com/lit/ds/symlink/tps63802.pdf).

| Load or condition | Value used | Consequence |
| --- | --- | --- |
| ESP32-S3 BLE transmit | 189 mA at 0 dBm; 204 mA at 9 dBm; 340 mA at 20 dBm | RF peaks determine power integrity; average BLE consumption depends on firmware and connection interval. [Espressif datasheet](https://documentation.espressif.com/esp32-s3-mini-1_mini-1u_datasheet_en.pdf). |
| 3V3 prototype load test | 500 mA | Includes margin for the MCU, audio processing and peripherals. It is a test allocation, not a measured operating current. |
| Motor startup | 120 mA on SYS through the 3.0 V LDO | Combine with BLE load steps. The motor rail can enter dropout near the battery discharge limit. [Motor specification](https://www.vybronics.com/wp-content/uploads/datasheet-files/Vybronics-VC0825B002F-datasheet.pdf). |
| Discharge-end battery load | About 0.77 A | `3.3 × 0.5 / (3.0 × 0.85) + 0.120`, using an assumed 85% converter efficiency. Compare against actual pack/PCM behavior and measure wiring/PCB loss. |
| Charge current | 150 mA nominal, approximately 0.375 C | A 400 mAh pack requires at least 2.67 hours at this constant current; taper and system loading increase the charging time. [BQ25185 datasheet](https://www.ti.com/lit/ds/symlink/bq25185.pdf). |
| Charger input limit | 500 mA | The power path can reduce charging or draw battery supplement during heavy operation. |
| Adapter current limit | 0.754 A nominal | `2000 / 2800 + 0.04`. Provides margin above the charger's input limit; short-circuit behavior must be measured. [TPS2595 datasheet](https://www.ti.com/lit/ds/symlink/tps2595.pdf). |

The regulator needs at least 4 µF effective VIN capacitance and 7 µF effective VOUT capacitance for this output voltage. **C13 is 22 µF/16 V in 1206**, the same C3216X5R1C226M160AB as C14/C15. The initial C2012X5R1E106K125AB 10 µF/25 V 0805 part was rejected at C13 after reviewing TDK's DC-bias curve: its typical capacitance is only about 5 µF near the charger's 4.5 V SYS level, leaving inadequate margin after tolerance and temperature. The BQ25185's stated ±2% SYS regulation accuracy gives a 4.59 V arithmetic upper value under its specified test condition. [BQ25185](https://www.ti.com/lit/ds/symlink/bq25185.pdf), [TDK 10 µF manufacturer information](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012X5R1E106K125AB).

For the revised 22 µF input, a design allowance of 50% DC-bias loss, 20% negative initial tolerance and 15% negative temperature change gives `22 × 0.50 × 0.80 × 0.85 = 7.48 µF`. C14/C15 together give 14.96 µF under those allowances, above the required 7 µF. TI's output-filter selection guidance anticipates 20% tolerance and up to 50% bias derating. The 50% figure is a design allowance, not a manufacturer's guaranteed minimum; qualify the exact fitted capacitor lot at actual rail voltage and temperature, including aging, and confirm startup, stability and load steps on hardware. [TPS63802](https://www.ti.com/lit/ds/symlink/tps63802.pdf), [TDK 22 µF information](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X5R1C226M160AB).

At the lowest normal contact supply, headroom is `4.75 V − contact/cable loss − series-diode drop`. As an example, 0.10 V wiring/contact loss and 0.40 V diode drop leave 4.25 V at IN. This is an engineering scenario, not a guaranteed measured path. Verify charge termination at the low supply limit and maximum system load. Charging a low cell at 150 mA can dissipate roughly `(VIN − VBAT) × ICHG` in the linear path; thermal regulation and enclosure heating require a temperature test.

Runtime estimates below assume 400 mAh nominal and **320 mAh usable**, allowing a planning reserve for aging, temperature, voltage cutoff and conversion loss. The average currents are proposed battery-side budgets to be replaced by measurements.

| Operating mode | Assumed average battery current | Calculated runtime |
| --- | --- | --- |
| Motion/SOS wake standby, BLE disconnected, microphone off | 0.15 mA | 89 days |
| Light-sleep standby with periodic activity | 0.8 mA | 16.7 days |
| BLE monitoring, microphone off | 8 mA | 40 hours |
| Continuous audio and keyword processing | 80 mA | 4 hours |
| Sustained emergency activity and repeated vibration | 170 mA | 1.9 hours |

These figures are not battery-life claims. BLE scheduling, CPU clock, PSRAM use, wake rate, keyword model and feedback duty cycle can change them substantially. A connected BLE session must be measured with the final phone software. The included test firmware keeps the MCU awake and periodically logs readings; it does not implement these power-saving modes.
