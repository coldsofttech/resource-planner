"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatCurrency,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { statusModal } from "../utils/modal.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

function formatNum(val) {
  const n = parseFloat(val);
  if (isNaN(n)) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDateTime(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusBadgeEl(status) {
  const span = document.createElement("span");
  if (status === "sent") {
    span.className = "rp-badge rp-badge-soft rp-badge-success";
    span.textContent = "Sent";
  } else if (status === "error") {
    span.className = "rp-badge rp-badge-soft rp-badge-danger";
    span.textContent = "Error";
  } else {
    span.className = "rp-badge rp-badge-soft";
    span.textContent = "Pending";
  }
  return span;
}

function buildEmailView(group) {
  const emailView = document.createElement("email-view");

  // To recipients
  const toItems = document.createElement("email-to-items");
  (group.to || []).forEach((c) => {
    const item = document.createElement("email-to-item");
    item.setAttribute("value", c.email || c.name || "");
    toItems.appendChild(item);
  });
  emailView.appendChild(toItems);

  // Cc recipients (only if present)
  if (group.cc && group.cc.length > 0) {
    const ccItems = document.createElement("email-cc-items");
    group.cc.forEach((c) => {
      const item = document.createElement("email-cc-item");
      item.setAttribute("value", c.email || c.name || "");
      ccItems.appendChild(item);
    });
    emailView.appendChild(ccItems);
  }

  // Subject
  const subject = document.createElement("email-subject");
  subject.textContent = group.subject || "(No subject)";
  emailView.appendChild(subject);

  // Body — application-generated HTML, safe for innerHTML
  const body = document.createElement("email-body");
  if (group.body) {
    body.innerHTML = group.body;
  } else {
    const placeholder = document.createElement("p");
    placeholder.style.color = "var(--rp-text-muted)";
    placeholder.textContent = "Email body will be generated when emails are triggered.";
    body.appendChild(placeholder);
  }
  emailView.appendChild(body);

  return emailView;
}

function buildGroupPanel(group, sprintCode, reviewType) {
  const panel = document.createElement("accordion-panel");
  panel.setAttribute("group", "rp-email-review-groups");
  panel.dataset.groupCode = group.group_code;

  // ── Header ────────────────────────────────────────────────────────────────
  const header = document.createElement("accordion-header");

  const wrapper = document.createElement("div");
  wrapper.className = "d-flex align-items-center justify-content-between w-100 pe-2";

  const left = document.createElement("div");
  left.className = "d-flex align-items-center gap-2";

  const nameEl = document.createElement("span");
  nameEl.className = "fw-medium";
  nameEl.textContent = group.group_name;

  left.appendChild(nameEl);

  const right = document.createElement("div");
  right.className = "d-flex align-items-center gap-3 text-muted";
  right.style.fontSize = "var(--rp-fs-13)";

  const daysEl = document.createElement("span");
  daysEl.title = "Total days";
  daysEl.textContent = `${formatNum(group.total_days)} days`;

  const costEl = document.createElement("span");
  costEl.title = "Total cost";
  costEl.textContent = formatCurrency(parseFloat(group.total_cost) || 0);

  const badgeWrapper = document.createElement("span");
  badgeWrapper.id = `rp-email-status-${esc(group.group_code)}`;
  badgeWrapper.appendChild(statusBadgeEl(group.status || "pending"));

  right.appendChild(daysEl);
  right.appendChild(costEl);
  right.appendChild(badgeWrapper);

  wrapper.appendChild(left);
  wrapper.appendChild(right);
  header.appendChild(wrapper);

  // ── Body ──────────────────────────────────────────────────────────────────
  const body = document.createElement("accordion-body");

  const bodyWrapper = document.createElement("div");
  bodyWrapper.className = "p-3";

  // Last sent timestamp row (shown only if sent)
  const metaRow = document.createElement("div");
  metaRow.className = "d-flex align-items-center justify-content-between mb-3";
  metaRow.id = `rp-email-meta-${esc(group.group_code)}`;

  const sentInfo = document.createElement("span");
  sentInfo.style.color = "var(--rp-text-muted)";
  sentInfo.style.fontSize = "var(--rp-fs-12)";
  const sentAt = formatDateTime(group.sent_at);
  sentInfo.textContent = sentAt ? `Last sent: ${sentAt}` : "";

  const resendBtn = document.createElement("primary-button");
  resendBtn.setAttribute("label", "Resend");
  resendBtn.setAttribute("prefix-icon", "bi-send");
  resendBtn.dataset.emailCode = group.email_code || "";
  resendBtn.dataset.groupCode = group.group_code;

  metaRow.appendChild(sentInfo);
  metaRow.appendChild(resendBtn);
  bodyWrapper.appendChild(metaRow);
  bodyWrapper.appendChild(buildEmailView(group));

  body.appendChild(bodyWrapper);

  panel.appendChild(header);
  panel.appendChild(body);
  return panel;
}

function updateGroupStatus(groupCode, status, sentAt) {
  const badgeWrapper = document.getElementById(`rp-email-status-${groupCode}`);
  if (badgeWrapper) {
    badgeWrapper.innerHTML = "";
    badgeWrapper.appendChild(statusBadgeEl(status));
  }
  const metaRow = document.getElementById(`rp-email-meta-${groupCode}`);
  if (metaRow) {
    const sentInfo = metaRow.querySelector("span");
    if (sentInfo) {
      const formatted = formatDateTime(sentAt);
      sentInfo.textContent = formatted ? `Last sent: ${formatted}` : "";
    }
  }
}

function renderGroups(groups, container, sprintCode, reviewType) {
  container.innerHTML = "";

  if (!groups.length) {
    container.innerHTML = `
      <div class="rp-empty-state">
        <span class="rp-empty-icon bi bi-envelope-slash"></span>
        <p class="rp-empty-title">No recharge groups found.</p>
        <p class="rp-empty-desc">No project groups with recharge records were found for this sprint and type.</p>
      </div>`;
    return;
  }

  groups.forEach((group, i) => {
    const panel = buildGroupPanel(group, sprintCode, reviewType);
    if (i > 0) panel.classList.add("mt-2");
    container.appendChild(panel);
  });
}

function initResendButtons(container, sprintCode, reviewType) {
  container.addEventListener("click", async (e) => {
    const btn = e.target.closest("primary-button[data-email-code]");
    if (!btn) return;

    const emailCode = btn.dataset.emailCode;
    const groupCode = btn.dataset.groupCode;

    if (!emailCode) {
      toast({
        type: "warning",
        title: "Not ready",
        message: "Email has not been triggered yet. Use Trigger All first.",
      });
      return;
    }

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Sending…");

    try {
      const { href, method } = API_URLS.rechargeEmails.resend(emailCode);
      await apiFetch(href, { method });
      restoreButton(btn, snap);
      updateGroupStatus(groupCode, "sent", new Date().toISOString());
      toast({
        type: "success",
        title: "Email resent",
        message: "The email was resent successfully.",
      });
    } catch (err) {
      restoreButton(btn, snap);
      updateGroupStatus(groupCode, "error", null);
      const msg = err?.data?.error?.message ?? "Failed to resend email.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initTriggerAllButton(sprintCode, reviewType) {
  const btn = document.getElementById("rp-recharge-email-trigger-btn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    statusModal.open({
      iconType: "warning",
      title: "Trigger All Emails",
      body: `This will send recharge ${reviewType} emails to all project group contacts for sprint <strong>${esc(sprintCode)}</strong>. This action cannot be undone.`,
      closeable: true,
      dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
      primaryBtn: {
        label: "Send All Emails",
        icon: "bi-send",
        onClick: () => triggerAllEmails(btn, sprintCode, reviewType),
      },
    });
  });
}

async function triggerAllEmails(triggerBtn, sprintCode, reviewType) {
  statusModal.update({
    iconType: "info",
    title: "Sending emails…",
    body: "Please wait while emails are being dispatched.",
    closeable: false,
    dismissBtn: null,
    primaryBtn: null,
  });

  try {
    const { href, method } = API_URLS.rechargeEmails.triggerAll();
    const res = await apiFetch(href, {
      method,
      body: JSON.stringify({ sprint: sprintCode, type: reviewType }),
    });
    const result = res?.data ?? res;

    statusModal.update({
      iconType: result.errors > 0 ? "warning" : "success",
      title: result.errors > 0 ? "Some emails failed" : "Emails sent",
      body: `Sent: ${result.sent} · Errors: ${result.errors} · Total: ${result.total}`,
      closeable: true,
      primaryBtn: { label: "Close", onClick: () => statusModal.close() },
    });

    // Reload the page data to reflect updated statuses
    await loadReviewGroups(sprintCode, reviewType);
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to trigger emails.";
    statusModal.update({
      iconType: "error",
      title: "Error",
      body: msg,
      closeable: true,
      primaryBtn: { label: "Close", onClick: () => statusModal.close() },
    });
  }
}

async function loadReviewGroups(sprintCode, reviewType) {
  const container = document.getElementById("rp-recharge-email-review-container");
  if (!container) return;

  try {
    const { href, method } = API_URLS.rechargeEmails.list(sprintCode, reviewType);
    const res = await apiFetch(href, { method });
    const groups = res?.data?.results ?? res?.results ?? [];
    renderGroups(groups, container, sprintCode, reviewType);
    initResendButtons(container, sprintCode, reviewType);
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to load email review data.";
    toast({ type: "error", title: "Error", message: msg });
    container.innerHTML = `
      <div class="rp-empty-state">
        <span class="rp-empty-icon bi bi-exclamation-triangle text-danger"></span>
        <p class="rp-empty-title">Failed to load email review data.</p>
      </div>`;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const root = document.getElementById("rp-recharge-email-review-root");
  if (!root) return;

  const sprintCode = root.dataset.sprint || "";
  const reviewType = root.dataset.type || "forecast";

  setBreadcrumbs([
    { label: "Finance" },
    { label: "Recharges", href: UI_URLS.recharges.index() },
    { label: sprintCode },
    { label: `${reviewType.charAt(0).toUpperCase() + reviewType.slice(1)} Email Review` },
  ]);

  initTriggerAllButton(sprintCode, reviewType);
  await loadReviewGroups(sprintCode, reviewType);
});
