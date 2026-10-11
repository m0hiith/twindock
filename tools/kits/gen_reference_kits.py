"""Generates the reference-design kits in hardware/kits/*.json (FACTORY_PROMPTS.md K2).

Run from the repo root. The JSON files are the source of truth; this script only saves typing.
Evidence policy: Silicon Labs boards and their links were checked on silabs.com (2026-10-11 search);
BRD2605A pad names come from UG581 Table 3.2 (already in fl01_sensor_pack.json). Everything about
third-party parts (part numbers, addresses, supply ranges, sizes, costs) is from memory and marked
"unverified"; EFR32 dev-kit pad assignments are unverified too.
"""
import json
import sys
from pathlib import Path

OUT = Path("hardware/kits")

UNV = "unverified"
SILABS = {
    "siwx917": dict(part_number="SIWX917-DK2605A (board BRD2605A)", manufacturer="Silicon Labs", unit_cost_usd=40.0,
                    link="https://www.silabs.com/development-tools/wireless/wi-fi/siwx917-dk2605a-wifi-6-bluetooth-le-soc-dev-kit",
                    source="silabs.com", chip="SiWG917M111MGTBA", board="BRD2605A", label="SiWx917", sub="BRD2605A",
                    desc="SiWx917 Wi-Fi 6 + Bluetooth LE dev kit (SiWG917M111MGTBA SoC, Qwiic connector, 26 breakout pads)."),
    "xg24": dict(part_number="xG24-DK2601B", manufacturer="Silicon Labs", unit_cost_usd=None,
                 link="https://www.silabs.com/wireless/zigbee/efr32mg24-series-2-socs", source="silabs.com",
                 chip="EFR32MG24B310F1536IM48", board="BRD2601B", label="EFR32MG24", sub="xG24 Dev Kit",
                 desc="EFR32xG24 dev kit: EFR32MG24 SoC for Thread / Matter / Zigbee and Bluetooth LE."),
    "xg27": dict(part_number="xG27-DK2602A (board BRD2602A)", manufacturer="Silicon Labs", unit_cost_usd=None,
                 link="https://www.silabs.com/development-tools/wireless/efr32xg27-development-kit", source="silabs.com",
                 chip="EFR32BG27C140F768IM40", board="BRD2602A", label="EFR32BG27", sub="xG27 Dev Kit",
                 desc="EFR32xG27 dev kit: EFR32BG27 Bluetooth LE SoC, CR2032 holder, external battery connector."),
    "bg22": dict(part_number="SLTB010A (EFR32BG22 Thunderboard)", manufacturer="Silicon Labs", unit_cost_usd=None,
                 link="https://www.silabs.com/wireless/bluetooth/efr32bg22-series-2-socs", source="silabs.com",
                 chip="EFR32BG22", board="BRD4184", label="EFR32BG22", sub="Thunderboard",
                 desc="EFR32BG22 Thunderboard: Bluetooth LE SoC, CR2032 holder, switches between USB and battery power."),
}

# BRD2605A expansion pads (UG581 Table 3.2), number -> net. Left column odd, right column even.
PADS = {1: "GND", 3: "GPIO_25", 5: "GPIO_26", 7: "GPIO_27", 9: "GPIO_28", 11: "GPIO_29", 13: "GPIO_30", 15: "ULP_GPIO_7",
        17: "BOARD_ID_SCL", 19: "BOARD_ID_SDA", 21: "GPIO_6", 23: "GPIO_10", 25: "GPIO_12",
        2: "VMCU", 4: "ULP_GPIO_1", 6: "ULP_GPIO_2", 8: "ULP_GPIO_8", 10: "ULP_GPIO_10", 12: "ULP_GPIO_11", 14: "ULP_GPIO_9",
        16: "ULP_GPIO_6", 18: "5V", 20: "3V3", 22: "GPIO_11", 24: "GPIO_7", 26: "GND"}
BW, BH = 30.4, 55.0


def pad_xy(n: int) -> tuple[float, float, str]:
    left = n % 2 == 1
    i = (n - 1) // 2
    y = BH * (0.265 + i * (0.81 - 0.265) / 12)
    return (round(BW * 0.067, 2), round(y, 2), "left") if left else (round(BW * 0.91, 2), round(y, 2), "right")


def hole(x, y, d=2.8):
    return {"family": "pcb", "variant": "hole", "x_mm": round(x, 2), "y_mm": round(y, 2), "w_mm": d, "h_mm": d}


def silk(x, y, text, size=1.4):
    return {"family": "pcb", "variant": "silk", "label": text, "x_mm": x, "y_mm": y, "w_mm": len(text) * size * 0.62, "h_mm": size}


class Kit:
    def __init__(self, kit: dict, brain: str):
        self.k = {"version": 1, "kit": kit, "board": SILABS[brain]["board"], "sdk": "reference design (not built)",
                  "buses": [], "parts": [], "connections": [], "bom": [], "boot_sequence": [], "open_questions": []}
        self.brain = brain
        self.parts: dict[str, dict] = {}

    # ---- buses, parts, pins
    def bus(self, id, name, kind, v, controller=None, evidence=UNV, notes=None):
        b = {"id": id, "name": name, "kind": kind, "controller": controller, "voltage_v": v, "evidence": evidence}
        if notes:
            b["notes"] = notes
        self.k["buses"].append(b)

    def part(self, id, name, pn, kind, drawing, pins, caption, *, bus=None, address=None, supply=None, supplied_from=None,
             measures="", use="", bom=None, notes=None):
        p = {"id": id, "name": name, "part_number": pn, "quantity": 1, "location": "external", "kind": kind, "bus": bus,
             "address": address, "supplied_from": supplied_from, "enable_pin": None, "sdk_driver": None, "sdk_example": None,
             "measures": measures, "forklift_use": use, "caption": caption, "topics": [], "outline_pct": None,
             "status": "planned", "pins": pins, "drawing": drawing}
        if address:
            p["address_evidence"] = UNV
        if supply:
            p["supply"] = {"min_v": supply[0], "max_v": supply[1]}
        if notes:
            p["notes"] = notes
        self.k["parts"].append(p)
        self.parts[id] = p
        if bom is not False:
            b = bom or {}
            self.k["bom"].append({"id": id, "part_number": b.get("pn", pn), "manufacturer": b.get("mfr", UNV),
                                  "description": b.get("desc", name), "quantity": b.get("qty", 1),
                                  "unit_cost_usd": b.get("cost"), "link": b.get("link"), "source": b.get("source", UNV),
                                  "covers": [id] + b.get("also", [])})
        return p

    def wire(self, a, b, signal, color, medium="wire", bus=None):
        cid = (a + "_" + b).replace(".", "_").replace("+", "p").replace("-", "n").lower()
        self.k["connections"].append({"id": cid, "from": a, "to": b, "signal": signal, "bus": bus, "medium": medium,
                                      "wire_color": color, "status": "planned", "evidence": UNV})

    def qwiic(self, a, b, power_bus="vmcu", i2c="i2c"):
        for sig, col, bus in (("GND", "black", power_bus), ("3V3", "red", power_bus), ("SDA", "blue", i2c), ("SCL", "yellow", i2c)):
            self.wire(f"{a}.{sig}", f"{b}.{sig}", sig, col, "qwiic_cable", bus)

    def question(self, id, q, blocks):
        self.k["open_questions"].append({"id": id, "question": q, "blocks": blocks})

    def save(self):
        f = OUT / f"{self.k['kit']['id']}.json"
        f.write_text(json.dumps(self.k, indent=2, ensure_ascii=False) + "\n")
        return f

    # ---- the processor board
    def mcu(self, used: dict, caption: str):
        """used: pin name -> signal. SiWx917 pins are breakout pads padN (UG581) or qwiic.<sig>; EFR32 boards use
        the same 26-pad layout but their mapping is unverified."""
        s = SILABS[self.brain]
        feats = [hole(BW * 0.067 - 0.8, pad_xy(n)[1] - 0.8, 1.6) if n % 2 else hole(BW * 0.91 - 0.8, pad_xy(n)[1] - 0.8, 1.6) for n in PADS]
        feats += [
            {"family": "connector", "variant": "qwiic", "x_mm": 0.3, "y_mm": 3.5, "w_mm": 4.4, "h_mm": 7.4, "rot": 90},
            {"family": "antenna", "variant": "chip", "x_mm": 13.6, "y_mm": 0.8, "w_mm": 3.2, "h_mm": 1.6},
            {"family": "chip", "variant": "qfn", "label": s["label"], "x_mm": 11.7, "y_mm": 16.5, "w_mm": 7.0, "h_mm": 7.0},
            {"family": "crystal", "label": "40M", "x_mm": 20.5, "y_mm": 18.0, "w_mm": 2.5, "h_mm": 2.0},
            {"family": "button", "x_mm": 8.0, "y_mm": 38.5, "w_mm": 3.6, "h_mm": 3.6},
            {"family": "button", "x_mm": 18.8, "y_mm": 38.5, "w_mm": 3.6, "h_mm": 3.6},
            {"family": "led", "color": "#2BB673", "x_mm": 6.2, "y_mm": 46.8, "w_mm": 1.6, "h_mm": 0.8},
            {"family": "connector", "variant": "usb_c", "x_mm": 10.7, "y_mm": 47.4, "w_mm": 9.0, "h_mm": 7.3},
            silk(16.5, 5.2, s["label"], 1.6), silk(16.5, 7.4, s["sub"], 1.1),
        ]
        if self.brain in ("xg27", "bg22"):
            feats.append({"family": "pcb", "variant": "silk", "label": "CR2032 on back", "x_mm": 9.0, "y_mm": 31.0, "w_mm": 12, "h_mm": 1.2})
        pins = []
        for name, sig in used.items():
            if name.startswith("qwiic."):
                i = ["GND", "3V3", "SDA", "SCL"].index(name.split(".")[1])
                pins.append({"name": name, "signal": sig, "gpio": None, "x_mm": 0.3, "y_mm": round(7.2 + (i - 1.5) * 1.0, 2),
                             "side": "left", "evidence": "user-guide" if self.brain == "siwx917" else UNV,
                             "source": "UG581 3.6.2 Table 3.3" if self.brain == "siwx917" else "dev kit user guide (to check)"})
                continue
            n = int(name[3:])
            x, y, side = pad_xy(n)
            net = PADS[n]
            ok = self.brain == "siwx917" and not sig.startswith("ADC")
            pin = {"name": name, "signal": sig, "gpio": net if "GPIO" in net else None, "x_mm": x, "y_mm": y, "side": side,
                   "evidence": "user-guide" if ok else UNV,
                   "source": f"UG581 Table 3.2 pad {n} ({net})" if self.brain == "siwx917" else "pad mapping to be checked in the dev kit user guide"}
            pins.append(pin)
        d = {"family": "pcb", "w_mm": BW, "h_mm": BH, "pcb_color": "black", "dims_evidence": "datasheet" if self.brain == "siwx917" else "typical",
             "label": s["label"], "features": feats}
        self.part("mcu", f"{s['label']} dev kit ({s['board']})", s["part_number"], "soc", d, pins, caption,
                  bom={"pn": s["part_number"], "mfr": s["manufacturer"], "desc": s["desc"], "cost": s["unit_cost_usd"],
                       "link": s["link"], "source": s["source"]})
        if self.brain != "siwx917":
            self.question("pad_map", f"Map every pad used here to a real pin of the {s['part_number']} expansion header (its user guide); "
                                     "this design reuses the BRD2605A pad numbering as a placeholder.", ["mcu"])


# ---- drawings for common third-party parts -------------------------------------------------------------------------

def header_pins(names_signals, w, side="top", y=None, x0=None):
    n = len(names_signals)
    cx = w / 2 if x0 is None else x0
    out = []
    for i, (nm, sig) in enumerate(names_signals):
        x = round(cx + (i - (n - 1) / 2) * 2.54, 2)
        out.append({"name": nm, "signal": sig, "gpio": None, "x_mm": x, "y_mm": y if y is not None else (1.57 if side == "top" else None),
                    "side": side, "evidence": UNV})
    return out


def header_feat(n, w, y, x0=None):
    cx = w / 2 if x0 is None else x0
    return {"family": "connector", "variant": f"header_{n}", "x_mm": round(cx - n * 1.27, 2), "y_mm": y, "w_mm": round(n * 2.54, 2), "h_mm": 2.54}


def qwiic_in(w, prefix="qwiic_in"):
    cx = w / 2
    feat = {"family": "connector", "variant": "qwiic", "x_mm": round(cx - 3.7, 2), "y_mm": 0, "w_mm": 7.4, "h_mm": 4.4, "rot": 180}
    pins = [{"name": f"{prefix}.{s}", "signal": s, "gpio": None, "x_mm": round(cx + (i - 1.5) * 1.0, 2), "y_mm": 0.4, "side": "top",
             "evidence": "datasheet", "source": "Qwiic connector standard (JST SH 4-pin: GND, 3.3V, SDA, SCL)"}
            for i, s in enumerate(["GND", "3V3", "SDA", "SCL"])]
    return feat, pins


def qwiic_out(w, h, prefix="qwiic_out"):
    cx = w / 2
    feat = {"family": "connector", "variant": "qwiic", "x_mm": round(cx - 3.7, 2), "y_mm": round(h - 4.4, 2), "w_mm": 7.4, "h_mm": 4.4}
    pins = [{"name": f"{prefix}.{s}", "signal": s, "gpio": None, "x_mm": round(cx + (i - 1.5) * 1.0, 2), "y_mm": round(h - 0.4, 2),
             "side": "bottom", "evidence": "datasheet", "source": "Qwiic connector standard"} for i, s in enumerate(["GND", "3V3", "SDA", "SCL"])]
    return feat, pins


def breakout(w, h, color, chip, extra=(), header=None, qin=False, qout=False):
    """A small breakout PCB: mounting holes, the main chip, optional Qwiic in/out and a top pin header."""
    feats = [hole(1.0, h - 3.8), hole(w - 3.8, h - 3.8)] if h > 14 else []
    if chip:
        label, variant, cw, ch, cy = chip
        feats.append({"family": "chip", "variant": variant, "label": label, "x_mm": round((w - cw) / 2, 2), "y_mm": cy, "w_mm": cw, "h_mm": ch})
    feats += list(extra)
    pins = []
    if qin:
        f, p = qwiic_in(w)
        feats.append(f)
        pins += p
    if qout:
        f, p = qwiic_out(w, h)
        feats.append(f)
        pins += p
    if header:
        feats.append(header_feat(len(header), w, 0.3))
        pins += header_pins(header, w)
    return {"family": "pcb", "w_mm": w, "h_mm": h, "pcb_color": color, "dims_evidence": "typical", "features": feats}, pins


