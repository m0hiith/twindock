"""Pydantic models mirroring /shared/schemas, plus the layout file format.

extra="forbid" matches additionalProperties: false in the schemas.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_serializer

Kind = Literal["forklift", "truck", "pallet", "dock", "rack", "charger", "gateway"]
Source = Literal["device", "manual", "auto"]
Action = Literal["goto", "pick", "drop", "load", "charge", "dock", "depart"]
MoverKind = Literal["forklift", "truck"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- MQTT payloads (board <-> broker)

class Hello(Strict):
    board: str
    radio_board: str
    fw_version: str
    leds: list[str]
    buttons: list[str]
    sensors: list[str]


class Status(Strict):
    ts_ms: int
    uptime_s: int | None = None
    wifi_rssi_dbm: int | None = None
    wifi_connected: bool | None = None
    ip: str | None = None
    fw_version: str | None = None
    msgs_sent: int | None = None
    reconnects: int | None = None
    buffered: int | None = None
    replay: bool | None = None


class ButtonMsg(Strict):
    ts_ms: int
    button: str
    state: Literal["pressed", "released"]


class LedMsg(Strict):
    ts_ms: int
    led: str
    on: bool
    cmd_id: str | None = None


class Sighting(Strict):
    name: str
    addr: str
    rssi_dbm: int


class BleMsg(Strict):
    ts_ms: int
    sightings: list[Sighting]


class SensorMsg(Strict):
    ts_ms: int
    value: float
    unit: str


class CmdLed(Strict):
    led: str
    on: bool
    cmd_id: str


# ---------------------------------------------------------------- WebSocket client -> server

class MoveUnit(Strict):
    type: Literal["move_unit"]
    cmd_id: str
    unit_id: str
    target_node: str
    action: Action = "goto"
    dry_run: bool = False
    pallet_id: str | None = None


class SelectUnit(Strict):
    type: Literal["select_unit"]
    cmd_id: str
    unit_id: str | None


class LedCommand(Strict):
    type: Literal["led_command"]
    cmd_id: str
    led: str
    on: bool


class SetAutoMode(Strict):
    type: Literal["set_auto_mode"]
    cmd_id: str
    enabled: bool


ClientMessage = Annotated[Union[MoveUnit, SelectUnit, LedCommand, SetAutoMode], Field(discriminator="type")]


# ---------------------------------------------------------------- Wire entities

class PlanStep(Strict):
    node: str
    action: Action


# Fields the schema allows to be null; every other optional field is omitted when None.
_NULLABLE_UNIT_FIELDS = {"node", "target_node", "carrying", "docked_at", "holder"}


class Unit(Strict):
    id: str
    kind: Kind
    source: Source
    state: str
    label: str | None = None
    x: float
    z: float
    heading_rad: float
    speed_mps: float | None = None
    node: str | None = None
    target_node: str | None = None
    path: list[str] | None = None
    task: str | None = None
    battery_pct: float | None = None
    carrying: str | None = None
    docked_at: str | None = None
    holder: str | None = None
    cargo: list[str] | None = None
    plan: list[PlanStep] | None = None
    meta: dict[str, str | float | bool] | None = None

    @model_serializer(mode="wrap")
    def _drop_absent(self, handler: Any) -> dict[str, Any]:
        d: dict[str, Any] = handler(self)
        return {k: v for k, v in d.items() if v is not None or k in _NULLABLE_UNIT_FIELDS}


class Timed(Strict):
    """A device message plus when the backend received it."""
    model_config = ConfigDict(extra="forbid")
    data: dict[str, Any]
    received_ms: int


class TimedHello(Timed):
    retained: bool


class ButtonState(Strict):
    state: Literal["pressed", "released"]
    received_ms: int
    ts_ms: int


class PendingLed(Strict):
    cmd_id: str
    on: bool
    sent_ms: int


class LedState(Strict):
    on: bool | None
    received_ms: int | None
    pending: PendingLed | None


class Gateway(Strict):
    online: bool
    fake: bool
    last_seen_ms: int | None
    hello: TimedHello | None
    status: Timed | None
    buttons: dict[str, ButtonState]
    leds: dict[str, LedState]
    ble: Timed | None
    sensors: dict[str, Timed]


# ---------------------------------------------------------------- WebSocket server -> client

class WorldSnapshot(Strict):
    type: Literal["world_snapshot"] = "world_snapshot"
    seq: int
    server_ts_ms: int
    layout_version: str
    auto_mode: bool
    selected_unit_id: str | None
    units: list[Unit]
    gateway: Gateway


class UnitUpdate(Strict):
    type: Literal["unit_update"] = "unit_update"
    seq: int
    server_ts_ms: int
    units: list[Unit]
    removed: list[str] | None = None
    auto_mode: bool | None = None

    @model_serializer(mode="wrap")
    def _drop_absent(self, handler: Any) -> dict[str, Any]:
        d: dict[str, Any] = handler(self)
        return {k: v for k, v in d.items() if v is not None}


class RawMqtt(Strict):
    topic: str
    payload: Any
    received_ms: int


class GatewayUpdate(Strict):
    type: Literal["gateway_update"] = "gateway_update"
    seq: int
    server_ts_ms: int
    gateway: Gateway
    raw: RawMqtt | None = None

    @model_serializer(mode="wrap")
    def _drop_absent(self, handler: Any) -> dict[str, Any]:
        d: dict[str, Any] = handler(self)
        if d.get("raw") is None:
            d.pop("raw", None)
        return d


class SelectionChanged(Strict):
    type: Literal["selection_changed"] = "selection_changed"
    seq: int
    selected_unit_id: str | None
    by: str


class CommandAck(Strict):
    type: Literal["command_ack"] = "command_ack"
    cmd_id: str
    command: Literal["move_unit", "select_unit", "led_command", "set_auto_mode"]
    ok: bool
    reason: str | None = None
    path: list[str] | None = None

    @model_serializer(mode="wrap")
    def _drop_absent(self, handler: Any) -> dict[str, Any]:
        d: dict[str, Any] = handler(self)
        return {k: v for k, v in d.items() if v is not None}


class BleTracks(Strict):
    """Shape is checked against ws/ble_tracks.json; built by BleTracker.wire()."""
    type: Literal["ble_tracks"] = "ble_tracks"
    seq: int
    server_ts_ms: int
    config: dict[str, Any]
    tracks: list[dict[str, Any]]


class Event(Strict):
    type: Literal["event"] = "event"
    seq: int
    server_ts_ms: int
    level: Literal["info", "warn", "error"]
    source: str
    text: str
    unit_id: str | None = None

    @model_serializer(mode="wrap")
    def _drop_absent(self, handler: Any) -> dict[str, Any]:
        d: dict[str, Any] = handler(self)
        return {k: v for k, v in d.items() if v is not None}


# ---------------------------------------------------------------- Layout file (backend/world/layout.json)

NodeType = Literal["rack_slot", "zone", "dock", "bay", "charger", "junction", "gate", "exit"]


class Node(BaseModel):
    id: str
    type: NodeType
    x: float
    z: float
    kinds: list[MoverKind]
    label: str | None = None
    spots: list[tuple[float, float]] = []


class Lane(BaseModel):
    a: str
    b: str
    kinds: list[MoverKind]
    reverse_into: str | None = None  # trucks back into this end of the lane


class DockDef(BaseModel):
    id: str
    node: str
    bay_node: str
    door: str
    label: str


class ChargerDef(BaseModel):
    id: str
    node: str
    label: str


class RackDef(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    row: str
    slots: list[str]


class GatewayDef(BaseModel):
    id: str
    label: str
    x: float
    z: float
    ble_range_m: float


class SeedStep(BaseModel):
    node: str
    action: Action


class SeedForklift(BaseModel):
    id: str
    node: str
    heading_rad: float
    battery_pct: float
    charging: bool = False
    meta: dict[str, str]
    plan: list[SeedStep] = []


class SeedTruck(BaseModel):
    id: str
    node: str
    heading_rad: float
    state: Literal["arriving", "docked", "gone"]
    capacity: int
    inbound: bool
    meta: dict[str, str]


class SeedPallet(BaseModel):
    id: str
    at: str  # node id, or a truck id for pallets already on a truck
    meta: dict[str, str]


class Seed(BaseModel):
    forklifts: list[SeedForklift]
    trucks: list[SeedTruck]
    pallets: list[SeedPallet]
    dock_states: dict[str, Literal["available", "occupied", "maintenance"]]


class Layout(BaseModel):
    model_config = ConfigDict(extra="allow")  # buildings, roads, decor... are for the frontend
    version: str
    nodes: list[Node]
    lanes: list[Lane]
    racks: list[RackDef]
    docks: list[DockDef]
    chargers: list[ChargerDef]
    gate_node: str
    exit_node: str
    gateway: GatewayDef
    seed: Seed
