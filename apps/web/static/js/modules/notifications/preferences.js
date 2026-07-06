"use strict";

import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

const CATEGORY_DESCRIPTION = {
  general: "Everyday updates and confirmations.",
  mention: "When someone mentions you in a comment.",
  todo: "Assigned tasks and reminders.",
};

function buildRow({ category, category_label, is_enabled, is_suppressible }) {
  const row = document.createElement("div");
  row.className = "rp-notif-pref-row";

  const info = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = category_label;
  info.appendChild(title);

  const desc = document.createElement("div");
  desc.className = "rp-notif-pref-desc";
  desc.textContent = CATEGORY_DESCRIPTION[category] ?? "";
  info.appendChild(desc);

  row.appendChild(info);

  const toggle = document.createElement("toggle-field");
  toggle.dataset.category = category;
  if (is_enabled) toggle.setAttribute("checked", "");
  if (!is_suppressible) {
    toggle.setAttribute("disabled", "");
    toggle.setAttribute("label", "Always on");
  }
  row.appendChild(toggle);

  if (is_suppressible) {
    toggle.addEventListener("change", async () => {
      const enabled = toggle.checked;
      try {
        const { href, method } = API_URLS.notifications.preferences.update(category);
        await apiFetch(href, { method, body: JSON.stringify({ is_enabled: enabled }) });
        toast({
          type: "success",
          title: "Preference updated",
          message: `${category_label} notifications ${enabled ? "enabled" : "disabled"}.`,
        });
      } catch {
        toggle.checked = !enabled;
        toast({
          type: "error",
          title: "Error",
          message: "Failed to update preference.",
        });
      }
    });
  }

  return row;
}

async function initPreferences() {
  const list = document.getElementById("rp-notification-prefs-list");
  if (!list) return;

  try {
    const { href, method } = API_URLS.notifications.preferences.list();
    const resp = await apiFetch(href, { method });
    const prefs = resp?.data ?? [];
    const frag = document.createDocumentFragment();
    prefs.forEach((pref) => frag.appendChild(buildRow(pref)));
    list.replaceChildren(frag);
  } catch {
    list.replaceChildren();
    const error = document.createElement("div");
    error.className = "rp-notif-empty";
    error.textContent = "Couldn't load notification preferences.";
    list.appendChild(error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initPreferences();
});
