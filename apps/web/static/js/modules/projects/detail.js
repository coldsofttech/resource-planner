"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatCurrency,
  formatDate,
  getCsrfToken,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

const projectCode = window.location.pathname.split("/").filter(Boolean)[1];

let currentProject = null;
let currentProjectTags = [];
let currentProjectLabels = [];
let pendingLabelDeletions = [];
let currentEstimates = [];
let estimatesLoaded = false;
let pendingEstimateRow = null;
let budgetsLoaded = false;
let pendingBudgetRow = null;
let loadedBudgets = [];
let _pendingEditApprovePayload = null;
let linksLoaded = false;
let pendingLinkRow = null;
let attachmentsLoaded = false;
let pendingAttachmentRow = null;
let pendingContactRow = null;
let contactsLoaded = false;

function setView(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val ?? "—";
}

function statusBadgeClass(name) {
  const n = (name || "").toLowerCase();
  if (n.includes("progress")) return "rp-badge rp-badge-soft rp-badge-info";
  if (n.includes("complet") || n.includes("cancel"))
    return "rp-badge rp-badge-soft rp-badge-success";
  if (n.includes("hold")) return "rp-badge rp-badge-soft rp-badge-warning";
  return "rp-badge rp-badge-soft";
}

function statusIsInProgress(name) {
  return (name || "").toLowerCase().includes("progress");
}

function statusIsCompleted(name) {
  return (name || "").toLowerCase().includes("complet");
}

function updateSprintFieldVisibility(statusName) {
  const startedWrapper = document.getElementById("rp-edit-project-sprint-started-in-wrapper");
  const completedWrapper = document.getElementById("rp-edit-project-sprint-completed-in-wrapper");
  const showStarted = statusIsInProgress(statusName);
  const showCompleted = statusIsCompleted(statusName);

  const startedField = document.getElementById("rp-edit-project-sprint-started-in");
  const completedField = document.getElementById("rp-edit-project-sprint-completed-in");

  if (startedWrapper) {
    // Keep visible if status is IN_PROGRESS (required) or a value is already set (optional)
    const hasValue = !!startedField?.value;
    startedWrapper.hidden = !showStarted && !hasValue;
    if (startedField) {
      if (showStarted) {
        startedField.setAttribute("required", "");
      } else {
        startedField.removeAttribute("required");
        if (!hasValue) startedField.value = "";
      }
      if (hasValue) {
        startedField.setAttribute("unassign", "");
      } else {
        startedField.removeAttribute("unassign");
      }
    }
  }
  if (completedWrapper) {
    // Keep visible if status is COMPLETED (required) or a value is already set (optional)
    const hasValue = !!completedField?.value;
    completedWrapper.hidden = !showCompleted && !hasValue;
    if (completedField) {
      if (showCompleted) {
        completedField.setAttribute("required", "");
      } else {
        completedField.removeAttribute("required");
        if (!hasValue) completedField.value = "";
      }
      if (hasValue) {
        completedField.setAttribute("unassign", "");
      } else {
        completedField.removeAttribute("unassign");
      }
    }
  }
}

function confidenceBadgeClass(value) {
  if (value === "high" || value === "very_high") return "rp-badge rp-badge-soft rp-badge-danger";
  if (value === "medium") return "rp-badge rp-badge-soft rp-badge-warning";
  return "rp-badge rp-badge-soft rp-badge-info";
}

function priorityBadgeClass(value) {
  if (value === "high" || value === "very_high") return "rp-badge rp-badge-soft rp-badge-danger";
  if (value === "medium") return "rp-badge rp-badge-soft rp-badge-warning";
  return "rp-badge rp-badge-soft rp-badge-info";
}

function renderTeamBadges(project) {
  const container = document.getElementById("rp-project-detail-teams-badges");
  if (!container) return;

  const badges = [];
  if (project.assigned_team_name) {
    badges.push(
      `<span class="rp-badge rp-badge-success">${esc(project.assigned_team_name)}</span>`,
    );
  }
  for (const c of project.collaborators ?? []) {
    badges.push(`<span class="rp-badge rp-badge-soft rp-badge-info">${esc(c.team_name)}</span>`);
  }

  container.innerHTML = badges.length
    ? badges.join("")
    : '<span class="text-muted rp-fs-13">No teams assigned.</span>';
}

function renderLabelBadges(labels) {
  const container = document.getElementById("rp-project-detail-labels-badges");
  if (!container) return;

  const badges = labels.map(
    (lbl) =>
      `<span class="rp-badge ${lbl.is_default ? "rp-badge-success" : "rp-badge-soft rp-badge-info"}">${esc(lbl.label)}</span>`,
  );

  container.innerHTML = badges.length
    ? badges.join("")
    : '<span class="text-muted rp-fs-13">No labels added.</span>';
}

function renderEditDrawerLabels(labels) {
  const container = document.getElementById("rp-edit-project-labels-container");
  const emptyEl = document.getElementById("rp-edit-project-labels-empty");
  if (!container) return;

  pendingLabelDeletions = [];

  if (!labels.length) {
    container.innerHTML = "";
    if (emptyEl) emptyEl.hidden = false;
    return;
  }

  if (emptyEl) emptyEl.hidden = true;

  container.innerHTML = labels
    .map(
      (lbl) =>
        `<span class="rp-badge ${lbl.is_default ? "rp-badge-success" : "rp-badge-soft rp-badge-info"} d-inline-flex align-items-center gap-1" data-label-code="${esc(lbl.code)}">` +
        `${esc(lbl.label)}` +
        `<button type="button" class="rp-badge-remove ms-1" aria-label="Remove ${esc(lbl.label)}" data-remove-label="${esc(lbl.code)}" style="background:none;border:none;padding:0;line-height:1;cursor:pointer;opacity:.7;">&times;</button>` +
        `</span>`,
    )
    .join("");

  container.querySelectorAll("[data-remove-label]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.getAttribute("data-remove-label");
      if (!pendingLabelDeletions.includes(code)) pendingLabelDeletions.push(code);
      btn.closest("[data-label-code]")?.remove();
      if (!container.querySelectorAll("[data-label-code]").length) {
        if (emptyEl) emptyEl.hidden = false;
      }
    });
  });
}

function syncCollaboratorOptions(excludeCode) {
  const collaboratorsField = document.getElementById("rp-edit-project-collaborators");
  if (!collaboratorsField) return;

  // Cache the full options list on the first call after options have loaded
  if (collaboratorsField._initialOptions?.length && !collaboratorsField._allTeamOptions) {
    collaboratorsField._allTeamOptions = [...collaboratorsField._initialOptions];
  }

  const allOptions = collaboratorsField._allTeamOptions || collaboratorsField._initialOptions || [];

  collaboratorsField._initialOptions = excludeCode
    ? allOptions.filter((o) => o.value !== excludeCode)
    : [...allOptions];

  // Remove excluded team from already-selected chips
  if (excludeCode && collaboratorsField._selectedValues) {
    const prevLength = collaboratorsField._selectedValues.length;
    collaboratorsField._selectedValues = collaboratorsField._selectedValues.filter(
      (sv) => sv.value !== excludeCode,
    );
    if (collaboratorsField._selectedValues.length !== prevLength) {
      collaboratorsField._refreshChipsAndInput?.();
    }
  }
}

function updateFollowButton(isFollowing) {
  const btn = document.getElementById("rp-project-follow-btn");
  if (!btn) return;
  if (isFollowing) {
    btn.setAttribute("label", "Following");
    btn.setAttribute("prefix-icon", "bi-star-fill");
  } else {
    btn.setAttribute("label", "Follow");
    btn.setAttribute("prefix-icon", "bi-star");
  }
  btn.removeAttribute("disabled");
}

function initFollowButton() {
  const btn = document.getElementById("rp-project-follow-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    if (!currentProject) return;
    btn.setAttribute("disabled", "");

    const isFollowing = btn.getAttribute("label") === "Following";

    if (isFollowing && currentProject.follower_code) {
      const { href, method } = API_URLS.projectFollowers.delete(
        projectCode,
        currentProject.follower_code,
      );
      try {
        await apiFetch(href, { method });
        currentProject.is_following = false;
        currentProject.follower_code = null;
        updateFollowButton(false);
        toast({
          type: "success",
          title: "Unfollowed",
          message: "You are no longer following this project.",
        });
      } catch {
        btn.removeAttribute("disabled");
        toast({
          type: "error",
          title: "Error",
          message: "Failed to unfollow project. Please try again.",
        });
      }
    } else if (!isFollowing) {
      const { href, method } = API_URLS.projectFollowers.create(projectCode);
      try {
        const resp = await apiFetch(href, { method });
        currentProject.is_following = true;
        currentProject.follower_code = resp?.data?.code ?? null;
        updateFollowButton(true);
        toast({
          type: "success",
          title: "Following",
          message: "You are now following this project.",
        });
      } catch {
        btn.removeAttribute("disabled");
        toast({
          type: "error",
          title: "Error",
          message: "Failed to follow project. Please try again.",
        });
      }
    } else {
      btn.removeAttribute("disabled");
    }
  });
}

async function loadProjectTags() {
  try {
    const { href, method } = API_URLS.projectTags.list(projectCode);
    const resp = await apiFetch(href, { method });
    currentProjectTags = resp?.data ?? [];

    const tagsField = document.getElementById("rp-project-detail-tags");
    if (tagsField) {
      tagsField._selectedValues = currentProjectTags.map((t) => ({
        id: t.tag_code,
        label: t.tag_name,
        value: t.tag_code,
      }));
      tagsField._refreshChipsAndInput?.();
    }
  } catch {
    // non-fatal
  }
}

async function loadProjectLabels() {
  try {
    const { href, method } = API_URLS.projectLabels.list(projectCode);
    const resp = await apiFetch(href, { method });
    currentProjectLabels = resp?.results ?? resp?.data ?? [];
    renderLabelBadges(currentProjectLabels);
  } catch {
    currentProjectLabels = [];
    renderLabelBadges([]);
  }
}

