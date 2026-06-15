"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { statusModal } from "../utils/modal.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

const pathParts = window.location.pathname.split("/").filter(Boolean);
const userCode =
  pathParts[0] === "users" && pathParts[1] && pathParts[1].startsWith("USER-")
    ? pathParts[1]
    : null;

let currentUser = null;

async function loadUserDetails() {
  try {
    const { href, method } = API_URLS.users.adminDetail(userCode);
    const resp = await apiFetch(href, { method });
    const user = resp?.data ?? null;
    if (!user) return null;

    currentUser = user;

    const displayName =
      user.display_name || `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email;

    const titleEl = document.getElementById("rp-user-detail-title");
    if (titleEl) titleEl.textContent = displayName;

    setBreadcrumbs([
      { label: "Administration" },
      { label: "Users", href: UI_URLS.users.list() },
      { label: displayName },
    ]);

    const avatarEl = document.getElementById("rp-user-detail-avatar");
    if (avatarEl) {
      avatarEl.setAttribute("name", displayName);
      avatarEl.setAttribute("avatar-url", `/api/v1/users/${userCode}/avatar/`);
    }

    const setConditional = (id, val) => {
      const el = document.getElementById(id);
      if (!el) return;
      const hasVal = val != null && String(val).trim() !== "";
      el.hidden = !hasVal;
      if (hasVal) el.value = val;
    };

    setConditional("rp-user-detail-first-name", user.first_name);
    setConditional("rp-user-detail-last-name", user.last_name);
    setConditional("rp-user-detail-display-name", user.display_name);

    const emailEl = document.getElementById("rp-user-detail-email");
    if (emailEl) emailEl.value = user.email || "—";

    const groupsEl = document.getElementById("rp-user-detail-groups");
    if (groupsEl) {
      const names = (user.groups ?? []).map((g) => g.name);
      groupsEl.hidden = !names.length;
      if (names.length) groupsEl.value = names;
    }

    setConditional("rp-user-detail-location", user.location?.label ?? null);
    setConditional("rp-user-detail-role", user.role?.label ?? null);
    setConditional("rp-user-detail-emp-type", user.employment_type?.label ?? null);

    const lastLoginEl = document.getElementById("rp-user-detail-last-login");
    if (lastLoginEl)
      lastLoginEl.value = user.last_login ? formatDate(user.last_login) : "Never logged in";

    const createdEl = document.getElementById("rp-user-detail-created-at");
    if (createdEl) createdEl.value = user.created_at ? formatDate(user.created_at) : "—";

    setConditional("rp-user-detail-created-by", user.created_by?.email ?? null);

    document.getElementById("rp-user-detail-permissions")?.loadEffective(userCode);

    const resetBtn = document.getElementById("rp-user-detail-reset-password-btn");
    if (resetBtn) {
      const canReset = !user.is_superuser && user.auth_type === "classic";
      if (canReset) resetBtn.removeAttribute("hidden");
      else resetBtn.setAttribute("hidden", "");
    }

    return user;
  } catch {
    toast({ type: "error", title: "Could not load user", message: "Refresh the page to retry." });
    return null;
  }
}

function initAssignPermissions() {
  const btn = document.getElementById("rp-user-detail-assign-permissions-btn");
  const drawer = document.getElementById("rp-user-detail-assign-permissions-drawer");
  const panel = document.getElementById("rp-user-detail-permissions-panel");
  if (!btn || !drawer || !panel) return;

  btn.removeAttribute("hidden");

  btn.addEventListener("click", async () => {
    drawer.show();
    await panel.load(userCode);
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");
    try {
      await panel.save();
      restoreButton(submitBtn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      document.getElementById("rp-user-detail-permissions")?.loadEffective(userCode);
      toast({
        type: "success",
        title: "Permissions updated",
        message: "User permissions have been saved.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      toast({
        type: "error",
        title: "Error",
        message: err?.message ?? "Failed to save permissions. Please try again.",
      });
    }
  });
}

function initResetPassword() {
  const btn = document.getElementById("rp-user-detail-reset-password-btn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    if (!currentUser) return;
    const displayName = currentUser.display_name || currentUser.email;
    statusModal.open({
      iconType: "warning",
      title: "Send password reset link?",
      body: `A password reset link will be emailed to ${esc(displayName)}. The link will expire based on the configured timeout.`,
      primaryBtn: {
        label: "Send reset link",
        icon: "bi-key",
        onClick: async () => {
          statusModal.update({
            iconType: "info",
            title: "Sending…",
            body: "Sending the password reset email.",
          });
          const { href, method } = API_URLS.users.adminResetPassword(userCode);
          try {
            await apiFetch(href, { method });
            statusModal.close();
            toast({
              type: "success",
              title: "Reset link sent",
              message: `A password reset link has been emailed to ${esc(currentUser.email)}.`,
            });
          } catch (err) {
            statusModal.close();
            const msg = err?.data?.error?.message ?? "Failed to send reset link. Please try again.";
            toast({ type: "error", title: "Error", message: msg });
          }
        },
      },
      dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
    });
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!userCode) return;

  await loadUserDetails();
  if (!currentUser?.is_superuser) {
    initAssignPermissions();
  }
  initResetPassword();
});
