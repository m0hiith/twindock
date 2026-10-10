export type * from "./generated";
import type {
  BleTracks, CommandAck, DeviceUpdate, Event, GatewayUpdate, LedCommand, MoveUnit, SelectionChanged, SelectUnit,
  SetAutoMode, UnitUpdate, WorldSnapshot,
} from "./generated";

export type ServerMessage =
  WorldSnapshot | UnitUpdate | GatewayUpdate | SelectionChanged | CommandAck | Event | BleTracks | DeviceUpdate;
export type ClientMessage = MoveUnit | SelectUnit | LedCommand | SetAutoMode;
