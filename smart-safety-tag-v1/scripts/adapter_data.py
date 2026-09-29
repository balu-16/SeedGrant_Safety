"""Protected USB-C charging fixture, upstream of the exposed pogo contacts."""

from circuit_data import Component
from parts import PARTS as TAG_PARTS, Part, p


PARTS = {key: TAG_PARTS[key] for key in ("R", "C", "ESD", "TP")}
PARTS.update({
    "USBC": Part("USB_C_6P", "J", (
        p("A5", "CC1"), p("B5", "CC2"),
        p("A9", "VBUS", "power_out"), p("B9", "VBUS"),
        p("A12", "GND", "power_out"), p("B12", "GND"), p("SH", "SHELL"),
    ), "USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal",
        "https://gct.co/connector/usb4125"),
    "EFUSE": Part("TPS259530", "U", (
        p(1, "dVdt"), p(2, "EN/UVLO"), p(3, "IN", "power_in"),
        p(4, "IN", "power_in"), p(5, "OUT", "power_out", "R"),
        p(6, "FLT", "open_collector", "R"), p(7, "ILM"),
        p(8, "GND", "power_in"), p(9, "EP", "power_in"),
    ), "Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm",
        "https://www.ti.com/lit/ds/symlink/tps2595.pdf"),
    "POGO": Part("PogoPin_0900_1", "P", (p(1, "CONTACT"),),
                 "PogoPin_MillMax_0900-1",
                 "https://www.mill-max.com/sites/default/files/external/catalog/2021-02/023-028.pdf"),
})


def c(ref, part, value, nets, mpn="", footprint="", notes=""):
    return Component(ref, part, value, "adapter", {str(k): v for k, v in nets.items()},
                     mpn, footprint, notes)


COMPONENTS = [
    c("J1", "USBC", "USB-C 5V input", {"A5": "CC1", "B5": "CC2",
                                  "A9": "USB_5V", "B9": "USB_5V",
                                  "A12": "GND", "B12": "GND", "SH": "GND"}, "USB4125-GF-A"),
    c("R1", "R", "5.1k 1%", {1: "CC1", 2: "GND"}),
    c("R2", "R", "5.1k 1%", {1: "CC2", 2: "GND"}),
    c("D1", "ESD", "TPD1E10B06DYAR", {1: "USB_5V", 2: "GND"}, "TPD1E10B06DYAR"),
    c("C1", "C", "1uF 25V X7R", {1: "USB_5V", 2: "GND"}),
    c("U1", "EFUSE", "TPS259530DSGR", {1: "DV_DT", 2: "EF_EN",
                                        3: "USB_5V", 4: "USB_5V",
                                        5: "PROTECTED_5V", 7: "ILIM",
                                        8: "GND", 9: "GND"}, "TPS259530DSGR"),
    c("C2", "C", "3.3nF 16V X7R", {1: "DV_DT", 2: "GND"}),
    c("R3", "R", "200k 1%", {1: "USB_5V", 2: "EF_EN"}),
    c("R4", "R", "100k 1%", {1: "EF_EN", 2: "GND"}),
    c("R5", "R", "2.8k 1%", {1: "ILIM", 2: "GND"}),
    c("C3", "C", "1uF 10V X7R", {1: "PROTECTED_5V", 2: "GND"}),
    c("D2", "ESD", "TPD1E10B06DYAR", {1: "PROTECTED_5V", 2: "GND"}, "TPD1E10B06DYAR"),
    c("P1", "POGO", "TAG +5V", {1: "PROTECTED_5V"}, "0900-1-15-20-75-14-11-0"),
    c("P2", "POGO", "TAG GND", {1: "GND"}, "0900-1-15-20-75-14-11-0"),
    c("TP1", "TP", "PROTECTED_5V", {1: "PROTECTED_5V"}),
    c("TP2", "TP", "GND", {1: "GND"}),
]


from passive_parts import resolve_passives
COMPONENTS[:] = resolve_passives(COMPONENTS)
