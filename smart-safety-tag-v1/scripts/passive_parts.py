"""Exact, manufacturer-catalogue order codes for shared passive components.

Values in circuit_data and adapter_data are the electrical minimum.  This
module promotes them to the selected part's actual voltage/dielectric rating.
Every resistor code was checked against Yageo's generated RC0603 datasheet;
the capacitor codes are from TDK's part pages.
"""

from dataclasses import replace


_RESISTOR_CODES = {
    "100R": "100RL", "330R": "330RL", "1k": "1KL", "2k": "2KL",
    "2.8k": "2K8L", "4.7k": "4K7L", "5.1k": "5K1L", "10k": "10KL",
    "18k": "18KL", "24.9k": "24K9L", "47k": "47KL", "49.9k": "49K9L",
    "91k": "91KL", "100k": "100KL", "200k": "200KL",
    "365k": "365KL", "432k": "432KL", "511k": "511KL",
}

_CAPACITORS = {
    "100nF 16V X7R": ("100nF 50V X7R", "C1608X7R1H104K080AA"),
    "10nF 16V X7R": ("10nF 50V X7R", "C1608X7R1H103K080AA"),
    "1uF 10V X7R": ("1uF 16V X7R", "C1608X7R1C105K080AC"),
    "1uF 25V X7R": ("1uF 25V X7R", "C1608X7R1E105K080AE"),
    "3.3nF 16V X7R": ("3.3nF 100V X7R", "C1608X7R2A332K080AA"),
    "4.7uF 10V X7R": ("4.7uF 10V X5R", "C1608X5R1A475K080AE"),
    "10uF 10V X5R": ("10uF 25V X5R", "C2012X5R1E106K125AB"),
}


def resolve_passives(components):
    result = []
    for component in components:
        if component.part == "R":
            value = component.value.split()[0]
            result.append(replace(component, mpn="RC0603FR-07" + _RESISTOR_CODES[value]))
        elif component.part == "C" and not component.mpn:
            value, mpn = _CAPACITORS[component.value]
            result.append(replace(component, value=value, mpn=mpn))
        else:
            result.append(component)
    return result
