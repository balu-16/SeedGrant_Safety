# Smart Safety Tag V1 — Prototype Bring-up

Record the board revision, firmware hash, battery lot, instruments, ambient temperature and measured results for every assembled prototype. The procedure below specifies tests to perform; it is not a record of tests already completed.

## Assembly and first power

1. Inspect the board against the front/back assembly PDFs. Confirm IC orientation, RGB common anode, diode cathodes, the motor flyback diode, connector polarity and hidden-pad solder joints. Check that the microphone's 0.40 mm unplated hole is clear. Keep the battery and motor disconnected initially.
2. With power removed, check for a persistent short from BAT, SYS, 3V3, MIC_3V0 and CHG_RAW to GND. Allow capacitors to charge during resistance measurements. Verify the battery's actual lead polarity separately; do not infer it from the plastic connector.
3. Apply 3.7 V to J1/BAT from a current-limited battery simulator, initially limiting current to 50 mA and holding EN/TP6 low. Verify SYS and 3V3 polarity and check for heating. Increase the available current to 1 A before releasing EN, since an ESP32 boot can exceed the initial limit. Use a short, low-resistance supply connection.
4. Measure 3V3 at TP1 and at U1's supply. The nominal value is 3.308 V; the divider/reference arithmetic range is 3.220–3.398 V before ripple and load effects. Capture startup and BLE transmission with an oscilloscope. Reject excessive droop, oscillation, brownouts or an overvoltage excursion beyond component ratings.
5. Check MIC_3V0 and MOTOR_3V0 while disabled, then while enabled by the test firmware. Their nominal enabled voltage is 3.0 V. Test the regulator from 3.0 to 4.2 V BAT, including a 500 mA 3V3 load step, and repeat with motor startup. Log rail minima, ripple, temperatures and supply current; confirm the fitted capacitors' effective capacitance and converter stability.

## Programming and peripheral tests

Use the six test pads and the connection sequence in [gpio-map.md](gpio-map.md). Build/flash commands and prebuilt image locations are in [the firmware README](../firmware/hardware-tests/README.md). UART logic must be 3.3 V. The tag has manual GPIO0/EN boot control; the charging adapter does not provide a programming USB connection.

| Test | Procedure and expected observation |
| --- | --- |
| Boot and memory | Reset with GPIO0 released. Capture the 115200 baud log. Confirm ESP32-S3 boot, 4 MB flash configuration, PSRAM initialization/memory test, and no reset loop. A successful build does not establish successful board boot. |
| I²C | Check 400 kHz bus waveforms and idle-high SDA/SCL. LIS2DW12 is at 0x18 and MAX17048 at 0x36. Resolve missing devices, poor rise times or bus errors before continuing. |
| Accelerometer | Require WHO_AM_I = 0x44. The test configures 50 Hz low-power sampling and prints signed raw XYZ periodically. Rotate the board through all axes and verify readings change with gravity; these are raw counts, not calibrated g values. |
| Fuel gauge | Compare logged VCELL with a calibrated meter at BAT at several voltages. SOC is an algorithm estimate; check its trend during a complete charge/discharge cycle with the selected pack. Validate alert threshold and recovery separately before relying on GPIO5. |
| RGB LED | The boot test briefly lights red, green and blue. Verify color, polarity and current through each resistor, then check visibility through the proposed enclosure. |
| Motor | After rail checks, attach and secure the motor. Verify one approximately 120 ms pulse at boot and on SOS press. Measure startup current, MOTOR_3V0, MOSFET drain transient and simultaneous 3V3 droop. Confirm acceptable behavior at low battery voltage. |
| SOS | Press/release SW1 repeatedly, including slow and brief presses. Require the expected UART events and feedback pulse, with no events while untouched. Test with the button actuator fitted. This application polls the input; the separate wake test below is still required. |
| Microphone | During boot, four captures report sample count and mean-square PCM amplitude. Speak/tap during capture and compare with quiet conditions; reset to repeat. Verify 2.048 MHz at the PDM clock, nominal 3.0 V supply and valid data. DMA completion alone cannot prove audio sensitivity, signal quality or keyword accuracy. |
| BLE | Scan for `SafetyTag-HW` using a BLE client, connect, disconnect and confirm advertising resumes. Log range/RSSI and reconnect behavior. The test advertises standard GAP/GATT services; it does not provide a custom SOS characteristic or send a phone emergency message. |

