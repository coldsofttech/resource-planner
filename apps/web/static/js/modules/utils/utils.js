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
  const { skipAuth401Redirect = false, ...rest } = options;
  const defaults = {
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
  };
  const config = {
    ...defaults,
    ...rest,
    headers: Object.fromEntries(
      Object.entries({ ...defaults.headers, ...(rest.headers || {}) }).filter(
        ([, v]) => v !== undefined,
      ),
    ),
  };
  const res = await fetch(url, config);

  if (!res.ok) {
    if (res.status === 401 && !skipAuth401Redirect) {
      window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
      return;
    }

    const body = await res.json().catch(() => ({}));
    throw { status: res.status, data: body };
  }

  if (res.status === 204) return null;

  return res.json();
}

/**
 * Format an ISO date string ("YYYY-MM-DD") or ISO datetime string as a
 * localised date. Date-only strings are parsed as local midnight to avoid
 * timezone-driven day shifts.
 */
export function formatDate(iso) {
  if (!iso) return "—";
  const d = iso.includes("T") ? new Date(iso) : new Date(iso + "T00:00:00");
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

/**
 * Format an ISO datetime string as a localised date + time (medium date, short time).
 */
export function formatDateTime(iso) {
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

/**
 * Format the updated_at / updated_by fields into a drawer footer meta string.
 * Expects a row object with `updated_at` (ISO datetime) and optional
 * `updated_by.email`.
 */
export function formatMeta(row) {
  if (!row.updated_at) return "";
  const by = row.updated_by?.email ?? "—";
  return `Updated ${formatDate(row.updated_at)} · ${by}`;
}
