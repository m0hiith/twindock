// WebSocket link to the backend. Reconnects with backoff; every message is schema-checked.
// The URL comes from the page's own origin (wss on https), so the same build works behind any host.
// Every (re)connection gets a fresh world_snapshot from the server (Engine.on_connect), which replaces
// the whole local world: after a hosted backend wakes up or restarts, nothing stale survives.
import type { ClientMessage, CommandAck } from "../contract";
import { checkClientMessage, parseServerMessage } from "../contract/validate";
import { useWorld } from "./world";

type Outgoing = ClientMessage extends infer M ? (M extends ClientMessage ? Omit<M, "cmd_id"> : never) : never;

let socket: WebSocket | null = null;
let backoffMs = 500;
let counter = 0;

function url(): string {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/ws`;
}

export function connect(): void {
  const { setConn, apply } = useWorld.getState();
  const ws = new WebSocket(url());
  socket = ws;
  ws.onopen = () => {
    backoffMs = 500;
    setConn("live");
  };
  ws.onmessage = (e) => {
    const m = parseServerMessage(String(e.data));
    if (!m) return;
    apply(m);
    if (m.type === "command_ack") {
      waiting.get(m.cmd_id)?.(m);
      waiting.delete(m.cmd_id);
    }
  };
  ws.onclose = () => {
    if (socket !== ws) return;
    setConn("reconnecting");
    for (const resolve of waiting.values()) resolve(localFailure("Connection lost before the server replied"));
    waiting.clear();
    // Jitter so many screens don't reconnect in lockstep when a sleeping host wakes up.
    setTimeout(connect, backoffMs * (0.75 + Math.random() * 0.5));
    backoffMs = Math.min(backoffMs * 2, 10000);
  };
}

/** Send an intent. Returns the cmd_id so callers can match the command_ack. */
export function send(msg: Outgoing): string | null {
  const cmd_id = `${Date.now().toString(36)}-${(++counter).toString(36)}`;
  const full = { ...msg, cmd_id } as ClientMessage;
  checkClientMessage(full);
  if (!socket || socket.readyState !== WebSocket.OPEN) return null;
  socket.send(JSON.stringify(full));
  return cmd_id;
}

const ACK_TIMEOUT_MS = 5000;
/** The browser itself saw the command not get through (no socket, no reply in time). Kept apart
 *  from CommandAck so it is never shown as if the server had rejected the command. */
export interface LocalFailure { type: "local_failure"; reason: string }
export type Reply = CommandAck | LocalFailure;

const waiting = new Map<string, (a: Reply) => void>();

function localFailure(reason: string): LocalFailure {
  return { type: "local_failure", reason };
}

/** Send an intent and wait for its command_ack (or a local failure after 5 s). */
export function request(msg: Outgoing): { cmd_id: string; ack: Promise<Reply> } {
  const cmd_id = send(msg);
  if (cmd_id === null) {
    return { cmd_id: `local-${++counter}`, ack: Promise.resolve(localFailure("Not connected to the server")) };
  }
  const ack = new Promise<Reply>((resolve) => {
    waiting.set(cmd_id, resolve);
    setTimeout(() => {
      if (waiting.delete(cmd_id)) resolve(localFailure("No reply from the server within 5 s"));
    }, ACK_TIMEOUT_MS);
  });
  return { cmd_id, ack };
}