## Charging and temperature interlock

First test the adapter alone from a dedicated, regulated 5 V USB-C supply rated for at least 1 A. The adapter is power-only, has separate 5.1 kΩ CC pull-downs and does not enumerate or request USB-PD. Measure the pogo polarity and unloaded voltage. Load the output gradually; compare current limiting with the calculated 0.754 A nominal, including device tolerance. Test short response and recovery using a controlled fixture before mating the tag.

Verify the keyed mechanical fixture before connecting a cell: tag J2.1 must mate to adapter P1/+5 V, and J2.2 to P2/GND. Back-view drawings mirror the apparent left/right arrangement. With the tag on a simulator, confirm the reverse diode blocks a reversed 5 V contact input and verify the protected source responds to shorted contacts. Record leakage and heating. Perform powered and unpowered ESD tests with a suitable test setup before claiming an ESD rating.

For charging measurements, use a battery simulator able to **sink** charging current; an ordinary source-only bench supply is unsuitable. At room temperature, check approximately 150 mA nominal cell charging when the system load permits, 4.2 V charge regulation, taper/termination, status outputs and transitions when adapter power is removed. Sweep external power from 4.75 to 5.25 V at the adapter and measure the actual tag IN voltage after contact/diode loss. Verify operation during BLE and vibration, including input-current limiting and battery supplement. Log charger and enclosure temperatures at low cell voltage and high system load.

Exercise the temperature interlock first with a resistance box in place of RT1 and a simulator on BAT. Approximate nominal B3435 values are 28.7 kΩ at 0 °C, 10 kΩ at 25 °C and 4.85 kΩ at 45 °C. Measure TS_MR, HOT_REF, COLD_REF, CHG_OK and /CE while sweeping resistance in both directions. Require inhibited charging at modeled 0 °C/45 °C limits and allowed charging near 25 °C; record actual hysteresis and thresholds. Test an open and short RT1 and GPIO16 inhibition. A sustained TS/MR short can invoke the charger's additional reset/factory functions; characterize this first without a real cell. Restore all normal connections before attaching the pack.

After electrical checks, bond RT1 thermally to the protected pack through the specified insulating interface. Use independent cell and RT1 temperature probes to assess thermal lag in the assembled enclosure. Charging must stay within the pack's 0–45 °C specification. The resistor calculation does not establish sensor contact, thermal lag or a pack-temperature guarantee.

## Wake, runtime, RF and mechanical qualification

The included application remains awake. To verify wake behavior, use a separate test build that configures the LIS2DW12 interrupt generator and latch, assigns its RTC GPIO wake source and GPIO1's active-low SOS wake, disables microphone/motor/LED outputs, then enters sleep. Confirm the intended interrupt polarity, clear the latched interrupt after wake, log the wake reason and measure sleeping battery current. Repeat motion/SOS wake with the production button filter, cell voltage limits and enclosure. No wake result is claimed until this test runs on hardware.

Measure battery-side current and runtime with final BLE intervals, phone connection, audio model, alarm duty cycle and battery cutoff. Continuous keyword inference keeps the audio/MCU path running; it cannot use the deep-sleep budget in [power-budget.md](power-budget.md). Evaluate the eventual keyword model for missed detections, false triggers, background noise and voice variation before using it for a safety function.

Check BLE range with the battery, motor, clip, magnets and enclosure in their final positions. Keep metal and the battery outside the module's antenna keepout. Inspect cell insulation, pouch pressure, wire strain relief, pogo compression, contact wear, button accessibility and microphone seal. Verify any intended environmental rating through actual enclosure tests. Save measurements and pass/fail decisions in [verification.md](verification.md) before a production release.
