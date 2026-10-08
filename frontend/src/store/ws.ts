// WebSocket link to the backend. Reconnects with backoff; every message is schema-checked.
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
    for (const [id, resolve] of waiting) resolve(localFailure(id, "Connection lost"));
    waiting.clear();
    setTimeout(connect, backoffMs);
    backoffMs = Math.min(backoffMs * 2, 5000);
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
const waiting = new Map<string, (a: CommandAck) => void>();

/** A failure the client noticed itself (no socket, no reply). Never confused with a server ack:
 *  it only ever says the command did not get through. */
function localFailure(cmd_id: string, reason: string, command: CommandAck["command"] = "move_unit"): CommandAck {
  return { type: "command_ack", cmd_id, command, ok: false, reason };
}

/** Send an intent and wait for its command_ack (or a local failure after 5 s). */
export function request(msg: Outgoing): { cmd_id: string; ack: Promise<CommandAck> } {
  const cmd_id = send(msg);
  if (cmd_id === null) {
    return { cmd_id: `local-${++counter}`, ack: Promise.resolve(localFailure("", "Not connected to the server", msg.type)) };
  }
  const ack = new Promise<CommandAck>((resolve) => {
    waiting.set(cmd_id, resolve);
    setTimeout(() => {
      if (waiting.delete(cmd_id)) resolve(localFailure(cmd_id, "No reply from the server", msg.type));
    }, ACK_TIMEOUT_MS);
  });
  return { cmd_id, ack };
}
