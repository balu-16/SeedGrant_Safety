#!/usr/bin/env python3
"""Check the proposed BQ25185 TS/MR hardware charge-temperature window.

All limits are electrical corners, not a substitute for measuring thermal
coupling between the battery cell and the board-mounted thermistor.
"""

from itertools import product
from math import exp

from circuit_data import COMPONENTS


R25_OHM = 10_000
BETA_K = 3435
TS_CURRENT_A = (36.5e-6, 39.5e-6)  # BQ25185 specified min/max with adapter
CHARGER_INPUT_V = (4.25, 5.10)  # 5 V +/-5% contact supply and series diode
NTC_R25_TOL = 0.01
NTC_BETA_TOL = 0.01
REFERENCE_TOL = 0.01
COMPARATOR_UNCERTAINTY_V = 0.0205  # TLV7042 dual: 8 mV offset + half of 25 mV max hysteresis

# 1% E96 resistors; the hot threshold is deliberately below the pack's 45 C max.
def resistance(ref: str) -> float:
    component = next(c for c in COMPONENTS if c.reference == ref)
    text = component.value.split()[0]
    multiplier = {"R": 1, "k": 1_000, "M": 1_000_000}[text[-1]]
    return float(text[:-1]) * multiplier


HOT_TOP_OHM = resistance("R11")
HOT_BOTTOM_OHM = resistance("R12")
COLD_TOP_OHM = resistance("R13")
COLD_BOTTOM_OHM = resistance("R14")


def ntc_ohms(celsius: float, r25: float, beta: float) -> float:
    kelvin = celsius + 273.15
    return r25 * exp(beta * (1 / kelvin - 1 / 298.15))


def reference(voltage: float, top: float, bottom: float) -> float:
    return voltage * bottom / (top + bottom)


def corner_voltages(celsius: float) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    ntc_values = [
        ntc_ohms(celsius, R25_OHM * (1 + rt), BETA_K * (1 + bt)) * current
        for rt, bt, current in product(
            (-NTC_R25_TOL, NTC_R25_TOL),
            (-NTC_BETA_TOL, NTC_BETA_TOL),
            TS_CURRENT_A,
        )
    ]

    def ref_range(top_nominal: float, bottom_nominal: float) -> tuple[float, float]:
        values = [
            reference(v, top_nominal * (1 + tt), bottom_nominal * (1 + bt))
            for v, tt, bt in product(
                CHARGER_INPUT_V,
                (-REFERENCE_TOL, REFERENCE_TOL),
                (-REFERENCE_TOL, REFERENCE_TOL),
            )
        ]
        return min(values), max(values)

    return (
        (min(ntc_values), max(ntc_values)),
        ref_range(HOT_TOP_OHM, HOT_BOTTOM_OHM),
        ref_range(COLD_TOP_OHM, COLD_BOTTOM_OHM),
    )


def charge_certainly_blocked_at_hot(celsius: float) -> bool:
    ts, hot, _ = corner_voltages(celsius)
    return ts[1] + COMPARATOR_UNCERTAINTY_V < hot[0]


def charge_certainly_blocked_at_cold(celsius: float) -> bool:
    ts, _, cold = corner_voltages(celsius)
    return ts[0] - COMPARATOR_UNCERTAINTY_V > cold[1]


def charge_certainly_allowed(celsius: float) -> bool:
    ts, hot, cold = corner_voltages(celsius)
    return ts[0] - COMPARATOR_UNCERTAINTY_V > hot[1] and ts[1] + COMPARATOR_UNCERTAINTY_V < cold[0]


if __name__ == "__main__":
    for temp in (0, 10, 15, 25, 38, 40, 45):
        ts, hot, cold = corner_voltages(temp)
        print(
            f"{temp:2d} C: TS={ts[0]:.3f}..{ts[1]:.3f} V; "
            f"hot-ref={hot[0]:.3f}..{hot[1]:.3f} V; "
            f"cold-ref={cold[0]:.3f}..{cold[1]:.3f} V"
        )
    assert charge_certainly_blocked_at_hot(45), "45 C safety bound failed"
    assert charge_certainly_blocked_at_cold(0), "0 C safety bound failed"
    assert charge_certainly_allowed(25), "25 C normal-charge window failed"
    print("Electrical corner check: charge inhibited at 0 C/45 C and allowed at 25 C")
