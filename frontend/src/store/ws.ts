// WebSocket link to the backend. Reconnects with backoff; every message is schema-checked.
import type { ClientMessage } from "../contract";
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
    if (m) apply(m);
  };
  ws.onclose = () => {
    if (socket !== ws) return;
    setConn("reconnecting");
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