def leads(names_signals, x0, y, pitch=1.6, side="top"):
    return [{"name": nm, "signal": sig, "gpio": None, "x_mm": round(x0 + i * pitch, 2), "y_mm": y, "side": side, "evidence": UNV}
            for i, (nm, sig) in enumerate(names_signals)]


def buck(k: Kit, vin_bus: str, vin: float, out_bus: str, vout: float, rng=(6.0, 36.0), why="", name="Step-down regulator"):
    d, pins = breakout(17.8, 12.7, "green", ("BUCK", "soic", 4.9, 3.9, 6.0), header=[("VIN", "VIN"), ("GND", "GND"), ("VOUT", "VOUT")])
    k.part("buck", name, f"{vout:g} V step-down module (e.g. Pololu D24V10F3 class)", "module", d, pins,
           f"Turns the {vin:g} V supply into the {vout:g} V the board needs. {why}".strip(),
           supply=rng, supplied_from=vin_bus, measures="", use="",
           bom={"desc": f"Switching regulator, {rng[0]:g}-{rng[1]:g} V in, {vout:g} V out, about 1 A", "cost": 8.0})


def power_in(k: Kit, v: float, label: str):
    """Supply terminal + fuse + TVS, drawn as one small protection board."""
    feats = [{"family": "connector", "variant": "screw_2", "x_mm": 1.0, "y_mm": 1.0, "w_mm": 10.16, "h_mm": 7.5},
             {"family": "passive", "variant": "r0805", "label": "F", "x_mm": 13.0, "y_mm": 3.0, "w_mm": 3.2, "h_mm": 1.6},
             {"family": "chip", "variant": "soic", "label": "TVS", "x_mm": 13.0, "y_mm": 6.0, "w_mm": 4.3, "h_mm": 3.6}]
    pins = [{"name": "OUT+", "signal": "VIN", "gpio": None, "x_mm": 19.5, "y_mm": 5.0, "side": "right", "evidence": UNV},
            {"name": "GND", "signal": "GND", "gpio": None, "x_mm": 19.5, "y_mm": 8.0, "side": "right", "evidence": UNV}]
    d = {"family": "pcb", "w_mm": 20.0, "h_mm": 11.0, "pcb_color": "green", "dims_evidence": "typical", "features": feats}
    k.part("protection", f"{label} input protection", "Screw terminal + fuse + TVS diode", "module", d, pins,
           f"Where the {label} supply comes in: a fuse and a surge diode protect the electronics from spikes on the line.",
           bom={"desc": "2-way screw terminal, 1 A fuse, TVS diode (load-dump rated for vehicles)", "cost": 4.0})


def opto(k: Kit, n_ch: int, id="opto", name="Opto-isolated inputs"):
    w = 10.0 + n_ch * 5.08
    feats = [{"family": "connector", "variant": f"screw_{n_ch * 2}", "x_mm": 1.0, "y_mm": 14.0, "w_mm": round(n_ch * 2 * 5.08 / 2, 2), "h_mm": 8.0}]
    feats += [{"family": "chip", "variant": "soic", "label": "PC817", "x_mm": round(2 + i * 5.08, 2), "y_mm": 6.0, "w_mm": 4.6, "h_mm": 6.5} for i in range(n_ch)]
    feats.append(header_feat(n_ch + 2, w, 0.3))
    hdr = [("VCC", "3V3"), ("GND", "GND")] + [(f"OUT{i + 1}", f"IN{i + 1}") for i in range(n_ch)]
    pins = header_pins(hdr, w)
    pins += [{"name": f"IN{i + 1}+", "signal": f"FIELD{i + 1}", "gpio": None, "x_mm": round(2.5 + i * 5.08, 2), "y_mm": 21.5, "side": "bottom", "evidence": UNV} for i in range(n_ch)]
    d = {"family": "pcb", "w_mm": round(w, 2), "h_mm": 23.0, "pcb_color": "blue", "dims_evidence": "typical", "features": feats}
    k.part(id, name, f"{n_ch}-channel PC817 opto-isolator input board (24 V)", "module", d, pins,
           "Reads 24 V signals from the machine through light, so the machine's wiring never touches the board.",
           supply=(3.0, 5.5), supplied_from="vmcu", bom={"desc": f"{n_ch}-channel 24 V opto-isolated input board", "cost": 6.0})


def reed(k: Kit, id, name, caption):
    d = {"family": "reed_switch", "w_mm": 28.0, "h_mm": 6.0, "dims_evidence": "typical"}
    pins = [{"name": "A", "signal": f"{id.upper()}_IN", "gpio": None, "x_mm": 0.4, "y_mm": 3.0, "side": "left", "evidence": UNV},
            {"name": "B", "signal": "GND", "gpio": None, "x_mm": 27.6, "y_mm": 3.0, "side": "right", "evidence": UNV}]
    k.part(id, name, "Surface-mount magnetic reed contact (normally open)", "transducer", d, pins, caption,
           bom={"desc": "Magnetic door contact with its magnet, normally open", "cost": 4.0})


def magnet(k: Kit, id="magnet", qty=1, name="Actuating magnet"):
    k.part(id, name, "Magnet for reed contact", "transducer", {"family": "magnet", "w_mm": 28.0, "h_mm": 8.0, "dims_evidence": "typical"}, [],
           "Sits on the moving part; when it comes close the reed contact closes.", bom={"qty": qty, "desc": "Magnet half of the door contact", "cost": 0.0})


def clamp(k: Kit, id="clamp", name="Current clamp"):
    d = {"family": "current_clamp", "w_mm": 31.0, "h_mm": 46.0, "dims_evidence": "typical"}
    pins = [{"name": "OUT", "signal": "CT_OUT", "gpio": None, "x_mm": 13.5, "y_mm": 45.6, "side": "bottom", "evidence": UNV},
            {"name": "REF", "signal": "CT_REF", "gpio": None, "x_mm": 17.5, "y_mm": 45.6, "side": "bottom", "evidence": UNV}]
    k.part(id, name, "SCT-013-030 split-core current transformer (30 A : 1 V)", "transducer", d, pins,
           "Clips around one motor wire and measures the current without cutting anything.",
           measures="Motor current", bom={"desc": "Split-core current transformer, 30 A, 1 V output", "cost": 9.0})


def ads1115(k: Kit, chans: list[tuple[str, str]], id="adc", address="0x48"):
    d, pins = breakout(28.0, 17.8, "blue", ("ADS1115", "soic", 4.9, 3.9, 9.0), header=[("VDD", "3V3"), ("GND", "GND"), ("SCL", "SCL"), ("SDA", "SDA")])
    d["features"].append({"family": "connector", "variant": f"header_{len(chans)}", "x_mm": round(14 - len(chans) * 1.27, 2), "y_mm": 14.8, "w_mm": round(len(chans) * 2.54, 2), "h_mm": 2.54})
    for i, (nm, sig) in enumerate(chans):
        pins.append({"name": nm, "signal": sig, "gpio": None, "x_mm": round(14 + (i - (len(chans) - 1) / 2) * 2.54, 2), "y_mm": 16.07, "side": "bottom", "evidence": UNV})
    k.part(id, "16-bit ADC", "ADS1115 breakout", "module", d, pins,
           "Turns the analog sensor voltages into numbers the board can read, much finer than the chip's own ADC.",
           bus="i2c", address=address, supply=(2.0, 5.5), supplied_from="vmcu", bom={"desc": "TI ADS1115 4-channel 16-bit ADC breakout", "cost": 10.0})


def bias(k: Kit, id="bias"):
    d = {"family": "pcb", "w_mm": 14.0, "h_mm": 10.0, "pcb_color": "green", "dims_evidence": "typical", "features": [
        {"family": "passive", "variant": "r0805", "label": "10k", "x_mm": 2.0, "y_mm": 2.5, "w_mm": 3.2, "h_mm": 1.6},
        {"family": "passive", "variant": "r0805", "label": "10k", "x_mm": 2.0, "y_mm": 5.5, "w_mm": 3.2, "h_mm": 1.6},
        {"family": "passive", "variant": "c0805", "x_mm": 8.0, "y_mm": 4.0, "w_mm": 3.2, "h_mm": 1.6}]}
    pins = [{"name": "VCC", "signal": "3V3", "gpio": None, "x_mm": 1.0, "y_mm": 0.4, "side": "top", "evidence": UNV},
            {"name": "GND", "signal": "GND", "gpio": None, "x_mm": 3.5, "y_mm": 0.4, "side": "top", "evidence": UNV},
            {"name": "MID", "signal": "CT_REF", "gpio": None, "x_mm": 7.0, "y_mm": 9.6, "side": "bottom", "evidence": UNV},
            {"name": "MID_ADC", "signal": "AIN_REF", "gpio": None, "x_mm": 10.0, "y_mm": 0.4, "side": "top", "evidence": UNV}]
    k.part(id, "Mid-supply bias", "2 × 10 kΩ divider + 10 µF capacitor", "module", d, pins,
           "Lifts the clamp's AC signal to half the supply so the ADC sees it swing both ways.",
           bom={"desc": "Two 10 kΩ resistors and a 10 µF capacitor on a scrap of prototype board", "cost": 1.0})


def std_buses_wifi(k: Kit, extra=()):
    k.bus("i2c", "I2C2 (ULP_I2C) via Qwiic and pads 15/16", "i2c", 3.3, "I2C2", "user-guide")
    k.bus("vmcu", "3.3 V (VMCU)", "power", 3.3, None, "user-guide")
    for b in extra:
        k.bus(*b)


