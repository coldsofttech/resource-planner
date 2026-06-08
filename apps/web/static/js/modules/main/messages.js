import { toast } from "../utils/toast.js";

const TYPE_MAP = {
  error: "error",
  warning: "warning",
  success: "success",
  info: "info",
  debug: "info",
};

/**
 * Reads the #django-messages JSON script tag (if present) and shows each
 * message as a toast. The tag is written by base.html when Django's
 * messages framework has pending messages.
 */
export function applyDjangoMessages() {
  const el = document.getElementById("django-messages");
  if (!el) return;
  try {
    const msgs = JSON.parse(el.textContent);
    msgs.forEach(({ type, message }) => {
      toast({ type: TYPE_MAP[type] ?? "info", message, duration: 6000 });
    });
  } catch {}
}

document.addEventListener("DOMContentLoaded", applyDjangoMessages);
