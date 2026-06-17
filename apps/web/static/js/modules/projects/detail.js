"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatCurrency,
  formatDate,
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
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:open", () => {
    document.getElementById("rp-edit-project-type")?.refresh?.();
    document.getElementById("rp-edit-project-programme")?.refresh?.();
    document.getElementById("rp-edit-project-status")?.refresh?.();
  });

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

function openEditEstimateDrawer(est) {
  const drawer = document.getElementById("rp-estimate-edit-drawer");
  if (!drawer) return;
  pendingEstimateRow = est;
  drawer.setTitle(est.version_display ?? "Estimate");
  const daysField = document.getElementById("rp-edit-estimate-days");
  const contingencyField = document.getElementById("rp-edit-estimate-contingency");
  const dayRateField = document.getElementById("rp-edit-estimate-day-rate");
  const statusField = document.getElementById("rp-edit-estimate-status");
  const linkField = document.getElementById("rp-edit-estimate-link");
  const noteField = document.getElementById("rp-edit-estimate-note");
  if (daysField) daysField.value = String(est.estimate_days ?? "");
  if (contingencyField) contingencyField.value = String(est.contingency_percentage ?? "");
  if (dayRateField) dayRateField.value = String(est.day_rate ?? "");
  if (statusField) statusField.value = est.status ?? "DRAFT";
  if (linkField) linkField.value = est.estimate_link ?? "";
  if (noteField) noteField.value = "";
  drawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
    el.hidden = true;
  });
  drawer.show();
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
        const emailBtn = tr.querySelector('[data-rp-action="rp:estimate:email"]');
        if (emailBtn) emailBtn.hidden = !row || row.status !== "DRAFT";
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
      const submitBtn = editDrawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Saving…");

      const prevCode = pendingEstimateRow.code;
      const payload = {
        estimate_days: parseFloat(document.getElementById("rp-edit-estimate-days")?.value || "0"),
        contingency_percentage: parseFloat(
          document.getElementById("rp-edit-estimate-contingency")?.value || "0",
        ),
        day_rate: parseInt(document.getElementById("rp-edit-estimate-day-rate")?.value || "0", 10),
        status: document.getElementById("rp-edit-estimate-status")?.value || "DRAFT",
        estimate_link: document.getElementById("rp-edit-estimate-link")?.value?.trim() || "",
        note: document.getElementById("rp-edit-estimate-note")?.value?.trim() || "",
      };

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
}

document.addEventListener("DOMContentLoaded", () => {
  if (!projectCode) return;
  loadProjectDetails();
  loadProjectTags();
  loadProjectLabels();
  initFollowButton();
  initEditButton();
  initEditDrawer();
  initTagsSaveButton();
  initAddLabelModal();
  initEstimatesTab();
});
