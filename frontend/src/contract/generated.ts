/* Generated from /shared/schemas by scripts/gen-types.mjs. Do not edit. */

/**
 * Waypoint graph node, e.g. DOCK_1, RACK_A3, CHARGER_C1, GATE_IN
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "node_id".
 */
export type NodeId = string;
/**
 * e.g. FL-01, TR-02, PL-07, GW-01
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "unit_id".
 */
export type UnitId = string;
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "cmd_id".
 */
export type CmdId = string;
/**
 * e.g. FL-01, TR-02, PL-07, GW-01
 */
export type UnitId1 = string;
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "kind".
 */
export type Kind = "forklift" | "truck" | "pallet" | "dock" | "rack" | "charger" | "gateway";
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "source".
 */
export type Source = "device" | "manual" | "auto";
/**
 * sdk-verified: found in the SDK board config (cite `source`). user-guide: from the board user guide UG581. datasheet: from the part's datasheet or a published spec (Qwiic). confirmed: also checked by the developer on the hardware. unverified: not confirmed, must not be used by firmware.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_evidence".
 */
export type WiringEvidence = "sdk-verified" | "user-guide" | "datasheet" | "confirmed" | "unverified";
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_id".
 */
export type WiringId = string;
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_pct".
 */
export type WiringPct = number;
/**
 * planned: not connected or not read yet. wired: physically connected (on-board parts and PCB traces are wired by the board itself). verified: firmware has read a plausible value from it.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_status".
 */
export type WiringStatus = "planned" | "wired" | "verified";
/**
 * <part id>.<pin name>, e.g. soc.ULP_GPIO_6 or vl53l1x.qwiic_in.SDA
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_pin_ref".
 */
export type WiringPinRef = string;
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "forklift_state".
 */
export type ForkliftState = "idle" | "driving" | "picking" | "carrying" | "loading" | "charging";
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "truck_state".
 */
export type TruckState = "arriving" | "docked" | "loading" | "departing" | "gone";
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "dock_state".
 */
export type DockState = "available" | "occupied" | "maintenance";

export interface TwinDockContract {
  gateway_ble?: GatewayBle;
  gateway_button?: GatewayButton;
  gateway_cmd_led?: GatewayCmdLed;
  gateway_hello?: GatewayHello;
  gateway_led?: GatewayLed;
  gateway_sensor?: GatewaySensor;
  gateway_status?: GatewayStatus;
  ble_tracks?: BleTracks;
  command_ack?: CommandAck;
  event?: Event;
  gateway_update?: GatewayUpdate;
  led_command?: LedCommand;
  move_unit?: MoveUnit;
  select_unit?: SelectUnit;
  selection_changed?: SelectionChanged;
  set_auto_mode?: SetAutoMode;
  unit_update?: UnitUpdate;
  world_snapshot?: WorldSnapshot;
  wiring?: Wiring;
}
/**
 * Every 2 s. Only advertisers whose name starts with TD-. Empty list means a scan ran and found none.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_ble".
 */
export interface GatewayBle {
  ts_ms: number;
  /**
   * @maxItems 32
   */
  sightings: {
    name: string;
    addr: string;
    rssi_dbm: number;
  }[];
}
/**
 * Sent on every debounced state change.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_button".
 */
export interface GatewayButton {
  ts_ms: number;
  button: string;
  state: "pressed" | "released";
}
/**
 * Backend to board. The board drives the LED and confirms on twin/gateway/led with the same cmd_id.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_cmd_led".
 */
export interface GatewayCmdLed {
  led: string;
  on: boolean;
  cmd_id: string;
}
/**
 * Retained. Board identity and the hardware it exposes. Lists must match HARDWARE.md.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_hello".
 */