def i2c_hdr(k: Kit, part):
    k.wire("mcu.pad20", f"{part}.VDD" if f"{part}.VDD" in pins_of(k, part) else f"{part}.VIN", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", f"{part}.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad16", f"{part}.SDA", "SDA", "blue", bus="i2c")
    k.wire("mcu.pad15", f"{part}.SCL", "SCL", "yellow", bus="i2c")


def pins_of(k: Kit, part):
    return {f"{part}.{p['name']}" for p in k.parts[part]["pins"]}


def kit(id, name, asset, status_radio, power, mounting, purpose, captions, publishes, budget=None, life=None):
    proto, chip, reason = status_radio
    k = {"id": id, "name": name, "asset_type": asset, "status": "reference",
         "radio": {"protocol": proto, "chip": chip, "reason": reason, "evidence": "silabs.com"},
         "power_source": {"type": power[0], "description": power[1]}, "mounting": mounting, "purpose": purpose,
         "captions": captions, "publishes": [{"channel": c, **({"unit": u} if u else {}), "description": dsc} for c, u, dsc in publishes]}
    if budget:
        k["power_budget"] = {"average_ma": budget[0], "peak_ma": budget[1], "supply_v": budget[2], "assumptions": budget[3]}
    if life:
        k["est_battery_life"] = {"days": life[0], "assumptions": life[1]}
    return k


WIFI = "SiWG917M111MGTBA"
ALL: list[Kit] = []


def reg(k):
    ALL.append(k)
    return k


# =================================================================== Logistics
def truck_telematics():
    k = reg(Kit(kit("truck_telematics", "Truck telematics", "truck",
                    ("wifi", WIFI, "Vehicle-powered, so no battery limit; Wi-Fi 6 to the cab's cellular hotspot carries position and events, BLE spots pallet tags."),
                    ("vehicle", "12 / 24 V vehicle supply through a fuse, a surge diode and a step-down regulator to 3.3 V."),
                    "Board and GNSS in a small IP54 box behind the cab; door contact on the cargo door frame; probe inside the cargo box.",
                    "Where the truck is, how fast it goes, whether the cargo door is open, cargo temperature and harsh driving.",
                    ["Tells the yard where each truck is and how it is being driven.",
                     "Warns when the cargo door opens away from a dock, or the cargo gets too warm.",
                     "Runs off the truck's own battery; it sends its data over the truck's Wi-Fi hotspot."],
                    [("speed_kmh", "km/h", "Speed over ground (GNSS)"), ("door_open", None, "Cargo door contact"),
                     ("cargo_temp_c", "°C", "Cargo temperature probe"), ("harsh_event", None, "Hard brake / hard acceleration / impact from the IMU")],
                    budget=(120, 350, 12.0, "SiWx917 Wi-Fi connected with 5 s reports (~60 mA), GNSS module tracking (~30 mA), IMU and probe (<5 mA), regulator losses. Estimate."),
                    ), "siwx917"))
    std_buses_wifi(k, [("uart", "UART (pads 12/14, shared with VCOM)", "gpio", 3.3, "ULP_UART"), ("onewire", "1-Wire (pad 3)", "gpio", 3.3),
                       ("vin", "Vehicle supply", "power", 24.0), ("gpio", "Digital inputs", "gpio", 3.3)])
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND",
           "pad20": "3V3", "pad12": "UART_TX", "pad14": "UART_RX", "pad3": "ONEWIRE", "pad5": "DOOR_IN"},
          "The brain: reads GNSS, the IMU, the door and the probe, and sends it all over Wi-Fi.")
    power_in(k, 24, "Vehicle")
    buck(k, "vin", 24.0, "vmcu", 3.3, (4.5, 36.0), "It also survives the 24 V trucks' higher voltage.")
    d, p = breakout(25.4, 25.4, "black", ("MAX-M10S", "module", 10.0, 10.0, 5.0),
                    extra=[{"family": "antenna", "variant": "ufl", "x_mm": 19.5, "y_mm": 4.0, "w_mm": 3.0, "h_mm": 3.0}],
                    header=[("VCC", "3V3"), ("GND", "GND"), ("TX", "TX"), ("RX", "RX")])
    k.part("gnss", "GNSS receiver", "u-blox MAX-M10S GNSS breakout", "module", d, p,
           "Works out where the truck is from satellites and how fast it moves.", bus="uart", supply=(2.7, 3.6), supplied_from="vmcu",
           measures="Position, speed", bom={"desc": "u-blox MAX-M10S breakout with u.FL antenna connector", "cost": 45.0})
    d, p = breakout(25.4, 25.4, "black", ("ICM-42688", "lga", 3.0, 2.5, 10.0), qin=True)
    k.part("imu", "6-axis IMU", "ICM-42688-P Qwiic breakout", "module", d, p,
           "Feels hard braking, sharp acceleration and bumps.", bus="i2c", address="0x68", supply=(1.71, 3.6), supplied_from="vmcu",
           measures="Acceleration, rotation", bom={"desc": "TDK ICM-42688-P 6-axis IMU breakout, Qwiic", "cost": 18.0})
    reed(k, "door", "Cargo door contact", "Closes when the cargo door is shut; the board sees it open the moment the door moves.")
    magnet(k)
    k.part("probe", "Cargo temperature probe", "DS18B20 waterproof probe", "transducer",
           {"family": "probe", "w_mm": 60.0, "h_mm": 6.0, "dims_evidence": "typical"},
           leads([("VDD", "3V3"), ("DQ", "ONEWIRE"), ("GND", "GND")], 56.0, 1.0, 1.4),
           "A stainless probe inside the cargo box that reports its temperature over one data wire.",
           bus="onewire", supply=(3.0, 5.5), supplied_from="vmcu", measures="Cargo temperature",
           bom={"desc": "DS18B20 1-Wire temperature probe, stainless tip, 1 m cable", "cost": 6.0})
    k.part("pullup", "1-Wire pull-up", "4.7 kΩ resistor", "module",
           {"family": "passive", "variant": "r0805", "label": "472", "w_mm": 6.0, "h_mm": 2.4, "dims_evidence": "typical"},
           [{"name": "A", "signal": "3V3", "gpio": None, "x_mm": 0.3, "y_mm": 1.2, "side": "left", "evidence": UNV},
            {"name": "B", "signal": "ONEWIRE", "gpio": None, "x_mm": 5.7, "y_mm": 1.2, "side": "right", "evidence": UNV}],
           "Holds the probe's data wire high between messages, as 1-Wire needs.", bom={"desc": "4.7 kΩ resistor", "cost": 0.1})
    k.wire("protection.OUT+", "buck.VIN", "VIN", "red", bus="vin")
    k.wire("protection.GND", "buck.GND", "GND", "black", bus="vin")
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.wire("mcu.pad20", "gnss.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "gnss.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad12", "gnss.RX", "UART_TX", "green", bus="uart")
    k.wire("mcu.pad14", "gnss.TX", "UART_RX", "white", bus="uart")
    k.qwiic("mcu.qwiic", "imu.qwiic_in")
    k.wire("mcu.pad5", "door.A", "DOOR_IN", "white", bus="gpio")
    k.wire("door.B", "mcu.pad26", "GND", "black", bus="gpio")
    k.wire("probe.VDD", "mcu.pad20", "3V3", "red", bus="onewire")
    k.wire("probe.DQ", "mcu.pad3", "ONEWIRE", "yellow", bus="onewire")
    k.wire("probe.GND", "mcu.pad26", "GND", "black", bus="onewire")
    k.wire("pullup.A", "mcu.pad20", "3V3", "red", bus="onewire")
    k.wire("pullup.B", "mcu.pad3", "ONEWIRE", "yellow", bus="onewire")
    k.question("uart_vcom", "Pads 12/14 are the VCOM UART; confirm the GNSS can share them or move it to another UART-capable pin.", ["gnss"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["gnss", "imu", "probe", "buck"])
    k.save()


def dock_bay():
    k = reg(Kit(kit("dock_bay", "Dock bay monitor", "dock",
                    ("wifi", WIFI, "Mains-powered at the dock door, so Wi-Fi's power draw doesn't matter and the warehouse Wi-Fi is already there."),
                    ("mains", "24 V DC from the dock door controller, stepped down to 3.3 V."),
                    "Board in the dock controller's enclosure; ToF sensor above the door looking down at the trailer; reed contacts on the door rails.",
                    "Is a trailer at the door, is the door open or shut, is the leveler out, and the dock light.",
                    ["Shows at a glance which dock doors have a trailer and which are open.",
                     "Switches the dock light on when a trailer is parked.", "Reads the leveler state from the dock's own controller."],
                    [("occupied", None, "Trailer present (ToF distance)"), ("door_position", None, "open / closed from the two door contacts"),
                     ("leveler", None, "deployed / stowed from the leveler controller"), ("dock_light", None, "Dock light relay state")],
                    budget=(90, 250, 24.0, "SiWx917 connected (~60 mA at 3.3 V), ToF ranging (~20 mA), relay coil when on (~70 mA at 5 V). Estimate."),
                    ), "siwx917"))
    std_buses_wifi(k, [("v24", "24 V DC from the dock controller", "power", 24.0), ("gpio", "Digital I/O", "gpio", 3.3)])
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND",
           "pad20": "3V3", "pad3": "DOOR_UP", "pad5": "DOOR_DOWN", "pad7": "LIGHT_RELAY", "pad9": "LEVELER_IN"},
          "Reads the door contacts, the ToF sensor and the leveler, drives the light relay, reports over Wi-Fi.")
    buck(k, "v24", 24.0, "vmcu", 3.3, (4.5, 36.0))
    d, p = breakout(25.4, 25.4, "red", None, extra=[{"family": "sensor_window", "variant": "tof", "x_mm": 10.25, "y_mm": 9.0, "w_mm": 4.9, "h_mm": 2.5}], qin=True)
    k.part("tof", "Trailer distance (ToF)", "VL53L1X Qwiic breakout", "module", d, p,
           "Measures the distance down to the trailer roof: short distance means a trailer is parked.", bus="i2c", address="0x29",
           supply=(2.6, 3.5), supplied_from="vmcu", measures="Distance (up to ~4 m)", bom={"desc": "ST VL53L1X time-of-flight breakout, Qwiic", "cost": 22.0})
    reed(k, "door_up", "Door open contact", "Closes when the roll-up door is fully open.")
    reed(k, "door_down", "Door closed contact", "Closes when the door is fully shut.")
    magnet(k, qty=2, name="Door magnets")
    d, p = breakout(26.0, 17.0, "blue", None, extra=[{"family": "relay", "label": "5 V 10 A", "x_mm": 3.0, "y_mm": 4.0, "w_mm": 15.0, "h_mm": 11.0},
                                                     {"family": "connector", "variant": "screw_3", "x_mm": 18.5, "y_mm": 4.0, "w_mm": 7.0, "h_mm": 11.0}],
                    header=[("VCC", "3V3"), ("GND", "GND"), ("IN", "LIGHT_RELAY")])
    k.part("relay", "Dock light relay", "1-channel relay module (3.3 V input)", "module", d, p,
           "Switches the dock light on and off; the light's mains wiring stays on the relay's screw terminals.",
           supply=(3.0, 5.5), supplied_from="vmcu", bom={"desc": "1-channel relay module, 3.3 V logic input", "cost": 5.0})
    opto(k, 1, name="Leveler input")
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.qwiic("mcu.qwiic", "tof.qwiic_in")
    k.wire("mcu.pad3", "door_up.A", "DOOR_UP_IN", "white", bus="gpio")
    k.wire("door_up.B", "mcu.pad26", "GND", "black", bus="gpio")
    k.wire("mcu.pad5", "door_down.A", "DOOR_DOWN_IN", "white", bus="gpio")
    k.wire("door_down.B", "mcu.pad26", "GND", "black", bus="gpio")
    k.wire("mcu.pad20", "relay.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "relay.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad7", "relay.IN", "LIGHT_RELAY", "orange", bus="gpio")
    k.wire("mcu.pad20", "opto.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "opto.GND", "GND", "black", bus="vmcu")
    k.wire("opto.OUT1", "mcu.pad9", "IN1", "green", bus="gpio")
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["tof", "relay", "opto", "buck"])
    k.question("tof_range", "Check that the ToF's range covers the mounting height above the trailer (VL53L1X long mode is about 4 m); otherwise use a radar presence sensor.", ["tof"])
    k.save()


def pallet_asset_tag():
    k = reg(Kit(kit("pallet_asset_tag", "Pallet asset tag", "pallet",
                    ("ble", "EFR32BG22", "A coin cell must last years: Bluetooth LE advertising every few seconds draws microamps on average, and the warehouse gateways already scan BLE."),
                    ("battery", "One CR2032 coin cell in the board's holder."),
                    "Screwed or zip-tied to the pallet's side block, button facing out.",
                    "A pallet that can be found: it advertises its ID, and its button and LED answer a 'find me'.",
                    ["Lets the warehouse find a pallet by asking it to blink.", "Runs for years on a coin cell because it only talks in short radio blips."],
                    [("find_me", None, "True while the tag is blinking for a 'find me' request")],
                    budget=(0.012, 8, 3.0, "BLE advertising every 2 s (~5 µA average for the radio), sleep current a few µA, LED blink only on request. Estimate."),
                    life=(900, "CR2032 ~220 mAh usable at 12 µA average, one 10 s find-me a day, room temperature. Estimate, not measured."),
                    ), "bg22"))
    k.bus("vbat", "Coin cell (3.0 V)", "power", 3.0)
    k.bus("gpio", "GPIO", "gpio", 3.0)
    k.mcu({"pad1": "GND", "pad20": "VBAT", "pad3": "BUTTON_IN", "pad5": "LED_OUT"}, "Advertises the tag's ID over Bluetooth LE and handles the button and the LED.")
    d = {"family": "button", "w_mm": 6.0, "h_mm": 6.0, "dims_evidence": "typical"}
    k.part("button", "Find-me button", "6 × 6 mm tactile switch", "transducer", d,
           [{"name": "A", "signal": "BUTTON_IN", "gpio": None, "x_mm": 0.3, "y_mm": 1.2, "side": "top", "evidence": UNV},
            {"name": "B", "signal": "GND", "gpio": None, "x_mm": 5.7, "y_mm": 1.2, "side": "top", "evidence": UNV}],
           "Press it to make the tag announce itself, or to stop it blinking.", bom={"desc": "6 mm tactile switch", "cost": 0.2})
    d = {"family": "led", "color": "#E5392B", "w_mm": 5.0, "h_mm": 2.5, "dims_evidence": "typical"}
    k.part("led", "Find-me LED", "Red LED + 1 kΩ resistor", "transducer", d,
           [{"name": "A", "signal": "LED_OUT", "gpio": None, "x_mm": 0.3, "y_mm": 1.25, "side": "left", "evidence": UNV},
            {"name": "K", "signal": "GND", "gpio": None, "x_mm": 4.7, "y_mm": 1.25, "side": "right", "evidence": UNV}],
           "Blinks when someone looks for this pallet.", bom={"desc": "Red LED with series resistor", "cost": 0.2})
    k.wire("mcu.pad3", "button.A", "BUTTON_IN", "white", bus="gpio")
    k.wire("button.B", "mcu.pad1", "GND", "black", bus="gpio")
    k.wire("mcu.pad5", "led.A", "LED_OUT", "red", bus="gpio")
    k.wire("led.K", "mcu.pad1", "GND", "black", bus="gpio")
    k.question("product_tag", "A production tag would be a custom coin-cell board around the EFR32BG22; the Thunderboard is the prototype.", ["mcu"])
    k.save()


# =================================================================== Production
def machine_monitor():
    k = reg(Kit(kit("machine_monitor", "Machine monitor", "machine",
                    ("wifi", WIFI, "Mains-powered in the machine cabinet; Wi-Fi carries 1 s vibration and current data without a mesh."),
                    ("mains", "24 V DC from the machine cabinet supply, stepped down to 3.3 V."),
                    "Board on a DIN-rail carrier in the cabinet; clamp on one motor phase; accelerometer glued to the motor housing; thermocouple on the bearing.",
                    "Machine state, motor current, vibration, surface temperature and cycle count, without touching the machine's PLC.",
                    ["Tells you when a machine is running, idle or stopped with a fault.", "Spots a wearing bearing early from rising vibration and heat.",
                     "Counts cycles from the machine's own cycle signal."],
                    [("state", None, "running / idle / fault / maintenance from the stack light and current"), ("current_a", "A", "Motor current (clamp)"),
                     ("vibration_rms", "mm/s", "Vibration velocity RMS (accelerometer)"), ("temperature_c", "°C", "Bearing surface temperature (thermocouple)"),
                     ("units", None, "Good units (cycle input)"), ("rejects", None, "Rejected units"), ("cycle_time_s", "s", "Last cycle time"),
                     ("alarm", None, "Fault text when the stack light goes red")],
                    budget=(95, 220, 24.0, "SiWx917 connected (~60 mA), ADC + accelerometer (~1 mA), thermocouple amp (~1.5 mA), opto inputs (~5 mA). Estimate."),
                    ), "siwx917"))
    std_buses_wifi(k, [("spi", "SPI (pads 4/6/8/10)", "spi", 3.3, "ULP_SSI"), ("analog", "Clamp signal", "analog", None),
                       ("v24", "24 V DC cabinet supply", "power", 24.0), ("gpio", "Digital inputs", "gpio", 3.3)])
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND",
           "pad20": "3V3", "pad16": "SDA", "pad15": "SCL", "pad6": "MISO", "pad8": "SCK", "pad10": "CS", "pad3": "RUN_IN", "pad5": "FAULT_IN", "pad7": "CYCLE_IN"},
          "Samples vibration and current, reads the stack light and cycle signal, and publishes once a second.")
    buck(k, "v24", 24.0, "vmcu", 3.3, (4.5, 36.0))
    clamp(k)
    bias(k)
    ads1115(k, [("A0", "AIN_CT"), ("A1", "AIN_REF")])
    d, p = breakout(25.4, 17.8, "black", ("LIS3DH", "lga", 3.0, 3.0, 7.0), qin=True)
    k.part("accel", "3-axis accelerometer", "LIS3DH Qwiic breakout", "module", d, p,
           "Feels the motor shake; more shaking than usual means wear or imbalance.", bus="i2c", address="0x19", supply=(1.71, 3.6),
           supplied_from="vmcu", measures="Vibration", bom={"desc": "ST LIS3DH 3-axis accelerometer breakout, Qwiic", "cost": 6.0})
    d, p = breakout(25.4, 22.0, "blue", ("MAX31855", "soic", 4.9, 3.9, 8.0),
                    extra=[{"family": "connector", "variant": "screw_2", "x_mm": 7.6, "y_mm": 14.0, "w_mm": 10.16, "h_mm": 7.5}],
                    header=[("VIN", "3V3"), ("GND", "GND"), ("DO", "MISO"), ("CS", "CS"), ("CLK", "SCK")])
    p += [{"name": "TC+", "signal": "TC+", "gpio": None, "x_mm": 10.1, "y_mm": 21.6, "side": "bottom", "evidence": UNV},
          {"name": "TC-", "signal": "TC-", "gpio": None, "x_mm": 15.2, "y_mm": 21.6, "side": "bottom", "evidence": UNV}]
    k.part("tc_amp", "Thermocouple amplifier", "MAX31855K breakout", "module", d, p,
           "Reads the thermocouple and turns it into a temperature the board can read over SPI.", bus="spi", supply=(3.0, 3.6),
           supplied_from="vmcu", measures="Temperature", bom={"desc": "Analog Devices MAX31855K thermocouple-to-digital breakout", "cost": 15.0})
    k.part("thermocouple", "Bearing thermocouple", "Type K thermocouple, adhesive patch", "transducer",
           {"family": "probe", "w_mm": 50.0, "h_mm": 6.0, "dims_evidence": "typical"},
           [{"name": "TC+", "signal": "TC+", "gpio": None, "x_mm": 46.0, "y_mm": 1.0, "side": "top", "evidence": UNV},
            {"name": "TC-", "signal": "TC-", "gpio": None, "x_mm": 48.0, "y_mm": 1.0, "side": "top", "evidence": UNV}],
           "Stuck onto the bearing housing; a warmer bearing than usual is a warning sign.", measures="Surface temperature",
           bom={"desc": "Type K thermocouple with adhesive patch", "cost": 7.0})
    opto(k, 3, name="Stack light and cycle inputs")
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.qwiic("mcu.qwiic", "accel.qwiic_in")
    i2c_hdr(k, "adc")
    k.wire("clamp.OUT", "adc.A0", "AIN_CT", "white", bus="analog")
    k.wire("clamp.REF", "bias.MID", "CT_REF", "grey", bus="analog")
    k.wire("bias.MID_ADC", "adc.A1", "AIN_REF", "grey", bus="analog")
    k.wire("bias.VCC", "mcu.pad20", "3V3", "red", bus="vmcu")
    k.wire("bias.GND", "mcu.pad26", "GND", "black", bus="vmcu")
    k.wire("mcu.pad20", "tc_amp.VIN", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "tc_amp.GND", "GND", "black", bus="vmcu")
    k.wire("tc_amp.DO", "mcu.pad6", "MISO", "green", bus="spi")
    k.wire("mcu.pad10", "tc_amp.CS", "CS", "white", bus="spi")
    k.wire("mcu.pad8", "tc_amp.CLK", "SCK", "yellow", bus="spi")
    k.wire("thermocouple.TC+", "tc_amp.TC+", "TC+", "yellow", bus="analog")
    k.wire("thermocouple.TC-", "tc_amp.TC-", "TC-", "red", bus="analog")
    k.wire("mcu.pad20", "opto.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "opto.GND", "GND", "black", bus="vmcu")
    k.wire("opto.OUT1", "mcu.pad3", "IN1", "green", bus="gpio")
    k.wire("opto.OUT2", "mcu.pad5", "IN2", "orange", bus="gpio")
    k.wire("opto.OUT3", "mcu.pad7", "IN3", "brown", bus="gpio")
    k.question("spi_share", "Pads 4-10 are the on-board IMU/flash SPI; confirm the MAX31855 can share the bus with its own chip select (pad 10 is the IMU CS when SENSOR_ENABLE = 1).", ["tc_amp"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["clamp", "adc", "accel", "tc_amp", "opto"])
    k.save()


def conveyor_monitor():
    k = reg(Kit(kit("conveyor_monitor", "Conveyor monitor", "conveyor",
                    ("wifi", WIFI, "Mains-powered beside the conveyor drive; Wi-Fi is already on the shop floor."),
                    ("mains", "24 V DC from the conveyor control panel, stepped down to 3.3 V."),
                    "Board in the drive's control box; clamp on a motor phase; hall sensor facing a magnet on the tail roller; ToF above the belt before the transfer point.",
                    "Motor current, belt speed and jams.",
                    ["Shows the belt speed and spots a jam before boxes pile up.", "A stalled belt draws more current: the clamp sees it."],
                    [("motor_current_a", "A", "Drive motor current (clamp)"), ("belt_speed_m_s", "m/s", "Belt speed from roller pulses"),
                     ("jam", None, "Box held in front of the ToF sensor too long")],
                    budget=(85, 200, 24.0, "SiWx917 connected (~60 mA), ToF (~20 mA), ADC + hall (<3 mA). Estimate."),
                    ), "siwx917"))
    std_buses_wifi(k, [("analog", "Clamp signal", "analog", None), ("v24", "24 V DC panel supply", "power", 24.0), ("gpio", "Pulse input", "gpio", 3.3)])
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND",
           "pad20": "3V3", "pad16": "SDA", "pad15": "SCL", "pad3": "HALL_IN"}, "Counts roller pulses, reads current and the jam sensor, reports over Wi-Fi.")
    buck(k, "v24", 24.0, "vmcu", 3.3, (4.5, 36.0))
    clamp(k)
    bias(k)
    ads1115(k, [("A0", "AIN_CT"), ("A1", "AIN_REF")])
    d, p = breakout(25.4, 25.4, "red", None, extra=[{"family": "sensor_window", "variant": "tof", "x_mm": 10.25, "y_mm": 9.0, "w_mm": 4.9, "h_mm": 2.5}], qin=True)
    k.part("tof", "Jam sensor (ToF)", "VL53L1X Qwiic breakout", "module", d, p,
           "Looks across the belt: a box that stays in view too long means a jam.", bus="i2c", address="0x29", supply=(2.6, 3.5),
           supplied_from="vmcu", measures="Distance to the next box", bom={"desc": "ST VL53L1X time-of-flight breakout, Qwiic", "cost": 22.0})
    d, p = breakout(15.0, 12.0, "green", ("A3144", "soic", 4.0, 3.0, 4.5), header=[("VCC", "3V3"), ("GND", "GND"), ("OUT", "HALL_IN")])
    k.part("hall", "Roller pulse sensor", "Hall-effect switch module", "module", d, p,
           "Clicks once per turn of the roller as its magnet passes, which gives the belt speed.", supply=(3.0, 24.0), supplied_from="vmcu",
           measures="Roller turns", bom={"desc": "Hall-effect switch module (3.3 V compatible)", "cost": 3.0})
    magnet(k, name="Roller magnet")
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.qwiic("mcu.qwiic", "tof.qwiic_in")
    i2c_hdr(k, "adc")
    k.wire("clamp.OUT", "adc.A0", "AIN_CT", "white", bus="analog")
    k.wire("clamp.REF", "bias.MID", "CT_REF", "grey", bus="analog")
    k.wire("bias.MID_ADC", "adc.A1", "AIN_REF", "grey", bus="analog")
    k.wire("bias.VCC", "mcu.pad20", "3V3", "red", bus="vmcu")
    k.wire("bias.GND", "mcu.pad26", "GND", "black", bus="vmcu")
    k.wire("mcu.pad20", "hall.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "hall.GND", "GND", "black", bus="vmcu")
    k.wire("hall.OUT", "mcu.pad3", "HALL_IN", "green", bus="gpio")
    k.question("hall_supply", "Many A3144 modules need 4.5 V or more; pick a hall switch rated for 3.3 V (or power it from 5 V with a divider on OUT).", ["hall"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["clamp", "adc", "tof", "hall"])
    k.save()


def compressor_monitor():
    k = reg(Kit(kit("compressor_monitor", "Compressor monitor", "utility",
                    ("wifi", WIFI, "Mains-powered in the compressor room; Wi-Fi reaches the utilities block without a mesh."),
                    ("mains", "24 V DC from the compressor's control supply, stepped down to 3.3 V and 5 V."),
                    "Board in a small box on the compressor room wall; pressure transducer on the receiver tank; dew-point transmitter after the dryer; clamp on the motor.",
                    "Line pressure, motor current and power, load state, delivered air (estimated), run hours, discharge temperature and dew point.",
                    ["Shows the air pressure the factory gets, and when the compressor loads and unloads.", "A leak shows up as the compressor running more often.",
                     "Wet air damages tools: the dew point says how dry it is."],
                    [("pressure_bar", "bar", "Receiver pressure"), ("current_a", "A", "Motor current"), ("run_hours", "h", "Loaded hours (from current)"),
                     ("dew_point_c", "°C", "Pressure dew point after the dryer"), ("tripped", None, "Compressor tripped (the controller's fault contact)"),
                     ("loaded", None, "Loaded or unloaded (from motor current: loaded current is well above unloaded)"),
                     ("power_kw", "kW", "Electrical power, computed on the node from current (√3 × 400 V × I × PF)"),
                     ("flow_nm3_min", "Nm³/min", "Delivered air, estimated: the compressor's rated FAD while loaded (no flow meter)"),
                     ("discharge_c", "°C", "Discharge air temperature (thermocouple on the outlet pipe)")],
                    budget=(110, 260, 24.0, "SiWx917 connected (~60 mA), 4-20 mA loop (up to 20 mA at 24 V), pressure transducer (~5 mA at 5 V). Estimate."),
                    ), "siwx917"))
    std_buses_wifi(k, [("analog", "Analog inputs", "analog", None), ("v24", "24 V DC", "power", 24.0), ("v5", "5 V (from pad 18)", "power", 5.0),
                       ("spi", "SPI (pads 4/6/8/10)", "spi", 3.3, "ULP_SSI")])
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND", "pad20": "3V3",
           "pad16": "SDA", "pad15": "SCL", "pad6": "MISO", "pad8": "SCK", "pad10": "CS"},
          "Reads three analog sensors through the ADC and the discharge thermocouple over SPI, and reports over Wi-Fi.")
    buck(k, "v24", 24.0, "vmcu", 3.3, (4.5, 36.0))
    clamp(k)
    bias(k)
    ads1115(k, [("A0", "AIN_CT"), ("A1", "AIN_REF"), ("A2", "AIN_PRESS"), ("A3", "AIN_DEW")])
    k.part("pressure", "Pressure transducer", "0-10 bar, 0.5-4.5 V ratiometric transducer (1/4\" BSP)", "transducer",
           {"family": "probe", "w_mm": 70.0, "h_mm": 22.0, "dims_evidence": "typical"},
           leads([("V+", "5V"), ("GND", "GND"), ("OUT", "AIN_PRESS")], 64.0, 1.0, 2.0),
           "Screws into the air tank and gives a voltage that rises with pressure.", supply=(4.75, 5.25), supplied_from="v5",
           measures="Pressure 0-10 bar", bom={"desc": "Stainless pressure transducer, 0-10 bar, 0.5-4.5 V out, 5 V supply", "cost": 25.0})
    k.part("divider", "Pressure signal divider", "10 kΩ / 20 kΩ divider", "module",
           {"family": "passive", "variant": "r0805", "label": "2:3", "w_mm": 8.0, "h_mm": 3.0, "dims_evidence": "typical"},
           [{"name": "IN", "signal": "AIN_PRESS", "gpio": None, "x_mm": 0.3, "y_mm": 1.5, "side": "left", "evidence": UNV},
            {"name": "OUT", "signal": "AIN_PRESS", "gpio": None, "x_mm": 7.7, "y_mm": 1.5, "side": "right", "evidence": UNV}],
           "Scales the transducer's 4.5 V maximum down to 3 V so the ADC input stays inside its supply.", bom={"desc": "10 kΩ and 20 kΩ resistors", "cost": 0.2})
    k.part("dewpoint", "Dew-point transmitter", "Pressure dew-point transmitter, 4-20 mA (-60 … +20 °C)", "transducer",
           {"family": "probe", "w_mm": 90.0, "h_mm": 18.0, "dims_evidence": "typical"},
           leads([("LOOP+", "V24"), ("LOOP-", "AIN_DEW")], 86.0, 1.0, 2.0),
           "Measures how much water is left in the compressed air after the dryer.", supply=(18.0, 30.0), supplied_from="v24",
           measures="Dew point", bom={"desc": "Industrial dew-point transmitter, 4-20 mA loop", "cost": 350.0})
    k.part("shunt", "Loop shunt", "150 Ω 0.1 % resistor", "module",
           {"family": "passive", "variant": "r0805", "label": "151", "w_mm": 6.0, "h_mm": 2.4, "dims_evidence": "typical"},
           [{"name": "A", "signal": "AIN_DEW", "gpio": None, "x_mm": 0.3, "y_mm": 1.2, "side": "left", "evidence": UNV},
            {"name": "B", "signal": "GND", "gpio": None, "x_mm": 5.7, "y_mm": 1.2, "side": "right", "evidence": UNV}],
           "Turns the 4-20 mA loop into 0.6-3.0 V for the ADC.", bom={"desc": "150 Ω precision resistor", "cost": 0.5})
    d, p = breakout(25.4, 22.0, "blue", ("MAX31855", "soic", 4.9, 3.9, 8.0),
                    extra=[{"family": "connector", "variant": "screw_2", "x_mm": 7.6, "y_mm": 14.0, "w_mm": 10.16, "h_mm": 7.5}],
                    header=[("VIN", "3V3"), ("GND", "GND"), ("DO", "MISO"), ("CS", "CS"), ("CLK", "SCK")])
    p += [{"name": "TC+", "signal": "TC+", "gpio": None, "x_mm": 10.1, "y_mm": 21.6, "side": "bottom", "evidence": UNV},
          {"name": "TC-", "signal": "TC-", "gpio": None, "x_mm": 15.2, "y_mm": 21.6, "side": "bottom", "evidence": UNV}]
    k.part("tc_amp", "Thermocouple amplifier", "MAX31855K breakout", "module", d, p,
           "Reads the thermocouple and turns it into a temperature the board can read over SPI.", bus="spi", supply=(3.0, 3.6),
           supplied_from="vmcu", measures="Temperature", bom={"desc": "Analog Devices MAX31855K thermocouple-to-digital breakout", "cost": 15.0})
    k.part("thermocouple", "Discharge thermocouple", "Type K thermocouple, pipe-clamp probe", "transducer",
           {"family": "probe", "w_mm": 50.0, "h_mm": 6.0, "dims_evidence": "typical"},
           [{"name": "TC+", "signal": "TC+", "gpio": None, "x_mm": 46.0, "y_mm": 1.0, "side": "top", "evidence": UNV},
            {"name": "TC-", "signal": "TC-", "gpio": None, "x_mm": 48.0, "y_mm": 1.0, "side": "top", "evidence": UNV}],
           "Clamped to the discharge pipe; a hotter discharge than usual means a cooling or oil problem.", measures="Discharge temperature",
           bom={"desc": "Type K thermocouple, pipe-clamp", "cost": 9.0})
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.wire("mcu.pad20", "adc.VDD", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "adc.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad16", "adc.SDA", "SDA", "blue", bus="i2c")
    k.wire("mcu.pad15", "adc.SCL", "SCL", "yellow", bus="i2c")
    k.wire("clamp.OUT", "adc.A0", "AIN_CT", "white", bus="analog")
    k.wire("clamp.REF", "bias.MID", "CT_REF", "grey", bus="analog")
    k.wire("bias.MID_ADC", "adc.A1", "AIN_REF", "grey", bus="analog")
    k.wire("bias.VCC", "mcu.pad20", "3V3", "red", bus="vmcu")
    k.wire("bias.GND", "mcu.pad26", "GND", "black", bus="vmcu")
    k.wire("pressure.OUT", "divider.IN", "AIN_PRESS", "white", bus="analog")
    k.wire("divider.OUT", "adc.A2", "AIN_PRESS", "white", bus="analog")
    k.wire("pressure.GND", "mcu.pad1", "GND", "black", bus="v5")
    k.wire("dewpoint.LOOP-", "shunt.A", "AIN_DEW", "white", bus="analog")
    k.wire("shunt.A", "adc.A3", "AIN_DEW", "white", bus="analog")
    k.wire("shunt.B", "mcu.pad1", "GND", "black", bus="analog")
    # 5 V for the transducer and 24 V for the loop come from the supply side (drawn to the regulator input).
    k.wire("buck.VIN", "dewpoint.LOOP+", "V24", "red", bus="v24")
    k.wire("mcu.pad20", "tc_amp.VIN", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "tc_amp.GND", "GND", "black", bus="vmcu")
    k.wire("tc_amp.DO", "mcu.pad6", "MISO", "green", bus="spi")
    k.wire("mcu.pad10", "tc_amp.CS", "CS", "white", bus="spi")
    k.wire("mcu.pad8", "tc_amp.CLK", "SCK", "yellow", bus="spi")
    k.wire("thermocouple.TC+", "tc_amp.TC+", "TC+", "yellow", bus="analog")
    k.wire("thermocouple.TC-", "tc_amp.TC-", "TC-", "red", bus="analog")
    k.question("spi_share", "Pads 4-10 are the on-board IMU/flash SPI; confirm the MAX31855 can share the bus with its own chip select.", ["tc_amp"])
    k.question("five_volt", "Pad 18 (5 V) is only live on USB power; give the pressure transducer its own 5 V regulator from the 24 V supply.", ["pressure"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["pressure", "dewpoint", "adc", "clamp", "tc_amp"])
    k.save()


# =================================================================== People
def worker_badge():
    k = reg(Kit(kit("worker_badge", "Worker badge", "worker",
                    ("ble", "EFR32BG27", "Worn all shift on a small battery: Bluetooth LE advertising sips power, and zone gateways locate it by signal strength."),
                    ("battery", "300 mAh LiPo with a USB-C charger, charged overnight in a rack."),
                    "Clip-on badge on the chest strap or lanyard; motor and buzzer inside the case, SOS button on the front edge.",
                    "Zone location, falls and man-down, SOS, and buzz/beep/flash alerts for the wearer.",
                    ["Lets a worker call for help with one long press.", "Notices a fall or someone lying still, and asks before raising the alarm.",
                     "Buzzes the wearer when a forklift gets too close or a zone must be evacuated."],
                    [("position", "m", "Zone position from gateway RSSI (computed by the site, not by the badge)"),
                     ("fall", None, "Free fall followed by an impact (IMU)"), ("sos", None, "SOS button held for 2 s"),
                     ("cancel", None, "Worker cancelled a fall / no-movement pre-alert on the badge"),
                     ("checkin", None, "Lone-worker check-in (double press)")],
                    budget=(0.9, 90, 3.7, "BLE advertising 1 Hz (~15 µA), IMU in low-power motion detection (~10 µA), SHT45 every 30 s (<1 µA), alerts a few seconds a day (motor ~70 mA). Estimate."),
                    life=(14, "300 mAh LiPo at ~0.9 mA average including a handful of alerts per shift; worn 10 h a day. Estimate, not measured."),
                    ), "xg27"))
    k.bus("i2c", "I2C", "i2c", 3.3)
    k.bus("vbat", "Battery rail (LiPo, regulated 3.3 V on the dev kit)", "power", 3.3)
    k.bus("gpio", "GPIO", "gpio", 3.3)
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad1": "GND", "pad26": "GND", "pad20": "3V3",
           "pad3": "SOS_IN", "pad5": "BUZZER_OUT", "pad7": "LED_OUT", "pad2": "VBAT_IN"},
          "Advertises over Bluetooth LE, watches the IMU for falls and the SOS button, and drives the alerts.")
    d, p = breakout(25.4, 17.8, "black", ("LIS3DH", "lga", 3.0, 3.0, 7.0), qin=True, qout=True)
    k.part("imu", "Accelerometer (fall / man-down)", "LIS3DH Qwiic breakout", "module", d, p,
           "Notices a free fall followed by a hit, or someone not moving at all.", bus="i2c", address="0x19", supply=(1.71, 3.6),
           supplied_from="vbat", measures="Acceleration", bom={"desc": "ST LIS3DH accelerometer breakout, Qwiic", "cost": 6.0})
    d, p = breakout(25.4, 17.8, "black", ("DRV2605L", "soic", 3.0, 3.0, 7.0), qin=True, qout=True,
                    extra=[{"family": "connector", "variant": "screw_2", "x_mm": 15.0, "y_mm": 9.0, "w_mm": 9.0, "h_mm": 6.5}])
    p += [{"name": "OUT+", "signal": "MOTOR+", "gpio": None, "x_mm": 17.0, "y_mm": 15.2, "side": "bottom", "evidence": UNV},
          {"name": "OUT-", "signal": "MOTOR-", "gpio": None, "x_mm": 22.0, "y_mm": 15.2, "side": "bottom", "evidence": UNV}]
    k.part("haptic", "Haptic driver", "DRV2605L Qwiic breakout", "module", d, p,
           "Drives the vibration motor with short, distinct buzz patterns.", bus="i2c", address="0x5A", supply=(2.0, 5.2),
           supplied_from="vbat", bom={"desc": "TI DRV2605L haptic driver breakout, Qwiic", "cost": 8.0})
    k.part("motor", "Vibration motor", "10 mm coin ERM vibration motor", "transducer",
           {"family": "buzzer", "w_mm": 10.0, "h_mm": 10.0, "dims_evidence": "typical"},
           [{"name": "+", "signal": "MOTOR+", "gpio": None, "x_mm": 3.5, "y_mm": 0.3, "side": "top", "evidence": UNV},
            {"name": "-", "signal": "MOTOR-", "gpio": None, "x_mm": 6.5, "y_mm": 0.3, "side": "top", "evidence": UNV}],
           "Buzzes against the chest so the wearer feels an alert even in a noisy hall.", bom={"desc": "3 V coin vibration motor", "cost": 2.0})
    d, p = breakout(25.4, 17.8, "black", ("SHT45", "lga", 1.5, 1.5, 7.0), qin=True)
    k.part("sht", "Ambient temperature / humidity", "SHT45 Qwiic breakout", "module", d, p,
           "Measures the air around the worker (not the skin) for heat-stress reminders.", bus="i2c", address="0x44", supply=(1.08, 3.6),
           supplied_from="vbat", measures="Air temperature, humidity", bom={"desc": "Sensirion SHT45 breakout, Qwiic", "cost": 14.0})
    k.part("sos", "SOS button", "12 mm tactile switch with cap", "transducer", {"family": "button", "w_mm": 12.0, "h_mm": 12.0, "dims_evidence": "typical"},
           [{"name": "A", "signal": "SOS_IN", "gpio": None, "x_mm": 1.0, "y_mm": 0.3, "side": "top", "evidence": UNV},
            {"name": "B", "signal": "GND", "gpio": None, "x_mm": 11.0, "y_mm": 0.3, "side": "top", "evidence": UNV}],
           "Hold it for two seconds to call for help.", bom={"desc": "12 mm tactile switch with red cap", "cost": 0.5})
    k.part("buzzer", "Buzzer", "Piezo transducer 12 mm", "transducer", {"family": "buzzer", "w_mm": 12.0, "h_mm": 12.0, "dims_evidence": "typical"},
           [{"name": "+", "signal": "BUZZER_OUT", "gpio": None, "x_mm": 4.0, "y_mm": 0.3, "side": "top", "evidence": UNV},
            {"name": "-", "signal": "GND", "gpio": None, "x_mm": 8.0, "y_mm": 0.3, "side": "top", "evidence": UNV}],
           "Beeps for alerts and evacuations.", bom={"desc": "12 mm piezo transducer", "cost": 1.0})
    k.part("led", "Alert LED", "Red LED + 470 Ω", "transducer", {"family": "led", "color": "#E5392B", "w_mm": 5.0, "h_mm": 2.5, "dims_evidence": "typical"},
           [{"name": "A", "signal": "LED_OUT", "gpio": None, "x_mm": 0.3, "y_mm": 1.25, "side": "left", "evidence": UNV},
            {"name": "K", "signal": "GND", "gpio": None, "x_mm": 4.7, "y_mm": 1.25, "side": "right", "evidence": UNV}],
           "Flashes so people nearby can see who is in trouble.", bom={"desc": "Red LED with series resistor", "cost": 0.2})
    k.part("battery", "Battery", "LiPo 3.7 V 300 mAh with protection", "transducer",
           {"family": "lipo", "label": "3.7 V 300 mAh", "w_mm": 40.0, "h_mm": 25.0, "dims_evidence": "typical"},
           [{"name": "+", "signal": "VBAT", "gpio": None, "x_mm": 39.6, "y_mm": 10.0, "side": "right", "evidence": UNV},
            {"name": "-", "signal": "GND", "gpio": None, "x_mm": 39.6, "y_mm": 15.0, "side": "right", "evidence": UNV}],
           "The badge's battery, charged overnight.", bom={"desc": "3.7 V 300 mAh LiPo with protection circuit", "cost": 6.0})
    k.qwiic("mcu.qwiic", "imu.qwiic_in", "vbat")
    k.qwiic("imu.qwiic_out", "haptic.qwiic_in", "vbat")
    k.qwiic("haptic.qwiic_out", "sht.qwiic_in", "vbat")
    k.wire("haptic.OUT+", "motor.+", "MOTOR+", "red")
    k.wire("haptic.OUT-", "motor.-", "MOTOR-", "black")
    k.wire("mcu.pad3", "sos.A", "SOS_IN", "white", bus="gpio")
    k.wire("sos.B", "mcu.pad26", "GND", "black", bus="gpio")
    k.wire("mcu.pad5", "buzzer.+", "BUZZER_OUT", "orange", bus="gpio")
    k.wire("buzzer.-", "mcu.pad26", "GND", "black", bus="gpio")
    k.wire("mcu.pad7", "led.A", "LED_OUT", "red", bus="gpio")
    k.wire("led.K", "mcu.pad26", "GND", "black", bus="gpio")
    k.wire("battery.+", "mcu.pad2", "VBAT", "red", bus="vbat")
    k.wire("battery.-", "mcu.pad1", "GND", "black", bus="vbat")
    k.question("lipo_input", "Check the xG27 dev kit's external battery input accepts a 4.2 V LiPo directly; if not, add a 3.3 V LDO and a charger (e.g. MCP73831).", ["battery", "mcu"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["imu", "haptic", "sht", "battery"])
    k.save()


def smart_helmet_clip():
    k = reg(Kit(kit("smart_helmet_clip", "Smart helmet clip", "worker",
                    ("ble", "EFR32BG22", "Coin-cell clip that only needs to report 'worn' and impacts; BLE advertising lasts months on a CR2032."),
                    ("battery", "One CR2032 coin cell in the board's holder."),
                    "Clipped inside the helmet's suspension band; the proximity sensor faces the wearer's forehead.",
                    "Proves the helmet is worn (presence + motion) and reports hard knocks.",
                    ["Confirms the helmet is on the head in zones that need one; a missing helmet gets a reminder, never a penalty.",
                     "Notices a hard knock on the helmet."],
                    [("worn", None, "Helmet on the head (forehead proximity + recent motion)"), ("impact_g", "g", "Peak of a hard knock")],
                    budget=(0.03, 12, 3.0, "BLE advertising every 5 s, proximity sensor sampled every 10 s, accelerometer in wake-on-shock mode. Estimate."),
                    life=(250, "CR2032 ~220 mAh at ~30 µA average plus self-discharge. Estimate, not measured."),
                    ), "bg22"))
    k.bus("i2c", "I2C", "i2c", 3.0)
    k.bus("spi", "SPI", "spi", 3.0)
    k.bus("vbat", "Coin cell (3.0 V)", "power", 3.0)
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad1": "GND", "pad20": "3V3",
           "pad4": "MOSI", "pad6": "MISO", "pad8": "SCK", "pad10": "CS"}, "Advertises 'worn' and impact events over Bluetooth LE.")
    d, p = breakout(25.4, 17.8, "black", ("VCNL4040", "lga", 4.0, 2.0, 7.0), qin=True)
    k.part("prox", "Forehead proximity", "VCNL4040 Qwiic breakout", "module", d, p,
           "Sees the forehead a few millimetres away when the helmet is on.", bus="i2c", address="0x60", supply=(2.5, 3.6),
           supplied_from="vbat", measures="Proximity", bom={"desc": "Vishay VCNL4040 proximity sensor breakout, Qwiic", "cost": 7.0})
    d, p = breakout(25.4, 17.8, "black", ("ADXL372", "lga", 3.0, 3.25, 7.0), header=[("VIN", "3V3"), ("GND", "GND"), ("MOSI", "MOSI"), ("MISO", "MISO"), ("SCK", "SCK"), ("CS", "CS")])
    k.part("accel", "High-g accelerometer", "ADXL372 breakout (±200 g)", "module", d, p,
           "Measures how hard a knock was, up to 200 g, sleeping until something hits.", bus="spi", supply=(1.6, 3.5), supplied_from="vbat",
           measures="Impact acceleration", bom={"desc": "Analog Devices ADXL372 high-g accelerometer breakout", "cost": 25.0})
    k.qwiic("mcu.qwiic", "prox.qwiic_in", "vbat")
    k.wire("mcu.pad20", "accel.VIN", "3V3", "red", bus="vbat")
    k.wire("mcu.pad1", "accel.GND", "GND", "black", bus="vbat")
    k.wire("mcu.pad4", "accel.MOSI", "MOSI", "blue", bus="spi")
    k.wire("accel.MISO", "mcu.pad6", "MISO", "green", bus="spi")
    k.wire("mcu.pad8", "accel.SCK", "SCK", "yellow", bus="spi")
    k.wire("mcu.pad10", "accel.CS", "CS", "white", bus="spi")
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["prox", "accel"])
    k.save()


