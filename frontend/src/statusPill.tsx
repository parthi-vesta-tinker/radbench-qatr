import { AlertCircle, Check, Circle } from "lucide-react";

// Presentation-only severity. Backend status strings are unchanged; nothing here is persisted.
const DANGER = ["error", "failed", "unavailable"];
const ATTENTION = ["degraded", "not_configured", "needs_attention", "needs_input", "unknown"];

export type Tier = "danger" | "attention" | "neutral";
export const tierOf = (status: string): Tier =>
  DANGER.includes(status) ? "danger" : ATTENTION.includes(status) ? "attention" : "neutral";

const sentence = (status: string) => {
  const words = status.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
};

export function StatusPill({ status, size = 13 }: { status: string; size?: number }) {
  const tier = tierOf(status);
  // Icon as well as colour, so severity does not depend on colour alone.
  const icon = tier === "neutral" ? <Check size={size}/> : <AlertCircle size={size}/>;
  return <span className={"status-pill " + tier}>{icon}{sentence(status)}</span>;
}

export function StatusDot({ tier }: { tier: Tier }) {
  return tier === "neutral" ? <Check size={15}/> : tier === "danger" ? <AlertCircle size={15}/> : <Circle size={13}/>;
}