async function loadProjectDetails() {
  try {
    const { href, method } = API_URLS.projects.detail(projectCode);
    const resp = await apiFetch(href, { method });
    currentProject = resp?.data ?? null;
    if (!currentProject) return;

    const displayName = currentProject.display_name || currentProject.name;

    const titleEl = document.getElementById("rp-project-detail-title");
    if (titleEl) titleEl.textContent = displayName;

    const headerIdenticon = document.getElementById("rp-project-header-identicon");
    if (headerIdenticon) headerIdenticon.setAttribute("name", currentProject.name);

    setBreadcrumbs([
      { label: "Project" },
      { label: "Projects", href: UI_URLS.projects.list() },
      { label: displayName },
    ]);

    // General Information
    setView("rp-project-detail-id", currentProject.code);
    setView("rp-project-detail-name", currentProject.name);
    setView("rp-project-detail-type", currentProject.project_type_name);
    setView("rp-project-detail-programme", currentProject.programme_name || "—");
    setView("rp-project-detail-description", currentProject.description || "—");

    // Status badge — name-based color matching
    const statusEl = document.getElementById("rp-project-detail-status");
    if (statusEl) {
      statusEl.setAttribute("badge", statusBadgeClass(currentProject.status_name));
      statusEl.value = currentProject.status_name || "—";
    }
    const subStatusEl = document.getElementById("rp-project-detail-sub-status");
    if (subStatusEl) {
      if (currentProject.sub_status_name) {
        subStatusEl.setAttribute("badge", statusBadgeClass(currentProject.sub_status_name));
        subStatusEl.value = currentProject.sub_status_name;
      } else {
        subStatusEl.removeAttribute("badge");
        subStatusEl.value = "—";
      }
    }

    // Confidence badge
    const confLabels = { low: "Low", medium: "Medium", high: "High", very_high: "Very High" };
    const confEl = document.getElementById("rp-project-detail-confidence");
    if (confEl) {
      if (currentProject.confidence) {
        confEl.setAttribute("badge", confidenceBadgeClass(currentProject.confidence));
        confEl.value = confLabels[currentProject.confidence] ?? currentProject.confidence;
      } else {
        confEl.removeAttribute("badge");
        confEl.value = "—";
      }
    }

    // Priority badge
    const priLabels = { low: "Low", medium: "Medium", high: "High", very_high: "Very High" };
    const priorityEl = document.getElementById("rp-project-detail-priority");
    if (priorityEl) {
      if (currentProject.priority) {
        priorityEl.setAttribute("badge", priorityBadgeClass(currentProject.priority));
        priorityEl.value = priLabels[currentProject.priority] ?? currentProject.priority;
      } else {
        priorityEl.removeAttribute("badge");
        priorityEl.value = "—";
      }
    }

    setView(
      "rp-project-detail-start-date",
      currentProject.start_date ? formatDate(currentProject.start_date) : "—",
    );
    setView(
      "rp-project-detail-end-date",
      currentProject.end_date ? formatDate(currentProject.end_date) : "—",
    );

    // Sprint started in — visible whenever a value is recorded
    const sprintStartedViewEl = document.getElementById("rp-project-detail-sprint-started-in");
    if (sprintStartedViewEl) {
      const show = !!currentProject.sprint_started_in_name;
      sprintStartedViewEl.hidden = !show;
      if (show) {
        sprintStartedViewEl.value = currentProject.sprint_started_in_name;
      }
    }

    // Sprint completed in — visible whenever a value is recorded
    const sprintCompletedViewEl = document.getElementById("rp-project-detail-sprint-completed-in");
    if (sprintCompletedViewEl) {
      const show = !!currentProject.sprint_completed_in_name;
      sprintCompletedViewEl.hidden = !show;
      if (show) {
        sprintCompletedViewEl.value = currentProject.sprint_completed_in_name;
      }
    }

    // Meta
    setView(
      "rp-project-detail-created-at",
      currentProject.created_at ? formatDate(currentProject.created_at) : "—",
    );
    setView("rp-project-detail-created-by", currentProject.created_by?.email || "—");
    setView(
      "rp-project-detail-updated-at",
      currentProject.updated_at ? formatDate(currentProject.updated_at) : "—",
    );
    setView("rp-project-detail-updated-by", currentProject.updated_by?.email || "—");

    // Operational
    const effortsEl = document.getElementById("rp-project-detail-efforts-issued");
    if (effortsEl) {
      effortsEl.setAttribute(
        "badge",
        currentProject.efforts_issued
          ? "rp-badge rp-badge-soft rp-badge-success"
          : "rp-badge rp-badge-soft rp-badge-warning",
      );
      effortsEl.value = currentProject.efforts_issued ? "Yes" : "No";
    }
    setView(
      "rp-project-detail-commitment-date",
      currentProject.commitment_date ? formatDate(currentProject.commitment_date) : "—",
    );
    const runCostEl = document.getElementById("rp-project-detail-run-cost");
    if (runCostEl) {
      runCostEl.setAttribute(
        "badge",
        currentProject.run_cost_applies
          ? "rp-badge rp-badge-soft rp-badge-success"
          : "rp-badge rp-badge-soft rp-badge-warning",
      );
      runCostEl.value = currentProject.run_cost_applies ? "Yes" : "No";
    }

    // Teams tab — render as badges
    renderTeamBadges(currentProject);

    // Code & Labels tab — code value
    setView("rp-project-detail-code-value", currentProject.project_code_value || "—");

    // Enable edit button after project loads
    const editBtn = document.getElementById("rp-project-edit-btn");
    if (editBtn) editBtn.removeAttribute("disabled");

    updateFollowButton(currentProject.is_following);

    // Wire comments panel
    const commentsPanel = document.getElementById("rp-project-comments-panel");
    if (commentsPanel) {
      const { href } = API_URLS.projectComments.list(projectCode);
      commentsPanel.setAttribute("comments-url", href);
    }
  } catch {
    toast({
      type: "error",
      title: "Could not load project",
      message: "Refresh the page to retry.",
    });
  }
}

function openEditDrawer() {
  if (!currentProject) return;
  const drawer = document.getElementById("rp-project-edit-drawer");
  if (!drawer) return;

  const displayName = currentProject.display_name || currentProject.name;

  const identicon = document.getElementById("rp-project-edit-identicon");
  if (identicon) identicon.setAttribute("name", currentProject.name);
  drawer.setTitle(displayName);

  const nameField = document.getElementById("rp-edit-project-name");
  if (nameField) nameField.value = currentProject.name;

  const typeField = document.getElementById("rp-edit-project-type");
  if (typeField) typeField.value = currentProject.project_type_code || "";

  const progField = document.getElementById("rp-edit-project-programme");
  if (progField) progField.value = currentProject.programme_code || "";

  const statusField = document.getElementById("rp-edit-project-status");
  if (statusField) statusField.value = currentProject.status_code || "";

  const subStatusField = document.getElementById("rp-edit-project-sub-status");
  if (subStatusField) subStatusField.value = currentProject.sub_status_code || "";

  const confField = document.getElementById("rp-edit-project-confidence");
  if (confField) confField.value = currentProject.confidence || "";

  const priorityField = document.getElementById("rp-edit-project-priority");
  if (priorityField) priorityField.value = currentProject.priority || "";

  const startField = document.getElementById("rp-edit-project-start-date");
  if (startField) startField.value = currentProject.start_date || "";

  const endField = document.getElementById("rp-edit-project-end-date");
  if (endField) endField.value = currentProject.end_date || "";

  const sprintStartedField = document.getElementById("rp-edit-project-sprint-started-in");
  if (sprintStartedField) sprintStartedField.value = currentProject.sprint_started_in_code || "";
  const sprintCompletedField = document.getElementById("rp-edit-project-sprint-completed-in");
  if (sprintCompletedField)
    sprintCompletedField.value = currentProject.sprint_completed_in_code || "";
  updateSprintFieldVisibility(currentProject.status_name || "");

  const descField = document.getElementById("rp-edit-project-description");
  if (descField) descField.value = currentProject.description || "";

  const effortsField = document.getElementById("rp-edit-project-efforts-issued");
  if (effortsField) effortsField.checked = !!currentProject.efforts_issued;

  const commitmentField = document.getElementById("rp-edit-project-commitment-date");
  if (commitmentField) commitmentField.value = currentProject.commitment_date || "";

  const runCostField = document.getElementById("rp-edit-project-run-cost");
  if (runCostField) runCostField.checked = !!currentProject.run_cost_applies;

  // Teams — conditionally show unassign option only if a team is already assigned
  const assignedTeamField = document.getElementById("rp-edit-project-assigned-team");
  if (assignedTeamField) {
    if (currentProject.assigned_team_code) {
      assignedTeamField.setAttribute("unassign", "");
    } else {
      assignedTeamField.removeAttribute("unassign");
    }
    assignedTeamField.value = currentProject.assigned_team_code || "";
  }

  const collaboratorsField = document.getElementById("rp-edit-project-collaborators");
  if (collaboratorsField) {
    const assignedCode = currentProject.assigned_team_code || "";
    const codes = (currentProject.collaborators ?? [])
      .map((c) => c.team_code)
      .filter((c) => c !== assignedCode);
    collaboratorsField.value = JSON.stringify(codes);
  }

  // Sync collaborator options to exclude the currently assigned team
  syncCollaboratorOptions(currentProject.assigned_team_code || "");

  // Labels accordion
  renderEditDrawerLabels(currentProjectLabels);

  // Project Code accordion — editable text field
  const codeField = document.getElementById("rp-edit-project-code-value");
  if (codeField) codeField.value = currentProject.project_code_value || "";

  drawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
    el.hidden = true;
  });

  drawer.show();
}

function initEditButton() {
  const btn = document.getElementById("rp-project-edit-btn");
  if (!btn) return;
  btn.addEventListener("click", openEditDrawer);
}

