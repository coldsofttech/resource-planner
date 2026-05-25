/**
 * Capture an rp-button element's current label/icon/disabled state so it can
 * be restored after an async operation completes (success or failure).
 */
export function snapshotButton(btn) {
  return {
    label: btn.getAttribute("label"),
    prefixIcon: btn.getAttribute("prefix-icon"),
    suffixIcon: btn.getAttribute("suffix-icon"),
    disabled: btn.hasAttribute("disabled"),
  };
}

/**
 * Disable an rp-button and switch it to the loading state.
 * Clears both icon slots, sets the provided label, and shows a hourglass icon.
 */
export function setBusyButton(btn, label = "Loading…") {
  btn.setAttribute("disabled", "");
  btn.removeAttribute("prefix-icon");
  btn.removeAttribute("suffix-icon");
  btn.setAttribute("label", label);
  btn.setAttribute("suffix-icon", "bi-hourglass-split");
}

/**
 * Restore an rp-button to a previously captured snapshot.
 * Optional overrides are merged on top of the snapshot before applying, so
 * callers can express a transient success/warning state without a separate
 * attribute-manipulation block:
 *
 *   restoreButton(btn, snap, { label: "Connected", prefixIcon: null, suffixIcon: "bi-check-circle-fill" })
 *
 * Non-null values set the attribute; null values remove it.
 */
export function restoreButton(btn, snapshot, overrides = {}) {
  const state = { ...snapshot, ...overrides };

  if (state.disabled) {
    btn.setAttribute("disabled", "");
  } else {
    btn.removeAttribute("disabled");
  }

  if (state.label !== null) btn.setAttribute("label", state.label);
  else btn.removeAttribute("label");

  if (state.prefixIcon !== null) btn.setAttribute("prefix-icon", state.prefixIcon);
  else btn.removeAttribute("prefix-icon");

  if (state.suffixIcon !== null) btn.setAttribute("suffix-icon", state.suffixIcon);
  else btn.removeAttribute("suffix-icon");
}

/**
 * Update an anchor element's href and visible text together.
 * Falls back to href="#" and the fallback text when url is empty/falsy.
 */
export function setLink(el, url, fallbackText = "—") {
  if (!el) return;
  el.href = url || "#";
  el.textContent = url || fallbackText;
}

export function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');

  if (meta) return meta.getAttribute("content");

  const cookie = document.cookie.split(";").find((c) => c.trim().startsWith("csrftoken="));
  return cookie ? cookie.split("=")[1].trim() : "";
}

export async function apiFetch(url, options = {}) {
  const defaults = {
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
  };
  const config = {
    ...defaults,
    ...options,
    headers: {
      ...defaults.headers,
      ...(options.headers || {}),
    },
  };
  const res = await fetch(url, config);

  if (!res.ok) {
    if (res.status === 401) {
      window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
      return;
    }

    const body = await res.json().catch(() => ({}));

    throw { status: res.status, data: body };
  }

  if (res.status === 204) return null;

  return res.json();
}
