export type * from "./generated";
import type {
  CommandAck, Event, GatewayUpdate, LedCommand, MoveUnit, SelectionChanged, SelectUnit, SetAutoMode,
  UnitUpdate, WorldSnapshot,
} from "./generated";

export type ServerMessage = WorldSnapshot | UnitUpdate | GatewayUpdate | SelectionChanged | CommandAck | Event;
export type ClientMessage = MoveUnit | SelectUnit | LedCommand | SetAutoMode;