function initEditDrawer() {
  const drawer = document.getElementById("rp-project-edit-drawer");
  if (!drawer) return;

  function validateForm() {
    ["rp-edit-project-name", "rp-edit-project-type", "rp-edit-project-status"].forEach((id) => {
      document.getElementById(id)?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    });

    // Validate sprint fields only when they are required (i.e. visible)
    const startedWrapper = document.getElementById("rp-edit-project-sprint-started-in-wrapper");
    const completedWrapper = document.getElementById("rp-edit-project-sprint-completed-in-wrapper");
    if (startedWrapper && !startedWrapper.hidden) {
      document
        .getElementById("rp-edit-project-sprint-started-in")
        ?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    }
    if (completedWrapper && !completedWrapper.hidden) {
      document
        .getElementById("rp-edit-project-sprint-completed-in")
        ?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    }

    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:open", () => {
    document.getElementById("rp-edit-project-type")?.refresh?.();
    document.getElementById("rp-edit-project-programme")?.refresh?.();
    document.getElementById("rp-edit-project-status")?.refresh?.();
    document.getElementById("rp-edit-project-sprint-started-in")?.refresh?.();
    document.getElementById("rp-edit-project-sprint-completed-in")?.refresh?.();
  });

  // Update sprint field visibility when the status changes
  const statusFieldEl = document.getElementById("rp-edit-project-status");
  if (statusFieldEl) {
    statusFieldEl.addEventListener("change", () => {
      const opt = (statusFieldEl._initialOptions || []).find(
        (o) => o.value === statusFieldEl.value,
      );
      updateSprintFieldVisibility(opt?.label ?? "");
    });
  }

  // Re-sync collaborator options whenever the assigned team changes
  const assignedTeamField = document.getElementById("rp-edit-project-assigned-team");
  if (assignedTeamField) {
    assignedTeamField.addEventListener("change", () => {
      syncCollaboratorOptions(assignedTeamField.value || "");
    });
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!currentProject || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const name = document.getElementById("rp-edit-project-name")?.value?.trim() ?? "";
    const projectTypeCode = document.getElementById("rp-edit-project-type")?.value ?? "";
    const programmeField = document.getElementById("rp-edit-project-programme");
    let programmeCode = programmeField?.value ?? "";
    const statusCode = document.getElementById("rp-edit-project-status")?.value ?? "";
    const subStatusCode = document.getElementById("rp-edit-project-sub-status")?.value ?? "";
    const confidence = document.getElementById("rp-edit-project-confidence")?.value ?? "";
    const priority = document.getElementById("rp-edit-project-priority")?.value ?? "";
    const startDate = document.getElementById("rp-edit-project-start-date")?.value ?? "";
    const endDate = document.getElementById("rp-edit-project-end-date")?.value ?? "";
    const description = document.getElementById("rp-edit-project-description")?.value?.trim() ?? "";
    const effortsIssued =
      document.getElementById("rp-edit-project-efforts-issued")?.checked ?? false;
    const commitmentDate = document.getElementById("rp-edit-project-commitment-date")?.value ?? "";
    const runCostApplies = document.getElementById("rp-edit-project-run-cost")?.checked ?? false;
    const assignedTeamCode = document.getElementById("rp-edit-project-assigned-team")?.value ?? "";
    const projectCodeValue =
      document.getElementById("rp-edit-project-code-value")?.value?.trim() ?? "";

    let newCollaboratorCodes = [];
    try {
      const rawVal = document.getElementById("rp-edit-project-collaborators")?.value ?? "[]";
      newCollaboratorCodes = JSON.parse(rawVal);
    } catch {
      newCollaboratorCodes = [];
    }

    // Create a new programme on the fly if the user typed one that doesn't match existing options
    if (!programmeCode) {
      const typedProgramme = programmeField?.inputText ?? "";
      if (typedProgramme) {
        try {
          const { href: ph, method: pm } = API_URLS.programmes.create();
          const pr = await apiFetch(ph, {
            method: pm,
            body: JSON.stringify({ name: typedProgramme, is_active: true }),
          });
          programmeCode = pr?.data?.code ?? "";
        } catch {
          restoreButton(submitBtn, snap);
          toast({
            type: "error",
            title: "Error",
            message: "Failed to create programme. Please try again.",
          });
          return;
        }
      }
    }

    const sprintStartedInCode =
      document.getElementById("rp-edit-project-sprint-started-in")?.value || null;
    const sprintCompletedInCode =
      document.getElementById("rp-edit-project-sprint-completed-in")?.value || null;

    const payload = {
      name,
      project_type_code: projectTypeCode,
      status_code: statusCode,
      programme_code: programmeCode || null,
      sub_status_code: subStatusCode || null,
      confidence: confidence || null,
      priority: priority || null,
      start_date: startDate || null,
      end_date: endDate || null,
      description: description || "",
      efforts_issued: effortsIssued,
      commitment_date: commitmentDate || null,
      run_cost_applies: runCostApplies,
      assigned_team_code: assignedTeamCode || null,
      project_code_value: projectCodeValue || null,
      sprint_started_in_code: sprintStartedInCode,
      sprint_completed_in_code: sprintCompletedInCode,
    };

    const { href, method } = API_URLS.projects.update(projectCode);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });

      // Reconcile collaborating teams — exclude the assigned team from collaborators
      const effectiveCollaboratorCodes = assignedTeamCode
        ? newCollaboratorCodes.filter((c) => c !== assignedTeamCode)
        : newCollaboratorCodes;
      const currentCollaboratorCodes = (currentProject.collaborators ?? []).map((c) => c.team_code);
      const toAdd = effectiveCollaboratorCodes.filter((c) => !currentCollaboratorCodes.includes(c));
      const toRemove = currentCollaboratorCodes.filter(
        (c) => !effectiveCollaboratorCodes.includes(c),
      );

      const addPromises = toAdd.map((teamCode) => {
        const { href: ah, method: am } = API_URLS.projects.addCollaborator(projectCode);
        return apiFetch(ah, { method: am, body: JSON.stringify({ team_code: teamCode }) }).catch(
          (err) => {
            if (err?.status === 409) return null; // already a collaborator — ignore
            throw err;
          },
        );
      });
      const removePromises = toRemove.map((teamCode) => {
        const { href: rh, method: rm } = API_URLS.projects.removeCollaborator(
          projectCode,
          teamCode,
        );
        return apiFetch(rh, { method: rm });
      });

      // Delete labels marked for removal
      const removeLabelPromises = pendingLabelDeletions.map((labelCode) => {
        const { href: lh, method: lm } = API_URLS.projectLabels.delete(projectCode, labelCode);
        return apiFetch(lh, { method: lm });
      });

      await Promise.all([...addPromises, ...removePromises, ...removeLabelPromises]);

      pendingLabelDeletions = [];
      restoreButton(submitBtn, snap);
      drawer.hide();
      await loadProjectDetails();
      await loadProjectLabels();
      toast({ type: "success", title: "Project saved", message: `"${name}" has been updated.` });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to save project. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initAddLabelModal() {
  const addBtn = document.getElementById("rp-project-add-label-btn");
  const modal = document.getElementById("rp-project-add-label-modal");
  if (!addBtn || !modal) return;

  function closeModal() {
    modal.style.display = "none";
  }

  function resetLabelForm() {
    const labelInput = document.getElementById("rp-add-label-input");
    const isDefaultToggle = document.getElementById("rp-add-label-is-default");
    if (labelInput) labelInput.value = "";
    if (isDefaultToggle) isDefaultToggle.checked = false;
    modal.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
      el.hidden = true;
    });
  }

  addBtn.addEventListener("click", () => {
    resetLabelForm();
    modal.style.display = "grid";
  });

  document.getElementById("rp-add-label-modal-close")?.addEventListener("click", closeModal);
  document.getElementById("rp-add-label-modal-cancel")?.addEventListener("click", closeModal);

  // Close on backdrop click
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  // Suggest button
  const suggestBtn = document.getElementById("rp-add-label-suggest-btn");
  if (suggestBtn) {
    suggestBtn.addEventListener("click", async () => {
      const snap = snapshotButton(suggestBtn);
      setBusyButton(suggestBtn, "Suggesting…");
      try {
        const { href, method } = API_URLS.projectLabels.suggest(projectCode);
        const resp = await apiFetch(href, { method });
        const suggested = resp?.data?.label ?? resp?.data ?? null;
        if (suggested) {
          const labelInput = document.getElementById("rp-add-label-input");
          if (labelInput) labelInput.value = String(suggested).toUpperCase();
        }
        restoreButton(suggestBtn, snap);
      } catch {
        restoreButton(suggestBtn, snap);
        toast({
          type: "error",
          title: "Error",
          message: "Failed to get suggestion. Please try again.",
        });
      }
    });
  }

  // Submit button
  const submitBtn = document.getElementById("rp-add-label-modal-submit");
  if (submitBtn) {
    submitBtn.addEventListener("click", async () => {
      const labelInput = document.getElementById("rp-add-label-input");
      const isDefaultToggle = document.getElementById("rp-add-label-is-default");

      labelInput?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
      if (modal.querySelector("[data-rp-error]:not([hidden])")) return;

      const labelVal = labelInput?.value?.trim() ?? "";
      if (!labelVal) return;

      if (!/^[A-Z0-9_]+$/.test(labelVal)) {
        toast({
          type: "error",
          title: "Invalid label",
          message:
            "Label must contain only uppercase letters (A–Z), digits (0–9), and underscores.",
        });
        return;
      }

      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Saving…");

      const isDefault = isDefaultToggle?.checked ?? false;

      try {
        const { href, method } = API_URLS.projectLabels.create(projectCode);
        await apiFetch(href, {
          method,
          body: JSON.stringify({ label: labelVal, is_default: isDefault }),
        });
        restoreButton(submitBtn, snap);
        closeModal();
        await loadProjectLabels();
        renderEditDrawerLabels(currentProjectLabels);
        toast({ type: "success", title: "Label added", message: `"${labelVal}" has been added.` });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to add label. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }
}

function initTagsSaveButton() {
  const saveBtn = document.getElementById("rp-project-tags-save-btn");
  const tagsField = document.getElementById("rp-project-detail-tags");
  if (!saveBtn || !tagsField) return;

  saveBtn.addEventListener("click", async () => {
    const selectedChips = tagsField.values ?? [];

    // Partition chips into known tags (TAG- code) and free-form (typed name)
    const knownChips = selectedChips.filter((v) => /^TAG-/i.test(v.value));
    const freeFormChips = selectedChips.filter((v) => !/^TAG-/i.test(v.value));

    const selectedCodes = knownChips.map((v) => v.value);
    const currentTagCodes = currentProjectTags.map((t) => t.tag_code);
    const currentTagNames = currentProjectTags.map((t) => (t.tag_name ?? "").toLowerCase());

    const toAddByCode = selectedCodes.filter((c) => !currentTagCodes.includes(c));
    const freeFormToAdd = freeFormChips.filter(
      (v) => !currentTagNames.includes(v.value.toLowerCase()),
    );
    const toRemove = currentProjectTags.filter((t) => {
      const stillByCode = selectedCodes.includes(t.tag_code);
      const stillByName = freeFormChips.some(
        (v) => v.value.toLowerCase() === (t.tag_name ?? "").toLowerCase(),
      );
      return !stillByCode && !stillByName;
    });

    if (!toAddByCode.length && !freeFormToAdd.length && !toRemove.length) {
      toast({ type: "info", title: "No changes", message: "Tags are already up to date." });
      return;
    }

    const snap = snapshotButton(saveBtn);
    setBusyButton(saveBtn, "Saving…");

    try {
      const addByCodePromises = toAddByCode.map((tagCode) => {
        const { href, method } = API_URLS.projectTags.create(projectCode);
        return apiFetch(href, { method, body: JSON.stringify({ tag_code: tagCode }) }).catch(
          (err) => {
            if (err?.status === 409) return null;
            throw err;
          },
        );
      });
      const addFreeFormPromises = freeFormToAdd.map((chip) => {
        const { href, method } = API_URLS.projectTags.create(projectCode);
        return apiFetch(href, { method, body: JSON.stringify({ tag_name: chip.value }) }).catch(
          (err) => {
            if (err?.status === 409) return null;
            throw err;
          },
        );
      });
      const removePromises = toRemove.map((t) => {
        const { href, method } = API_URLS.projectTags.delete(projectCode, t.code);
        return apiFetch(href, { method });
      });

      await Promise.all([...addByCodePromises, ...addFreeFormPromises, ...removePromises]);
      await loadProjectTags();
      restoreButton(saveBtn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      setTimeout(() => restoreButton(saveBtn, snap), 2500);
      toast({ type: "success", title: "Tags saved", message: "Project tags have been updated." });
    } catch (err) {
      restoreButton(saveBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update tags. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
      await loadProjectTags();
    }
  });
}

function estimateSizeClass(size) {
  switch (size) {
    case "XS":
      return "rp-badge rp-badge-soft";
    case "S":
      return "rp-badge rp-badge-soft rp-badge-info";
    case "M":
      return "rp-badge rp-badge-soft rp-badge-success";
    case "L":
      return "rp-badge rp-badge-soft rp-badge-warning";
    case "XL":
      return "rp-badge rp-badge-soft rp-badge-danger";
    default:
      return "rp-badge rp-badge-soft";
  }
}

function estimateStatusClass(status) {
  switch (status) {
    case "APPROVED":
      return "rp-badge rp-badge-soft rp-badge-success";
    case "REVIEWED":
      return "rp-badge rp-badge-soft rp-badge-info";
    case "SHARED":
      return "rp-badge rp-badge-soft rp-badge-warning";
    default:
      return "rp-badge rp-badge-soft";
  }
}

function estimateStatusLabel(status) {
  const labels = {
    DRAFT: "Draft",
    REVIEWED: "Reviewed",
    SHARED: "Shared",
    APPROVED: "Approved",
    SUPERSEDED: "Superseded",
  };
  return labels[status] ?? status;
}

window.renderProjectEstimateRow = function renderProjectEstimateRow(row) {
  return (
    `<td class="rp-mono text-end">${esc(row.version_display ?? "")}</td>` +
    `<td class="text-end">${esc(String(row.estimate_days ?? ""))}d</td>` +
    `<td class="text-end">${esc(String(row.contingency_percentage ?? ""))}%</td>` +
    `<td>${esc(formatCurrency(row.total_cost ?? 0))}</td>` +
    `<td><span class="${estimateSizeClass(row.size)}">${esc(row.size ?? "")}</span></td>` +
    `<td><span class="${estimateStatusClass(row.status)}">${esc(estimateStatusLabel(row.status))}</span></td>`
  );
};

async function loadEstimateVersions() {
  const picker = document.getElementById("rp-estimate-version-picker");
  if (!picker) return;
  try {
    const { href, method } = API_URLS.projectEstimates.list(projectCode);
    const resp = await apiFetch(`${href}?page_size=100`, { method });
    const rows = resp?.data?.results ?? [];
    picker._initialOptions = rows.length
      ? [
          { id: "", label: "— Select a version —", value: "", selected: false, disabled: false },
          ...rows.map((est) => ({
            id: "",
            label: est.version_display,
            value: est.code,
            selected: false,
            disabled: false,
          })),
        ]
      : [{ id: "", label: "— No versions —", value: "", selected: false, disabled: false }];
    picker._doRender();
  } catch {
    // ignore — picker stays as-is
  }
}

async function loadEstimateHistory(estimateCode) {
  const container = document.getElementById("rp-estimate-history-list");
  if (!container) return;

  if (!estimateCode) {
    container.empty("Select a version to view its history.");
    return;
  }

  container.loading();

  const actionIcons = {
    CREATED: "bi-plus-circle-fill",
    UPDATED: "bi-pencil-fill",
    APPROVED: "bi-check-circle-fill",
    SUPERSEDED: "bi-arrow-counterclockwise",
  };
  const actionIconColors = {
    CREATED: "accent",
    UPDATED: "muted",
    APPROVED: "success",
    SUPERSEDED: "muted",
  };

  try {
    const { href, method } = API_URLS.projectEstimates.history(projectCode, estimateCode);
    const resp = await apiFetch(href, { method });
    const rows = resp?.data ?? [];

    if (!rows.length) {
      container.empty("No history available.");
      return;
    }

    const items = rows.map((row, idx) => {
      const isLast = idx === rows.length - 1;
      const statusChange = row.previous_status
        ? `${estimateStatusLabel(row.previous_status)} → ${estimateStatusLabel(row.new_status)}`
        : estimateStatusLabel(row.new_status);
      const dateStr = row.changed_on ? formatDate(row.changed_on) : "";
      const byStr = row.changed_by?.email ? ` · ${row.changed_by.email}` : "";

      const item = document.createElement("history-item");
      item.setAttribute("label", row.action.charAt(0) + row.action.slice(1).toLowerCase());
      item.setAttribute("icon", actionIcons[row.action] ?? "bi-circle-fill");
      item.setAttribute("icon-color", actionIconColors[row.action] ?? "muted");
      item.setAttribute("status", statusChange);
      if (row.note) item.setAttribute("note", row.note);
      item.setAttribute("meta", dateStr + byStr);
      if (!isLast) item.setAttribute("connector", "");
      return item;
    });

    container.setItems(items);
  } catch {
    container.error();
  }
}

async function triggerEstimateEmail(est) {
  try {
    const { href, method } = API_URLS.projectEstimates.update(projectCode, est.code);
    await apiFetch(href, { method, body: JSON.stringify({ approval_email_sent: true }) });
    toast({
      type: "success",
      title: "Email triggered",
      message: "Approval email has been triggered.",
    });
    document.getElementById("rp-estimates-table")?.refresh();
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to trigger email. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  }
}

function openCreateEstimateDrawer() {
  const drawer = document.getElementById("rp-estimate-create-drawer");
  if (!drawer) return;
  [
    "rp-new-estimate-days",
    "rp-new-estimate-contingency",
    "rp-new-estimate-link",
    "rp-new-estimate-note",
  ].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  const sharedByField = document.getElementById("rp-new-estimate-shared-by");
  if (sharedByField) {
    sharedByField._selectedValues = [];
    sharedByField._refreshChipsAndInput?.();
  }
  drawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
    el.hidden = true;
  });
  drawer.show();
}

async function openEditEstimateDrawer(est) {
  const drawer = document.getElementById("rp-estimate-edit-drawer");
  if (!drawer) return;
  pendingEstimateRow = est;
  drawer.setTitle(est.version_display ?? "Estimate");

  let detail = null;
  try {
    const { href, method } = API_URLS.projectEstimates.detail(projectCode, est.code);
    const resp = await apiFetch(href, { method });
    detail = resp?.data ?? null;
  } catch {
    // fall back to row data only
  }

  const daysField = document.getElementById("rp-edit-estimate-days");
  const contingencyField = document.getElementById("rp-edit-estimate-contingency");
  const statusField = document.getElementById("rp-edit-estimate-status");
  const sharedByField = document.getElementById("rp-edit-estimate-shared-by");
  const reviewedByField = document.getElementById("rp-edit-estimate-reviewed-by");
  const linkField = document.getElementById("rp-edit-estimate-link");
  const noteField = document.getElementById("rp-edit-estimate-note");

  if (daysField) daysField.value = String(est.estimate_days ?? "");
  if (contingencyField) contingencyField.value = String(est.contingency_percentage ?? "");
  if (statusField) statusField.value = est.status ?? "DRAFT";
  if (linkField) linkField.value = est.estimate_link ?? "";
  if (noteField) noteField.value = "";

  if (sharedByField) {
    const sharedBy = detail?.shared_by ?? [];
    sharedByField._selectedValues = sharedBy.map((u) => ({
      id: u.id,
      label: u.name || u.email,
      value: u.id,
    }));
    sharedByField._refreshChipsAndInput?.();
  }
  if (reviewedByField) {
    const reviewedBy = detail?.reviewed_by ?? [];
    reviewedByField._selectedValues = reviewedBy.map((u) => ({
      id: u.id,
      label: u.name || u.email,
      value: u.id,
    }));
    reviewedByField._refreshChipsAndInput?.();
  }

  drawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
    el.hidden = true;
  });
  drawer.show();
}

