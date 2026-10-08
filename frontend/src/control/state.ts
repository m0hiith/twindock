// Control Room view state. Nothing here is world state: the proposal is a server-validated
// dry run waiting for the operator's confirm, and the log records commands and their acks.
import { create } from "zustand";
import type { CommandAck, MoveUnit } from "../contract";
import { request } from "../store/ws";

export type Action = NonNullable<MoveUnit["action"]>;

/** One thing the selected unit could be told to do. */
export interface Candidate {
  key: string;
  label: string;
  sub?: string;
  target: string;
  action: Action;
  pallet_id?: string;
}

/** A candidate plus the server's dry-run answer. */
export interface Checked extends Candidate {
  ok: boolean;
  reason?: string;
  path?: string[];
}

export interface LogEntry {
  cmd_id: string;
  text: string;
  sent_ms: number;
  ack: CommandAck | null;
}

interface ControlState {
  proposal: (Checked & { unit_id: string }) | null;
  /** Reason shown after tapping a disabled destination. */
  notice: { text: string; at: number } | null;
  log: LogEntry[];
  propose: (p: ControlState["proposal"]) => void;
  setNotice: (text: string | null) => void;
  /** Send a command for real, log it, and record its ack when it arrives. */
  run: (msg: Parameters<typeof request>[0], text: string) => Promise<CommandAck>;
}

const MAX_LOG = 100;

export const useControl = create<ControlState>((set) => ({
  proposal: null,
  notice: null,
  log: [],
  propose: (proposal) => set({ proposal, notice: null }),
  setNotice: (text) => set({ notice: text ? { text, at: Date.now() } : null }),
  run: async (msg, text) => {
    const { cmd_id, ack } = request(msg);
    set((s) => ({ log: [...s.log, { cmd_id, text, sent_ms: Date.now(), ack: null }].slice(-MAX_LOG) }));
    const a = await ack;
    set((s) => ({ log: s.log.map((e) => (e.cmd_id === cmd_id ? { ...e, ack: a } : e)) }));
    return a;
  },
}));

export const actionVerb: Record<Action, string> = {
  goto: "Drive to", pick: "Pick at", drop: "Drop at", load: "Load at", charge: "Charge at", dock: "Dock at", depart: "Depart via",
};
