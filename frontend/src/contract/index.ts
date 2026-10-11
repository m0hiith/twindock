export type * from "./generated";
import type {
  AckAlert, AlertsUpdate, SafetyCommand, ScenarioCommand, BleTracks, CommandAck, DeviceUpdate, Event, GatewayUpdate, LedCommand, MachineCommand, MoveUnit, ProductionUpdate, SafetyUpdate,
  SelectionChanged, SelectUnit, SetAutoMode, SetSimSpeed, SimClock, UnitUpdate, WorldSnapshot, ControlUpdate, ControlDecision, LogisticsUpdate,
} from "./generated";

export type ServerMessage =
  WorldSnapshot | UnitUpdate | GatewayUpdate | SelectionChanged | CommandAck | Event | BleTracks | DeviceUpdate
  | ProductionUpdate | SafetyUpdate | AlertsUpdate | SimClock | ControlUpdate | LogisticsUpdate;
export type ClientMessage = MoveUnit | SelectUnit | LedCommand | SetAutoMode | MachineCommand | AckAlert | ScenarioCommand | SafetyCommand | SetSimSpeed | ControlDecision;