async function advanceEstimateStatus(row, newStatus, extra = {}) {
  const { href, method } = API_URLS.projectEstimates.update(projectCode, row.code);
  await apiFetch(href, { method, body: JSON.stringify({ status: newStatus, ...extra }) });
  document.getElementById("rp-estimates-table")?.refresh();
  loadEstimateVersions();
  const picker = document.getElementById("rp-estimate-version-picker");
  if (picker?.value === row.code) await loadEstimateHistory(row.code);
  toast({
    type: "success",
    title: "Status updated",
    message: `Estimate moved to ${estimateStatusLabel(newStatus)}.`,
  });
}

function openAdvanceEstimateFlow(row) {
  pendingEstimateRow = row;
  if (row.status === "DRAFT") {
    const modal = document.getElementById("rp-estimate-reviewed-modal");
    if (!modal) return;
    const field = document.getElementById("rp-estimate-reviewed-by-field");
    if (field) {
      field._selectedValues = [];
      field._refreshChipsAndInput?.();
    }
    modal.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
      el.hidden = true;
    });
    modal.show();
  } else if (row.status === "REVIEWED") {
    advanceEstimateStatus(row, "SHARED", {})
      .then(() => {
        pendingEstimateRow = null;
      })
      .catch((err) => {
        pendingEstimateRow = null;
        toast({
          type: "error",
          title: "Error",
          message: err?.data?.error?.message ?? "Failed to update estimate.",
        });
      });
  } else if (row.status === "SHARED") {
    if (currentProject?.project_code_value) {
      advanceEstimateStatus(row, "APPROVED", {})
        .then(() => {
          pendingEstimateRow = null;
        })
        .catch((err) => {
          pendingEstimateRow = null;
          toast({
            type: "error",
            title: "Error",
            message: err?.data?.error?.message ?? "Failed to approve estimate.",
          });
        });
    } else {
      const modal = document.getElementById("rp-estimate-approve-modal");
      if (!modal) return;
      const codeField = document.getElementById("rp-estimate-approve-code-field");
      if (codeField) codeField.value = "";
      modal.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
        el.hidden = true;
      });
      modal.show();
    }
  }
}

function initAdvanceFlow(table) {
  if (!table) return;

  table.addEventListener("rp:estimate:advance", (e) => openAdvanceEstimateFlow(e.detail.row));

  const reviewedModal = document.getElementById("rp-estimate-reviewed-modal");
  if (reviewedModal) {
    reviewedModal.addEventListener("rp:cancel", () => {
      pendingEstimateRow = null;
    });

    reviewedModal.addEventListener("rp:primary", async () => {
      if (!pendingEstimateRow) return;
      const field = document.getElementById("rp-estimate-reviewed-by-field");
      const codes = (field?.values ?? []).map((v) => v.value);
      if (!codes.length) {
        field?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
        toast({
          type: "warning",
          title: "Reviewed By required",
          message: "Please select at least one reviewer.",
        });
        return;
      }
      const primaryBtn = reviewedModal.querySelector("[data-primary-modal]");
      const snap = snapshotButton(primaryBtn);
      setBusyButton(primaryBtn, "Saving…");
      try {
        await advanceEstimateStatus(pendingEstimateRow, "REVIEWED", { reviewed_by_codes: codes });
        reviewedModal.hide();
        pendingEstimateRow = null;
        restoreButton(primaryBtn, snap);
      } catch (err) {
        restoreButton(primaryBtn, snap);
        toast({
          type: "error",
          title: "Error",
          message: err?.data?.error?.message ?? "Failed to update estimate.",
        });
      }
    });
  }

  const approveModal = document.getElementById("rp-estimate-approve-modal");
  if (approveModal) {
    approveModal.addEventListener("rp:cancel", () => {
      if (_pendingEditApprovePayload) {
        _pendingEditApprovePayload = null;
        // pendingEstimateRow stays set — edit drawer is still open
      } else {
        pendingEstimateRow = null;
      }
    });

    approveModal.addEventListener("rp:primary", async () => {
      if (!pendingEstimateRow && !_pendingEditApprovePayload) return;
      const codeField = document.getElementById("rp-estimate-approve-code-field");
      const codeVal = codeField?.value?.trim() ?? "";
      if (!codeVal) {
        codeField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
        return;
      }
      const primaryBtn = approveModal.querySelector("[data-primary-modal]");
      const snap = snapshotButton(primaryBtn);
      setBusyButton(primaryBtn, "Approving…");
      try {
        const { href: ph, method: pm } = API_URLS.projects.update(projectCode);
        await apiFetch(ph, { method: pm, body: JSON.stringify({ project_code_value: codeVal }) });
        if (currentProject) {
          currentProject.project_code_value = codeVal;
          setView("rp-project-detail-code-value", codeVal);
        }
        if (_pendingEditApprovePayload) {
          // Opened from the edit drawer — save the estimate update directly
          const { estimateCode, payload } = _pendingEditApprovePayload;
          _pendingEditApprovePayload = null;
          const { href, method } = API_URLS.projectEstimates.update(projectCode, estimateCode);
          await apiFetch(href, { method, body: JSON.stringify(payload) });
          approveModal.hide();
          const editDr = document.getElementById("rp-estimate-edit-drawer");
          editDr?.hide();
          pendingEstimateRow = null;
          restoreButton(primaryBtn, snap);
          table?.refresh();
          loadEstimateVersions();
          const versionPicker = document.getElementById("rp-estimate-version-picker");
          if (versionPicker?.value === estimateCode) await loadEstimateHistory(estimateCode);
          toast({
            type: "success",
            title: "Estimate updated",
            message: "The estimate has been saved.",
          });
        } else {
          // Opened from the advance flow
          await advanceEstimateStatus(pendingEstimateRow, "APPROVED", {});
          approveModal.hide();
          pendingEstimateRow = null;
          restoreButton(primaryBtn, snap);
        }
      } catch (err) {
        restoreButton(primaryBtn, snap);
        toast({
          type: "error",
          title: "Error",
          message: err?.data?.error?.message ?? "Failed to approve estimate.",
        });
      }
    });
  }
}

