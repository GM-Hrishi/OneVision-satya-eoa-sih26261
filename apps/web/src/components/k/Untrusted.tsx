// Renders document-derived text as an inert, truncated text node (guardrail 8). The full text is not exposed.
import { inertSnippet } from "@/lib/untrusted";

export function Untrusted({ value, max, className }: { value: unknown; max?: number; className?: string }) {
  return <span className={className}>{inertSnippet(value, max)}</span>;
}
