"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// /sprints/SPRINT-x/forecast  →  parts[1] = SPRINT-x
const pathParts = window.location.pathname.split("/").filter(Boolean);
const sprintCode = pathParts[1] || null;

// Team code currently pending an upload action
let pendingTeamCode = null;

function formatDateTime(iso) {
  if (!iso) return "—";
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

function statusBadgeHtml(status) {
  if (status === "confirmed")
    return `<span class="rp-badge rp-badge-soft rp-badge-success">Confirmed</span>`;
  if (status === "superseded") return `<span class="rp-badge rp-badge-soft">Superseded</span>`;
  if (status === "active")
    return `<span class="rp-badge rp-badge-soft rp-badge-info">Active</span>`;
  return "";
}

window.renderForecastImportRow = function renderForecastImportRow(row) {
  const version = `v${row.version_number}`;
  const fileName = esc(row.file_name || "—");
  const importedAt = formatDateTime(row.created_at);
  const importedBy = esc(row.created_by || "—");

  const badge =
    row.status === "confirmed"
      ? `<span class="rp-badge rp-badge-soft rp-badge-success">Confirmed</span>`
      : row.status === "superseded"
        ? `<span class="rp-badge rp-badge-soft">Superseded</span>`
        : `<span class="rp-badge rp-badge-soft rp-badge-info">Active</span>`;

  return `
    <td><span class="rp-mono">${esc(version)}</span></td>
    <td>${fileName}</td>
    <td>${badge}</td>
    <td>${importedAt}</td>
    <td>${importedBy}</td>
  `;
};

function buildImportTable(teamCode) {
  const table = document.createElement("data-table");
  table.id = `rp-forecast-imports-table-${teamCode}`;
  table.setAttribute("row-template", "renderForecastImportRow");
  table.setAttribute("empty-message", "No forecast data imported yet for this team.");
  table.setAttribute("url", API_URLS.sprints.forecastImports(sprintCode, teamCode).href);
  table.style.cursor = "pointer";

  const cols = document.createElement("table-columns");

  const colDefs = [
    { label: "Version", key: "version_number" },
    { label: "File Name", key: "file_name" },
    { label: "Status", key: "status" },
    { label: "Imported At", key: "created_at" },
    { label: "Imported By", key: "created_by" },
  ];

  colDefs.forEach(({ label, key }) => {
    const col = document.createElement("table-column");
    col.setAttribute("label", label);
    col.setAttribute("key", key);
    cols.appendChild(col);
  });

  table.appendChild(cols);
  return table;
}

function buildTeamAccordion(team) {
  const panel = document.createElement("accordion-panel");
  panel.setAttribute("group", "rp-forecast-teams");
  panel.dataset.teamCode = team.code;

  // ── Header ────────────────────────────────────────────────────────────────
  const header = document.createElement("accordion-header");

  const wrapper = document.createElement("div");
  wrapper.className = "d-flex align-items-center justify-content-between w-100 pe-2";

  // Left: avatar + name + status badge
  const left = document.createElement("div");
  left.className = "d-flex align-items-center gap-2";

  const avatar = document.createElement("identicon-field");
  avatar.setAttribute("name", team.name);
  avatar.setAttribute("variant", "monogram");
  avatar.setAttribute("size", "md");

  const nameEl = document.createElement("span");
  nameEl.className = "fw-medium";
  nameEl.textContent = team.name;

  // Placeholder badge — filled in after the latest import is fetched
  const badgePlaceholder = document.createElement("span");
  badgePlaceholder.id = `rp-forecast-team-status-${team.code}`;

  left.appendChild(avatar);
  left.appendChild(nameEl);
  left.appendChild(badgePlaceholder);

  // Right: <secondary-button> for upload
  const importBtn = document.createElement("secondary-button");
  importBtn.setAttribute("label", "Import");
  importBtn.setAttribute("prefix-icon", "bi-upload");
  importBtn.dataset.teamCode = team.code;

  wrapper.appendChild(left);
  wrapper.appendChild(importBtn);
  header.appendChild(wrapper);

  // ── Body ──────────────────────────────────────────────────────────────────
  const body = document.createElement("accordion-body");
  body.appendChild(buildImportTable(team.code));

  panel.appendChild(header);
  panel.appendChild(body);
  return panel;
}

async function refreshTeamStatusBadge(teamCode) {
  try {
    const { href, method } = API_URLS.sprints.forecastImports(sprintCode, teamCode);
    const resp = await apiFetch(`${href}?page_size=1`, { method });
    const latest = resp?.data?.results?.[0] ?? null;
    const badge = document.getElementById(`rp-forecast-team-status-${teamCode}`);
    if (badge) badge.innerHTML = latest ? statusBadgeHtml(latest.status) : "";
  } catch {
    // silently ignore — badge stays empty
  }
}

function renderTeams(teams) {
  const container = document.getElementById("rp-forecast-teams-container");
  if (!container) return;

  if (!teams.length) {
    container.innerHTML = `
      <div class="rp-empty-state">
        <span class="rp-empty-icon bi bi-people"></span>
        <p class="rp-empty-title">No active teams found.</p>
      </div>`;
    return;
  }

  container.innerHTML = "";
  teams.forEach((team, i) => {
    const panel = buildTeamAccordion(team);
    if (i > 0) panel.classList.add("mt-2");
    container.appendChild(panel);
    // Load the latest import status badge for each team in the background
    refreshTeamStatusBadge(team.code);
  });
}

function showClosedError(container) {
  container.innerHTML = `
    <div class="rp-empty-state">
      <span class="rp-empty-icon bi bi-lock-fill" style="color:var(--rp-badge-warning-text)"></span>
      <p class="rp-empty-title">Sprint is closed</p>
      <p class="rp-empty-desc">Forecast data cannot be imported for a closed sprint. Please contact your administrator.</p>
    </div>`;
}

async function loadSprintAndTeams() {
  const container = document.getElementById("rp-forecast-teams-container");
  if (!sprintCode || !container) return;

  try {
    const { href, method } = API_URLS.sprints.detail(sprintCode);
    const resp = await apiFetch(href, { method });
    const sprint = resp?.data ?? null;
    if (!sprint) return;

    const titleEl = document.getElementById("rp-forecast-title");
    if (titleEl) titleEl.textContent = `${sprint.name} — Forecast`;

    setBreadcrumbs([
      { label: "Project" },
      { label: "Planning" },
      { label: "Sprints", href: UI_URLS.sprints.list() },
      { label: sprint.name, href: UI_URLS.sprints.detail(sprintCode) },
      { label: "Forecast" },
    ]);

    if (sprint.is_closed) {
      showClosedError(container);
      return;
    }

    await loadTeams(container);
  } catch {
    container.innerHTML = `
      <div class="rp-empty-state">
        <span class="rp-empty-icon bi bi-exclamation-circle" style="color:var(--rp-danger)"></span>
        <p class="rp-empty-title">Failed to load sprint. Refresh the page to retry.</p>
      </div>`;
  }
}

async function loadTeams(container) {
  try {
    const { href, method } = API_URLS.teams.list();
    const resp = await apiFetch(href + "?is_active=true&page_size=100", {
      method,
    });
    const teams = resp?.data?.results ?? [];
    renderTeams(teams);
  } catch {
    container.innerHTML = `
      <div class="rp-empty-state">
        <span class="rp-empty-icon bi bi-exclamation-circle" style="color:var(--rp-danger)"></span>
        <p class="rp-empty-title">Failed to load teams. Refresh the page to retry.</p>
      </div>`;
  }
}

function initUpload() {
  const fileInput = document.getElementById("rp-forecast-file-input");
  if (!fileInput) return;

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file || !pendingTeamCode || !sprintCode) return;

    const teamCode = pendingTeamCode;

    // Reset so the same file can be re-selected if needed
    fileInput.value = "";

    const { href, method } = API_URLS.sprints.forecastUpload(sprintCode, teamCode);
    const formData = new FormData();
    formData.append("file", file);

    try {
      await apiFetch(href, {
        method,
        body: formData,
        headers: { "Content-Type": undefined }, // let browser set multipart boundary
      });
      toast({
        type: "success",
        title: "Forecast uploaded",
        message: "The file has been recorded successfully.",
      });
      const teamTable = document.getElementById(`rp-forecast-imports-table-${teamCode}`);
      teamTable?.refresh();
      refreshTeamStatusBadge(teamCode);
    } catch (err) {
      const msg =
        err?.data?.error?.message ?? err?.data?.message ?? "Upload failed. Please try again.";
      toast({ type: "error", title: "Upload failed", message: msg });
    } finally {
      pendingTeamCode = null;
    }
  });
}

