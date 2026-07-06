"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

// ---- Shared state ----
let planCode = "";
let versionNumber = 0;
let snapshotCode = "";

// ---- Row renderer ----

window.renderSnapshotAllocationRow = function renderSnapshotAllocationRow(row) {
  return `
    <td>${esc(row.sprint_name)}</td>
    <td>${esc(row.member_name)}</td>
    <td>${esc(row.team_name)}</td>
    <td>${esc(row.project_name)}</td>
    <td>${esc(row.assignment_type_display)}</td>
    <td>${esc(row.days)}d</td>
  `;
};

// ---- Filter option HTML builders ----

function optionsHtml(options, valueKey, labelKey) {
  return options
    .map((opt) => `<value value="${esc(opt[valueKey])}">${esc(opt[labelKey])}</value>`)
    .join("");
}

function stringOptionsHtml(values) {
  return values.map((v) => `<value value="${esc(v)}">${esc(v)}</value>`).join("");
}

// ---- Build page ----

function buildPage(options) {
  const container = document.getElementById("rp-snapshot-allocations-container");
  if (!container) return;

  const sprintOptions = optionsHtml(options.sprints ?? [], "value", "label");
  const memberOptions = stringOptionsHtml(options.members ?? []);
  const teamOptions = stringOptionsHtml(options.teams ?? []);
  const projectOptions = stringOptionsHtml(options.projects ?? []);
  const typeOptions = optionsHtml(options.types ?? [], "value", "label");

  container.innerHTML = `
    <list-view show-active-filters>
    <filter-panel id="rp-snapshot-allocations-filter-panel">
      <dropdown-field id="rp-snapshot-allocations-sprint" name="sprint" label="Sprint" show-label>
        <values-list>
          <value value="">All Sprints</value>
          ${sprintOptions}
        </values-list>
      </dropdown-field>
      <dropdown-field id="rp-snapshot-allocations-member" name="member" label="Member" show-label>
        <values-list>
          <value value="">All Members</value>
          ${memberOptions}
        </values-list>
      </dropdown-field>
      <dropdown-field id="rp-snapshot-allocations-team" name="team" label="Team" show-label>
        <values-list>
          <value value="">All Teams</value>
          ${teamOptions}
        </values-list>
      </dropdown-field>
      <dropdown-field id="rp-snapshot-allocations-project" name="project" label="Project" show-label>
        <values-list>
          <value value="">All Projects</value>
          ${projectOptions}
        </values-list>
      </dropdown-field>
      <dropdown-field id="rp-snapshot-allocations-type" name="type" label="Type" show-label>
        <values-list>
          <value value="">All Types</value>
          ${typeOptions}
        </values-list>
      </dropdown-field>
    </filter-panel>
    <data-table id="rp-snapshot-allocations-table" url="${API_URLS.resourcePlans.snapshotAllocations(planCode, versionNumber, snapshotCode).href}" paginated page-size="25" row-template="renderSnapshotAllocationRow" empty-message="No allocations captured in this snapshot.">
      <table-columns>
        <table-column label="Sprint" key="sprint_name"></table-column>
        <table-column label="Member" key="member_name"></table-column>
        <table-column label="Team" key="team_name"></table-column>
        <table-column label="Project" key="project_name"></table-column>
        <table-column label="Type" key="assignment_type_display"></table-column>
        <table-column label="Days" key="days" numeric></table-column>
      </table-columns>
    </data-table>
    </list-view>
  `;
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", async () => {
  const planCodeField = document.getElementById("rp-snapshot-allocations-plan-code");
  const versionField = document.getElementById("rp-snapshot-allocations-version-number");
  const snapshotCodeField = document.getElementById("rp-snapshot-allocations-snapshot-code");
  if (!planCodeField || !versionField || !snapshotCodeField) return;

  planCode = planCodeField.value;
  versionNumber = parseInt(versionField.value, 10);
  snapshotCode = snapshotCodeField.value;

  try {
    const { href, method } = API_URLS.resourcePlans.snapshotAllocationFilterOptions(
      planCode,
      versionNumber,
      snapshotCode,
    );
    const res = await apiFetch(href, { method });
    buildPage(res?.data ?? {});
  } catch (err) {
    const loading = document.getElementById("rp-snapshot-allocations-loading");
    if (loading) loading.remove();
    const msg = err?.data?.error?.message ?? "Failed to load snapshot allocations.";
    toast({ type: "error", title: "Error", message: msg });
  }
});
