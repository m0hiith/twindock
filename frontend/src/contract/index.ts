export type * from "./generated";
import type {
  BleTracks, CommandAck, Event, GatewayUpdate, LedCommand, MoveUnit, SelectionChanged, SelectUnit, SetAutoMode,
  UnitUpdate, WorldSnapshot,
} from "./generated";

export type ServerMessage = WorldSnapshot | UnitUpdate | GatewayUpdate | SelectionChanged | CommandAck | Event | BleTracks;
export type ClientMessage = MoveUnit | SelectUnit | LedCommand | SetAutoMode;
