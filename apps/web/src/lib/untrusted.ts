// Text derived from an uploaded document (extracted values, AI-reader-text snippets, file names, OCR text)
// is UNTRUSTED. It is only ever rendered as a React text child (escaped, inert): never as HTML, markdown or a
// link, and always truncated. This helper does the truncation; rendering stays in JSX.
export const MAX_SNIPPET = 160;

/** Collapse whitespace and cut to `max` characters, adding an ellipsis. Never interprets the text. */
export function inertSnippet(value: unknown, max: number = MAX_SNIPPET): string {
  const text = (typeof value === "string" ? value : value === null || value === undefined ? "" : String(value)).replace(/\s+/g, " ").trim();
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}