export interface GatewayHello {
  /**
   * e.g. BRD2605A. The fake board sends FAKE.
   */
  board: string;
  /**
   * Radio board ID, or empty string when the kit is a single board.
   */
  radio_board: string;
  /**
   * "fake" means tools/fake_board.py.
   */
  fw_version: string;
  leds: string[];
  buttons: string[];
  sensors: string[];
}
/**
 * Confirmation of the real LED state after it changed (not a command). cmd_id echoes the command that caused it, if any.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_led".
 */
export interface GatewayLed {
  ts_ms: number;
  led: string;
  on: boolean;
  cmd_id?: string;
}
/**
 * Only for sensors marked verified in HARDWARE.md and listed in hello.sensors.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_sensor".
 */
export interface GatewaySensor {
  ts_ms: number;
  value: number;
  unit: string;
}
/**
 * Every 5 s. Fields the SDK cannot provide are omitted, never invented. Only ts_ms is required.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_status".
 */
export interface GatewayStatus {
  /**
   * Board time in ms when the sample was taken (kept on buffered replays).
   */
  ts_ms: number;
  uptime_s?: number;
  wifi_rssi_dbm?: number;
  wifi_connected?: boolean;
  ip?: string;
  fw_version?: string;
  msgs_sent?: number;
  reconnects?: number;
  /**
   * Messages flushed from the offline buffer on the last reconnect.
   */
  buffered?: number;
  /**
   * true on messages flushed from the offline buffer. The backend keeps them in history but does not treat them as the current status.
   */
  replay?: boolean;
}
/**
 * BLE tag tracking state after each twin/gateway/ble message and when a tag is lost. Smoothed values are computed by the backend from real sightings only; used by the /device calibration helper.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "ble_tracks".
 */
export interface BleTracks {
  type: "ble_tracks";
  seq: number;
  server_ts_ms: number;
  /**
   * backend/world/ble_zones.json as loaded. Empty zones = tracking off.
   */
  config: {
    window: number;
    stable_s: number;
    lost_after_s: number;
    /**
     * Nearest first; thresholds strictly decreasing.
     */
    zones: {
      node: NodeId;
      min_rssi_dbm: number;
    }[];
  };
  tracks: {
    name: string;
    addr: string;
    /**
     * Forklift this tag maps to (TD-FL01 -> FL-01), or null.
     */
    unit_id: UnitId | null;
    last_rssi_dbm: number;
    /**
     * Moving average of the last `window` readings.
     */
    avg_rssi_dbm: number | null;
    readings: number;
    /**
     * Server time of the last scan that saw this tag.
     */
    last_seen_ms: number;
    /**
     * Zone the current average falls in, before hysteresis. null = beyond every zone or tracking off.
     */
    raw_zone: NodeId | null;
    /**
     * Committed zone. null with has_zone = beyond every zone.
     */
    zone: NodeId | null;
    has_zone: boolean;
    pending_zone: NodeId | null;
    /**
     * When the pending zone (possibly null = beyond every zone) started; null = nothing pending.
     */
    pending_since_ms: number | null;
  }[];
}
/**
 * Reply to one client command. For led_command, ok:true means sent to the board; the LED changes only on the board's confirmation.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "command_ack".
 */
export interface CommandAck {
  type: "command_ack";
  cmd_id: CmdId;
  command: "move_unit" | "select_unit" | "led_command" | "set_auto_mode";
  ok: boolean;
  /**
   * Short human reason when ok is false.
   */
  reason?: string;
  /**
   * Planned path for an accepted (or dry-run) move_unit.
   */
  path?: NodeId[];
}
/**
 * Human-readable notice for the event log: physical button actions, auto mode, LED timeouts, dropped device messages.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "event".
 */
export interface Event {
  type: "event";
  seq: number;
  server_ts_ms: number;
  level: "info" | "warn" | "error";
  /**
   * BTN0, BTN1, auto, gateway, system, or a client id.
   */
  source: string;
  text: string;
  unit_id?: UnitId;
}
/**
 * Full gateway state after any device message or a stale/online transition. raw carries the MQTT message that caused it (for the /device log).
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway_update".
 */