function initImportActions() {
  const container = document.getElementById("rp-forecast-teams-container");
  if (!container) return;

  container.addEventListener("click", (e) => {
    const btn = e.target.closest("secondary-button[data-team-code]");
    if (!btn) return;
    e.stopPropagation(); // prevent accordion toggle
    const teamCode = btn.dataset.teamCode;
    const fileInput = document.getElementById("rp-forecast-file-input");
    if (!fileInput) {
      toast({
        type: "error",
        title: "Permission denied",
        message: "You do not have permission to upload forecast data.",
      });
      return;
    }
    pendingTeamCode = teamCode;
    fileInput.click();
  });
}

function initDownloadTemplateButton() {
  const btn = document.getElementById("rp-forecast-template-btn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    if (!sprintCode) return;
    const { href } = API_URLS.sprints.forecastTemplate(sprintCode);
    window.location.href = href;
  });
}

function initImportRowNavigation() {
  const container = document.getElementById("rp-forecast-teams-container");
  if (!container) return;

  container.addEventListener("click", (e) => {
    if (e.target.closest("secondary-button")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const table = tr.closest("data-table");
    if (!table) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows?.[idx];
    if (!row?.code) return;
    window.location.href = UI_URLS.sprints.forecastImportDetail(sprintCode, row.code);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("rp-forecast-teams-container");
  if (!container) return;

  loadSprintAndTeams();
  initUpload();
  initImportActions();
  initImportRowNavigation();
  initDownloadTemplateButton();
});
