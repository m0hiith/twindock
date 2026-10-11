/* Generated from /shared/schemas by scripts/gen-types.mjs. Do not edit. */

/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "device_type".
 */
export type DeviceType =
  | "gateway"
  | "machine_monitor"
  | "env_sensor"
  | "door_sensor"
  | "occupancy_sensor"
  | "badge"
  | "asset_tag"
  | "power_meter"
  | "light"
  | "air_quality"
  | "truck_telematics"
  | "dock_bay"
  | "conveyor_monitor"
  | "compressor_monitor"
  | "helmet_clip"
  | "gas_detector"
  | "leak_sensor"
  | "tank_level"
  | "fire_panel"
  | "water_quality";
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "protocol".
 */
export type Protocol = "wifi" | "ble" | "thread" | "matter";
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "channel".
 */
export type Channel = string;
/**
 * [x, z] in metres
 *
 * @minItems 2
 * @maxItems 2
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "xz".
 */
export type Xz = [number, number];
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "cmd_id".
 */
export type CmdId = string;
/**
 * e.g. FL-01, TR-02, PL-07, GW-01, M-01 (machine), WK-01 (worker)
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "unit_id".
 */
export type UnitId = string;
/**
 * e.g. GW-01 (the real board), MM-01, BG-03
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "device_id".
 */
export type DeviceId = string;
/**
 * e.g. WH-01, FAC-01. Never 'gateway', so twin/gateway/* can't be a site topic.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "site_id".
 */
export type SiteId = string;
/**
 * Waypoint graph node, e.g. DOCK_1, RACK_A3, CHARGER_C1, GATE_IN
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "node_id".
 */
export type NodeId = string;
/**
 * e.g. FAC01_PRODUCTION
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "zone_id".
 */
export type ZoneId = string;
/**
 * e.g. FL-01, TR-02, PL-07, GW-01, M-01 (machine), WK-01 (worker)
 */
export type UnitId1 = string;
/**
 * online: last message <= 15 s old; stale: <= 60 s; offline: older or never; fault: the device reports a fault.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "device_status".
 */
export type DeviceStatus = "online" | "stale" | "offline" | "fault";
/**
 * e.g. FL-01, TR-02, PL-07, GW-01, M-01 (machine), WK-01 (worker)
 */
export type UnitId2 = string;
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "kind".
 */
export type Kind = "forklift" | "truck" | "pallet" | "dock" | "rack" | "charger" | "gateway" | "machine" | "worker";
/**
 * device = real board data; sim = produced by tools/site_sim.py, never real.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "source".
 */
export type Source = "device" | "manual" | "auto" | "sim";
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "zone_kind".
 */
export type ZoneKind =
  | "canteen"
  | "cold_room"
  | "docks"
  | "etp"
  | "gate"
  | "green"
  | "hazmat"
  | "lab"
  | "muster"
  | "office"
  | "parking"
  | "production"
  | "storage"
  | "utilities"
  | "workshop"
  | "yard"
  | "medical"
  | "pump_house"
  | "raw_store";
/**
 * [x, z] in metres
 *
 * @minItems 2
 * @maxItems 2
 */
export type Xz1 = [number, number];
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
 * datasheet: dimensions from the datasheet or the breakout's product page. typical: the usual size for this kind of part, because the exact model is not chosen yet.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_dims_evidence".
 */
export type WiringDimsEvidence = "datasheet" | "typical";
/**
 * <part id>.<pin name>, e.g. soc.ULP_GPIO_6 or vl53l1x.qwiic_in.SDA
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_pin_ref".
 */
export type WiringPinRef = string;
/**
 * Where a part number or spec came from. datasheet: the manufacturer datasheet or product page. silabs.com: the Silicon Labs product page. unverified: not checked yet, shown as such everywhere.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_source".
 */
