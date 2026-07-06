"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// /sprints/SPRINT-x/actuals  →  parts[1] = SPRINT-x
const pathParts = window.location.pathname.split("/").filter(Boolean);
const sprintCode = pathParts[1] || null;

// Team code currently pending an upload action
let pendingTeamCode = null;

// Tracks confirmed state per team to gate the Review Complete button
const teamConfirmedMap = new Map();

function updateReviewCompleteBtn() {
  const btn = document.getElementById("rp-actuals-review-complete-btn");
  if (!btn) return;
  const anyConfirmed = [...teamConfirmedMap.values()].some(Boolean);
  if (anyConfirmed) {
    btn.removeAttribute("disabled");
  } else {
    btn.setAttribute("disabled", "");
  }
}

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

window.renderActualsImportRow = function renderActualsImportRow(row) {
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
  table.id = `rp-actuals-imports-table-${teamCode}`;
  table.setAttribute("row-template", "renderActualsImportRow");
  table.setAttribute("empty-message", "No actuals data imported yet for this team.");
  table.setAttribute("url", API_URLS.sprints.actualsImports(sprintCode, teamCode).href);
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
  panel.setAttribute("group", "rp-actuals-teams");
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
  badgePlaceholder.id = `rp-actuals-team-status-${team.code}`;

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
    const { href, method } = API_URLS.sprints.actualsImports(sprintCode, teamCode);
    const resp = await apiFetch(`${href}?page_size=1`, { method });
    const latest = resp?.data?.results?.[0] ?? null;
    const badge = document.getElementById(`rp-actuals-team-status-${teamCode}`);
    if (badge) badge.innerHTML = latest ? statusBadgeHtml(latest.status) : "";
    teamConfirmedMap.set(teamCode, latest?.status === "confirmed");
    updateReviewCompleteBtn();
  } catch {
    // silently ignore — badge stays empty
  }
}