# =================================================================== Building and environment
def env_node():
    k = reg(Kit(kit("env_node", "Environment node", "environment",
                    ("thread", "EFR32MG24", "A Thread/Matter mesh covers a whole building from many small nodes, and every mains-powered node is a router for the others."),
                    ("usb", "5 V USB adapter; a 1000 mAh LiPo keeps it running through power cuts. The particle sensor's fan makes pure battery power impractical."),
                    "Wall-mounted at 1.5 m, away from doors and machines, with the particle sensor's inlet facing down.",
                    "Temperature, humidity, CO₂ and fine dust (PM2.5) in a room.",
                    ["Shows where the air is stale (high CO₂) or dusty.", "Feeds heat-index rest reminders for workers.",
                     "Talks Thread, so many nodes form one mesh that reaches the whole site."],
                    [("temperature", "°C", "Air temperature (SHT45)"), ("humidity", "%RH", "Relative humidity (SHT45)"),
                     ("co2_ppm", "ppm", "CO₂ (SCD40, photoacoustic NDIR)"), ("pm25_ugm3", "µg/m³", "PM2.5 (SPS30)")],
                    budget=(70, 220, 5.0, "SPS30 fan running continuously (~60 mA at 5 V), SCD40 periodic measurement (~15 mA avg), MG24 Thread router (~10 mA). Estimate."),
                    life=(1, "Back-up LiPo 1000 mAh at ~75 mA with the fan on: about 13 hours. Estimate."),
                    ), "xg24"))
    k.bus("i2c", "I2C", "i2c", 3.3)
    k.bus("vmcu", "3.3 V", "power", 3.3)
    k.bus("v5", "5 V USB", "power", 5.0)
    k.mcu({"qwiic.GND": "GND", "qwiic.3V3": "3V3", "qwiic.SDA": "SDA", "qwiic.SCL": "SCL", "pad1": "GND", "pad18": "5V", "pad16": "SDA", "pad15": "SCL"},
          "Thread router node: reads the three sensors every 5 s and passes mesh traffic for its neighbours.")
    d, p = breakout(25.4, 25.4, "black", ("SCD40", "lga", 10.1, 10.1, 6.0), qin=True, qout=True)
    k.part("co2", "CO₂ sensor", "Sensirion SCD40 Qwiic breakout", "module", d, p,
           "Measures carbon dioxide: high values mean a stuffy room that needs fresh air.", bus="i2c", address="0x62", supply=(2.4, 5.5),
           supplied_from="vmcu", measures="CO₂, temperature, humidity", bom={"desc": "Sensirion SCD40 CO₂ sensor breakout, Qwiic", "cost": 45.0})
    d, p = breakout(25.4, 17.8, "black", ("SHT45", "lga", 1.5, 1.5, 7.0), qin=True)
    k.part("sht", "Temperature / humidity", "Sensirion SHT45 Qwiic breakout", "module", d, p,
           "Accurate air temperature and humidity.", bus="i2c", address="0x44", supply=(1.08, 3.6), supplied_from="vmcu",
           measures="Temperature, humidity", bom={"desc": "Sensirion SHT45 breakout, Qwiic", "cost": 14.0})
    k.part("pm", "Particle sensor", "Sensirion SPS30", "module",
           {"family": "pcb", "w_mm": 41.0, "h_mm": 41.0, "pcb_color": "black", "dims_evidence": "typical", "label": "SPS30",
            "features": [{"family": "sensor_window", "variant": "gas", "x_mm": 8.0, "y_mm": 8.0, "w_mm": 25.0, "h_mm": 25.0},
                         {"family": "connector", "variant": "jst_ph_5", "x_mm": 15.0, "y_mm": 0.5, "w_mm": 11.0, "h_mm": 4.0}]},
           [{"name": "VDD", "signal": "5V", "gpio": None, "x_mm": 16.5, "y_mm": 0.6, "side": "top", "evidence": UNV},
            {"name": "SDA", "signal": "SDA", "gpio": None, "x_mm": 18.5, "y_mm": 0.6, "side": "top", "evidence": UNV},
            {"name": "SCL", "signal": "SCL", "gpio": None, "x_mm": 20.5, "y_mm": 0.6, "side": "top", "evidence": UNV},
            {"name": "SEL", "signal": "GND", "gpio": None, "x_mm": 22.5, "y_mm": 0.6, "side": "top", "evidence": UNV},
            {"name": "GND", "signal": "GND", "gpio": None, "x_mm": 24.5, "y_mm": 0.6, "side": "top", "evidence": UNV}],
           "A small fan pulls air through a laser chamber that counts fine dust particles.", bus="i2c", address="0x69", supply=(4.5, 5.5),
           supplied_from="v5", measures="PM1.0 / PM2.5 / PM4 / PM10", bom={"desc": "Sensirion SPS30 particulate matter sensor with cable", "cost": 45.0})
    k.qwiic("mcu.qwiic", "co2.qwiic_in")
    k.qwiic("co2.qwiic_out", "sht.qwiic_in")
    k.wire("mcu.pad18", "pm.VDD", "5V", "red", "jst_cable", "v5")
    k.wire("mcu.pad16", "pm.SDA", "SDA", "green", "jst_cable", "i2c")
    k.wire("mcu.pad15", "pm.SCL", "SCL", "yellow", "jst_cable", "i2c")
    k.wire("pm.SEL", "mcu.pad1", "GND", "black", "jst_cable", "i2c")
    k.wire("pm.GND", "mcu.pad1", "GND", "black", "jst_cable", "v5")
    k.question("pm_levels", "The SPS30 runs at 5 V; check its I2C lines are 3.3 V compatible (they are documented as 5 V tolerant only on some revisions) or add a level shifter.", ["pm"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["co2", "sht", "pm"])
    k.save()


def gas_detector_node():
    k = reg(Kit(kit("gas_detector_node", "Gas detector node", "environment",
                    ("wifi", WIFI, "Mains-powered with an alarm relay; Wi-Fi gets an alarm to the monitoring room in about a second without depending on a battery mesh."),
                    ("mains", "24 V DC from the building's safety supply, stepped down to 3.3 V."),
                    "Wall-mounted at breathing height (CO) in the hazardous store and utilities; relay drives a local sounder/beacon.",
                    "Carbon monoxide and oxygen levels in a zone, with a local alarm relay.",
                    ["Warns everyone in and around a zone when gas reaches a dangerous level.", "Adds to, never replaces, a certified gas detection system: TwinDock only advises.",
                     "Its relay can sound a local beacon even if the network is down."],
                    [("co_ppm", "ppm", "Carbon monoxide (electrochemical cell)"), ("o2_pct", "%", "Oxygen (electrochemical cell)"),
                     ("alarm", None, "Alarm threshold reached (relay energised)")],
                    budget=(95, 250, 24.0, "SiWx917 connected (~60 mA), gas module (~10 mA), relay coil when in alarm (~70 mA at 5 V). Estimate."),
                    ), "siwx917"))
    std_buses_wifi(k, [("uart", "UART (pads 12/14)", "gpio", 3.3, "ULP_UART"), ("analog", "O₂ cell", "analog", None),
                       ("v24", "24 V DC", "power", 24.0), ("gpio", "Relay output", "gpio", 3.3)])
    k.mcu({"pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND", "pad20": "3V3", "pad12": "UART_TX", "pad14": "UART_RX", "pad16": "SDA", "pad15": "SCL", "pad7": "ALARM_RELAY"},
          "Reads the CO module and the O₂ cell, drives the alarm relay, reports over Wi-Fi.")
    buck(k, "v24", 24.0, "vmcu", 3.3, (4.5, 36.0))
    d, p = breakout(32.0, 22.0, "green", None, extra=[{"family": "sensor_window", "variant": "gas", "x_mm": 7.0, "y_mm": 4.0, "w_mm": 16.0, "h_mm": 16.0}],
                    header=[("VCC", "3V3"), ("GND", "GND"), ("TX", "TX"), ("RX", "RX")])
    k.part("co", "CO sensor module", "Electrochemical CO module, UART (0-500 ppm)", "module", d, p,
           "An electrochemical cell that reports carbon monoxide in parts per million.", bus="uart", supply=(3.0, 5.5), supplied_from="vmcu",
           measures="CO 0-500 ppm", bom={"desc": "Electrochemical CO sensor module with UART output (e.g. Winsen ZE15-CO class)", "cost": 30.0})
    k.part("o2", "O₂ cell", "Electrochemical oxygen cell (mV output)", "transducer",
           {"family": "sensor_window", "variant": "gas", "w_mm": 20.0, "h_mm": 20.0, "dims_evidence": "typical"},
           [{"name": "+", "signal": "AIN_O2", "gpio": None, "x_mm": 8.0, "y_mm": 19.6, "side": "bottom", "evidence": UNV},
            {"name": "-", "signal": "GND", "gpio": None, "x_mm": 12.0, "y_mm": 19.6, "side": "bottom", "evidence": UNV}],
           "Gives a small voltage proportional to the oxygen in the air; low oxygen is as dangerous as toxic gas.", measures="O₂ 0-25 %",
           bom={"desc": "Electrochemical O₂ cell, millivolt output", "cost": 40.0})
    ads1115(k, [("A0", "AIN_O2")])
    d, p = breakout(26.0, 17.0, "blue", None, extra=[{"family": "relay", "label": "5 V 10 A", "x_mm": 3.0, "y_mm": 4.0, "w_mm": 15.0, "h_mm": 11.0},
                                                     {"family": "connector", "variant": "screw_3", "x_mm": 18.5, "y_mm": 4.0, "w_mm": 7.0, "h_mm": 11.0}],
                    header=[("VCC", "3V3"), ("GND", "GND"), ("IN", "ALARM_RELAY")])
    k.part("relay", "Alarm relay", "1-channel relay module (3.3 V input)", "module", d, p,
           "Switches a local sounder and beacon when gas is detected.", supply=(3.0, 5.5), supplied_from="vmcu",
           bom={"desc": "1-channel relay module, 3.3 V logic input", "cost": 5.0})
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.wire("mcu.pad20", "co.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "co.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad12", "co.RX", "UART_TX", "green", bus="uart")
    k.wire("co.TX", "mcu.pad14", "UART_RX", "white", bus="uart")
    i2c_hdr(k, "adc")
    k.wire("o2.+", "adc.A0", "AIN_O2", "white", bus="analog")
    k.wire("o2.-", "mcu.pad26", "GND", "black", bus="analog")
    k.wire("mcu.pad20", "relay.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "relay.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad7", "relay.IN", "ALARM_RELAY", "orange", bus="gpio")
    k.question("certified", "This node is not a certified gas detector (no ATEX/IECEx rating, no SIL). It must only add information next to the site's certified system.", ["co", "o2"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["co", "o2", "adc", "relay"])
    k.save()


def door_access():
    k = reg(Kit(kit("door_access", "Door access node", "building",
                    ("thread", "EFR32MG24", "Doors are spread around the building and mains-powered: Thread nodes route for each other, so no door needs its own Wi-Fi coverage."),
                    ("mains", "12 V DC from the door's access supply, stepped down to 3.3 V."),
                    "Board in the door's junction box; reed contact on the frame; badge reader beside the door at 1.1 m.",
                    "Door open/closed and which badge was presented.",
                    ["Shows whether a door is open, and for how long.", "Records badge presentations for restricted rooms."],
                    [("open", None, "Door contact")],
                    budget=(25, 120, 12.0, "MG24 Thread router (~10 mA), reader idle (~60 mA at 12 V, from the access supply). Estimate."),
                    ), "xg24"))
    k.bus("vmcu", "3.3 V", "power", 3.3)
    k.bus("v12", "12 V door supply", "power", 12.0)
    k.bus("gpio", "GPIO", "gpio", 3.3)
    k.bus("wiegand", "Wiegand D0/D1 (5 V side)", "gpio", 5.0)
    k.mcu({"pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND", "pad20": "3V3", "pad3": "DOOR_IN", "pad5": "WG_D0", "pad7": "WG_D1"},
          "Thread router at the door: reads the contact and the badge reader.")
    buck(k, "v12", 12.0, "vmcu", 3.3, (4.5, 36.0))
    reed(k, "door", "Door contact", "Closes when the door is shut.")
    magnet(k)
    k.part("reader", "Badge reader", "125 kHz / 13.56 MHz badge reader, Wiegand 26 output", "module",
           {"family": "pcb", "w_mm": 45.0, "h_mm": 80.0, "pcb_color": "black", "dims_evidence": "typical", "label": "READER",
            "features": [{"family": "led", "color": "#2BB673", "x_mm": 20.0, "y_mm": 6.0, "w_mm": 5.0, "h_mm": 2.5}, silk(12.0, 40.0, "BADGE", 2.4)]},
           [{"name": "12V", "signal": "V12", "gpio": None, "x_mm": 16.0, "y_mm": 79.6, "side": "bottom", "evidence": UNV},
            {"name": "GND", "signal": "GND", "gpio": None, "x_mm": 20.0, "y_mm": 79.6, "side": "bottom", "evidence": UNV},
            {"name": "D0", "signal": "WG_D0_5V", "gpio": None, "x_mm": 24.0, "y_mm": 79.6, "side": "bottom", "evidence": UNV},
            {"name": "D1", "signal": "WG_D1_5V", "gpio": None, "x_mm": 28.0, "y_mm": 79.6, "side": "bottom", "evidence": UNV}],
           "Reads the badge someone holds up and sends its number down two wires.", supply=(9.0, 14.0), supplied_from="v12",
           measures="Badge number", bom={"desc": "Wall reader with Wiegand 26 output, 12 V", "cost": 25.0})
    d, p = breakout(15.0, 13.0, "blue", ("BSS138", "soic", 3.0, 3.0, 5.0), header=[("LV", "3V3"), ("GND", "GND"), ("A1", "WG_D0"), ("A2", "WG_D1")])
    p += [{"name": "B1", "signal": "WG_D0_5V", "gpio": None, "x_mm": 5.0, "y_mm": 12.6, "side": "bottom", "evidence": UNV},
          {"name": "B2", "signal": "WG_D1_5V", "gpio": None, "x_mm": 10.0, "y_mm": 12.6, "side": "bottom", "evidence": UNV}]
    k.part("shifter", "Level shifter", "BSS138 4-channel level shifter", "module", d, p,
           "Brings the reader's 5 V signals down to the 3.3 V the board can take.", supply=(1.8, 5.5), supplied_from="vmcu",
           bom={"desc": "BSS138 bidirectional level shifter breakout", "cost": 4.0})
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.wire("buck.VIN", "reader.12V", "V12", "red", bus="v12")
    k.wire("reader.GND", "mcu.pad26", "GND", "black", bus="v12")
    k.wire("mcu.pad3", "door.A", "DOOR_IN", "white", bus="gpio")
    k.wire("door.B", "mcu.pad26", "GND", "black", bus="gpio")
    k.wire("mcu.pad20", "shifter.LV", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "shifter.GND", "GND", "black", bus="vmcu")
    k.wire("shifter.A1", "mcu.pad5", "WG_D0", "green", bus="gpio")
    k.wire("shifter.A2", "mcu.pad7", "WG_D1", "white", bus="gpio")
    k.wire("reader.D0", "shifter.B1", "WG_D0_5V", "green", bus="wiegand")
    k.wire("reader.D1", "shifter.B2", "WG_D1_5V", "white", bus="wiegand")
    k.question("hv_ref", "The shifter's 5 V reference (HV) has to come from a 5 V rail; add a small 5 V regulator from the 12 V supply.", ["shifter"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["reader", "shifter", "door"])
    k.save()


def energy_meter():
    k = reg(Kit(kit("energy_meter", "Energy meter bridge", "energy",
                    ("wifi", WIFI, "Sits in a mains distribution board; Wi-Fi brings meter readings out of a metal cabinet's gland more reliably than a mesh would."),
                    ("din_rail", "5 V DIN-rail power supply in the same distribution board, into the dev kit's USB-C."),
                    "DIN-rail meter on the feeder; the bridge board in a DIN-rail enclosure next to it, antenna through the cabinet gland.",
                    "Power, energy and voltage of one feeder, read from a certified meter over Modbus.",
                    ["Shows how much power each building uses right now and today.", "The certified meter does the measuring; the bridge only reads it."],
                    [("power_kw", "kW", "Active power"), ("energy_kwh", "kWh", "Imported energy register"), ("voltage_v", "V", "Line voltage"),
                     ("power_factor", None, "Total power factor")],
                    budget=(70, 200, 5.0, "SiWx917 connected (~60 mA), RS-485 transceiver (~1 mA idle). Estimate."),
                    ), "siwx917"))
    k.bus("vmcu", "3.3 V (VMCU)", "power", 3.3, None, "user-guide")
    k.bus("uart", "UART (pads 12/14)", "gpio", 3.3, "ULP_UART")
    k.bus("rs485", "RS-485 Modbus RTU", "gpio", None)
    k.bus("gpio", "GPIO", "gpio", 3.3)
    k.bus("v5", "5 V DIN supply", "power", 5.0)
    k.mcu({"pad1": "GND", "pad26": "GND", "pad20": "3V3", "pad12": "UART_TX", "pad14": "UART_RX", "pad3": "RS485_DE", "pad18": "5V"},
          "Polls the meter over Modbus every 5 s and publishes the values over Wi-Fi.")
    d, p = breakout(25.4, 17.8, "blue", ("MAX3485", "soic", 4.9, 3.9, 7.0),
                    extra=[{"family": "connector", "variant": "screw_3", "x_mm": 6.0, "y_mm": 11.5, "w_mm": 13.0, "h_mm": 6.0}],
                    header=[("VCC", "3V3"), ("GND", "GND"), ("DI", "TXD"), ("RO", "RXD"), ("DE", "RS485_DE")])
    p += [{"name": "A", "signal": "RS485_A", "gpio": None, "x_mm": 9.0, "y_mm": 17.4, "side": "bottom", "evidence": UNV},
          {"name": "B", "signal": "RS485_B", "gpio": None, "x_mm": 13.0, "y_mm": 17.4, "side": "bottom", "evidence": UNV}]
    k.part("rs485", "RS-485 transceiver", "MAX3485 breakout (3.3 V)", "module", d, p,
           "Turns the board's serial port into the two-wire RS-485 line the meter speaks.", bus="uart", supply=(3.0, 3.6), supplied_from="vmcu",
           bom={"desc": "MAX3485 3.3 V RS-485 transceiver breakout", "cost": 5.0})
    # Three-phase and CT-operated: the feeders it meters (compressor, production, incomer) are 400 V three-phase and
    # well above the 100 A a direct-connected single-phase meter (SDM230) can take.
    k.part("meter", "DIN-rail energy meter", "Eastron SDM630MCT-Modbus (with 3 × 400/5 A CTs)", "module",
           {"family": "din_meter", "label": "SDM630MCT", "w_mm": 72.0, "h_mm": 100.0, "dims_evidence": "typical"},
           [{"name": "A", "signal": "RS485_A", "gpio": None, "x_mm": 14.0, "y_mm": 0.4, "side": "top", "evidence": UNV},
            {"name": "B", "signal": "RS485_B", "gpio": None, "x_mm": 22.0, "y_mm": 0.4, "side": "top", "evidence": UNV}],
           "The certified meter that actually measures the electricity; we only read its registers.", bus="rs485", measures="kW, kWh, V, A",
           bom={"desc": "Three-phase CT-operated DIN-rail meter with Modbus RTU, class 1, plus three 400/5 A split-core CTs", "cost": 160.0})
    k.part("psu", "DIN-rail 5 V supply", "Mean Well HDR-15-5", "module",
           {"family": "din_meter", "label": "5V PSU", "w_mm": 18.0, "h_mm": 90.0, "dims_evidence": "typical"},
           [{"name": "V+", "signal": "5V", "gpio": None, "x_mm": 6.0, "y_mm": 0.4, "side": "top", "evidence": UNV},
            {"name": "V-", "signal": "GND", "gpio": None, "x_mm": 12.0, "y_mm": 0.4, "side": "top", "evidence": UNV}],
           "Powers the bridge from the same distribution board.", supply=(85.0, 264.0), measures="",
           bom={"desc": "15 W 5 V DIN-rail power supply", "cost": 15.0})
    k.wire("psu.V+", "mcu.pad18", "5V", "red", bus="v5")
    k.wire("psu.V-", "mcu.pad1", "GND", "black", bus="v5")
    k.wire("mcu.pad20", "rs485.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "rs485.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad12", "rs485.DI", "UART_TX", "green", bus="uart")
    k.wire("rs485.RO", "mcu.pad14", "UART_RX", "white", bus="uart")
    k.wire("mcu.pad3", "rs485.DE", "RS485_DE", "orange", bus="gpio")
    k.wire("rs485.A", "meter.A", "RS485_A", "orange", bus="rs485")
    k.wire("rs485.B", "meter.B", "RS485_B", "white", bus="rs485")
    k.question("five_in", "Pad 18 is 5 V on USB power; check feeding 5 V into it is allowed (UG581) or power the kit through USB-C from the supply.", ["psu"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["meter", "rs485", "psu"])
    k.save()


def water_leak_node():
    k = reg(Kit(kit("water_leak_node", "Water leak node", "building",
                    ("thread", "EFR32MG24", "Battery sensor on the floor of plant rooms: a Thread sleepy end device wakes only on a leak or a heartbeat."),
                    ("battery", "Two AA lithium cells (3.0 V)."),
                    "On the floor under the press hydraulics or the pump skid, probe pads touching the floor.",
                    "Water (or hydraulic oil) on the floor.",
                    ["Raises a warning the moment liquid bridges the two probe pads.", "Sleeps the rest of the time: the batteries last years."],
                    [("wet", None, "Liquid detected between the probe contacts")],
                    budget=(0.02, 15, 3.0, "Sleepy end device, 30 s heartbeat poll, wake on the comparator's edge. Estimate."),
                    life=(1800, "2 × AA lithium (~3000 mAh) at ~20 µA average, self-discharge included. Estimate, not measured."),
                    ), "xg24"))
    k.bus("vbat", "2 × AA (3.0 V)", "power", 3.0)
    k.bus("gpio", "GPIO", "gpio", 3.0)
    k.mcu({"pad1": "GND", "pad2": "VBAT_IN", "pad20": "3V3", "pad3": "LEAK_IN"}, "Sleeps until the comparator reports a leak, then wakes and tells the mesh.")
    d, p = breakout(30.0, 16.0, "green", ("LM393", "soic", 4.9, 3.9, 5.0), header=[("VCC", "3V3"), ("GND", "GND"), ("DO", "LEAK_IN")])
    p += [{"name": "P1", "signal": "PROBE_A", "gpio": None, "x_mm": 26.0, "y_mm": 15.6, "side": "bottom", "evidence": UNV},
          {"name": "P2", "signal": "PROBE_B", "gpio": None, "x_mm": 28.5, "y_mm": 15.6, "side": "bottom", "evidence": UNV}]
    k.part("comparator", "Leak comparator", "LM393 comparator module", "module", d, p,
           "Turns 'water between the probe pads' into a clean on/off signal.", supply=(3.0, 5.5), supplied_from="vbat",
           bom={"desc": "LM393 comparator module with sensitivity trimmer", "cost": 2.0})
    k.part("probe", "Leak probe", "Gold-plated floor probe (two contacts)", "transducer",
           {"family": "pcb", "w_mm": 40.0, "h_mm": 20.0, "pcb_color": "black", "dims_evidence": "typical", "label": "PROBE",
            "features": [{"family": "antenna", "variant": "trace", "x_mm": 4.0, "y_mm": 6.0, "w_mm": 32.0, "h_mm": 8.0}]},
           [{"name": "A", "signal": "PROBE_A", "gpio": None, "x_mm": 18.0, "y_mm": 0.4, "side": "top", "evidence": UNV},
            {"name": "B", "signal": "PROBE_B", "gpio": None, "x_mm": 22.0, "y_mm": 0.4, "side": "top", "evidence": UNV}],
           "Two interleaved gold tracks that conduct when water bridges them.", bom={"desc": "Floor leak probe with interleaved contacts", "cost": 5.0})
    k.part("battery", "Battery", "2 × AA lithium in holder", "transducer",
           {"family": "lipo", "label": "2×AA 3.0 V", "w_mm": 32.0, "h_mm": 58.0, "dims_evidence": "typical"},
           [{"name": "+", "signal": "VBAT", "gpio": None, "x_mm": 31.6, "y_mm": 25.0, "side": "right", "evidence": UNV},
            {"name": "-", "signal": "GND", "gpio": None, "x_mm": 31.6, "y_mm": 32.0, "side": "right", "evidence": UNV}],
           "Two AA lithium cells keep it running for years.", bom={"desc": "2 × AA lithium cells and holder", "cost": 6.0})
    k.wire("battery.+", "mcu.pad2", "VBAT", "red", bus="vbat")
    k.wire("battery.-", "mcu.pad1", "GND", "black", bus="vbat")
    k.wire("mcu.pad20", "comparator.VCC", "3V3", "red", bus="vbat")
    k.wire("mcu.pad1", "comparator.GND", "GND", "black", bus="vbat")
    k.wire("comparator.DO", "mcu.pad3", "LEAK_IN", "white", bus="gpio")
    k.wire("probe.A", "comparator.P1", "PROBE_A", "orange")
    k.wire("probe.B", "comparator.P2", "PROBE_B", "white")
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["comparator", "probe"])
    k.save()


def tank_level_node():
    k = reg(Kit(kit("tank_level_node", "Tank level node", "utility",
                    ("thread", "EFR32MG24", "Tanks sit at the edge of the site; a mains-powered Thread router extends the mesh there while reporting the level."),
                    ("usb", "5 V adapter from the pump house supply."),
                    "Ultrasonic transducer in the tank roof through a 1\" gland; board in the pump-house box with the pump contactor's auxiliary contact wired in.",
                    "Tank level and whether the refill pump runs.",
                    ["Shows how full each water tank is.", "Warns before a tank runs dry or overflows."],
                    [("level_pct", "%", "Level from the ultrasonic distance and the tank's height"), ("pump_on", None, "Refill pump contactor")],
                    budget=(30, 60, 5.0, "MG24 Thread router (~10 mA), ultrasonic module (~8 mA), opto input (~3 mA). Estimate."),
                    ), "xg24"))
    k.bus("vmcu", "3.3 V", "power", 3.3)
    k.bus("v5", "5 V", "power", 5.0)
    k.bus("uart", "UART", "gpio", 3.3)
    k.bus("gpio", "GPIO", "gpio", 3.3)
    k.mcu({"pad1": "GND", "pad26": "GND", "pad18": "5V", "pad20": "3V3", "pad14": "UART_RX", "pad3": "IN1"}, "Thread router: reads the level and the pump state.")
    d, p = breakout(42.0, 28.0, "black", ("A02YYUW", "soic", 6.0, 4.0, 10.0), header=[("VCC", "5V"), ("GND", "GND"), ("TX", "TX")])
    k.part("level", "Ultrasonic level sensor", "Waterproof ultrasonic distance sensor, UART (A02YYUW class)", "module", d, p,
           "Measures the distance down to the water surface with sound pulses.", bus="uart", supply=(3.3, 5.0), supplied_from="v5",
           measures="Distance 3-450 cm", bom={"desc": "Waterproof ultrasonic distance sensor with UART output", "cost": 15.0})
    opto(k, 1, name="Pump contactor input")
    k.wire("mcu.pad18", "level.VCC", "5V", "red", bus="v5")
    k.wire("mcu.pad26", "level.GND", "GND", "black", bus="v5")
    k.wire("level.TX", "mcu.pad14", "UART_RX", "white", bus="uart")
    k.wire("mcu.pad20", "opto.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad1", "opto.GND", "GND", "black", bus="vmcu")
    k.wire("opto.OUT1", "mcu.pad3", "IN1", "green", bus="gpio")
    k.question("uart_level", "Check the sensor's TX level is 3.3 V safe when powered at 5 V (add a divider otherwise).", ["level"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["level", "opto"])
    k.save()


def genset_bridge():
    """Reads the standby generator's existing auto-mains-failure controller over Modbus. The controller (not this kit)
    detects the mains failure, starts the engine and switches the transfer switch; the bridge only reads its registers."""
    k = reg(Kit(kit("genset_bridge", "Generator controller bridge", "energy",
                    ("wifi", WIFI, "In the generator room's control cabinet; Wi-Fi reaches the utilities block, and the controller already speaks Modbus."),
                    ("din_rail", "24 V DC from the generator's battery-backed control supply through a DIN-rail step-down to 5 V, into the dev kit's USB-C."),
                    "Bridge in a DIN-rail enclosure in the generator control cabinet, on the controller's spare RS-485 port.",
                    "Engine state, speed, coolant temperature, fuel use, load and the transfer switch position, read from the existing AMF controller.",
                    ["Shows the generator starting, taking the critical load and cooling down after the grid returns.",
                     "Only reads the controller: starting, stopping and switching stay with the certified generator controller."],
                    [("engine_state", None, "Engine state: off, start_delay, cranking, accelerating, running, cooldown"), ("rpm", "rpm", "Engine speed"),
                     ("coolant_c", "°C", "Coolant temperature"), ("fuel_lph", "L/h", "Fuel rate"), ("load_kw", "kW", "Generator load"),
                     ("transfer", None, "Transfer switch position: mains, generator or open"), ("mains_ok", None, "Controller sees healthy mains")],
                    budget=(70, 200, 5.0, "SiWx917 connected (~60 mA), RS-485 transceiver (~1 mA idle). Estimate."),
                    ), "siwx917"))
    k.bus("vmcu", "3.3 V (VMCU)", "power", 3.3, None, "user-guide")
    k.bus("uart", "UART (pads 12/14)", "gpio", 3.3, "ULP_UART")
    k.bus("rs485", "RS-485 Modbus RTU", "gpio", None)
    k.bus("gpio", "GPIO", "gpio", 3.3)
    k.bus("v5", "5 V DIN supply", "power", 5.0)
    k.mcu({"pad1": "GND", "pad26": "GND", "pad20": "3V3", "pad12": "UART_TX", "pad14": "UART_RX", "pad3": "RS485_DE", "pad18": "5V"},
          "Polls the generator controller's registers over Modbus every 5 s (state changes at once) and publishes them over Wi-Fi.")
    d, p = breakout(25.4, 17.8, "blue", ("MAX3485", "soic", 4.9, 3.9, 7.0),
                    extra=[{"family": "connector", "variant": "screw_3", "x_mm": 6.0, "y_mm": 11.5, "w_mm": 13.0, "h_mm": 6.0}],
                    header=[("VCC", "3V3"), ("GND", "GND"), ("DI", "TXD"), ("RO", "RXD"), ("DE", "RS485_DE")])
    p += [{"name": "A", "signal": "RS485_A", "gpio": None, "x_mm": 9.0, "y_mm": 17.4, "side": "bottom", "evidence": UNV},
          {"name": "B", "signal": "RS485_B", "gpio": None, "x_mm": 13.0, "y_mm": 17.4, "side": "bottom", "evidence": UNV}]
    k.part("rs485", "RS-485 transceiver", "MAX3485 breakout (3.3 V)", "module", d, p,
           "Turns the board's serial port into the two-wire RS-485 line the controller speaks.", bus="uart", supply=(3.0, 3.6), supplied_from="vmcu",
           bom={"desc": "MAX3485 3.3 V RS-485 transceiver breakout", "cost": 5.0})
    k.part("amf", "Generator AMF controller (existing)", "Deep Sea Electronics DSE7320 MKII auto mains failure controller (already on the generator)", "module",
           {"family": "din_meter", "label": "DSE7320", "w_mm": 240.0, "h_mm": 172.0, "dims_evidence": "typical"},
           [{"name": "A", "signal": "RS485_A", "gpio": None, "x_mm": 110.0, "y_mm": 0.4, "side": "top", "evidence": UNV},
            {"name": "B", "signal": "RS485_B", "gpio": None, "x_mm": 120.0, "y_mm": 0.4, "side": "top", "evidence": UNV}],
           "The generator's own controller: it detects the mains failure, starts the engine and switches the load. The bridge only reads it.",
           bus="rs485", measures="Engine state, speed, coolant temperature, fuel, load, transfer switch", bom={"desc": "Existing on the generator (not bought)", "cost": 0.0})
    k.part("psu", "DIN-rail 5 V supply", "Mean Well DDR-15G-5 (9-36 V in)", "module",
           {"family": "din_meter", "label": "5V", "w_mm": 18.0, "h_mm": 90.0, "dims_evidence": "typical"},
           [{"name": "V+", "signal": "5V", "gpio": None, "x_mm": 6.0, "y_mm": 0.4, "side": "top", "evidence": UNV},
            {"name": "V-", "signal": "GND", "gpio": None, "x_mm": 12.0, "y_mm": 0.4, "side": "top", "evidence": UNV}],
           "Powers the bridge from the generator's 24 V control battery, so it keeps reporting while the mains is down.", supply=(9.0, 36.0), measures="",
           bom={"desc": "15 W DC-DC DIN-rail converter, 9-36 V in, 5 V out", "cost": 18.0})
    k.wire("psu.V+", "mcu.pad18", "5V", "red", bus="v5")
    k.wire("psu.V-", "mcu.pad1", "GND", "black", bus="v5")
    k.wire("mcu.pad20", "rs485.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "rs485.GND", "GND", "black", bus="vmcu")
    k.wire("mcu.pad12", "rs485.DI", "UART_TX", "green", bus="uart")
    k.wire("rs485.RO", "mcu.pad14", "UART_RX", "white", bus="uart")
    k.wire("mcu.pad3", "rs485.DE", "RS485_DE", "orange", bus="gpio")
    k.wire("rs485.A", "amf.A", "RS485_A", "orange", bus="rs485")
    k.wire("rs485.B", "amf.B", "RS485_B", "white", bus="rs485")
    k.question("five_in", "Pad 18 is 5 V on USB power; check feeding 5 V into it is allowed (UG581) or power the kit through USB-C from the supply.", ["psu"])
    k.question("registers", "Map the controller's Modbus registers (engine state, rpm, coolant, fuel rate, load, transfer) from its GenComm register document; read-only access only.", ["amf"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["amf", "rs485", "psu"])
    k.save()


def fire_panel_bridge():
    k = reg(Kit(kit("fire_panel_bridge", "Fire panel bridge", "fire",
                    ("wifi", WIFI, "Mains/battery-backed panel room; Wi-Fi delivers an alarm to the monitoring room in about a second."),
                    ("mains", "24 V DC auxiliary output of the fire panel (battery-backed), stepped down to 3.3 V."),
                    "Next to the fire panel, wired to its spare volt-free alarm and trouble relay contacts through opto inputs.",
                    "Fire alarm and panel trouble, read from an existing certified fire panel.",
                    ["Shows a fire alarm on the monitoring screens and starts the evacuation advice.",
                     "Only reads the panel's spare contacts: it never replaces, silences or controls the certified fire system."],
                    [("alarm", None, "Panel general alarm contact"), ("trouble", None, "Panel trouble / fault contact")],
                    budget=(70, 180, 24.0, "SiWx917 connected (~60 mA), two opto inputs (~6 mA). Estimate."),
                    ), "siwx917"))
    k.bus("vmcu", "3.3 V (VMCU)", "power", 3.3, None, "user-guide")
    k.bus("v24", "24 V panel auxiliary", "power", 24.0)
    k.bus("gpio", "Digital inputs", "gpio", 3.3)
    k.mcu({"pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND", "pad20": "3V3", "pad3": "ALARM_IN", "pad5": "TROUBLE_IN"},
          "Watches the two contacts and reports every change and a 10 s heartbeat.")
    buck(k, "v24", 24.0, "vmcu", 3.3, (4.5, 36.0))
    opto(k, 2, name="Panel contact inputs")
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    k.wire("mcu.pad20", "opto.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "opto.GND", "GND", "black", bus="vmcu")
    k.wire("opto.OUT1", "mcu.pad3", "IN1", "red", bus="gpio")
    k.wire("opto.OUT2", "mcu.pad5", "IN2", "orange", bus="gpio")
    k.question("panel_contacts", "Use only spare volt-free contacts approved by the fire panel's maintainer; the bridge must not load the panel's own circuits.", ["opto"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["opto", "buck"])
    k.save()


def water_quality_node():
    k = reg(Kit(kit("water_quality_node", "Water quality node", "utility",
                    ("wifi", WIFI, "Mains-powered in the ETP control cabinet; Wi-Fi reaches the utilities block and the probes need a steady supply and a fast ADC."),
                    ("mains", "24 V DC from the ETP control panel, stepped down to 3.3 V."),
                    "Board in the ETP cabinet; pH and turbidity probes in a flow cell on the inflow or outflow pipe.",
                    "pH and turbidity of the effluent, at the plant inflow or its outflow.",
                    ["Shows whether the treated water leaving the plant is inside its limits.", "A pH or cloudiness reading outside the limits raises a warning."],
                    [("ph", "pH", "pH (probe + interface board)"), ("turbidity_ntu", "NTU", "Turbidity (optical sensor)")],
                    budget=(80, 200, 24.0, "SiWx917 connected (~60 mA), probe interface boards (~10 mA each at 5 V), ADC. Estimate."),
                    ), "siwx917"))
    std_buses_wifi(k, [("analog", "Probe outputs", "analog", None), ("v24", "24 V DC", "power", 24.0)])
    k.mcu({"pad2": "VMCU_IN", "pad1": "GND", "pad26": "GND", "pad20": "3V3", "pad16": "SDA", "pad15": "SCL"}, "Reads both probes through the ADC and reports over Wi-Fi.")
    buck(k, "v24", 24.0, "vmcu", 3.3, (4.5, 36.0))
    ads1115(k, [("A0", "AIN_PH"), ("A1", "AIN_NTU")])
    k.part("ph_board", "pH interface board", "Analog pH interface board (BNC input, 0-3 V output)", "module",
           {"family": "pcb", "w_mm": 42.0, "h_mm": 32.0, "pcb_color": "black", "dims_evidence": "typical", "label": "pH",
            "features": [{"family": "connector", "variant": "jst_ph_3", "x_mm": 2.0, "y_mm": 24.0, "w_mm": 6.0, "h_mm": 6.0}, silk(12.0, 14.0, "pH BOARD", 2.0)]},
           [{"name": "VCC", "signal": "3V3", "gpio": None, "x_mm": 3.0, "y_mm": 31.6, "side": "bottom", "evidence": UNV},
            {"name": "GND", "signal": "GND", "gpio": None, "x_mm": 5.0, "y_mm": 31.6, "side": "bottom", "evidence": UNV},
            {"name": "OUT", "signal": "AIN_PH", "gpio": None, "x_mm": 7.0, "y_mm": 31.6, "side": "bottom", "evidence": UNV},
            {"name": "BNC", "signal": "PH_SIGNAL", "gpio": None, "x_mm": 41.6, "y_mm": 6.0, "side": "right", "evidence": UNV}],
           "Amplifies the tiny signal from the pH probe into a voltage the ADC can read.", supply=(3.0, 5.5), supplied_from="vmcu",
           bom={"desc": "Analog pH interface board with BNC connector", "cost": 30.0})
    k.part("ph_probe", "pH probe", "Industrial pH electrode, BNC", "transducer",
           {"family": "probe", "w_mm": 120.0, "h_mm": 14.0, "dims_evidence": "typical"},
           [{"name": "BNC", "signal": "PH_SIGNAL", "gpio": None, "x_mm": 119.6, "y_mm": 7.0, "side": "right", "evidence": UNV}],
           "The glass electrode that sits in the water.", measures="pH", bom={"desc": "Industrial pH electrode with BNC connector and 1 m cable", "cost": 60.0})
    k.part("turbidity", "Turbidity sensor", "Optical turbidity sensor module (analog output)", "module",
           {"family": "pcb", "w_mm": 40.0, "h_mm": 30.0, "pcb_color": "black", "dims_evidence": "typical", "label": "NTU",
            "features": [{"family": "sensor_window", "variant": "light", "x_mm": 28.0, "y_mm": 8.0, "w_mm": 8.0, "h_mm": 8.0}]},
           [{"name": "VCC", "signal": "3V3", "gpio": None, "x_mm": 4.0, "y_mm": 29.6, "side": "bottom", "evidence": UNV},
            {"name": "GND", "signal": "GND", "gpio": None, "x_mm": 6.0, "y_mm": 29.6, "side": "bottom", "evidence": UNV},
            {"name": "OUT", "signal": "AIN_NTU", "gpio": None, "x_mm": 8.0, "y_mm": 29.6, "side": "bottom", "evidence": UNV}],
           "Shines light through the water and measures how cloudy it is.", supply=(3.0, 5.5), supplied_from="vmcu", measures="Turbidity",
           bom={"desc": "Optical turbidity sensor with analog output", "cost": 20.0})
    k.wire("buck.VOUT", "mcu.pad2", "3V3", "red", bus="vmcu")
    k.wire("buck.GND", "mcu.pad1", "GND", "black", bus="vmcu")
    i2c_hdr(k, "adc")
    k.wire("mcu.pad20", "ph_board.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "ph_board.GND", "GND", "black", bus="vmcu")
    k.wire("ph_board.OUT", "adc.A0", "AIN_PH", "white", bus="analog")
    k.wire("ph_probe.BNC", "ph_board.BNC", "PH_SIGNAL", "grey", bus="analog")
    k.wire("mcu.pad20", "turbidity.VCC", "3V3", "red", bus="vmcu")
    k.wire("mcu.pad26", "turbidity.GND", "GND", "black", bus="vmcu")
    k.wire("turbidity.OUT", "adc.A1", "AIN_NTU", "white", bus="analog")
    k.question("probe_cal", "pH probes need two-point calibration and turbidity sensors a reference; plan a calibration routine (not simulated here).", ["ph_probe", "turbidity"])
    k.question("parts_tbc", "All third-party part numbers, sizes, supply ranges and costs are from memory: check each datasheet before ordering.", ["ph_board", "ph_probe", "turbidity", "adc"])
    k.save()


if __name__ == "__main__":
    for fn in (truck_telematics, dock_bay, pallet_asset_tag, machine_monitor, conveyor_monitor, compressor_monitor, worker_badge,
               smart_helmet_clip, env_node, gas_detector_node, door_access, energy_meter, genset_bridge, water_leak_node, tank_level_node, fire_panel_bridge,
               water_quality_node):
        fn()
    print("wrote", len(ALL), "kits", file=sys.stderr)