export type WiringSource = "datasheet" | "silabs.com" | "unverified";
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
  site_cmd?: SiteCmd;
  site_hello?: SiteHello;
  site_reading?: SiteReading;
  site_status?: SiteStatus;
  ack_alert?: AckAlert;
  alerts_update?: AlertsUpdate;
  ble_tracks?: BleTracks;
  command_ack?: CommandAck;
  device_update?: DeviceUpdate;
  event?: Event;
  gateway_update?: GatewayUpdate;
  led_command?: LedCommand;
  machine_command?: MachineCommand;
  move_unit?: MoveUnit;
  production_update?: ProductionUpdate;
  safety_command?: SafetyCommand;
  safety_update?: SafetyUpdate;
  scenario_command?: ScenarioCommand;
  select_unit?: SelectUnit;
  selection_changed?: SelectionChanged;
  set_auto_mode?: SetAutoMode;
  set_sim_speed?: SetSimSpeed;
  sim_clock?: SimClock;
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
 * Backend to the simulator, for simulated devices only (never GW-01). Actions: degrade, restore, maintenance (machine monitors); jam (conveyor monitors); door_open, door_close (door sensors); route (badges); goto, buzz, fall, still, cancel, sos, checkin, skip_checkin (badges, demo); leak, clear (gas detectors, leak sensors); alarm, reset (fire panel bridge); find_me (asset tags, seconds); silence (any sim device stops publishing, to demonstrate staleness).
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "site_cmd".
 */
export interface SiteCmd {
  cmd_id: string;
  on?: boolean;
  seconds?: number;
  x?: number;
  z?: number;
  route?: string;
  /**
   * goto only: walkway waypoints [x, z] to follow on the way to (x, z).
   *
   * @maxItems 80
   */
  path?: [number, number][];
}
/**
 * Retained. Announces a commissioned device, like the board's hello. The backend checks it against backend/world/sites.json.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "site_hello".
 */
export interface SiteHello {
  type: DeviceType;
  protocol: Protocol;
  capabilities: Channel[];
  fw_version: string;
  /**
   * Everything on twin/<site>/... is simulated. Real devices other than GW-01 do not exist yet.
   */
  source: "sim";
}
/**
 * One reading on a channel listed in the device's hello capabilities.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "site_reading".
 */
export interface SiteReading {
  ts_ms: number;
  /**
   * Number, flag, state name, or [x, z] metres for a badge position.
   */
  value: (number | boolean | string) | Xz;
  unit?: string;
  /**
   * Everything on twin/<site>/... is simulated. Real devices other than GW-01 do not exist yet.
   */
  source: "sim";
}
/**
 * Device health, every 10 s.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "site_status".
 */
export interface SiteStatus {
  ts_ms: number;
  battery_pct?: number;
  rssi_dbm?: number;
  fault?: string | null;
  /**
   * Everything on twin/<site>/... is simulated. Real devices other than GW-01 do not exist yet.
   */
  source: "sim";
}
/**
 * Acknowledge an open alert. `by` is who acknowledged it as shown to everyone (no sign-in on this demo: the screen's name, e.g. "Control Room (phone)").
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "ack_alert".
 */
export interface AckAlert {
  type: "ack_alert";
  cmd_id: CmdId;
  alert_id: string;
  by: string;
}
/**
 * All open alerts (sorted: critical first, newest first) followed by recently resolved ones, plus every rule from backend/rules/*.yaml. On connect and whenever an alert is raised, acknowledged or resolved.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "alerts_update".
 */