function renderTeams(teams) {
  const container = document.getElementById("rp-actuals-teams-container");
  if (!container) return;

  teamConfirmedMap.clear();

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
      <p class="rp-empty-desc">Actuals data cannot be imported for a closed sprint. Please contact your administrator.</p>
    </div>`;
}

async function loadSprintAndTeams() {
  const container = document.getElementById("rp-actuals-teams-container");
  if (!sprintCode || !container) return;

  try {
    const { href, method } = API_URLS.sprints.detail(sprintCode);
    const resp = await apiFetch(href, { method });
    const sprint = resp?.data ?? null;
    if (!sprint) return;

    const titleEl = document.getElementById("rp-actuals-title");
    if (titleEl) titleEl.textContent = `${sprint.name} — Actuals`;

    setBreadcrumbs([
      { label: "Project" },
      { label: "Planning" },
      { label: "Sprints", href: UI_URLS.sprints.list() },
      { label: sprint.name, href: UI_URLS.sprints.detail(sprintCode) },
      { label: "Actuals" },
    ]);

    const syncBtn = document.getElementById("rp-actuals-sync-btn");
    if (syncBtn) {
      if (sprint.actuals_review_complete) {
        syncBtn.removeAttribute("disabled");
      } else {
        syncBtn.setAttribute("disabled", "");
      }
    }

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
  const fileInput = document.getElementById("rp-actuals-file-input");
  if (!fileInput) return;

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file || !pendingTeamCode || !sprintCode) return;

    const teamCode = pendingTeamCode;

    // Reset so the same file can be re-selected if needed
    fileInput.value = "";

    const { href, method } = API_URLS.sprints.actualsUpload(sprintCode, teamCode);
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
        title: "Actuals uploaded",
        message: "The file has been recorded successfully.",
      });
      const teamTable = document.getElementById(`rp-actuals-imports-table-${teamCode}`);
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
  const container = document.getElementById("rp-actuals-teams-container");
  if (!container) return;

  container.addEventListener("click", (e) => {
    const btn = e.target.closest("secondary-button[data-team-code]");
    if (!btn) return;
    e.stopPropagation(); // prevent accordion toggle
    const teamCode = btn.dataset.teamCode;
    const fileInput = document.getElementById("rp-actuals-file-input");
    if (!fileInput) {
      toast({
        type: "error",
        title: "Permission denied",
        message: "You do not have permission to upload actuals data.",
      });
      return;
    }
    pendingTeamCode = teamCode;
    fileInput.click();
  });
}

function initDownloadTemplateButton() {
  const btn = document.getElementById("rp-actuals-template-btn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    if (!sprintCode) return;
    const { href } = API_URLS.sprints.actualsTemplate(sprintCode);
    window.location.href = href;
  });
}

async function openReviewCompleteDrawer(drawer) {
  const loading = document.getElementById("rp-actuals-review-complete-loading");
  const body = document.getElementById("rp-actuals-review-complete-body");
  const incompleteSection = document.getElementById("rp-actuals-review-complete-incomplete");
  const allOkSection = document.getElementById("rp-actuals-review-complete-all-ok");
  const teamList = document.getElementById("rp-actuals-review-complete-team-list");
  const overrideField = document.getElementById("rp-actuals-review-complete-override");
  const notesField = document.getElementById("rp-actuals-review-complete-notes");
  const submitBtn = drawer.querySelector("[data-footer-primary]");

  // Reset to loading state
  if (loading) loading.hidden = false;
  if (body) body.hidden = true;
  if (incompleteSection) incompleteSection.hidden = true;
  if (allOkSection) allOkSection.hidden = true;
  if (submitBtn) submitBtn.setAttribute("disabled", "");
  if (overrideField) overrideField.dispatchEvent(new Event("rp:reset", { bubbles: false }));
  if (notesField) {
    notesField.value = "";
    notesField.dispatchEvent(new Event("rp:reset", { bubbles: false }));
  }

  drawer.show();

  try {
    const { href, method } = API_URLS.teams.list();
    const resp = await apiFetch(`${href}?is_active=true&page_size=100`, { method });
    const teams = resp?.data?.results ?? [];

    // Check each team's latest confirmed import status in parallel
    const checks = await Promise.all(
      teams.map(async (team) => {
        try {
          const { href: ih, method: im } = API_URLS.sprints.actualsImports(sprintCode, team.code);
          const ir = await apiFetch(`${ih}?page_size=1`, { method: im });
          const latest = ir?.data?.results?.[0] ?? null;
          return { team, isConfirmed: latest?.status === "confirmed", hasImport: !!latest };
        } catch {
          return { team, isConfirmed: false, hasImport: false };
        }
      }),
    );

    const incompleteTeams = checks.filter((c) => !c.isConfirmed);

    if (loading) loading.hidden = true;
    if (body) body.hidden = false;

    if (incompleteTeams.length > 0) {
      if (teamList) {
        teamList.innerHTML = incompleteTeams
          .map(({ team, hasImport }) => {
            const reason = hasImport ? "Not Confirmed" : "No Import";
            const badgeCls = hasImport ? "rp-badge-info" : "rp-badge-warning";
            return `<div class="d-flex align-items-center justify-content-between py-2 border-bottom">
              <div class="d-flex align-items-center gap-2">
                <identicon-field name="${esc(team.name)}" variant="monogram" size="sm"></identicon-field>
                <span class="fw-medium">${esc(team.name)}</span>
              </div>
              <span class="rp-badge rp-badge-soft ${esc(badgeCls)}">${reason}</span>
            </div>`;
          })
          .join("");
      }
      if (incompleteSection) incompleteSection.hidden = false;
    } else {
      if (allOkSection) allOkSection.hidden = false;
      if (submitBtn) submitBtn.removeAttribute("disabled");
    }
  } catch {
    if (loading) loading.hidden = true;
    if (body) body.hidden = false;
    if (teamList)
      teamList.innerHTML = `<p class="mb-0" style="color:var(--rp-danger)">Failed to load team statuses. Close and retry.</p>`;
    if (incompleteSection) incompleteSection.hidden = false;
  }
}

function initReviewCompleteButton() {
  const btn = document.getElementById("rp-actuals-review-complete-btn");
  const drawer = document.getElementById("rp-actuals-review-complete-drawer");
  if (!btn || !drawer) return;

  const overrideField = document.getElementById("rp-actuals-review-complete-override");
  const submitBtn = drawer.querySelector("[data-footer-primary]");

  btn.addEventListener("click", () => openReviewCompleteDrawer(drawer));

  // Enable / disable the Complete button based on override checkbox state
  if (overrideField && submitBtn) {
    overrideField.addEventListener("change", () => {
      if (overrideField.checked) {
        submitBtn.removeAttribute("disabled");
      } else {
        submitBtn.setAttribute("disabled", "");
      }
    });
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    const notesField = document.getElementById("rp-actuals-review-complete-notes");
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Completing…");

    const notes = notesField?.value?.trim() ?? "";
    const override = overrideField?.checked ?? false;

    try {
      const { href, method } = API_URLS.sprints.actualsReviewComplete(sprintCode);
      await apiFetch(href, { method, body: JSON.stringify({ notes, override }) });
      drawer.hide();
      toast({
        type: "success",
        title: "Review complete",
        message: "Sprint actuals review has been marked complete.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to complete review. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportRowNavigation() {
  const container = document.getElementById("rp-actuals-teams-container");
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
    window.location.href = UI_URLS.sprints.actualsImportDetail(sprintCode, row.code);
  });
}

function initSyncProjectActualsButton() {
  const btn = document.getElementById("rp-actuals-sync-btn");
  const drawer = document.getElementById("rp-actuals-sync-drawer");
  if (!btn || !drawer) return;

  const scopeField = document.getElementById("rp-actuals-sync-scope");
  const projectsSection = document.getElementById("rp-actuals-sync-projects-section");
  const projectsLoading = document.getElementById("rp-actuals-sync-projects-loading");
  const projectsList = document.getElementById("rp-actuals-sync-projects-list");

  function resetDrawer() {
    if (scopeField) scopeField.dispatchEvent(new Event("rp:reset", { bubbles: false }));
    if (projectsSection) projectsSection.hidden = true;
    if (projectsLoading) projectsLoading.hidden = false;
    if (projectsList) {
      projectsList.hidden = true;
      projectsList.innerHTML = "";
    }
  }

  async function loadProjects() {
    try {
      const { href, method } = API_URLS.sprints.actualsProjects(sprintCode);
      const resp = await apiFetch(href, { method });
      const projects = resp?.data?.results ?? [];

      if (projectsList) {
        if (!projects.length) {
          projectsList.innerHTML = `<p class="mb-0" style="color:var(--rp-muted)">No projects with actuals data found for this sprint.</p>`;
        } else {
          projectsList.innerHTML = "";
          projects.forEach((p) => {
            const wrapper = document.createElement("div");
            wrapper.className = "py-2 border-bottom";
            const cb = document.createElement("checkbox-field");
            cb.setAttribute("label", p.name);
            cb.dataset.projectCode = p.code;
            wrapper.appendChild(cb);
            projectsList.appendChild(wrapper);
          });
        }
        projectsList.hidden = false;
      }
      if (projectsLoading) projectsLoading.hidden = true;
    } catch {
      if (projectsLoading) projectsLoading.hidden = true;
      if (projectsList) {
        projectsList.innerHTML = `<p class="mb-0" style="color:var(--rp-danger)">Failed to load projects. Close and retry.</p>`;
        projectsList.hidden = false;
      }
    }
  }

  btn.addEventListener("click", () => {
    resetDrawer();
    drawer.show();
    loadProjects();
  });

  if (scopeField) {
    scopeField.addEventListener("change", () => {
      const isSpecific = scopeField.value === "specific";
      if (projectsSection) projectsSection.hidden = !isSpecific;
    });
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    const scope = scopeField?.value ?? "all";
    const allProjects = scope !== "specific";

    let projectCodes = [];
    if (!allProjects) {
      const checkboxes = projectsList
        ? Array.from(projectsList.querySelectorAll("checkbox-field"))
        : [];
      projectCodes = checkboxes.filter((cb) => cb.checked).map((cb) => cb.dataset.projectCode);

      if (!projectCodes.length) {
        toast({
          type: "warning",
          title: "No projects selected",
          message: "Please select at least one project or choose All Projects.",
        });
        return;
      }
    }

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Syncing…");

    try {
      const { href, method } = API_URLS.sprints.actualsSyncProjectActuals(sprintCode);
      const payload = allProjects
        ? { all_projects: true }
        : { all_projects: false, project_codes: projectCodes };
      const resp = await apiFetch(href, { method, body: JSON.stringify(payload) });
      const count = resp?.data?.created ?? 0;
      drawer.hide();
      toast({
        type: "success",
        title: "Project actuals synced",
        message: `${count} project actual record${count !== 1 ? "s" : ""} created.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to sync project actuals. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("rp-actuals-teams-container");
  if (!container) return;

  loadSprintAndTeams();
  initUpload();
  initImportActions();
  initImportRowNavigation();
  initDownloadTemplateButton();
  initReviewCompleteButton();
  initSyncProjectActualsButton();
});