export interface GatewayUpdate {
  type: "gateway_update";
  seq: number;
  server_ts_ms: number;
  gateway: Gateway;
  raw?: {
    topic: string;
    payload: unknown;
    received_ms: number;
  };
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "gateway".
 */
export interface Gateway {
  /**
   * False when twin/gateway/status is older than 15 s or never received.
   */
  online: boolean;
  /**
   * True when hello.fw_version == "fake". The UI must show a FAKE BOARD banner.
   */
  fake: boolean;
  last_seen_ms?: number | null;
  hello:
    | null
    | (Timed & {
        data: GatewayHello;
      });
  status:
    | null
    | (Timed & {
        data: GatewayStatus;
      });
  buttons: {
    [k: string]:
      | (Timed & {
          state: "pressed" | "released";
        })
      | undefined;
  };
  leds: {
    [k: string]:
      | {
          /**
           * Last confirmed state; null if never confirmed.
           */
          on: boolean | null;
          received_ms: number | null;
          pending: null | {
            cmd_id: string;
            on: boolean;
            sent_ms: number;
          };
        }
      | undefined;
  };
  ble:
    | null
    | (Timed & {
        data: GatewayBle;
      });
  sensors: {
    [k: string]:
      | (Timed & {
          data: GatewaySensor;
        })
      | undefined;
  };
}
/**
 * A device value plus when the backend received it. Absent/null means no message has arrived yet.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "timed".
 */
export interface Timed {
  received_ms: number;
}
/**
 * Forwarded to twin/gateway/cmd/led. Rejected if the LED is not in hello.leds or is rule-driven (LED0).
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "led_command".
 */
export interface LedCommand {
  type: "led_command";
  cmd_id: CmdId;
  led: string;
  on: boolean;
}
/**
 * Intent to move a unit to a node, optionally performing an action there. The server validates and plans the path.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "move_unit".
 */
export interface MoveUnit {
  type: "move_unit";
  cmd_id: CmdId;
  unit_id: UnitId;
  target_node: NodeId;
  action?: "goto" | "pick" | "drop" | "load" | "charge" | "dock" | "depart";
  /**
   * Validate and return the planned path without moving (for the Control Room preview).
   */
  dry_run?: boolean;
  pallet_id?: UnitId1;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "select_unit".
 */
export interface SelectUnit {
  type: "select_unit";
  cmd_id: CmdId;
  unit_id: UnitId | null;
}
/**
 * Selection is shared by all clients. by is a client id, or "BTN1" when the physical button changed it.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "selection_changed".
 */
export interface SelectionChanged {
  type: "selection_changed";
  seq: number;
  selected_unit_id: UnitId | null;
  by: string;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "set_auto_mode".
 */
export interface SetAutoMode {
  type: "set_auto_mode";
  cmd_id: CmdId;
  enabled: boolean;
}
/**
 * Changed units since the last tick (full unit objects). removed lists units that left the world.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "unit_update".
 */
export interface UnitUpdate {
  type: "unit_update";
  seq: number;
  server_ts_ms: number;
  units: Unit[];
  removed?: UnitId[];
  auto_mode?: boolean;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "unit".
 */
export interface Unit {
  id: UnitId;
  kind: Kind;
  source: Source;
  /**
   * One of the state enums for this kind.
   */
  state: string;
  label?: string;
  /**
   * Meters east of the NW corner.
   */
  x: number;
  /**
   * Meters south of the NW corner.
   */
  z: number;
  /**
   * 0 = facing +x (east), increasing towards +z.
   */
  heading_rad: number;
  speed_mps?: number;
  /**
   * Node the unit is at, null while between nodes.
   */
  node?: NodeId | null;
  target_node?: NodeId | null;
  /**
   * Remaining nodes to the target.
   */
  path?: NodeId[];
  /**
   * One-line human task, e.g. "Loading truck TR-01".
   */
  task?: string;
  battery_pct?: number;
  carrying?: UnitId | null;
  docked_at?: NodeId | null;
  /**
   * Static display fields (operator, model, plate...).
   */
  meta?: {
    [k: string]: string | number | boolean | undefined;
  };
  /**
   * Pallets only: the forklift carrying it or the truck it is loaded on.
   */
  holder?: UnitId | null;
  /**
   * Trucks only: pallets on board.
   */
  cargo?: UnitId[];
  /**
   * Forklifts: queued steps. BTN0 runs the first one.
   */
  plan?: PlanStep[];
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "plan_step".
 */
export interface PlanStep {
  node: NodeId;
  action: "goto" | "pick" | "drop" | "load" | "charge" | "dock" | "depart";
}
/**
 * Full state, sent on connect and after a reset.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "world_snapshot".
 */
export interface WorldSnapshot {
  type: "world_snapshot";
  seq: number;
  server_ts_ms: number;
  layout_version: string;
  auto_mode: boolean;
  selected_unit_id: UnitId | null;
  units: Unit[];
  gateway: Gateway;
}
/**
 * Single source of truth for how the forklift sensor pack is connected. Firmware pins (tools/gen_pins.py), the /wiring page and docs/hardware_sheet.pdf are all generated from it. Nothing here may be guessed: a value that is not confirmed from the SDK, a datasheet or the developer is null and its `evidence` is "unverified".
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring".
 */
export interface Wiring {
  version: 1;
  board: string;
  sdk: string;
  /**
   * Outline of the bare board for the /wiring page, used until frontend/public/board/top.jpg exists (and for parts whose outline_pct is still null). Positions are % of board width/height, top view, 0,0 = top-left.
   */
  board_drawing: {
    width_mm: number;
    height_mm: number;
    evidence: WiringEvidence;
    source: string;
    features: {
      id: WiringId;
      /**
       * Part id when the feature is in `parts`; null for landmarks drawn only for orientation.
       */
      part: string | null;
      label: string;
      kind: "chip" | "connector" | "button" | "led" | "switch" | "other";
      x: WiringPct;
      y: WiringPct;
      w: WiringPct;
      h: WiringPct;
    }[];
    pad_columns: {
      side: "left" | "right";
      x: WiringPct;
      y_first: WiringPct;
      y_last: WiringPct;
      pads: {
        number: number;
        net: string;
        function?: string;
      }[];
    }[];
    pads_source?: string;
  };
  buses: {
    id: WiringId;
    name: string;
    kind: "i2c" | "spi" | "i2s" | "gpio" | "power" | "analog";
    /**
     * SoC peripheral, e.g. I2C2 (ULP_I2C). null when not known.
     */
    controller: string | null;
    voltage_v: number | null;
    evidence: WiringEvidence;
    source?: string;
    notes?: string;
  }[];
  /**
   * @minItems 1
   */
  parts: [
    {
      id: WiringId;
      name: string;
      part_number: string;
      quantity: number;
      location: "on-board" | "external";
      kind: "soc" | "sensor" | "connector" | "module" | "transducer";
      /**
       * Bus id from `buses`, or null (SoC, connectors, analog parts).
       */
      bus: string | null;
      /**
       * 7-bit I2C address as 0xNN, or null for non-I2C parts.
       */
      address: string | null;
      address_evidence?: WiringEvidence;
      /**
       * Address the firmware moves the part to at boot (see boot_sequence). Clash checks use this when present.
       */
      runtime_address?: string;
      supply?: WiringVoltageRange;
      /**
       * Bus id of the power rail feeding this part.
       */
      supplied_from?: string | null;
      /**
       * pin_ref of a power/enable pin that must be driven before use.
       */
      enable_pin?: string | null;
      sdk_driver?: string | null;
      sdk_example?: string | null;
      measures?: string;
      forklift_use?: string;
      /**
       * One plain-language sentence for non-engineers on the /wiring page.
       */
      caption: string;
      /**
       * MQTT topics this part feeds. Each must exist in /shared (checked in W5).
       */
      topics?: string[];
      /**
       * Outline on top.jpg in % for on-board parts. null until measured from the photo.
       */
      outline_pct?: {
        x: number;
        y: number;
        w: number;
        h: number;
      } | null;
      status: WiringStatus;
      pins: WiringPin[];
      notes?: string;
    },
    ...{
      id: WiringId;
      name: string;
      part_number: string;
      quantity: number;
      location: "on-board" | "external";
      kind: "soc" | "sensor" | "connector" | "module" | "transducer";
      /**
       * Bus id from `buses`, or null (SoC, connectors, analog parts).
       */
      bus: string | null;
      /**
       * 7-bit I2C address as 0xNN, or null for non-I2C parts.
       */
      address: string | null;
      address_evidence?: WiringEvidence;
      /**
       * Address the firmware moves the part to at boot (see boot_sequence). Clash checks use this when present.
       */
      runtime_address?: string;
      supply?: WiringVoltageRange;
      /**
       * Bus id of the power rail feeding this part.
       */
      supplied_from?: string | null;
      /**
       * pin_ref of a power/enable pin that must be driven before use.
       */
      enable_pin?: string | null;
      sdk_driver?: string | null;
      sdk_example?: string | null;
      measures?: string;
      forklift_use?: string;
      /**
       * One plain-language sentence for non-engineers on the /wiring page.
       */
      caption: string;
      /**
       * MQTT topics this part feeds. Each must exist in /shared (checked in W5).
       */
      topics?: string[];
      /**
       * Outline on top.jpg in % for on-board parts. null until measured from the photo.
       */
      outline_pct?: {
        x: number;
        y: number;
        w: number;
        h: number;
      } | null;
      status: WiringStatus;
      pins: WiringPin[];
      notes?: string;
    }[]
  ];
  connections: {
    id: WiringId;
    from: WiringPinRef;
    to: WiringPinRef;
    signal: string;
    bus?: string | null;
    /**
     * pcb = trace on the dev kit, drawn as a highlight, not a wire.
     */
    medium: "pcb" | "qwiic_cable" | "wire";
    /**
     * Qwiic code: red 3.3 V, black GND, blue SDA, yellow SCL. null for PCB traces.
     */
    wire_color: "red" | "black" | "blue" | "yellow" | "white" | "green" | null;
    status: WiringStatus;
    evidence: WiringEvidence;
    source?: string;
  }[];
  /**
   * Ordered steps the firmware must run before reading sensors (e.g. re-addressing a part whose default address clashes).
   */
  boot_sequence: {
    step: number;
    action: string;
    pin?: WiringPinRef;
    address?: string;
    reason: string;
  }[];
  open_questions: {
    id: WiringId;
    question: string;
    /**
     * Part or connection ids that stay unverified until answered.
     */
    blocks: string[];
  }[];
}
/**
 * Allowed supply range from the datasheet.
 */
export interface WiringVoltageRange {
  min_v: number;
  max_v: number;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_pin".
 */
export interface WiringPin {
  /**
   * Pin name on this part (SDA, MOSI, qwiic_in.SDA, ULP_GPIO_6).
   */
  name: string;
  /**
   * Function: SDA, SCL, MOSI, MISO, SCK, CS, INT, 3V3, GND, EN, ...
   */
  signal: string;
  /**
   * SoC GPIO name when this pin is on the SoC or wired to it, else null.
   */
  gpio?: string | null;
  /**
   * Position on frontend/public/board/top.jpg (on-board parts and board pads only).
   */
  x_pct?: number | null;
  y_pct?: number | null;
  evidence: WiringEvidence;
  /**
   * File or document the value came from.
   */
  source?: string;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_voltage_range".
 */
export interface WiringVoltageRange1 {
  min_v: number;
  max_v: number;
}