export interface AlertsUpdate {
  type: "alerts_update";
  seq: number;
  server_ts_ms: number;
  alerts: {
    id: string;
    rule_id: string;
    severity: "info" | "warning" | "critical";
    title: string;
    subject_id: string;
    message: string;
    state: "raised" | "acknowledged" | "resolved";
    raised_ms: number;
    acknowledged_by: string | null;
    acknowledged_ms: number | null;
    resolved_ms: number | null;
    /**
     * Where the alert points: the camera flies to x/z on site_id.
     */
    target: {
      unit_id?: UnitId;
      device_id?: DeviceId;
      site_id?: SiteId;
      x?: number;
      z?: number;
    };
  }[];
  rules: {
    id: string;
    name: string;
    /**
     * The rule in plain language, for the rules page.
     */
    plain: string;
    subject: "machine" | "worker" | "device" | "gateway" | "line" | "site";
    severity: "info" | "warning" | "critical";
    for_s: number;
    enabled: boolean;
  }[];
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
  command:
    | "move_unit"
    | "select_unit"
    | "led_command"
    | "set_auto_mode"
    | "machine_command"
    | "ack_alert"
    | "scenario_command"
    | "safety_command"
    | "set_sim_speed";
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
 * Devices whose status, readings, battery or signal changed. At most 2 Hz.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "device_update".
 */
export interface DeviceUpdate {
  type: "device_update";
  seq: number;
  server_ts_ms: number;
  devices: Device[];
  removed?: DeviceId[];
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "device".
 */
export interface Device {
  id: DeviceId;
  site_id: SiteId;
  zone_id: ZoneId;
  type: DeviceType;
  protocol: Protocol;
  capabilities: Channel[];
  x: number;
  z: number;
  label?: string;
  attached_to?: UnitId1;
  battery_pct?: number | null;
  fw_version?: string | null;
  rssi_dbm?: number | null;
  /**
   * Backend time of the last message; null if never.
   */
  last_seen_ms: number | null;
  source: "device" | "sim";
  status: DeviceStatus;
  fault?: string | null;
  /**
   * Latest value per channel, each with its own receive time.
   */
  readings: {
    [k: string]: Reading | undefined;
  };
  /**
   * Id of the device kit (hardware/kits/<id>.json) this device is built from. One kit design, many devices.
   */
  kit?: string;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "reading".
 */
export interface Reading {
  value: (number | boolean | string) | Xz;
  unit?: string;
  received_ms: number;
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
 * Simulation control for a FAC-01 machine (the 'degrade' demo control on /control). Forwarded to tools/site_sim.py on twin/<site>/<device>/cmd/<action>; never to the real board.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "machine_command".
 */
export interface MachineCommand {
  type: "machine_command";
  cmd_id: CmdId;
  machine_id: UnitId;
  action: "degrade" | "restore" | "maintenance";
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
  pallet_id?: UnitId2;
}
/**
 * FAC-01 production analytics from the (simulated) machine monitors. On connect and at most 1 Hz.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "production_update".
 */
export interface ProductionUpdate {
  type: "production_update";
  seq: number;
  server_ts_ms: number;
  machines: {
    id: UnitId;
    device_id: DeviceId;
    label: string;
    /**
     * no_data: the machine monitor is not online, so the state is unknown.
     */
    state: "running" | "idle" | "fault" | "maintenance" | "no_data";
    state_since_ms: number | null;
    data_ms: number | null;
    cycle_time_s: number | null;
    ideal_cycle_s: number;
    current_a: number | null;
    vibration_rms: number | null;
    baseline: {
      learned: boolean;
      samples: number;
      mean: number | null;
      std: number | null;
    };
    z: number | null;
    /**
     * Abnormal compared with this machine's learned baseline. Not a failure prediction.
     */
    abnormal: boolean;
    units_today: number;
    rejects_today: number;
    last_fault: null | {
      text: string;
      at_ms: number;
    };
    availability: number | null;
    performance: number | null;
    quality: number | null;
    oee: number | null;
  }[];
  line: {
    units_today: number;
    pallets_made: number;
    /**
     * Full pallets with no free outbound spot.
     */
    pallets_waiting: number;
    units_toward_pallet: number;
    availability: number | null;
    performance: number | null;
    quality: number | null;
    oee: number | null;
  };
  config: {
    z_threshold: number;
    z_clear: number;
    baseline_s: number;
    window_samples: number;
    units_per_pallet: number;
  };
}
/**
 * Worker safety actions from the monitoring page (K3/K4): start or end an evacuation, close a worker's SOS or man-down once someone has reached them. The sim_* actions drive a SIMULATED badge through tools/site_sim.py (demo only; never a real device).
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "safety_command".
 */
export interface SafetyCommand {
  type: "safety_command";
  cmd_id: CmdId;
  action:
    | "start_evacuation"
    | "end_evacuation"
    | "clear_incident"
    | "sim_fall"
    | "sim_cancel"
    | "sim_sos"
    | "sim_checkin"
    | "sim_still";
  worker_id?: UnitId;
  reason?: string;
  by?: string;
}
/**
 * Worker safety from badges: proximity (with direction), restricted zones and time limits, falls/man-down, SOS, lone-worker check-ins, gas evacuation and evacuation headcount, today's counters. Workers are identified by id and role only (no names). Position and zone are only sent while that worker has an active safety condition or an evacuation is running (location_shown); otherwise screens get zone counts. On connect and at most 2 Hz.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "safety_update".
 */
export interface SafetyUpdate {
  type: "safety_update";
  seq: number;
  server_ts_ms: number;
  workers: {
    id: UnitId;
    role: string;
    badge_id: DeviceId;
    zone_id: ZoneId | null;
    x: number | null;
    z: number | null;
    /**
     * Badge online (last position at most 15 s old).
     */
    fresh: boolean;
    data_ms: number | null;
    near: {
      forklift: string;
      distance_m: number;
      level: "warning" | "critical";
      reversing?: boolean;
    } | null;
    restricted_zone: ZoneId | null;
    prealert: {
      kind: "fall" | "no_motion";
      deadline_ms: number;
    } | null;
    man_down: ("fall" | "no_motion") | null;
    sos_ms: number | null;
    evacuate: string | null;
    lone: ("warning" | "critical") | null;
    zone_overtime_min: number | null;
    first_aider: boolean;
    nearest_first_aider: {
      id: string;
      distance_m: number;
    } | null;
    mustered: string | null;
    location_shown: boolean;
  }[];
  /**
   * Workers with a fresh badge per zone id.
   */
  zone_counts: {
    [k: string]: number | undefined;
  };
  today: {
    warnings: number;
    criticals: number;
    restricted: number;
    closest_m: number | null;
    closest: null | {
      worker: UnitId;
      forklift: UnitId;
      at_ms: number;
    };
    falls: number;
    falls_cancelled: number;
    sos: number;
    last_fall_ms: number | null;
    last_sos_ms: number | null;
  };
  config: {
    warn_m: number;
    crit_m: number;
  };
  evacuation: {
    active: true;
    started_ms: number;
    reason: string;
    by: string;
    on_site: number;
    accounted: number;
    by_muster: {
      [k: string]: number | undefined;
    };
    unaccounted: {
      id: string;
      role: string;
      last_zone_id: string | null;
      last_seen_ms: number | null;
    }[];
  } | null;
  on_site: number;
  in_hazardous: number;
  gas_zones: string[];
  heat_zones: {
    [k: string]: number | undefined;
  };
  /**
   * Badges currently reminded about missing PPE. A count only: who it is is never sent or stored.
   */
  ppe_reminders: number;
  /**
   * How many workers are due a break. Who is only served to the worker and the supervisor.
   */
  breaks_due: number;
  privacy: {
    location: "alerts_only" | "always";
    retention_days: number;
  };
  /**
   * While an evacuation runs or a gas alarm is on: per zone with people (and the hazard zones), the walking route to the nearest muster point that is not next to the hazard. Advice only.
   */
  routes: {
    zone_id: string;
    muster_id: string;
    length_m: number;
    points: [number, number][];
  }[];
}
/**
 * Demo runner on /control (SITE_PROMPTS.md S10): trigger one simulated beat on cue, or reset the demo. Beats only drive the simulator (twin/<site>/<device>/cmd/*) and the movement engine; never the real board. Campus emergencies (F3): grid_failure (substation incomer loses the grid, generator starts), gas_leak (hazardous store), fire_alarm (warehouse fire panel bridge), compressor_fault (compressor trips, air pressure falls).
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "scenario_command".
 */
export interface ScenarioCommand {
  type: "scenario_command";
  cmd_id: CmdId;
  beat:
    | "degrade"
    | "near_miss"
    | "visitor"
    | "cold_door"
    | "stale"
    | "reset"
    | "grid_failure"
    | "gas_leak"
    | "fire_alarm"
    | "compressor_fault";
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
 * Run the simulation clock at x1 (real time, the default), x5 or x20. Refused while the real board is online: board data is always on real time.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "set_sim_speed".
 */
export interface SetSimSpeed {
  type: "set_sim_speed";
  cmd_id: CmdId;
  speed: 1 | 5 | 20;
}
/**
 * The simulation clock (backend/twindock/simclock.py): on connect, when the speed changes and every few seconds. sim_ms is the simulated time (also every message's server_ts_ms); speed 1 is real time. warm_start says how much simulated time was fast-forwarded before the backend served, with which seed. speed_locked is why the speed can't be changed now (the real board is online), or null.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "sim_clock".
 */
export interface SimClock {
  type: "sim_clock";
  seq: number;
  server_ts_ms: number;
  sim_ms: number;
  speed: 1 | 5 | 20;
  speeds: (1 | 5 | 20)[];
  warm_start: null | {
    sim_s: number;
    wall_s: number;
    seed: number;
  };
  speed_locked: string | null;
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
  sites: Site[];
  devices: Device[];
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "site".
 */
export interface Site {
  id: SiteId;
  name: string;
  short: string;
  kind: "warehouse" | "factory" | "mixed";
  layout_ref: string;
  bounds: {
    x: Xz;
    z: Xz;
  };
  zones: Zone[];
  home?: Xz1;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "zone".
 */
export interface Zone {
  id: ZoneId;
  site_id: SiteId;
  name: string;
  kind: ZoneKind;
  /**
   * @minItems 3
   */
  polygon: [Xz, Xz, Xz, ...Xz[]];
  /**
   * If present, only these worker roles may enter (S3).
   */
  restricted_roles?: string[];
  /**
   * Hazard level for worker safety (K3).
   */
  hazard?: "low" | "medium" | "high";
  /**
   * PPE required in the zone. Only the helmet can be sensed (helmet clip); missing PPE is a reminder on the badge, never a record.
   */
  ppe?: ("helmet" | "vest" | "hearing" | "glasses" | "gloves" | "respirator" | "safety_shoes")[];
  /**
   * Maximum continuous stay (hot or gas-risk zones).
   */
  time_limit_min?: number;
  /**
   * Someone alone here must check in every checkin_min minutes.
   */
  lone_worker?: boolean;
  checkin_min?: number;
}
/**
 * One device kit: the parts, pins, wires and bill of materials for one kind of asset. FL-01's sensor pack (status "built") is the only kit on real hardware; every other kit is a reference design (status "reference"): real, buyable parts with a correct wiring plan whose data is simulated. Firmware pins (tools/gen_pins.py), the /wiring/:kit_id page and docs/hardware_sheet.pdf are generated from it. Nothing here may be guessed: a value that is not confirmed from the SDK, a datasheet or the developer is null and its `evidence` is "unverified".
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring".
 */
export interface Wiring {
  version: 1;
  board: string;
  sdk: string;
  /**
   * Outline of the bare board for the /wiring page, used until frontend/public/board/top.jpg exists (and for parts whose outline_pct is still null). Positions are % of board width/height, top view, 0,0 = top-left. Optional: kits without a photographed dev board omit it and the page lays parts out from their own drawings.
   */
  board_drawing?: {
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
      drawing?: WiringDrawing;
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
      drawing?: WiringDrawing;
    }[]
  ];
  connections: {
    id: WiringId;
    from: WiringPinRef;
    to: WiringPinRef;
    signal: string;
    bus?: string | null;
    /**
     * pcb = trace on the dev kit, drawn as a highlight, not a wire. *_cable = a pre-made cable with moulded connectors, drawn as one cable per connector pair.
     */
    medium: "pcb" | "qwiic_cable" | "wire" | "m12_cable" | "jst_cable" | "usb_cable";
    /**
     * Qwiic code: red 3.3 V, black GND, blue SDA, yellow SCL. null for PCB traces.
     */
    wire_color: "red" | "black" | "blue" | "yellow" | "white" | "green" | "brown" | "grey" | "orange" | null;
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
  kit: {
    id: WiringId;
    name: string;
    /**
     * Groups kits in the /wiring picker and on /kits.
     */
    asset_type:
      | "forklift"
      | "truck"
      | "dock"
      | "pallet"
      | "machine"
      | "conveyor"
      | "utility"
      | "worker"
      | "building"
      | "environment"
      | "energy"
      | "fire";
    /**
     * built: real hardware, verified on the bench. reference: parts and wiring plan are real and buyable, data is simulated.
     */
    status: "built" | "reference";
    radio: {
      protocol: "wifi" | "ble" | "thread" | "matter" | "zigbee" | "wired";
      /**
       * Silicon Labs part or family, e.g. SiWG917 or EFR32MG24.
       */
      chip: string;
      /**
       * One line: why this radio for this job.
       */
      reason: string;
      evidence: WiringSource;
    };
    power_source: {
      type: "mains" | "vehicle" | "battery" | "din_rail" | "usb";
      description: string;
    };
    /**
     * An estimate, shown as one, with the assumptions behind it.
     */
    power_budget?: {
      average_ma: number;
      peak_ma?: number;
      supply_v?: number;
      assumptions: string;
    };
    mounting: string;
    purpose: string;
    /**
     * Estimate only, with its assumptions.
     */
    est_battery_life?: {
      days: number;
      assumptions: string;
    };
    /**
     * 2-3 plain-language sentences for non-engineers.
     */
    captions?: string[];
    /**
     * Channels a device built from this kit reports (twin/<site>/<device>/<channel>). A reference kit's channels are simulated: source is always sim.
     */
    publishes?: {
      channel: string;
      unit?: string;
      description: string;
    }[];
  };
  /**
   * @minItems 1
   */
  bom: [
    {
      id: WiringId;
      part_number: string;
      manufacturer: string;
      description: string;
      quantity: number;
      /**
       * Approximate, for budgeting. null when unknown.
       */
      unit_cost_usd: number | null;
      link: string | null;
      source: WiringSource;
      /**
       * Ids of the `parts` entries this line supplies (a dev kit covers its on-board parts too).
       *
       * @minItems 1
       */
      covers: [WiringId, ...WiringId[]];
    },
    ...{
      id: WiringId;
      part_number: string;
      manufacturer: string;
      description: string;
      quantity: number;
      /**
       * Approximate, for budgeting. null when unknown.
       */
      unit_cost_usd: number | null;
      link: string | null;
      source: WiringSource;
      /**
       * Ids of the `parts` entries this line supplies (a dev kit covers its on-board parts too).
       *
       * @minItems 1
       */
      covers: [WiringId, ...WiringId[]];
    }[]
  ];
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
  /**
   * Pad position on the part's drawing, mm from its top-left corner, so wires land on the real pads.
   */
  x_mm?: number | null;
  y_mm?: number | null;
  /**
   * Edge of the drawing the wire leaves from (defaults to the nearest edge to x_mm/y_mm).
   */
  side?: "left" | "right" | "top" | "bottom";
}
/**
 * How the part looks from above on the breadboard view, drawn at true size from real dimensions. If frontend/public/parts/<part_id>.jpg exists it is shown instead.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_drawing".
 */
export interface WiringDrawing {
  family:
    | "pcb"
    | "chip"
    | "connector"
    | "passive"
    | "crystal"
    | "antenna"
    | "led"
    | "button"
    | "coin_cell_holder"
    | "lipo"
    | "sensor_window"
    | "relay"
    | "terminal_block"
    | "current_clamp"
    | "load_cell"
    | "reed_switch"
    | "pir_dome"
    | "buzzer"
    | "magnet"
    | "probe"
    | "din_meter"
    | "enclosure";
  variant?: string;
  w_mm: number;
  h_mm: number;
  pcb_color?: "green" | "blue" | "black" | "red" | "white" | "yellow" | "none";
  label?: string;
  dims_evidence: WiringDimsEvidence;
  features?: WiringDrawingFeature[];
  /**
   * Body colour for parts whose colour matters (an LED's colour).
   */
  color?: string;
}
/**
 * A part drawn on top of its PCB (chip, connector, LED...), positioned in mm from the PCB's top-left corner.
 *
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_drawing_feature".
 */
export interface WiringDrawingFeature {
  family:
    | "pcb"
    | "chip"
    | "connector"
    | "passive"
    | "crystal"
    | "antenna"
    | "led"
    | "button"
    | "coin_cell_holder"
    | "lipo"
    | "sensor_window"
    | "relay"
    | "terminal_block"
    | "current_clamp"
    | "load_cell"
    | "reed_switch"
    | "pir_dome"
    | "buzzer"
    | "magnet"
    | "probe"
    | "din_meter"
    | "enclosure";
  /**
   * qfn, lga, soic, module, qwiic, jst_ph, screw, header, usb_c, m12, r0603, c0805, chip, trace, ufl, tof, gas, mic, light...
   */
  variant?: string;
  /**
   * Marking printed on the part (e.g. VL53L1X), kept short.
   */
  label?: string;
  x_mm: number;
  y_mm: number;
  w_mm: number;
  h_mm: number;
  rot?: 0 | 90 | 180 | 270;
  color?: string;
}
/**
 * This interface was referenced by `TwinDockContract`'s JSON-Schema
 * via the `definition` "wiring_voltage_range".
 */
export interface WiringVoltageRange1 {
  min_v: number;
  max_v: number;
}