function initEstimatesTab() {
  const table = document.getElementById("rp-estimates-table");
  const baseUrl = API_URLS.projectEstimates.list(projectCode).href;

  const activateTab = () => {
    if (!estimatesLoaded) {
      estimatesLoaded = true;
      if (table) table.setAttribute("url", baseUrl);
    } else {
      table?.refresh();
    }
    loadEstimateVersions();
  };

  const tabPanel = document.querySelector("tab-panel");
  if (tabPanel) {
    if (tabPanel.activeTab === "estimates") {
      activateTab();
    }
    tabPanel.addEventListener("rp:tab-change", (e) => {
      if (e.detail.tab === "estimates") activateTab();
    });
  }

  if (table) {
    table.addEventListener("rp:data:loaded", (e) => {
      const rows = e.detail.rows ?? [];
      table.querySelectorAll("tr[data-rp-row]").forEach((tr, idx) => {
        const row = rows[idx];
        const locked = !row || ["APPROVED", "SUPERSEDED"].includes(row.status);

        const editBtn = tr.querySelector('[data-rp-action="rp:estimate:edit"]');
        if (editBtn) editBtn.hidden = locked;

        const deleteBtn = tr.querySelector('[data-rp-action="rp:estimate:delete"]');
        if (deleteBtn) deleteBtn.hidden = locked;

        const emailBtn = tr.querySelector('[data-rp-action="rp:estimate:email"]');
        if (emailBtn) {
          emailBtn.hidden = !row || row.status !== "APPROVED";
          if (!emailBtn.hidden) {
            const label = row.approval_email_sent ? "Resend Email" : "Email";
            emailBtn.setAttribute("title", label);
            emailBtn.setAttribute("aria-label", label);
            const last = emailBtn.lastChild;
            if (last?.nodeType === Node.TEXT_NODE) last.textContent = label;
          }
        }

        const advanceBtn = tr.querySelector('[data-rp-action="rp:estimate:advance"]');
        if (advanceBtn) {
          advanceBtn.hidden = !row || !["DRAFT", "REVIEWED", "SHARED"].includes(row.status);
        }
      });
    });

    table.addEventListener("rp:estimate:edit", (e) => openEditEstimateDrawer(e.detail.row));

    table.addEventListener("rp:estimate:email", (e) => triggerEstimateEmail(e.detail.row));

    table.addEventListener("rp:estimate:delete", (e) => {
      pendingEstimateRow = e.detail.row;
      const modal = document.getElementById("rp-estimate-delete-modal");
      if (modal) {
        modal.setAttribute("title", `Delete ${pendingEstimateRow.version_display}?`);
        modal.setAttribute(
          "body",
          "This will permanently delete this estimate and cannot be undone.",
        );
        modal.setAttribute("confirm-value", pendingEstimateRow.version_display);
        modal.show();
      }
    });

    table.addEventListener("click", (e) => {
      if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
      const tr = e.target.closest("tr[data-rp-row]");
      if (!tr) return;
      const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
      const row = table.rows[idx];
      if (!row?.estimate_link) return;
      window.open(row.estimate_link, "_blank", "noopener,noreferrer");
    });
  }

  const picker = document.getElementById("rp-estimate-version-picker");
  if (picker) {
    picker.addEventListener("change", () => loadEstimateHistory(picker.value || ""));
  }

  const createBtn = document.getElementById("rp-estimate-create-btn");
  if (createBtn) {
    createBtn.addEventListener("click", openCreateEstimateDrawer);
  }

  const createDrawer = document.getElementById("rp-estimate-create-drawer");
  if (createDrawer) {
    createDrawer.addEventListener("rp:footer-primary", async () => {
      const sharedByField = document.getElementById("rp-new-estimate-shared-by");
      const sharedByCodes = (sharedByField?.values ?? []).map((v) => v.value);
      if (!sharedByCodes.length) {
        sharedByField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
        toast({
          type: "warning",
          title: "Shared By required",
          message: "Please select at least one person in Shared By.",
        });
        return;
      }

      const submitBtn = createDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Creating…");

      const payload = {
        estimate_days: parseFloat(document.getElementById("rp-new-estimate-days")?.value || "0"),
        contingency_percentage: parseFloat(
          document.getElementById("rp-new-estimate-contingency")?.value || "0",
        ),
        shared_by_codes: sharedByCodes,
        estimate_link: document.getElementById("rp-new-estimate-link")?.value?.trim() || "",
        note: document.getElementById("rp-new-estimate-note")?.value?.trim() || "",
        is_active: true,
      };

      try {
        const { href, method } = API_URLS.projectEstimates.create(projectCode);
        await apiFetch(href, { method, body: JSON.stringify(payload) });
        restoreButton(submitBtn, snap);
        createDrawer.hide();
        table?.refresh();
        loadEstimateVersions();
        toast({
          type: "success",
          title: "Estimate created",
          message: "A new estimate version has been added.",
        });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to create estimate. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  const editDrawer = document.getElementById("rp-estimate-edit-drawer");
  if (editDrawer) {
    editDrawer.addEventListener("rp:footer-primary", async () => {
      if (!pendingEstimateRow) return;

      const sharedByField = document.getElementById("rp-edit-estimate-shared-by");
      const reviewedByField = document.getElementById("rp-edit-estimate-reviewed-by");
      const newStatus = document.getElementById("rp-edit-estimate-status")?.value || "DRAFT";
      const reviewedByCodes = (reviewedByField?.values ?? []).map((v) => v.value);

      // Guard: any status at or beyond REVIEWED requires at least one reviewer
      if (["REVIEWED", "SHARED", "APPROVED"].includes(newStatus) && !reviewedByCodes.length) {
        reviewedByField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
        toast({
          type: "warning",
          title: "Reviewed By required",
          message: "Please select at least one reviewer.",
        });
        return;
      }

      const submitBtn = editDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Saving…");

      const prevCode = pendingEstimateRow.code;
      const payload = {
        estimate_days: parseFloat(document.getElementById("rp-edit-estimate-days")?.value || "0"),
        contingency_percentage: parseFloat(
          document.getElementById("rp-edit-estimate-contingency")?.value || "0",
        ),
        status: newStatus,
        estimate_link: document.getElementById("rp-edit-estimate-link")?.value?.trim() || "",
        note: document.getElementById("rp-edit-estimate-note")?.value?.trim() || "",
        shared_by_codes: (sharedByField?.values ?? []).map((v) => v.value),
        reviewed_by_codes: reviewedByCodes,
      };

      // Guard: APPROVED requires a project code — collect it via the approve modal
      if (newStatus === "APPROVED" && !currentProject?.project_code_value) {
        restoreButton(submitBtn, snap);
        _pendingEditApprovePayload = { estimateCode: prevCode, payload };
        const approveModal = document.getElementById("rp-estimate-approve-modal");
        if (approveModal) {
          const codeField = document.getElementById("rp-estimate-approve-code-field");
          if (codeField) codeField.value = "";
          approveModal.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
            el.hidden = true;
          });
          approveModal.show();
        }
        return;
      }

      try {
        const { href, method } = API_URLS.projectEstimates.update(projectCode, prevCode);
        await apiFetch(href, { method, body: JSON.stringify(payload) });
        restoreButton(submitBtn, snap);
        editDrawer.hide();
        pendingEstimateRow = null;
        table?.refresh();
        loadEstimateVersions();
        if (picker?.value === prevCode) {
          await loadEstimateHistory(prevCode);
        }
        toast({
          type: "success",
          title: "Estimate updated",
          message: "The estimate has been saved.",
        });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to update estimate. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  const deleteModal = document.getElementById("rp-estimate-delete-modal");
  if (deleteModal) {
    deleteModal.addEventListener("rp:delete", async () => {
      if (!pendingEstimateRow) return;
      const deleteBtn = deleteModal.querySelector("[data-delete-modal]");
      deleteBtn?.setAttribute("disabled", "");

      try {
        const { href, method } = API_URLS.projectEstimates.delete(
          projectCode,
          pendingEstimateRow.code,
        );
        await apiFetch(href, { method });
        deleteModal.hide();
        const historyContainer = document.getElementById("rp-estimate-history-list");
        if (historyContainer) historyContainer.empty("Select a version to view its history.");
        if (picker) picker.value = "";
        pendingEstimateRow = null;
        table?.refresh();
        loadEstimateVersions();
        toast({
          type: "success",
          title: "Estimate deleted",
          message: "The estimate has been removed.",
        });
      } catch (err) {
        deleteBtn?.removeAttribute("disabled");
        const msg = err?.data?.error?.message ?? "Failed to delete estimate. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  initAdvanceFlow(table);
}

function actualsRiskBadge(risk) {
  if (risk === "warning")
    return { label: "Warning", cls: "rp-badge rp-badge-soft rp-badge-warning" };
  if (risk === "at_risk")
    return { label: "At Risk", cls: "rp-badge rp-badge-soft rp-badge-danger" };
  return null;
}

function budgetRiskClass(color) {
  switch (color) {
    case "GREEN":
      return "rp-badge rp-badge-success";
    case "AMBER":
      return "rp-badge rp-badge-soft rp-badge-warning";
    case "RED":
      return "rp-badge rp-badge-soft rp-badge-danger";
    default:
      return "rp-badge rp-badge-soft";
  }
}

window.renderProjectBudgetRow = function renderProjectBudgetRow(row) {
  const fyName = esc(row.financial_year?.name ?? "");
  const allocated = esc(formatCurrency(parseFloat(row.allocated_budget ?? 0)));
  const refined =
    row.refined_budget != null ? esc(formatCurrency(parseFloat(row.refined_budget))) : "—";
  const estimateCost =
    row.estimate_version?.total_cost != null
      ? esc(formatCurrency(row.estimate_version.total_cost))
      : "—";
  const remaining = row.remaining_budget != null ? esc(formatCurrency(row.remaining_budget)) : "—";
  const riskPct = esc(row.risk?.percentage ?? "—");
  const riskShort = esc(row.risk?.short ?? "—");
  const riskClass = budgetRiskClass(row.risk?.color);
  return (
    `<td>${fyName}</td>` +
    `<td class="text-end">${allocated}</td>` +
    `<td class="text-end">${refined}</td>` +
    `<td class="text-end">${estimateCost}</td>` +
    `<td class="text-end">${remaining}</td>` +
    `<td class="text-end rp-fs-12">${riskPct}</td>` +
    `<td><span class="${riskClass}">${riskShort}</span></td>`
  );
};

window.renderActualsByFyRow = function renderActualsByFyRow(row) {
  return (
    `<td>${esc(row.fy ?? "—")}</td>` +
    `<td class="text-end">${(+row.total_days || 0).toFixed(2)}</td>` +
    `<td class="text-end">${formatCurrency(row.total_cost ?? 0)}</td>` +
    `<td class="text-end">${formatCurrency(row.cumulative_cost ?? 0)}</td>`
  );
};

window.renderActualsBySprintRow = function renderActualsBySprintRow(row) {
  return (
    `<td>${esc(row.sprint ?? "—")}</td>` +
    `<td class="text-end">${(+row.total_days || 0).toFixed(2)}</td>` +
    `<td class="text-end">${formatCurrency(row.total_cost ?? 0)}</td>` +
    `<td class="text-end">${formatCurrency(row.cumulative_cost ?? 0)}</td>`
  );
};

async function loadActualsSummary() {
  try {
    const { href, method } = API_URLS.projectActuals.summary(projectCode);
    const resp = await apiFetch(href, { method });
    const d = resp?.data ?? {};

    const estimateEl = document.getElementById("rp-actuals-estimate-cost");
    const estimateContEl = document.getElementById("rp-actuals-estimate-cost-contingency");
    const totalEl = document.getElementById("rp-actuals-total");
    const remainingEl = document.getElementById("rp-actuals-remaining");
    const riskBadge = document.getElementById("rp-actuals-risk-badge");

    if (estimateEl) estimateEl.textContent = formatCurrency(d.estimate_cost ?? 0);
    if (estimateContEl)
      estimateContEl.textContent = formatCurrency(d.estimate_cost_with_contingency ?? 0);
    if (totalEl) totalEl.textContent = formatCurrency(d.total_actuals ?? 0);
    if (remainingEl)
      remainingEl.textContent =
        d.remaining_amount != null ? formatCurrency(d.remaining_amount) : "—";
    if (riskBadge) {
      const badge = actualsRiskBadge(d.risk);
      if (badge) {
        riskBadge.textContent = badge.label;
        riskBadge.className = badge.cls;
        riskBadge.hidden = false;
      } else {
        riskBadge.hidden = true;
      }
    }
  } catch {
    // non-fatal
  }
}

let actualsLoaded = false;

function initActualsTab() {
  const fyTable = document.getElementById("rp-actuals-by-fy-table");
  const sprintTable = document.getElementById("rp-actuals-by-sprint-table");
  const fyPicker = document.getElementById("rp-actuals-fy-picker");
  const baseUrl = API_URLS.projectActuals.list(projectCode).href;

  const activateTab = () => {
    loadActualsSummary();
    if (!actualsLoaded) {
      actualsLoaded = true;
      if (fyTable) {
        fyTable.setAttribute("url", baseUrl);
        fyTable.removeAttribute("hidden");
      }
    } else {
      const fyCode = fyPicker?.value;
      if (fyCode) {
        sprintTable?.refresh();
      } else {
        fyTable?.refresh();
      }
    }
  };

  const tabPanel = document.querySelector("tab-panel");
  if (tabPanel) {
    if (tabPanel.activeTab === "actuals") activateTab();
    tabPanel.addEventListener("rp:tab-change", (e) => {
      if (e.detail.tab === "actuals") activateTab();
    });
  }

  if (fyPicker) {
    fyPicker.addEventListener("change", () => {
      const fyCode = fyPicker.value;
      if (fyCode) {
        if (fyTable) fyTable.setAttribute("hidden", "");
        if (sprintTable) {
          sprintTable.removeAttribute("hidden");
          const url = `${baseUrl}?fy=${encodeURIComponent(fyCode)}`;
          if (sprintTable.getAttribute("url") === url) {
            sprintTable.refresh();
          } else {
            sprintTable.setAttribute("url", url);
          }
        }
      } else {
        if (sprintTable) sprintTable.setAttribute("hidden", "");
        if (fyTable) {
          fyTable.removeAttribute("hidden");
          fyTable.refresh();
        }
      }
    });
  }

  initActualsConfig();
}

function initActualsConfig() {
  const configBtn = document.getElementById("rp-actuals-config-btn");
  const drawer = document.getElementById("rp-actuals-config-drawer");
  if (!configBtn || !drawer) return;

  const ignoreRiskField = document.getElementById("rp-actuals-config-ignore-risk");
  const ignorePrevFyField = document.getElementById("rp-actuals-config-ignore-prev-fy");
  const notesField = document.getElementById("rp-actuals-config-notes");

  configBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const { href, method } = API_URLS.projectActuals.config(projectCode);
      const resp = await apiFetch(href, { method });
      const d = resp?.data ?? {};
      if (ignoreRiskField) ignoreRiskField.checked = d.ignore_risk ?? false;
      if (ignorePrevFyField) ignorePrevFyField.checked = d.ignore_prev_fy_actuals ?? false;
      if (notesField) notesField.value = d.notes ?? "";
    } catch {
      if (ignoreRiskField) ignoreRiskField.checked = false;
      if (ignorePrevFyField) ignorePrevFyField.checked = false;
      if (notesField) notesField.value = "";
    }
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");
    try {
      const { href, method } = API_URLS.projectActuals.updateConfig(projectCode);
      await apiFetch(href, {
        method,
        body: JSON.stringify({
          ignore_risk: ignoreRiskField?.checked ?? false,
          ignore_prev_fy_actuals: ignorePrevFyField?.checked ?? false,
          notes: notesField?.value ?? "",
        }),
      });
      restoreButton(submitBtn, snap);
      drawer.hide();
      toast({ type: "success", title: "Saved", message: "Actuals configuration updated." });
      loadActualsSummary();
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to save configuration.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

async function loadBudgetLifetime() {
  try {
    const { href, method } = API_URLS.projectBudgets.lifetime(projectCode);
    const resp = await apiFetch(href, { method });
    const d = resp?.data ?? {};

    const allocatedEl = document.getElementById("rp-budget-lifetime-allocated-val");
    const estimateEl = document.getElementById("rp-budget-lifetime-estimate-val");
    const remainingEl = document.getElementById("rp-budget-lifetime-remaining-val");
    const riskBadge = document.getElementById("rp-budget-lifetime-risk-badge");

    if (allocatedEl) allocatedEl.textContent = formatCurrency(d.total_actual_budget ?? 0);
    if (estimateEl)
      estimateEl.textContent =
        d.total_estimate_cost != null ? formatCurrency(d.total_estimate_cost) : "—";
    if (remainingEl)
      remainingEl.textContent =
        d.total_remaining_budget != null ? formatCurrency(d.total_remaining_budget) : "—";

    if (riskBadge) {
      if (d.risk) {
        riskBadge.textContent = d.risk.short ?? "—";
        riskBadge.className = budgetRiskClass(d.risk.color);
        riskBadge.hidden = false;
      } else {
        riskBadge.hidden = true;
      }
    }
  } catch {
    // ignore
  }
}

async function loadBudgetHistory(budgetCode) {
  const container = document.getElementById("rp-budget-history-list");
  if (!container) return;

  if (!budgetCode) {
    container.empty("Select a financial year to view its history.");
    return;
  }

  container.loading();

  const actionIcons = {
    CREATED: "bi-plus-circle-fill",
    UPDATED: "bi-pencil-fill",
  };
  const actionIconColors = {
    CREATED: "accent",
    UPDATED: "muted",
  };

  try {
    const { href, method } = API_URLS.projectBudgets.history(projectCode, budgetCode);
    const resp = await apiFetch(href, { method });
    const rows = resp?.data ?? [];

    if (!rows.length) {
      container.empty("No history available.");
      return;
    }

    const items = rows.map((row, idx) => {
      const isLast = idx === rows.length - 1;
      const dateStr = row.changed_on ? formatDate(row.changed_on) : "";
      const byStr = row.changed_by?.email ? ` · ${row.changed_by.email}` : "";

      const parts = [];
      if (row.action === "CREATED") {
        if (row.new_allocated_budget != null)
          parts.push(`Allocated: ${formatCurrency(parseFloat(row.new_allocated_budget))}`);
        if (row.new_refined_budget != null)
          parts.push(`Refined: ${formatCurrency(parseFloat(row.new_refined_budget))}`);
        if (row.new_estimate_version)
          parts.push(`Estimate: ${row.new_estimate_version.version_display}`);
      } else {
        const pa =
          row.previous_allocated_budget != null
            ? formatCurrency(parseFloat(row.previous_allocated_budget))
            : "—";
        const na =
          row.new_allocated_budget != null
            ? formatCurrency(parseFloat(row.new_allocated_budget))
            : "—";
        if (pa !== na) parts.push(`Allocated: ${pa} → ${na}`);

        const pr =
          row.previous_refined_budget != null
            ? formatCurrency(parseFloat(row.previous_refined_budget))
            : "—";
        const nr =
          row.new_refined_budget != null ? formatCurrency(parseFloat(row.new_refined_budget)) : "—";
        if (pr !== nr) parts.push(`Refined: ${pr} → ${nr}`);

        const pe = row.previous_estimate_version?.version_display ?? "—";
        const ne = row.new_estimate_version?.version_display ?? "—";
        if (pe !== ne) parts.push(`Estimate: ${pe} → ${ne}`);
      }

      const item = document.createElement("history-item");
      item.setAttribute("label", row.action.charAt(0) + row.action.slice(1).toLowerCase());
      item.setAttribute("icon", actionIcons[row.action] ?? "bi-circle-fill");
      item.setAttribute("icon-color", actionIconColors[row.action] ?? "muted");
      if (parts.length) item.setAttribute("status", parts.join(" · "));
      if (row.note) item.setAttribute("note", row.note);
      item.setAttribute("meta", dateStr + byStr);
      if (!isLast) item.setAttribute("connector", "");
      return item;
    });

    container.setItems(items);
  } catch {
    container.error();
  }
}

async function loadBudgetEstimateOptions(targetPickerId) {
  const picker = document.getElementById(targetPickerId);
  if (!picker) return;
  try {
    const { href, method } = API_URLS.projectEstimates.list(projectCode);
    const resp = await apiFetch(`${href}?page_size=100`, { method });
    const rows = resp?.data?.results ?? [];
    picker._initialOptions = [
      { id: "", label: "— None —", value: "", selected: false, disabled: false },
      ...rows.map((est) => ({
        id: "",
        label: `${est.version_display} (${formatCurrency(est.total_cost ?? 0)})`,
        value: est.code,
        selected: false,
        disabled: false,
      })),
    ];
    picker._doRender();
  } catch {
    // ignore
  }
}

function openEditBudgetDrawer(row) {
  const drawer = document.getElementById("rp-budget-edit-drawer");
  if (!drawer) return;
  pendingBudgetRow = row;
  drawer.setTitle(row.financial_year?.name ?? "Edit Budget");

  const allocField = document.getElementById("rp-edit-budget-allocated");
  const refinedField = document.getElementById("rp-edit-budget-refined");
  const noteField = document.getElementById("rp-edit-budget-note");

  if (allocField) allocField.value = row.allocated_budget ?? "";
  if (refinedField) refinedField.value = row.refined_budget ?? "";
  if (noteField) noteField.value = "";

  drawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
    el.hidden = true;
  });

  loadBudgetEstimateOptions("rp-edit-budget-estimate").then(() => {
    const estimatePicker = document.getElementById("rp-edit-budget-estimate");
    if (estimatePicker && row.estimate_version?.code) {
      estimatePicker.value = row.estimate_version.code;
    } else if (estimatePicker) {
      estimatePicker.value = "";
    }
  });

  drawer.show();
}

function initBudgetsTab() {
  const table = document.getElementById("rp-budgets-table");
  const baseUrl = API_URLS.projectBudgets.list(projectCode).href;

  const activateTab = () => {
    if (!budgetsLoaded) {
      budgetsLoaded = true;
      if (table) table.setAttribute("url", baseUrl);
    } else {
      table?.refresh();
    }
    loadBudgetLifetime();
  };

  const tabPanel = document.querySelector("tab-panel");
  if (tabPanel) {
    if (tabPanel.activeTab === "budgets") activateTab();
    tabPanel.addEventListener("rp:tab-change", (e) => {
      if (e.detail.tab === "budgets") activateTab();
    });
  }

  if (table) {
    table.addEventListener("rp:data:loaded", (e) => {
      loadedBudgets = e.detail.rows ?? [];
      const fyPicker = document.getElementById("rp-budget-fy-picker");
      if (fyPicker) {
        fyPicker._initialOptions = [
          { id: "", label: "— Select a year —", value: "", selected: false, disabled: false },
          ...loadedBudgets.map((b) => ({
            id: b.financial_year?.code ?? "",
            label: b.financial_year?.name ?? "",
            value: b.financial_year?.code ?? "",
            selected: false,
            disabled: false,
          })),
        ];
        if (typeof fyPicker._doRender === "function") fyPicker._doRender();
        fyPicker.value = "";
      }
    });

    table.addEventListener("rp:budget:edit", (e) => openEditBudgetDrawer(e.detail.row));

    table.addEventListener("rp:budget:delete", (e) => {
      pendingBudgetRow = e.detail.row;
      const modal = document.getElementById("rp-budget-delete-modal");
      if (!modal) return;
      const fyName = pendingBudgetRow.financial_year?.name ?? "this budget";
      modal.setAttribute("title", `Delete budget for ${fyName}?`);
      modal.setAttribute("body", "This will permanently remove this budget and all its history.");
      modal.setAttribute("confirm-value", fyName);
      modal.show();
    });
  }

  const fyPicker = document.getElementById("rp-budget-fy-picker");
  if (fyPicker) {
    fyPicker.addEventListener("change", () => {
      const fyCode = fyPicker.value;
      if (!fyCode) {
        loadBudgetHistory(null);
        return;
      }
      const budget = loadedBudgets.find((b) => b.financial_year?.code === fyCode);
      loadBudgetHistory(budget?.code ?? null);
    });
  }

  const createBtn = document.getElementById("rp-budget-create-btn");
  const createDrawer = document.getElementById("rp-budget-create-drawer");
  if (createBtn && createDrawer) {
    createBtn.addEventListener("click", () => {
      ["rp-new-budget-allocated", "rp-new-budget-refined", "rp-new-budget-note"].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.value = "";
      });
      const fyField = document.getElementById("rp-new-budget-fy");
      if (fyField) fyField.value = "";
      createDrawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
        el.hidden = true;
      });
      loadBudgetEstimateOptions("rp-new-budget-estimate");
      createDrawer.show();
    });

    createDrawer.addEventListener("rp:footer-primary", async () => {
      const fyField = document.getElementById("rp-new-budget-fy");
      const allocField = document.getElementById("rp-new-budget-allocated");
      [fyField, allocField].forEach((f) =>
        f?.dispatchEvent(new Event("rp:validate", { bubbles: false })),
      );
      if (createDrawer.querySelector("[data-rp-error]:not([hidden])")) return;

      const fyCode = fyField?.value?.trim() ?? "";
      const allocated = allocField?.value?.trim() ?? "";
      if (!fyCode || !allocated) return;

      const submitBtn = createDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Creating…");

      const payload = {
        financial_year_code: fyCode,
        allocated_budget: parseFloat(allocated),
        refined_budget: document.getElementById("rp-new-budget-refined")?.value?.trim() || null,
        estimate_version_code:
          document.getElementById("rp-new-budget-estimate")?.value?.trim() || null,
        note: document.getElementById("rp-new-budget-note")?.value?.trim() || "",
      };

      try {
        const { href, method } = API_URLS.projectBudgets.create(projectCode);
        await apiFetch(href, { method, body: JSON.stringify(payload) });
        restoreButton(submitBtn, snap);
        createDrawer.hide();
        table?.refresh();
        loadBudgetLifetime();
        toast({
          type: "success",
          title: "Budget added",
          message: "The budget has been created successfully.",
        });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.message ?? "Failed to create budget. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  const editDrawer = document.getElementById("rp-budget-edit-drawer");
  if (editDrawer) {
    editDrawer.addEventListener("rp:footer-primary", async () => {
      if (!pendingBudgetRow) return;

      const allocField = document.getElementById("rp-edit-budget-allocated");
      if (allocField) allocField.dispatchEvent(new Event("rp:validate", { bubbles: false }));
      if (editDrawer.querySelector("[data-rp-error]:not([hidden])")) return;

      const submitBtn = editDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Saving…");

      const payload = {
        allocated_budget: parseFloat(allocField?.value ?? "0"),
        refined_budget: document.getElementById("rp-edit-budget-refined")?.value?.trim() || null,
        estimate_version_code:
          document.getElementById("rp-edit-budget-estimate")?.value?.trim() || null,
        note: document.getElementById("rp-edit-budget-note")?.value?.trim() || "",
      };

      try {
        const { href, method } = API_URLS.projectBudgets.update(projectCode, pendingBudgetRow.code);
        await apiFetch(href, { method, body: JSON.stringify(payload) });
        restoreButton(submitBtn, snap);
        editDrawer.hide();
        pendingBudgetRow = null;
        table?.refresh();
        loadBudgetLifetime();
        toast({ type: "success", title: "Budget updated", message: "Changes have been saved." });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.message ?? "Failed to update budget. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  const deleteModal = document.getElementById("rp-budget-delete-modal");
  if (deleteModal) {
    deleteModal.addEventListener("rp:delete", async () => {
      if (!pendingBudgetRow) return;
      const deleteBtn = deleteModal.querySelector("[data-delete-modal]");
      deleteBtn?.setAttribute("disabled", "");
      try {
        const { href, method } = API_URLS.projectBudgets.delete(projectCode, pendingBudgetRow.code);
        await apiFetch(href, { method });
        deleteModal.hide();
        const fyName = pendingBudgetRow.financial_year?.name ?? "Budget";
        pendingBudgetRow = null;
        table?.refresh();
        loadBudgetLifetime();
        toast({
          type: "success",
          title: "Budget deleted",
          message: `Budget for "${fyName}" has been removed.`,
        });
      } catch (err) {
        deleteBtn?.removeAttribute("disabled");
        const msg = err?.data?.message ?? "Failed to delete budget. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }
}

window.renderProjectLinkRow = function renderProjectLinkRow(row) {
  const urlDisplay = row.url ? row.url : "—";
  return (
    `<td>${esc(row.title ?? "")}</td>` +
    `<td><a href="${esc(row.url ?? "")}" target="_blank" rel="noopener noreferrer" class="rp-link">${esc(urlDisplay)}</a></td>`
  );
};

function initLinksTab() {
  const table = document.getElementById("rp-links-table");
  const baseUrl = API_URLS.projectLinks.list(projectCode).href;

  const activateTab = () => {
    if (!linksLoaded) {
      linksLoaded = true;
      if (table) table.setAttribute("url", baseUrl);
    } else {
      table?.refresh();
    }
  };

  const tabPanel = document.querySelector("tab-panel");
  if (tabPanel) {
    if (tabPanel.activeTab === "links") {
      activateTab();
    }
    tabPanel.addEventListener("rp:tab-change", (e) => {
      if (e.detail.tab === "links") activateTab();
    });
  }

  const createBtn = document.getElementById("rp-link-create-btn");
  const createDrawer = document.getElementById("rp-link-create-drawer");
  if (createBtn && createDrawer) {
    createBtn.addEventListener("click", () => {
      const titleField = document.getElementById("rp-new-link-title");
      const urlField = document.getElementById("rp-new-link-url");
      if (titleField) titleField.value = "";
      if (urlField) urlField.value = "";
      createDrawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
        el.hidden = true;
      });
      createDrawer.show();
    });

    createDrawer.addEventListener("rp:footer-primary", async () => {
      const titleField = document.getElementById("rp-new-link-title");
      const urlField = document.getElementById("rp-new-link-url");

      [titleField, urlField].forEach((f) =>
        f?.dispatchEvent(new Event("rp:validate", { bubbles: false })),
      );
      if (createDrawer.querySelector("[data-rp-error]:not([hidden])")) return;

      const title = titleField?.value?.trim() ?? "";
      const url = urlField?.value?.trim() ?? "";
      if (!title || !url) return;

      const submitBtn = createDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Adding…");

      try {
        const { href, method } = API_URLS.projectLinks.create(projectCode);
        await apiFetch(href, { method, body: JSON.stringify({ title, url }) });
        restoreButton(submitBtn, snap);
        createDrawer.hide();
        table?.refresh();
        toast({ type: "success", title: "Link added", message: `"${title}" has been added.` });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to add link. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  const editDrawer = document.getElementById("rp-link-edit-drawer");
  if (table && editDrawer) {
    table.addEventListener("rp:link:edit", (e) => {
      pendingLinkRow = e.detail.row;
      const titleField = document.getElementById("rp-edit-link-title");
      const urlField = document.getElementById("rp-edit-link-url");
      if (titleField) titleField.value = pendingLinkRow.title ?? "";
      if (urlField) urlField.value = pendingLinkRow.url ?? "";
      editDrawer.setTitle(pendingLinkRow.title ?? "Edit Link");
      editDrawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
        el.hidden = true;
      });
      editDrawer.show();
    });

    editDrawer.addEventListener("rp:footer-primary", async () => {
      if (!pendingLinkRow) return;

      const titleField = document.getElementById("rp-edit-link-title");
      const urlField = document.getElementById("rp-edit-link-url");

      [titleField, urlField].forEach((f) =>
        f?.dispatchEvent(new Event("rp:validate", { bubbles: false })),
      );
      if (editDrawer.querySelector("[data-rp-error]:not([hidden])")) return;

      const title = titleField?.value?.trim() ?? "";
      const url = urlField?.value?.trim() ?? "";
      if (!title || !url) return;

      const submitBtn = editDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Saving…");

      try {
        const { href, method } = API_URLS.projectLinks.update(projectCode, pendingLinkRow.code);
        await apiFetch(href, { method, body: JSON.stringify({ title, url }) });
        restoreButton(submitBtn, snap);
        editDrawer.hide();
        pendingLinkRow = null;
        table.refresh();
        toast({ type: "success", title: "Link updated", message: `"${title}" has been saved.` });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to update link. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  const deleteModal = document.getElementById("rp-link-delete-modal");
  if (table && deleteModal) {
    table.addEventListener("rp:link:delete", (e) => {
      pendingLinkRow = e.detail.row;
      deleteModal.setAttribute("title", `Delete "${pendingLinkRow.title}"?`);
      deleteModal.setAttribute(
        "body",
        "This will permanently remove this link and cannot be undone.",
      );
      deleteModal.setAttribute("confirm-value", pendingLinkRow.title);
      deleteModal.show();
    });

    deleteModal.addEventListener("rp:delete", async () => {
      if (!pendingLinkRow) return;
      const deleteBtn = deleteModal.querySelector("[data-delete-modal]");
      deleteBtn?.setAttribute("disabled", "");

      try {
        const { href, method } = API_URLS.projectLinks.delete(projectCode, pendingLinkRow.code);
        await apiFetch(href, { method });
        deleteModal.hide();
        const title = pendingLinkRow.title;
        pendingLinkRow = null;
        table?.refresh();
        toast({ type: "success", title: "Link deleted", message: `"${title}" has been removed.` });
      } catch (err) {
        deleteBtn?.removeAttribute("disabled");
        const msg = err?.data?.error?.message ?? "Failed to delete link. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }
}

function getFileIcon(contentType) {
  const ct = (contentType || "").toLowerCase();
  if (ct === "application/pdf") return "bi-file-pdf";
  if (ct.includes("spreadsheet") || ct.includes("excel") || ct === "text/csv")
    return "bi-file-earmark-spreadsheet";
  if (ct.includes("wordprocessing") || ct.includes("word") || ct.includes("msword"))
    return "bi-file-earmark-word";
  if (ct.includes("presentation") || ct.includes("powerpoint")) return "bi-file-earmark-slides";
  if (ct.startsWith("image/")) return "bi-file-earmark-image";
  if (ct.startsWith("video/")) return "bi-file-earmark-play";
  if (ct.startsWith("audio/")) return "bi-file-earmark-music";
  if (ct.includes("zip") || ct.includes("compressed") || ct.includes("tar") || ct.includes("gzip"))
    return "bi-file-earmark-zip";
  if (ct.startsWith("text/")) return "bi-file-earmark-text";
  return "bi-file-earmark";
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
}

window.renderProjectAttachmentRow = function renderProjectAttachmentRow(row) {
  const icon = getFileIcon(row.content_type);
  const uploadedBy = row.created_by
    ? esc(
        `${row.created_by.first_name ?? ""} ${row.created_by.last_name ?? ""}`.trim() ||
          row.created_by.email ||
          "",
      )
    : "—";
  return (
    `<td style="width:36px;"><i class="bi ${esc(icon)}" style="font-size:1.1rem;opacity:0.75;"></i></td>` +
    `<td>${esc(row.file_name ?? "")}</td>` +
    `<td>${esc(row.content_type || "—")}</td>` +
    `<td>${esc(formatFileSize(row.file_size))}</td>` +
    `<td>${uploadedBy}</td>`
  );
};

function initAttachmentsTab() {
  const table = document.getElementById("rp-attachments-table");
  const baseUrl = API_URLS.projectAttachments.list(projectCode).href;

  const activateTab = () => {
    if (!attachmentsLoaded) {
      attachmentsLoaded = true;
      if (table) table.setAttribute("url", baseUrl);
    } else {
      table?.refresh();
    }
  };

  const tabPanel = document.querySelector("tab-panel");
  if (tabPanel) {
    if (tabPanel.activeTab === "attachments") {
      activateTab();
    }
    tabPanel.addEventListener("rp:tab-change", (e) => {
      if (e.detail.tab === "attachments") activateTab();
    });
  }

  const uploadField = document.getElementById("rp-attachment-upload");
  if (uploadField) {
    uploadField.addEventListener("rp:change", async (e) => {
      const files = e.detail?.files;
      if (!files || files.length === 0) return;

      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);
        const uploadUrl = API_URLS.projectAttachments.upload(projectCode).href;
        try {
          await fetch(uploadUrl, {
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
            body: formData,
          }).then(async (res) => {
            if (!res.ok) {
              const body = await res.json().catch(() => ({}));
              throw body;
            }
            return res.json();
          });
          toast({
            type: "success",
            title: "Uploaded",
            message: `"${file.name}" has been attached.`,
          });
        } catch (err) {
          const msg = err?.message ?? `Failed to upload "${file.name}". Please try again.`;
          toast({ type: "error", title: "Upload failed", message: msg });
        }
      }
      uploadField.clear?.();
      table?.refresh();
    });
  }

  if (table) {
    table.addEventListener("rp:attachment:download", (e) => {
      const row = e.detail.row;
      const href = API_URLS.projectAttachments.download(projectCode, row.code);
      window.open(href, "_blank");
    });
  }

  const deleteModal = document.getElementById("rp-attachment-delete-modal");
  if (table && deleteModal) {
    table.addEventListener("rp:attachment:delete", (e) => {
      pendingAttachmentRow = e.detail.row;
      deleteModal.setAttribute("title", `Delete "${pendingAttachmentRow.file_name}"?`);
      deleteModal.setAttribute(
        "body",
        "This will permanently remove this attachment and cannot be undone.",
      );
      deleteModal.setAttribute("confirm-value", pendingAttachmentRow.file_name);
      deleteModal.show();
    });

    deleteModal.addEventListener("rp:delete", async () => {
      if (!pendingAttachmentRow) return;
      const deleteBtn = deleteModal.querySelector("[data-delete-modal]");
      deleteBtn?.setAttribute("disabled", "");

      try {
        const { href, method } = API_URLS.projectAttachments.delete(
          projectCode,
          pendingAttachmentRow.code,
        );
        await apiFetch(href, { method });
        deleteModal.hide();
        const name = pendingAttachmentRow.file_name;
        pendingAttachmentRow = null;
        table?.refresh();
        toast({
          type: "success",
          title: "Attachment deleted",
          message: `"${name}" has been removed.`,
        });
      } catch (err) {
        deleteBtn?.removeAttribute("disabled");
        const msg = err?.data?.message ?? "Failed to delete attachment. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }
}

window.renderProjectContactRow = function renderProjectContactRow(row) {
  return (
    `<td>${esc(row.contact_name ?? "")}</td>` +
    `<td class="rp-hide-mobile">${esc(row.contact_email || "—")}</td>` +
    `<td>${esc(row.role_display ?? row.role ?? "")}</td>`
  );
};

function initContactsSection() {
  const table = document.getElementById("rp-project-contacts-table");
  const tabPanel = document.querySelector("tab-panel");

  const activateContacts = () => {
    if (!contactsLoaded) {
      contactsLoaded = true;
      if (table) table.setAttribute("url", API_URLS.projectContacts.list(projectCode).href);
    } else {
      table?.refresh();
    }
  };

  if (tabPanel) {
    if (tabPanel.activeTab === "operational") activateContacts();
    tabPanel.addEventListener("rp:tab-change", (e) => {
      if (e.detail.tab === "operational") activateContacts();
    });
  }

  const addBtn = document.getElementById("rp-project-contact-add-btn");
  const createDrawer = document.getElementById("rp-project-contact-create-drawer");
  if (addBtn && createDrawer) {
    addBtn.addEventListener("click", () => {
      const nameField = document.getElementById("rp-new-contact-name");
      const emailField = document.getElementById("rp-new-contact-email");
      const roleField = document.getElementById("rp-new-contact-role");
      if (nameField) nameField.value = "";
      if (emailField) emailField.value = "";
      if (roleField) roleField.value = "";
      createDrawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
        el.hidden = true;
      });
      createDrawer.show();
    });

    createDrawer.addEventListener("rp:footer-primary", async () => {
      const nameField = document.getElementById("rp-new-contact-name");
      const emailField = document.getElementById("rp-new-contact-email");
      const roleField = document.getElementById("rp-new-contact-role");

      [nameField, roleField].forEach((f) =>
        f?.dispatchEvent(new Event("rp:validate", { bubbles: false })),
      );
      if (createDrawer.querySelector("[data-rp-error]:not([hidden])")) return;

      const name = nameField?.value?.trim() ?? "";
      const email = emailField?.value?.trim() ?? "";
      const role = roleField?.value ?? "";
      if (!name || !role) return;

      const submitBtn = createDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Adding…");

      try {
        const { href, method } = API_URLS.projectContacts.create(projectCode);
        await apiFetch(href, { method, body: JSON.stringify({ name, email, role }) });
        restoreButton(submitBtn, snap);
        createDrawer.hide();
        table?.refresh();
        toast({ type: "success", title: "Contact added", message: `"${name}" has been added.` });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to add contact. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  const deleteModal = document.getElementById("rp-project-contact-delete-modal");
  if (table && deleteModal) {
    table.addEventListener("rp:contact:delete", (e) => {
      pendingContactRow = e.detail.row;
      deleteModal.setAttribute("title", `Remove "${pendingContactRow.contact_name}"?`);
      deleteModal.setAttribute(
        "body",
        "This will remove the contact from this project. The contact record will be preserved.",
      );
      deleteModal.setAttribute("confirm-value", pendingContactRow.contact_name);
      deleteModal.show();
    });

    deleteModal.addEventListener("rp:delete", async () => {
      if (!pendingContactRow) return;
      const deleteBtn = deleteModal.querySelector("[data-delete-modal]");
      deleteBtn?.setAttribute("disabled", "");

      try {
        const { href, method } = API_URLS.projectContacts.delete(
          projectCode,
          pendingContactRow.code,
        );
        await apiFetch(href, { method });
        deleteModal.hide();
        const name = pendingContactRow.contact_name;
        pendingContactRow = null;
        table?.refresh();
        toast({
          type: "success",
          title: "Contact removed",
          message: `"${name}" has been removed.`,
        });
      } catch (err) {
        deleteBtn?.removeAttribute("disabled");
        const msg = err?.data?.error?.message ?? "Failed to remove contact. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!projectCode || !document.getElementById("rp-project-tabs")) return;
  loadProjectDetails();
  loadProjectTags();
  loadProjectLabels();
  initFollowButton();
  initEditButton();
  initEditDrawer();
  initTagsSaveButton();
  initAddLabelModal();
  initContactsSection();
  initEstimatesTab();
  initBudgetsTab();
  initActualsTab();
  initLinksTab();
  initAttachmentsTab();
});
