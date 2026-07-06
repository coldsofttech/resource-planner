import { apiFetch } from "./utils.js";
import { API_URLS } from "../main/urls.js";

const TYPE_CLASS = { info: "info", success: "success", warning: "warning", error: "danger" };
const TYPE_ICON = {
  info: "bi-info-circle-fill",
  success: "bi-check-circle-fill",
  warning: "bi-exclamation-triangle-fill",
  error: "bi-x-circle-fill",
};

// Maps toast type -> notifications backend notification_type. Errors persist as
// "error" so the notifications panel/list can render the same danger styling.
const NOTIFICATION_TYPE = { info: "info", success: "success", warning: "warning", error: "error" };

async function persistNotification({ type, title, message, category, link }) {
  try {
    const { href, method } = API_URLS.notifications.create();
    await apiFetch(href, {
      method,
      body: JSON.stringify({
        title: title || message || "Notification",
        body: message || "",
        category,
        notification_type: NOTIFICATION_TYPE[type] ?? "info",
        link,
      }),
    });
    window.dispatchEvent(new CustomEvent("rp:notification-created"));
  } catch {
    // Persistence is best-effort — the toast itself already informed the user.
  }
}

function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getOrCreateHost(position) {
  let host = document.querySelector(`.rp-toast-host.${position}`);
  if (!host) {
    host = document.createElement("div");
    host.className = `rp-toast-host ${position}`;
    document.body.appendChild(host);
  }
  return host;
}

function dismiss(toast, host) {
  if (!toast.isConnected) return;
  toast.classList.add("is-leaving");
  setTimeout(() => {
    toast.remove();
    if (host.children.length === 0) host.remove();
  }, 200);
}

export function toast({
  type = "info",
  title = "",
  message = "",
  actions = [],
  duration = 5000,
  persistent = false,
  position = "top-right",
  mini = false,
  persist = false,
  category = "general",
  link = "",
} = {}) {
  const host = getOrCreateHost(position);
  const typeClass = TYPE_CLASS[type] ?? "info";
  const icon = TYPE_ICON[type] ?? "bi-info-circle-fill";

  const actionsHTML = actions.length
    ? `<div class="rp-toast-actions">${actions
        .map(
          (a, i) =>
            `<button class="rp-btn rp-btn-muted" data-action="${i}">${esc(a.label)}</button>`,
        )
        .join("")}</div>`
    : "";

  const messageHTML = message ? `<div class="rp-toast-sub">${esc(message)}</div>` : "";

  const toast = document.createElement("div");
  toast.className = ["rp-toast", typeClass, mini && "mini", persistent && "persistent"]
    .filter(Boolean)
    .join(" ");

  if (!persistent && duration !== 5000) {
    toast.style.setProperty("--rp-toast-duration", `${duration / 1000}s`);
  }

  toast.innerHTML = `
    <div class="rp-toast-icon"><i class="bi ${icon}"></i></div>
    <div class="rp-toast-body">
      <strong>${esc(title)}</strong>
      ${messageHTML}
      ${actionsHTML}
    </div>
    <button class="rp-toast-close" aria-label="Dismiss"><i class="bi bi-x"></i></button>
  `;

  toast.querySelector(".rp-toast-close").addEventListener("click", () => dismiss(toast, host));

  actions.forEach((action, i) => {
    const btn = toast.querySelector(`[data-action="${i}"]`);
    if (btn && typeof action.onClick === "function") {
      btn.addEventListener("click", () => action.onClick());
    }
  });

  host.appendChild(toast);

  if (!persistent) {
    setTimeout(() => dismiss(toast, host), duration);
  }

  if (persist) {
    persistNotification({ type, title, message, category, link });
  }

  return { dismiss: () => dismiss(toast, host) };
}
