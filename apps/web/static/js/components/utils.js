/**
 * Escapes a value for safe insertion into HTML attribute values and text content.
 * Handles null and undefined by treating them as empty strings.
 */
export function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
