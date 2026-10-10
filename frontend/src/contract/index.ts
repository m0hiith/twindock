export type * from "./generated";
import type {
  BleTracks, CommandAck, DeviceUpdate, Event, GatewayUpdate, LedCommand, MachineCommand, MoveUnit, ProductionUpdate, SafetyUpdate,
  SelectionChanged, SelectUnit, SetAutoMode, UnitUpdate, WorldSnapshot,
} from "./generated";

export type ServerMessage =
  WorldSnapshot | UnitUpdate | GatewayUpdate | SelectionChanged | CommandAck | Event | BleTracks | DeviceUpdate
  | ProductionUpdate | SafetyUpdate;
export type ClientMessage = MoveUnit | SelectUnit | LedCommand | SetAutoMode | MachineCommand;
