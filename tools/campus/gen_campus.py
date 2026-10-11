#!/usr/bin/env python3
"""Expands the two-site model (WH-01 + FAC-01) into "Riverside Campus" (FACTORY_PROMPTS.md F1).

Run from the repo root:  .venv/bin/python tools/campus/gen_campus.py

Patches backend/world/layout.json and backend/world/sites.json in place. It is idempotent: everything it adds
is tagged (`"campus": true` on nodes, lanes, zones, devices, workers) and removed again before it adds it, so
editing this file and re-running is the way to change the campus. Geometry notes are in docs/campus_plan.md.

Coordinates: metres, x east, z south, origin at the warehouse's north-west corner (same grid as before).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "backend" / "world" / "layout.json"
SITES = ROOT / "backend" / "world" / "sites.json"


def rect(x: float, z: float, w: float, d: float) -> list[list[float]]:
    return [[x, z], [x + w, z], [x + w, z + d], [x, z + d]]


# ---------------------------------------------------------------------------------------------------------------
# Buildings (all new). `door` is the ped door node id; `h` is the roof height in metres.
# `zone` is the zone that carries hazard level, PPE and devices (see ZONES).
# ---------------------------------------------------------------------------------------------------------------
BUILDINGS = [
    dict(id="SEC_CABIN", kind="security", name="Security cabin", x=76, z=33, w=6, d=4, h=3.2, zone="WH01_GATE", door="WALK_CAB"),
    dict(id="ADMIN", kind="admin", name="Admin office and reception", x=58, z=56, w=20, d=16, h=7.2, zone="WH01_ADMIN", door="WALK_ADMIN"),
    dict(id="CANTEEN", kind="canteen", name="Canteen", x=88, z=56, w=16, d=12, h=4.5, zone="FAC01_CANTEEN", door="WALK_CANTEEN"),
    dict(id="MEDICAL", kind="medical", name="First aid and medical room", x=106, z=56, w=8, d=8, h=3.6, zone="FAC01_MEDICAL", door="WALK_MED"),
    dict(id="RAW_STORE", kind="raw_store", name="Raw material store", x=118, z=56, w=32, d=22, h=8.5, zone="FAC01_RAW", door="WALK_RAW",
         doors=[dict(id="R1", wall="east", at=62, w=4, node="RAW_DOCK_1"), dict(id="R2", wall="east", at=70, w=4, node="RAW_DOCK_2"),
                dict(id="RN", wall="north", at=130, w=3.2, node="RAW_N")]),
    dict(id="QC_LAB", kind="lab", name="Quality control lab", x=143, z=2, w=16, d=14, h=4.0, zone="FAC01_QC", door="WALK_QCL"),
    dict(id="WORKSHOP", kind="workshop", name="Maintenance workshop and spare-parts store", x=143, z=20, w=26, d=16, h=7.0, zone="FAC01_WORKSHOP", door="WALK_WS"),
    dict(id="SUBSTATION", kind="substation", name="Electrical substation and transformer", x=172, z=-6, w=16, d=14, h=5.0, zone="FAC01_SUBSTATION", door="WALK_SUB"),
    dict(id="GENERATOR", kind="generator", name="Diesel generator", x=196, z=-6, w=14, d=12, h=4.5, zone="FAC01_GENERATOR", door="WALK_GEN"),
    dict(id="COMPRESSOR", kind="compressor", name="Air compressor room", x=172, z=12, w=16, d=12, h=5.0, zone="FAC01_COMPRESSOR", door="WALK_COMP"),
    dict(id="PUMP_HOUSE", kind="pump_house", name="Water pump house", x=173, z=26, w=6, d=4, h=3.0, zone="FAC01_TANKS", door="WALK_TANK"),
    dict(id="HAZMAT", kind="hazmat", name="Hazardous materials store (bunded)", x=196, z=62, w=14, d=14, h=4.0, zone="FAC01_HAZMAT", door="WALK_HAZ"),
    dict(id="FIRE_PUMP", kind="fire_pump", name="Fire pump house", x=178, z=54, w=10, d=8, h=4.0, zone="FAC01_FIREPUMP", door="WALK_PUMP"),
]

# Outdoor structures (not buildings): tanks, ETP basins, weighbridge, barrier, parking, EV chargers.
TANKS = [dict(id="WT-1", x=177, z=32, r=3.5, h=8, label="Water tank 1", zone="FAC01_TANKS"),
         dict(id="WT-2", x=184, z=32, r=3.5, h=8, label="Water tank 2", zone="FAC01_TANKS"),
         dict(id="FT-1", x=194, z=59, r=4.0, h=6, label="Fire water tank", zone="FAC01_FIREPUMP"),
         dict(id="DT-1", x=205, z=-8, r=1.6, h=3, label="Diesel day tank", zone="FAC01_GENERATOR")]
ETP = dict(id="ETP", x=196, z=12, w=18, d=22, zone="FAC01_ETP", door="WALK_ETP",
           basins=[dict(x=198, z=14, w=7, d=8, label="Equalisation"), dict(x=207, z=14, w=5, d=8, label="Aeration"),
                   dict(x=198, z=24, w=14, d=7, label="Clarifier")])
WEIGHBRIDGE = dict(id="WEIGH", x=64, z=41, w=8, d=6, node="WEIGH", label="Weighbridge")
BARRIER = dict(id="BOOM", x=84, z0=40.5, z1=47.5, node="ROAD_E", label="Boom barrier")
PARKING = dict(
    cars=dict(x=-10, z=56, w=52, d=22, rows=4, bays_per_row=12, label="Car park"),
    two_wheelers=dict(x=46, z=56, w=10, d=8, label="Two-wheeler park"),
    ev_chargers=[dict(id=f"EV-{i + 1}", x=-8 + i * 3.2, z=57.2, w=1.0, d=1.0) for i in range(6)],
)
MUSTER = [dict(id="MP-1", name="Muster point 1 (car park south)", x=43.5, z=90.0, radius_m=6.0, node="PMP1"),
          dict(id="MP-2", name="Muster point 2 (raw store west)", x=116.0, z=92.0, radius_m=6.0, node="PMP2"),
          dict(id="MP-3", name="Muster point 3 (east fire pump)", x=166.0, z=88.0, radius_m=6.0, node="PMP3")]
SOLAR = [dict(id="PV-WH", building="WAREHOUSE", kwp=110.0, panels=[[2, 2, 40, 11], [2, 14, 40, 11]]),
         dict(id="PV-FAC", building="FACTORY", kwp=160.0, panels=[[90, 2, 48, 10], [90, 14, 38, 10]]),
         dict(id="PV-RAW", building="RAW_STORE", kwp=90.0, panels=[[120, 58, 28, 8.5], [120, 68, 28, 8.5]])]

ROADS = [  # painted vehicle roads added to the existing three (TRUCK_LANE is extended east)
    dict(id="RAW_ROAD", points=[[158, 44], [158, 98]], width=7, dashed=True),
    dict(id="SOUTH_ROAD", points=[[-10, 98], [215, 98]], width=7, dashed=True),
    dict(id="W_LINK", points=[[-10, 44], [-10, 98]], width=7, dashed=False),
    dict(id="E_LINK", points=[[215, 44], [215, 98]], width=7, dashed=False),
]

# Fire hydrant ring: pipe loop around the campus, a hydrant every ~28 m plus one at every building door.
HYDRANT_LOOP = [[-9, -9], [214, -9], [214, 102], [-9, 102]]

# ---------------------------------------------------------------------------------------------------------------
# Pedestrian graph. Names starting WALK_ are work stands / doors: simulated badges pause at them.
# ---------------------------------------------------------------------------------------------------------------
PED_NODES: dict[str, tuple[float, float, str, str]] = {
    # id: (x, z, type, label)
    # warehouse west staff door -> crossing X0 -> south walkway H1w
    "WALK_WH": (-1.5, 26, "door", "Warehouse staff door"), "P_WH2": (-1.5, 38, "junction", "Warehouse fence walkway"),
    "XN0": (-1.5, 39.2, "crossing", "Crossing X0 north"), "XS0": (-1.5, 48.8, "crossing", "Crossing X0 south"),
    "P1_m1": (-1.5, 52, "junction", "South walkway"), "P1_10": (10, 52, "junction", "South walkway"), "P1_20": (20, 52, "junction", "South walkway"),
    "P1_32": (32, 52, "junction", "South walkway"), "P1_43": (43.5, 52, "junction", "South walkway"), "P1_51": (51, 52, "junction", "South walkway"),
    "P1_68": (68, 52, "junction", "South walkway"), "P1_79": (79, 52, "junction", "South walkway"), "P1_96": (96, 52, "junction", "South walkway"),
    "P1_110": (110, 52, "junction", "South walkway"), "P1_116": (116, 52, "junction", "South walkway"),
    # gate: security cabin and crossing X4
    "WALK_CAB": (79, 38, "door", "Security cabin door"), "XN4": (79, 39.2, "crossing", "Crossing X4 north"), "XS4": (79, 48.8, "crossing", "Crossing X4 south"),
    # doors on the south walkway
    "WALK_PARK": (20, 55, "door", "Car park entrance"), "WALK_PARK2": (32, 55, "door", "Car park east entrance"), "WALK_2W": (51, 55, "door", "Two-wheeler park"),
    "WALK_ADMIN": (68, 55, "door", "Reception"), "WALK_CANTEEN": (96, 55, "door", "Canteen door"), "WALK_MED": (110, 55, "door", "First aid door"),
    # crossing X1 at the factory office, north walkway H0
    "WALK_FAC_OFF": (96, 38.5, "door", "Factory office south door"), "XN1": (96, 39.2, "crossing", "Crossing X1 north"), "XS1": (96, 48.8, "crossing", "Crossing X1 south"),
    "P0_108": (108, 38.5, "junction", "North walkway"), "P0_126": (126, 38.5, "junction", "North walkway (forklift crossing X7)"),
    "P0_134": (134, 38.5, "junction", "North walkway (forklift crossing X7)"), "P0_141": (141.5, 38.5, "junction", "North walkway"),
    "P0_150": (150, 38.5, "junction", "North walkway"), "P0_160": (160, 38.5, "junction", "North walkway"), "P0_172": (172, 38.5, "junction", "North walkway"),
    "P0_192": (192, 38.5, "junction", "North walkway"),
    # QC lab / workshop corridor x = 141.5
    "P_Q_N": (141.5, 2, "junction", "QC lab corridor"), "WALK_QCL": (141.5, 9, "door", "QC lab door"), "WALK_WS": (141.5, 29, "door", "Workshop door"),
    "P_FAC_E": (139, 10, "junction", "Factory east door"),
    # utilities corridor x = 192
    "P_U_N": (192, -7, "junction", "Utilities corridor"), "P_U0": (192, 0, "junction", "Utilities corridor"), "P_U1": (192, 18, "junction", "Utilities corridor"),
    "P_U2": (192, 22, "junction", "Utilities corridor"), "P_U3": (192, 31, "junction", "Utilities corridor"),
    "WALK_SUB": (189.5, 0, "door", "Substation door"), "WALK_GEN": (194.5, 0, "door", "Generator door"), "WALK_COMP": (189.5, 18, "door", "Compressor room door"),
    "WALK_ETP": (194.5, 22, "door", "ETP door"), "WALK_TANK": (189.5, 31, "door", "Water tanks and pumps"),
    "XN3": (192, 39.2, "crossing", "Crossing X3 north"), "XS3": (192, 48.8, "crossing", "Crossing X3 south"),
    # east south walkway H1e, fire pump, hazmat, muster 3
    "P1e_166": (166, 52, "junction", "South-east walkway"), "P1e_183": (183, 52, "junction", "South-east walkway"), "P1e_192": (192, 52, "junction", "South-east walkway"),
    "P1e_200": (200, 52, "junction", "South-east walkway"), "WALK_PUMP": (183, 53, "door", "Fire pump house door"),
    "P_V3a": (166, 69, "junction", "Hazmat walkway"), "WALK_HAZ": (194.5, 69, "door", "Hazmat store door"),
    # raw store west door, muster points
    "WALK_RAW": (116, 67, "door", "Raw store west door"), "P_V1b": (116, 80, "junction", "Raw store walkway"),
    "P_V0b": (43.5, 70, "junction", "Car park walkway"),
    "PMP1": (43.5, 90, "muster", "Muster point 1"), "PMP2": (116, 92, "muster", "Muster point 2"), "PMP3": (166, 88, "muster", "Muster point 3"),
}
PED_CHAINS = [  # consecutive ids are joined by a walkway lane
    ["WALK_WH", "P_WH2", "XN0"], ["XS0", "P1_m1", "P1_10", "P1_20", "P1_32", "P1_43", "P1_51", "P1_68", "P1_79", "P1_96", "P1_110", "P1_116"],
    ["WALK_CAB", "XN4"], ["XS4", "P1_79"],
    ["P1_20", "WALK_PARK"], ["P1_32", "WALK_PARK2"], ["P1_51", "WALK_2W"], ["P1_68", "WALK_ADMIN"], ["P1_96", "WALK_CANTEEN"], ["P1_110", "WALK_MED"],
    ["WALK_FAC_OFF", "XN1"], ["XS1", "P1_96"],
    ["WALK_FAC_OFF", "P0_108", "P0_126"], ["P0_134", "P0_141", "P0_150", "P0_160", "P0_172", "P0_192"],
    ["P_Q_N", "WALK_QCL", "WALK_WS", "P0_141"], ["P_FAC_E", "WALK_QCL"],
    ["P_U_N", "P_U0", "P_U1", "P_U2", "P_U3", "P0_192"], ["P_U0", "WALK_SUB"], ["P_U0", "WALK_GEN"], ["P_U1", "WALK_COMP"], ["P_U2", "WALK_ETP"], ["P_U3", "WALK_TANK"],
    ["P0_192", "XN3"], ["XS3", "P1e_192"], ["P1e_166", "P1e_183", "P1e_192", "P1e_200"], ["P1e_183", "WALK_PUMP"],
    ["P1e_166", "P_V3a", "PMP3"], ["P_V3a", "WALK_HAZ"],
    ["P1_116", "WALK_RAW", "P_V1b", "PMP2"], ["P1_43", "P_V0b", "PMP1"],
]
# Crossing lanes: a walkway that is allowed to cross a vehicle road (or forklift lane). (id, a, b)
CROSSINGS = [("X0", "XN0", "XS0", "road"), ("X1", "XN1", "XS1", "road"), ("X3", "XN3", "XS3", "road"), ("X4", "XN4", "XS4", "road"),
             ("X7", "P0_126", "P0_134", "forklift")]
# Walkway joining the existing factory floor to the new corridor (inside the hall, so not tested against forklift lanes).
LEGACY_LINKS = [("WALK_OFFICE", "WALK_FAC_OFF"), ("WALK_EAST", "P_FAC_E"),
                # the existing factory-floor stands, joined into one network (inside the hall, where people share aisles)
                ("WALK_OFFICE", "WALK_STAFF_DOOR"), ("WALK_STAFF_DOOR", "WALK_QC"), ("WALK_QC", "WALK_PACKER"), ("WALK_PACKER", "WALK_PRESS"),
                ("WALK_PRESS", "WALK_EAST"), ("WALK_EAST", "WALK_COLD_DOOR"), ("WALK_COLD_DOOR", "WALK_COLD"),
                ("WALK_STAFF_DOOR", "WALK_DOCK_DOOR"), ("WALK_DOCK_DOOR", "WALK_DOCKS")]

# ---------------------------------------------------------------------------------------------------------------
# Vehicle graph additions
# ---------------------------------------------------------------------------------------------------------------
VEH_NODES = [
    dict(id="WEIGH", type="junction", x=68, z=44, kinds=["truck"], label="Weighbridge"),
    dict(id="RD_110", type="junction", x=110, z=44, kinds=["truck"], label="Service road"),
    dict(id="RD_158", type="junction", x=158, z=44, kinds=["truck"], label="Raw material road"),
    dict(id="RD_186", type="junction", x=186, z=44, kinds=["truck"], label="Service road"),
    dict(id="RD_215", type="junction", x=215, z=44, kinds=["truck"], label="Service road end"),
    dict(id="RR_1", type="junction", x=158, z=56, kinds=["truck"], label="Raw material road"),
    dict(id="RR_2", type="junction", x=158, z=62, kinds=["truck"], label="Raw dock 1 approach"),
    dict(id="RR_3", type="junction", x=158, z=70, kinds=["truck"], label="Raw dock 2 approach"),
    dict(id="RR_4", type="junction", x=158, z=82, kinds=["truck"], label="Turning area"),
    dict(id="RAW_BAY_1", type="bay", x=156, z=62, kinds=["truck"], label="Raw dock 1 bay"),
    dict(id="RAW_BAY_2", type="bay", x=156, z=70, kinds=["truck"], label="Raw dock 2 bay"),
    dict(id="RAW_DOCK_1", type="dock", x=147, z=62, kinds=["forklift"], label="Raw store dock 1"),
    dict(id="RAW_DOCK_2", type="dock", x=147, z=70, kinds=["forklift"], label="Raw store dock 2"),
    dict(id="RAW_AISLE_E", type="junction", x=140, z=66, kinds=["forklift"], label="Raw store east aisle"),
    dict(id="RAW_AISLE_W", type="junction", x=130, z=66, kinds=["forklift"], label="Raw store west aisle"),
    dict(id="RAW_N", type="junction", x=130, z=57.5, kinds=["forklift"], label="Raw store north door"),
    dict(id="RAW_X1", type="junction", x=130, z=50, kinds=["forklift"], label="Raw material route"),
    dict(id="RAW_X2", type="junction", x=130, z=36, kinds=["forklift"], label="Raw material route"),
    dict(id="FAC_YARD", type="junction", x=113, z=32, kinds=["forklift"], label="Factory south yard"),
    dict(id="FAC_DOOR_S", type="junction", x=113, z=24, kinds=["forklift"], label="Factory south door"),
    # raw material flow (auto mode): trucks unload at the raw docks, FL-05 moves pallets to the line's inbound spot
    dict(id="RAW_STOCK", type="zone", x=136, z=69, kinds=["forklift"], label="Raw stock",
         spots=[[133.5, 68.0], [136.0, 68.0], [138.5, 68.0], [133.5, 70.5], [136.0, 70.5], [138.5, 70.5]]),
    dict(id="FAC_IN", type="zone", x=112, z=21.5, kinds=["forklift"], label="Factory inbound",
         spots=[[110.0, 21.0], [112.0, 21.0], [114.0, 21.0], [110.0, 22.8]]),
    dict(id="RAW_CHARGER", type="charger", x=127, z=64, kinds=["forklift"], label="Charger R1"),
]
RAW_DOCKS = [dict(id="DK-04", node="RAW_DOCK_1", bay_node="RAW_BAY_1", door="R1", label="Raw dock 1", area="raw"),
             dict(id="DK-05", node="RAW_DOCK_2", bay_node="RAW_BAY_2", door="R2", label="Raw dock 2", area="raw")]
RAW_CHARGER = dict(id="CH-03", node="RAW_CHARGER", label="Charger R1")
RAW_TRUCK = dict(id="TR-03", node="RD_110", heading_rad=3.1416, state="arriving", capacity=4, inbound=True,
                 meta={"plate": "RLH 5512", "carrier": "Ironbridge Supply", "route": "Inbound, raw material for FAC-01", "area": "raw"})
RAW_FORKLIFT = dict(id="FL-05", node="RAW_AISLE_W", heading_rad=0, battery_pct=88, meta={"operator": "Ines Duarte", "model": "Electric counterbalance, 1.6 t", "area": "raw"}, plan=[])
RAW_PALLETS = [dict(id=f"RM-{i + 1:02d}", at="TR-03", meta={"sku": f"RM-{3100 + i}", "contents": c}) for i, c in
               enumerate(["Steel coil, 2 t", "Resin pellets, 40 bags", "Packaging film, 12 rolls", "Fasteners, 20 boxes"])]
VEH_LANES = [
    ("GATE_IN", "WEIGH", ["truck"]), ("WEIGH", "ROAD_E", ["truck"]), ("WEIGH", "ROAD_IN", ["truck"]),
    ("ROAD_IN", "RD_110", ["truck"]), ("RD_110", "RD_158", ["truck"]), ("RD_158", "RD_186", ["truck"]), ("RD_186", "RD_215", ["truck"]),
    ("RD_158", "RR_1", ["truck"]), ("RR_1", "RR_2", ["truck"]), ("RR_2", "RR_3", ["truck"]), ("RR_3", "RR_4", ["truck"]),
    ("FAC_DOOR_S", "FAC_IN", ["forklift"]), ("RAW_AISLE_E", "RAW_STOCK", ["forklift"]), ("RAW_AISLE_W", "RAW_CHARGER", ["forklift"]),
    ("RAW_DOCK_1", "RAW_AISLE_E", ["forklift"]), ("RAW_DOCK_2", "RAW_AISLE_E", ["forklift"]), ("RAW_AISLE_E", "RAW_AISLE_W", ["forklift"]),
    ("RAW_AISLE_W", "RAW_N", ["forklift"]), ("RAW_N", "RAW_X1", ["forklift"]), ("RAW_X1", "RAW_X2", ["forklift"]), ("RAW_X2", "FAC_YARD", ["forklift"]),
    ("FAC_YARD", "FAC_DOOR_S", ["forklift"]), ("FAC_DOOR_S", "FAC_AISLE_1", ["forklift"]),
]
REVERSE = {("RR_2", "RAW_BAY_1"): "RAW_BAY_1", ("RR_3", "RAW_BAY_2"): "RAW_BAY_2"}

# ---------------------------------------------------------------------------------------------------------------
# Zones (sites.json). hazard/ppe/restricted_roles/lone_worker feed K3. Building zones are the building footprint.
# ---------------------------------------------------------------------------------------------------------------
Z = lambda site, id, name, kind, x, z, w, d, **kw: dict(site_id=site, id=id, name=name, kind=kind, polygon=rect(x, z, w, d), **kw)  # noqa: E731
ZONES = [
    Z("WH-01", "WH01_GATE", "Main gate", "gate", 63, 33, 20, 19, hazard="medium", ppe=["vest"]),
    Z("WH-01", "WH01_ADMIN", "Admin block", "office", 58, 56, 20, 16, hazard="low"),
    Z("WH-01", "WH01_PARKING", "Car park", "parking", -10, 56, 52, 22, hazard="low"),
    Z("WH-01", "WH01_2W", "Two-wheeler park", "parking", 46, 56, 10, 8, hazard="low"),
    Z("FAC-01", "FAC01_CANTEEN", "Canteen", "canteen", 88, 56, 16, 12, hazard="low"),
    Z("FAC-01", "FAC01_MEDICAL", "First aid", "medical", 106, 56, 8, 8, hazard="low"),
    Z("FAC-01", "FAC01_RAW", "Raw material store", "raw_store", 118, 56, 32, 22, hazard="medium", ppe=["vest", "safety_shoes", "helmet"]),
    Z("FAC-01", "FAC01_RAWYARD", "Raw material yard", "yard", 146, 54, 20, 40, hazard="medium", ppe=["vest"]),
    Z("FAC-01", "FAC01_QC", "QC lab", "lab", 143, 2, 16, 14, hazard="medium", ppe=["glasses", "gloves"]),
    Z("FAC-01", "FAC01_WORKSHOP", "Maintenance workshop", "workshop", 143, 20, 26, 16, hazard="high", ppe=["helmet", "glasses", "gloves", "hearing"]),
    Z("FAC-01", "FAC01_SUBSTATION", "Substation", "utilities", 172, -6, 16, 14, hazard="high", ppe=["helmet", "gloves"],
      restricted_roles=["utilities_operator", "maintenance"], lone_worker=True, checkin_min=10),
    Z("FAC-01", "FAC01_GENERATOR", "Generator", "utilities", 196, -10, 14, 16, hazard="high", ppe=["hearing", "helmet"],
      restricted_roles=["utilities_operator", "maintenance"], lone_worker=True, checkin_min=10),
    Z("FAC-01", "FAC01_COMPRESSOR", "Compressor room", "utilities", 172, 12, 16, 12, hazard="high", ppe=["hearing"],
      restricted_roles=["utilities_operator", "maintenance"], lone_worker=True, checkin_min=10),
    Z("FAC-01", "FAC01_TANKS", "Water tanks and pumps", "utilities", 172, 26, 16, 10, hazard="medium", ppe=["helmet"]),
    Z("FAC-01", "FAC01_ETP", "Effluent treatment plant", "etp", 196, 12, 18, 22, hazard="high", ppe=["gloves", "glasses", "safety_shoes"],
      restricted_roles=["etp_operator", "utilities_operator", "maintenance"], lone_worker=True, checkin_min=10),
    Z("FAC-01", "FAC01_HAZMAT", "Hazardous materials store", "hazmat", 196, 62, 14, 14, hazard="high", ppe=["respirator", "gloves", "glasses"],
      restricted_roles=["utilities_operator", "maintenance"], time_limit_min=30),
    Z("FAC-01", "FAC01_FIREPUMP", "Fire pump house", "pump_house", 178, 54, 20, 10, hazard="medium", ppe=["hearing"],
      restricted_roles=["utilities_operator", "maintenance", "security_guard"]),
]
SITE_BOUNDS = {"WH-01": ([-14, 83], [-12, 104]), "FAC-01": ([84, 216], [-12, 104])}
HOME = {"WH-01": [32, 27], "FAC-01": [150, 30]}

# ---------------------------------------------------------------------------------------------------------------
# Devices (sensible counts, kits from K2). (id, type, protocol, zone, x, z, capabilities, label, kit, extras)
# ---------------------------------------------------------------------------------------------------------------
ENV4 = ["temperature", "humidity", "co2_ppm", "pm25_ugm3"]
DEVICES = [
    ("DR-02", "door_sensor", "thread", "WH01_GATE", 79, 36.5, ["open"], "Security cabin door", "door_access", {}),
    ("PM-02", "power_meter", "wifi", "WH01_PARKING", 4, 58, ["power_kw", "energy_kwh", "voltage_v"], "EV chargers feeder", "energy_meter", {"sim": {"base_kw": 14.0}}),
    ("EN-05", "env_sensor", "thread", "WH01_ADMIN", 68, 64, ENV4, "Admin block air", "env_node", {}),
    ("DR-04", "door_sensor", "thread", "WH01_ADMIN", 68, 56.6, ["open"], "Reception door", "door_access", {}),
    ("FP-02", "fire_panel", "wifi", "WH01_ADMIN", 60, 58, ["alarm", "trouble"], "Admin fire panel bridge (read only)", "fire_panel_bridge", {}),
    ("EN-06", "env_sensor", "thread", "FAC01_CANTEEN", 96, 62, ENV4, "Canteen air", "env_node", {}),
    ("LK-02", "leak_sensor", "thread", "FAC01_CANTEEN", 92, 60, ["wet"], "Kitchen leak probe", "water_leak_node", {}),
    ("DR-05", "door_sensor", "thread", "FAC01_CANTEEN", 96, 56.6, ["open"], "Canteen door", "door_access", {}),
    ("DR-06", "door_sensor", "thread", "FAC01_MEDICAL", 110, 56.6, ["open"], "First aid door", "door_access", {}),
    ("DB-03", "dock_bay", "wifi", "FAC01_RAW", 149, 62, ["occupied", "door_position", "leveler", "dock_light"], "Raw dock 1 monitor", "dock_bay", {}),
    ("DB-04", "dock_bay", "wifi", "FAC01_RAW", 149, 70, ["occupied", "door_position", "leveler", "dock_light"], "Raw dock 2 monitor", "dock_bay", {}),
    ("EN-07", "env_sensor", "thread", "FAC01_RAW", 134, 68, ENV4, "Raw store air", "env_node", {}),
    ("PM-03", "power_meter", "wifi", "FAC01_RAW", 122, 60, ["power_kw", "energy_kwh", "voltage_v"], "Raw store feeder", "energy_meter", {"sim": {"base_kw": 8.0}}),
    ("MM-03", "machine_monitor", "wifi", "FAC01_PRODUCTION", 122, 3.5, ["state", "cycle_time_s", "current_a", "vibration_rms", "temperature_c", "units", "rejects", "alarm"],
     "Press 2 monitor", "machine_monitor", {"attached_to": "M-03", "sim": {"cycle_s": 6.0, "vibration_mm_s": 2.6, "current_a": 13.0, "reject_rate": 0.0, "alarms": ["Die jam", "Hydraulic pressure low"]}}),
    ("MM-04", "machine_monitor", "wifi", "FAC01_PRODUCTION", 111, 3.5, ["state", "cycle_time_s", "current_a", "vibration_rms", "temperature_c", "units", "rejects", "alarm"],
     "Packer 2 monitor", "machine_monitor", {"attached_to": "M-04", "sim": {"cycle_s": 8.0, "vibration_mm_s": 1.9, "current_a": 7.0, "reject_rate": 0.02, "alarms": ["Film jam"]}}),
    ("CV-02", "conveyor_monitor", "wifi", "FAC01_PRODUCTION", 104, 5.2, ["motor_current_a", "belt_speed_m_s", "jam"], "Line 2 conveyor monitor", "conveyor_monitor", {}),
    ("EN-08", "env_sensor", "thread", "FAC01_QC", 150, 9, ENV4, "QC lab air", "env_node", {}),
    ("DR-07", "door_sensor", "thread", "FAC01_QC", 144, 9, ["open"], "QC lab door", "door_access", {}),
    ("EN-09", "env_sensor", "thread", "FAC01_WORKSHOP", 156, 28, ENV4, "Workshop air", "env_node", {}),
    ("DR-08", "door_sensor", "thread", "FAC01_WORKSHOP", 144, 29, ["open"], "Workshop door", "door_access", {}),
    ("GD-02", "gas_detector", "wifi", "FAC01_WORKSHOP", 162, 34, ["co_ppm", "o2_pct", "alarm"], "Workshop gas detector", "gas_detector_node", {}),
    ("PM-04", "power_meter", "wifi", "FAC01_SUBSTATION", 180, -2, ["power_kw", "energy_kwh", "voltage_v"], "Substation incomer", "energy_meter", {"sim": {"base_kw": 120.0}}),
    ("DR-09", "door_sensor", "thread", "FAC01_SUBSTATION", 187.5, 0, ["open"], "Substation door", "door_access", {}),
    ("EN-10", "env_sensor", "thread", "FAC01_SUBSTATION", 176, 4, ENV4, "Substation air", "env_node", {}),
    ("PM-05", "power_meter", "wifi", "FAC01_GENERATOR", 203, 2, ["power_kw", "energy_kwh", "voltage_v"], "Generator output meter", "energy_meter", {"sim": {"base_kw": 0.0}}),
    ("TL-02", "tank_level", "thread", "FAC01_GENERATOR", 205, -8, ["level_pct", "pump_on"], "Diesel day tank", "tank_level_node", {}),
    ("PM-06", "power_meter", "wifi", "FAC01_COMPRESSOR", 176, 16, ["power_kw", "energy_kwh", "voltage_v"], "Compressor feeder", "energy_meter", {"sim": {"base_kw": 30.0}}),
    ("EN-11", "env_sensor", "thread", "FAC01_COMPRESSOR", 184, 20, ENV4, "Compressor room air", "env_node", {}),
    ("TL-03", "tank_level", "thread", "FAC01_TANKS", 184, 32, ["level_pct", "pump_on"], "Water tank 2", "tank_level_node", {}),
    ("TL-04", "tank_level", "thread", "FAC01_ETP", 205, 18, ["level_pct", "pump_on"], "ETP equalisation tank", "tank_level_node", {}),
    ("LK-03", "leak_sensor", "thread", "FAC01_ETP", 200, 28, ["wet"], "ETP bund leak probe", "water_leak_node", {}),
    ("GD-03", "gas_detector", "wifi", "FAC01_ETP", 203, 26, ["co_ppm", "o2_pct", "alarm"], "ETP gas detector", "gas_detector_node", {}),
    ("GD-04", "gas_detector", "wifi", "FAC01_HAZMAT", 203, 70, ["co_ppm", "o2_pct", "alarm"], "Hazmat store gas detector", "gas_detector_node", {}),
    ("LK-04", "leak_sensor", "thread", "FAC01_HAZMAT", 200, 66, ["wet"], "Hazmat bund leak probe", "water_leak_node", {}),
    ("DR-10", "door_sensor", "thread", "FAC01_HAZMAT", 196.4, 69, ["open"], "Hazmat store door", "door_access", {}),
    ("EN-13", "env_sensor", "thread", "FAC01_HAZMAT", 206, 73, ENV4, "Hazmat store air", "env_node", {}),
    ("FP-03", "fire_panel", "wifi", "FAC01_FIREPUMP", 182, 58, ["alarm", "trouble"], "Fire pump house panel bridge (read only)", "fire_panel_bridge", {}),
    ("TL-05", "tank_level", "thread", "FAC01_FIREPUMP", 194, 59, ["level_pct", "pump_on"], "Fire water tank", "tank_level_node", {}),
    ("PM-07", "power_meter", "wifi", "FAC01_FIREPUMP", 185, 56, ["power_kw", "energy_kwh", "voltage_v"], "Fire pump feeder", "energy_meter", {"sim": {"base_kw": 1.0}}),
    ("WQ-01", "water_quality", "wifi", "FAC01_ETP", 199, 16, ["ph", "turbidity_ntu"], "ETP inflow quality", "water_quality_node", {"sim": {"inflow": True}}),
    ("WQ-02", "water_quality", "wifi", "FAC01_ETP", 208, 28, ["ph", "turbidity_ntu"], "ETP outflow quality", "water_quality_node", {}),
]
UTILITIES = {
    "_doc": "Campus physics for the simulator (tools/sim_models.py Physics) and the energy summary. Feeder meters follow what runs in their zone; the incomer reads the whole campus minus solar; critical zones keep power (generator) in a grid failure.",
    "incomer": "PM-04",
    "generator": "PM-05",
    "diesel_tank": "TL-02",
    "generator_kw": 150,
    "generator_start_s": 8,
    "feeders": {
        "PM-01": "FAC01_PRODUCTION",
        "PM-02": "WH01_PARKING",
        "PM-03": "FAC01_RAW",
        "PM-06": "FAC01_COMPRESSOR",
        "PM-07": "FAC01_FIREPUMP"
    },
    "critical_zones": [
        "FAC01_FIREPUMP",
        "FAC01_HAZMAT",
        "FAC01_SUBSTATION",
        "FAC01_GENERATOR",
        "WH01_ADMIN"
    ],
    "other_load_kw": 40,
    "critical_share": 0.1,
    "diesel_pct_per_kwh": 0.35,
    "peak_kw": 160,
    "solar": [
        {
            "building": "WAREHOUSE",
            "kwp": 110
        },
        {
            "building": "FACTORY",
            "kwp": 160
        },
        {
            "building": "RAW_STORE",
            "kwp": 90
        }
    ],
    "quality_bands": {
        "ph": [
            6.5,
            8.5
        ],
        "turbidity_ntu": 25,
        "_note": "Example discharge limits for the demo; a real plant uses the values in its permit."
    }
}

MOVED = {  # existing devices that now live in the building built for them: id -> (zone, x, z)
    "CP-01": ("FAC01_COMPRESSOR", 180, 18), "TL-01": ("FAC01_TANKS", 177, 32), "TT-01": ("WH01_DOCKS", 22, 36.5),
}

WORKERS = [  # id, name, role, badge, route stands/nodes (consecutive ids are walkway-connected), first_aider, sim
    ("WK-05", "Sam Okafor", "security_guard", "BG-05", ["WALK_CAB", "XN4", "XS4", "P1_79", "P1_68", "WALK_ADMIN", "P1_68", "P1_79", "XS4", "XN4"], False, {}),
    ("WK-06", "Lena Fischer", "maintenance", "BG-06",
     ["WALK_WS", "P0_141", "P0_150", "P0_160", "P0_172", "P0_192", "P_U3", "P_U2", "P_U1", "WALK_COMP", "P_U1", "P_U0", "WALK_SUB", "P_U0", "P_U1", "P_U2", "P_U3",
      "P0_192", "P0_172", "P0_160", "P0_150", "P0_141"], False, {}),
    ("WK-07", "Tom Rivera", "utilities_operator", "BG-07",
     ["WALK_SUB", "P_U0", "P_U1", "WALK_COMP", "P_U1", "P_U2", "P_U3", "WALK_TANK", "P_U3", "P_U2", "P_U1", "P_U0"], False, {"checkin_s": 420}),
    ("WK-08", "Aisha Khan", "etp_operator", "BG-08", ["WALK_ETP", "P_U2", "P_U3", "P_U2"], False, {"checkin_s": 420}),
    ("WK-09", "Marta Novak", "canteen_staff", "BG-09", ["WALK_CANTEEN", "P1_96", "P1_110", "WALK_MED", "P1_110", "P1_96"], False, {}),
    ("WK-10", "Ravi Menon", "first_aider", "BG-10", ["WALK_MED", "P1_110", "P1_96", "WALK_CANTEEN", "P1_96", "P1_110"], True, {}),
]


# ---------------------------------------------------------------------------------------------------------------

def seg_intersect(p1, p2, p3, p4) -> tuple[float, float] | None:
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-9:
        return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


def build_layout(l: dict) -> None:
    # remove previous run
    l["nodes"] = [n for n in l["nodes"] if not n.get("campus")]
    l["lanes"] = [x for x in l["lanes"] if not x.get("campus")]
    # the weighbridge splits the old GATE_IN -> ROAD_E lane
    l["lanes"] = [x for x in l["lanes"] if {x["a"], x["b"]} not in ({"GATE_IN", "ROAD_E"}, {"GATE_IN", "ROAD_IN"})]
    ids = {n["id"] for n in l["nodes"]}
    for n in VEH_NODES:
        assert n["id"] not in ids, n["id"]
        l["nodes"].append({**n, "campus": True})
    for a, b, kinds in VEH_LANES:
        lane = {"a": a, "b": b, "kinds": kinds, "campus": True}
        l["lanes"].append(lane)
    for (a, b), rev in REVERSE.items():
        l["lanes"].append({"a": a, "b": b, "kinds": ["truck"], "reverse_into": rev, "campus": True})
    # raw material flow: docks, charger, seed truck, forklift and pallets (auto mode runs it; planner.py)
    l["docks"] = [d for d in l["docks"] if d.get("area") != "raw"] + [dict(d) for d in RAW_DOCKS]
    l["chargers"] = [c for c in l["chargers"] if c["id"] != "CH-03"] + [dict(RAW_CHARGER)]
    sd = l["seed"]
    sd["trucks"] = [t for t in sd["trucks"] if t["id"] != "TR-03"] + [json.loads(json.dumps(RAW_TRUCK))]
    sd["forklifts"] = [f for f in sd["forklifts"] if f["id"] != "FL-05"] + [json.loads(json.dumps(RAW_FORKLIFT))]
    sd["pallets"] = [p for p in sd["pallets"] if not p["id"].startswith("RM-")] + json.loads(json.dumps(RAW_PALLETS))
    for pid, (x, z, typ, label) in PED_NODES.items():
        l["nodes"].append({"id": pid, "type": typ, "x": x, "z": z, "kinds": [], "label": label, "campus": True})
    for chain in PED_CHAINS:
        for a, b in zip(chain, chain[1:]):
            l["lanes"].append({"a": a, "b": b, "kinds": [], "campus": True})
    for a, b in LEGACY_LINKS:
        l["lanes"].append({"a": a, "b": b, "kinds": [], "campus": True})
    for cid, a, b, _ in CROSSINGS:
        # the crossing lane is the one between a and b: mark it (it already exists in a chain, or add it)
        lane = next((x for x in l["lanes"] if {x["a"], x["b"]} == {a, b}), None)
        if lane is None:
            lane = {"a": a, "b": b, "kinds": [], "campus": True}
            l["lanes"].append(lane)
        lane["crossing"] = cid
    # roads
    l["roads"] = [r for r in l["roads"] if not r.get("campus")]
    for r in l["roads"]:
        if r["id"] == "TRUCK_LANE":
            r["points"] = [[-14, 44], [215, 44]]
    l["roads"] += [{**r, "campus": True} for r in ROADS]
    l["bounds"] = {"x": [-14, 216], "z": [-12, 104]}
    # second production line (line 2) north of line 1
    pl = l["production_line"]
    pl["machines"] = [m for m in pl["machines"] if m.get("line", 1) == 1]
    pl["machines"] += [{"id": "M-03", "label": "Press 2", "x": 122, "z": 3.5, "w": 4, "d": 3.2, "h": 3.4, "kind": "press", "line": 2},
                       {"id": "M-04", "label": "Packer 2", "x": 111, "z": 3.5, "w": 3.6, "d": 3, "h": 2.6, "kind": "packer", "line": 2}]
    pl["conveyor2"] = {"from": [97, 3.5], "to": [128, 3.5], "width": 1.4}
    # the campus description for the renderer, the tests and the monitoring centre
    hyd = []
    loop = HYDRANT_LOOP + [HYDRANT_LOOP[0]]
    for (x0, z0), (x1, z1) in zip(loop, loop[1:]):
        n = max(1, round(math.hypot(x1 - x0, z1 - z0) / 28))
        for i in range(n):
            hyd.append([round(x0 + (x1 - x0) * i / n, 1), round(z0 + (z1 - z0) * i / n, 1)])
    for b in BUILDINGS:
        if b["id"] not in ("SEC_CABIN",):
            hyd.append([round(b["x"] + b["w"] / 2, 1), round(b["z"] + (b["d"] + 1.2 if b["z"] > 40 else -1.2), 1)])
    crossings = []
    nodes = {n["id"]: n for n in l["nodes"]}
    veh = [(x["a"], x["b"]) for x in l["lanes"] if x["kinds"]]
    for cid, a, b, over in CROSSINGS:
        pa, pb = (nodes[a]["x"], nodes[a]["z"]), (nodes[b]["x"], nodes[b]["z"])
        hits = [h for va, vb in veh if (h := seg_intersect(pa, pb, (nodes[va]["x"], nodes[va]["z"]), (nodes[vb]["x"], nodes[vb]["z"])))]
        mid = hits[0] if hits else ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        crossings.append({"id": cid, "a": a, "b": b, "over": over, "x": round(mid[0], 2), "z": round(mid[1], 2),
                          "hotspot": {"x": round(mid[0], 2), "z": round(mid[1], 2), "radius_m": 4.0}})
    l["campus"] = {
        "name": "Riverside Campus", "plan": "docs/campus_plan.md",
        "buildings": BUILDINGS, "tanks": TANKS, "etp": ETP, "weighbridge": WEIGHBRIDGE, "barrier": BARRIER, "parking": PARKING,
        "muster_points": MUSTER, "solar": SOLAR, "hydrants": {"ring": HYDRANT_LOOP, "points": hyd},
        "crossings": crossings,
        "walkways": [{"id": f"W{i}", "points": [[nodes[n]["x"], nodes[n]["z"]] for n in ch], "width": 1.8} for i, ch in enumerate(PED_CHAINS)],
        "green_belt": [dict(x=-14, z=-12, w=230, d=3), dict(x=-14, z=101, w=230, d=3), dict(x=-14, z=-12, w=3, d=116), dict(x=213, z=-12, w=3, d=116),
                       dict(x=60, z=74, w=18, d=8), dict(x=86, z=70, w=26, d=10), dict(x=46, z=66, w=10, d=10)],
        "fence": {"lines": [[[-13, -11], [215, -11], [215, 39], [], [215, 49], [215, 103], [-13, 103], [-13, 49], [], [-13, 39], [-13, -11]]],
                  "gaps": "the main road leaves at both ends (x = -14 and x = 216); the main gate is the boom barrier at x = 84"},
        "flows": {
            "trucks": ["ROAD_E", "WEIGH", "GATE_IN", "YARD_E", "BAY_1"],
            "raw_material": ["RAW_BAY_1", "RAW_DOCK_1", "RAW_AISLE_E", "RAW_AISLE_W", "RAW_N", "RAW_X1", "RAW_X2", "FAC_YARD", "FAC_DOOR_S", "FAC_AISLE_1"],
            "finished_goods": ["FAC_AISLE_1", "FAC_AISLE_2", "FAC_OUT", "FAC_W", "LINK_MID", "WH_EAST", "MAIN_E", "MAIN_1", "DOCK_1"],
        },
    }


def build_sites(s: dict, l: dict) -> None:
    mine = {z["id"] for z in ZONES}
    for site in s["sites"]:
        site["zones"] = [z for z in site["zones"] if z["id"] not in mine]
    by = {x["id"]: x for x in s["sites"]}
    for site_id, (bx, bz) in SITE_BOUNDS.items():
        by[site_id]["bounds"] = {"x": bx, "z": bz}
        by[site_id]["home"] = HOME[site_id]
    for z in ZONES:
        by[z["site_id"]]["zones"].append(dict(z))
    # zone attributes for the existing zones (K3)
    attrs = {"WH01_STORAGE": dict(hazard="medium", ppe=["vest", "safety_shoes"]), "WH01_DOCKS": dict(hazard="medium", ppe=["vest", "safety_shoes"]),
             "WH01_YARD": dict(hazard="medium", ppe=["vest"]), "WH01_OFFICE": dict(hazard="low"),
             "FAC01_PRESS": dict(hazard="high", ppe=["helmet", "hearing", "safety_shoes"]),
             "FAC01_COLD": dict(hazard="medium", ppe=["gloves"], time_limit_min=20, lone_worker=True, checkin_min=10),
             "FAC01_PRODUCTION": dict(hazard="medium", ppe=["safety_shoes", "vest"]), "FAC01_DOCKS": dict(hazard="medium", ppe=["vest", "safety_shoes"]),
             "FAC01_OFFICE": dict(hazard="low")}
    for site in s["sites"]:
        for z in site["zones"]:
            z.update(attrs.get(z["id"], {}))
    s["utilities"] = UTILITIES
    for d in s["devices"]:
        if d["id"] == "CP-01" and "tripped" not in d["capabilities"]:
            d["capabilities"].append("tripped")
    s["muster_points"] = [dict(m) for m in MUSTER]  # `node` is the walkway node the route ends on
    # devices
    s["devices"] = [d for d in s["devices"] if not d.get("campus")]
    for d in s["devices"]:
        if d["id"] in MOVED:
            zone, x, z = MOVED[d["id"]]
            d.update(zone_id=zone, x=x, z=z)
            d["site_id"] = "FAC-01" if zone.startswith("FAC01") else "WH-01"
    zone_site = {z["id"]: site["id"] for site in s["sites"] for z in site["zones"]}
    for id_, typ, proto, zone, x, z, caps, label, kit, extra in DEVICES:
        s["devices"].append({"id": id_, "site_id": zone_site[zone], "zone_id": zone, "type": typ, "protocol": proto, "x": x, "z": z,
                             "capabilities": caps, "label": label, "kit": kit, "source": "sim", **extra, "campus": True})
    # workers + their badges
    s["workers"] = [w for w in s["workers"] if not w.get("campus")]
    nodes = {n["id"]: n for n in l["nodes"]}
    for wid, name, role, badge, route, aider, sim in WORKERS:
        s["workers"].append({"id": wid, "name": name, "role": role, "badge": badge, "routes": {"default": route}, "first_aider": aider, "campus": True})
        n0 = nodes[route[0]]
        zone = next((z["id"] for site in s["sites"] for z in site["zones"] if z["id"] in mine and _inside(n0["x"], n0["z"], z["polygon"])), None)
        site_id = "FAC-01" if n0["x"] >= 84 else "WH-01"  # a badge reports on its site's topic; walkways are outside every zone
        zone = zone or ("FAC01_RAWYARD" if site_id == "FAC-01" else "WH01_GATE")
        dev = {"id": badge, "site_id": site_id, "zone_id": zone, "type": "badge", "protocol": "ble", "x": n0["x"], "z": n0["z"],
               "capabilities": ["position", "fall", "sos", "cancel", "checkin"], "label": f"Badge of {wid}", "kit": "worker_badge", "source": "sim",
               "attached_to": wid, "sim": {"battery_pct": 70 + (sum(map(ord, badge)) % 25), **sim}, "campus": True}
        s["devices"].append(dev)


def _inside(x: float, z: float, poly: list[list[float]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi:
            inside = not inside
        j = i
    return inside


def main() -> None:
    l = json.loads(LAYOUT.read_text())
    s = json.loads(SITES.read_text())
    build_layout(l)
    build_sites(s, l)
    # production config for line 2
    s["production"]["ideal_cycle_s"].update({"M-03": 6.0, "M-04": 8.0})
    LAYOUT.write_text(json.dumps(l, indent=2, ensure_ascii=False) + "\n")
    SITES.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
    print(f"layout: {len(l['nodes'])} nodes, {len(l['lanes'])} lanes; sites: {sum(len(x['zones']) for x in s['sites'])} zones, "
          f"{len(s['devices'])} devices, {len(s['workers'])} workers")


if __name__ == "__main__":
    main()
