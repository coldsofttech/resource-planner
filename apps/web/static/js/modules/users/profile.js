"use strict";

import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";
import { esc } from "../../components/utils.js";

let profileData = null;

function formatDateTime(iso) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function setFieldValue(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.setAttribute("value", value ?? "");
  // After setAttribute triggers a re-render, the live input value is read as ""
  // by the _value getter (nullish-coalescing ignores empty strings). Directly
  // setting the input value here ensures the field visually reflects the data.
  const input = el.querySelector(".rp-input");
  if (input) input.value = value ?? "";
}

function setViewField(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = value || "—";
}

async function loadProfile() {
  try {
    const { href, method } = API_URLS.users.me();
    const resp = await apiFetch(href, { method });
    profileData = resp?.data ?? null;
    if (profileData) populateAll(profileData);
  } catch {
    toast({
      type: "error",
      title: "Could not load profile",
      message: "Refresh the page to retry.",
    });
  }
}

function populateAll(data) {
  // Avatar
  const avatarEl = document.getElementById("rp-profile-avatar");
  if (avatarEl) {
    avatarEl.setAttribute("seed", data.email || "");
    if (data.avatar_url) avatarEl.setAttribute("avatar-url", data.avatar_url);
    if (data.is_sso) {
      avatarEl.setAttribute("is-sso", "");
      if (data.sso_provider_name) avatarEl.setAttribute("sso-name", data.sso_provider_name);
    }
  }

  // Header name/email
  const displayNameEl = document.getElementById("rp-profile-display-name");
  if (displayNameEl)
    displayNameEl.textContent =
      data.display_name ||
      [data.first_name, data.last_name].filter(Boolean).join(" ") ||
      data.email;
  const emailEl = document.getElementById("rp-profile-email");
  if (emailEl) emailEl.textContent = data.email;

  // SSO badge in page title
  const badge = document.getElementById("rp-profile-sso-badge");
  if (badge) {
    if (data.is_sso && data.sso_provider_name) {
      badge.textContent = `SSO · ${data.sso_provider_name}`;
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  }

  // Account info
  setViewField("rp-profile-last-login", formatDateTime(data.last_login));
  setViewField(
    "rp-profile-pw-changed",
    data.is_sso ? "Managed by SSO" : formatDateTime(data.password_last_changed),
  );

  // Groups
  const groupsEl = document.getElementById("rp-profile-groups");
  if (groupsEl) {
    if (data.groups?.length) {
      groupsEl.innerHTML = data.groups
        .map(
          (g) =>
            `<span class="rp-badge" title="${esc(g.description || g.name)}">${esc(g.name)}</span>`,
        )
        .join("");
    } else {
      groupsEl.innerHTML = '<span class="rp-text-muted small">No groups assigned.</span>';
    }
  }

  // More info
  setViewField("rp-profile-location", data.location?.label || "—");
  setViewField("rp-profile-emp-type", data.employment_type?.label || "—");
  setViewField("rp-profile-role", data.role?.label || "—");

  // Account details form
  setFieldValue("rp-profile-first-name", data.first_name);
  setFieldValue("rp-profile-last-name", data.last_name);
  setFieldValue("rp-profile-display-name-field", data.display_name);
  setFieldValue("rp-profile-email-field", data.email);

  // Preferences form — timezone
  const tzField = document.getElementById("rp-profile-timezone");
  if (tzField && data.timezone) tzField.value = data.timezone;

  // Preferences form — skills
  const skillsField = document.getElementById("rp-profile-skills");
  if (skillsField && data.skills?.length) {
    const codes = data.skills.map((s) => s.code);
    skillsField.setAttribute("value", JSON.stringify(codes));
  }

  // Security section — show only for classic / superuser accounts
  const secPanel = document.getElementById("rp-profile-security-panel");
  if (secPanel) secPanel.hidden = !data.is_classic;
}

function initSaveDetails() {
  const btn = document.getElementById("rp-profile-save-details-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const firstField = document.getElementById("rp-profile-first-name");
    const lastField = document.getElementById("rp-profile-last-name");
    const displayField = document.getElementById("rp-profile-display-name-field");

    firstField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    lastField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    const hasError = document.querySelector(
      "#rp-profile-first-name [data-rp-error]:not([hidden]), #rp-profile-last-name [data-rp-error]:not([hidden])",
    );
    if (hasError) return;

    const payload = {
      first_name: firstField?.value || "",
      last_name: lastField?.value || "",
      display_name: displayField?.value || "",
    };

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Saving…");

    try {
      const { href, method } = API_URLS.users.updateProfile();
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(btn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      setTimeout(() => restoreButton(btn, snap), 2000);
      toast({
        type: "success",
        title: "Profile updated",
        message: "Your details have been saved.",
      });

      // Refresh local header display and top-bar user-profile component
      const displayName =
        payload.display_name || [payload.first_name, payload.last_name].filter(Boolean).join(" ");
      const displayNameEl = document.getElementById("rp-profile-display-name");
      if (displayNameEl) displayNameEl.textContent = displayName;
      _refreshTopBarProfile();
    } catch (err) {
      restoreButton(btn, snap);
      toast({
        type: "error",
        title: "Save failed",
        message: err?.data?.message || "Could not save your details.",
      });
    }
  });
}

function initSavePreferences() {
  const btn = document.getElementById("rp-profile-save-prefs-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const skillsField = document.getElementById("rp-profile-skills");
    const tzField = document.getElementById("rp-profile-timezone");

    // Use the .values getter (returns the internal chip array) for reliable skill reading.
    const skills = (skillsField?.values || []).map((s) => s.value);

    const timezone = tzField?.value || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";

    const payload = { skills, timezone };

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Saving…");

    try {
      const { href, method } = API_URLS.users.updateProfile();
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(btn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      setTimeout(() => restoreButton(btn, snap), 2000);
      toast({
        type: "success",
        title: "Preferences saved",
        message: "Your preferences have been updated.",
      });
      _refreshTopBarProfile();
    } catch (err) {
      restoreButton(btn, snap);
      toast({
        type: "error",
        title: "Save failed",
        message: err?.data?.message || "Could not save preferences.",
      });
    }
  });
}

function initChangePassword() {
  const btn = document.getElementById("rp-profile-change-pw-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const currentField = document.getElementById("rp-profile-current-pw");
    const newField = document.getElementById("rp-profile-new-pw");
    const confirmField = document.getElementById("rp-profile-confirm-pw");

    [currentField, newField, confirmField].forEach((f) =>
      f?.dispatchEvent(new Event("rp:validate", { bubbles: false })),
    );

    const hasError = document.querySelector(
      "#rp-profile-current-pw [data-rp-error]:not([hidden]), " +
        "#rp-profile-new-pw [data-rp-error]:not([hidden]), " +
        "#rp-profile-confirm-pw [data-rp-error]:not([hidden])",
    );
    if (hasError) return;

    const newPw = newField?.value || "";
    const confirmPw = confirmField?.value || "";
    if (newPw !== confirmPw) {
      toast({
        type: "error",
        title: "Passwords do not match",
        message: "Please make sure both password fields match.",
      });
      return;
    }

    const payload = {
      current_password: currentField?.value || "",
      new_password: newPw,
      confirm_password: confirmPw,
    };

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Updating…");

    try {
      const { href, method } = API_URLS.users.changePassword();
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(btn, snap, { label: "Updated", suffixIcon: "bi-check-circle-fill" });
      toast({
        type: "success",
        title: "Password updated",
        message: "Your password has been changed successfully.",
      });
      [currentField, newField, confirmField].forEach((f) => {
        if (f) f.value = "";
      });
    } catch (err) {
      restoreButton(btn, snap);
      toast({
        type: "error",
        title: "Failed",
        message: err?.data?.message || "Could not update password.",
      });
    }
  });
}

function _refreshTopBarProfile(e) {
  const topBar = document.querySelector("user-profile");
  if (!topBar) return;
  const bustedUrl = e?.detail?.avatarUrl;
  if (bustedUrl) {
    topBar.refresh(bustedUrl);
  } else {
    topBar._data = null;
    topBar._loadData();
  }
}

function initAvatarChange() {
  const avatarEl = document.getElementById("rp-profile-avatar");
  if (!avatarEl) return;

  avatarEl.addEventListener("rp:avatar:changed", _refreshTopBarProfile);
}

document.addEventListener("DOMContentLoaded", () => {
  initSaveDetails();
  initSavePreferences();
  initChangePassword();
  initAvatarChange();
  loadProfile();
});
