"use strict";

import { esc } from "../../components/utils.js";

const CATEGORY_ICON = {
  delivery: "bi-rocket-takeoff",
  operational_excellence: "bi-gear",
};

const CATEGORY_COLOR = {
  delivery: "primary",
  operational_excellence: "warning",
};

const CATEGORY_BORDER_VAR = {
  delivery: "var(--rp-primary, #4B65D9)",
  operational_excellence: "var(--rp-warning, #f59e0b)",
};

function renderEntryCard(entry, categoryValue, interactive) {
  const inputId = `rp-nom-${categoryValue}-${entry.code}`;
  const checkbox = interactive
    ? `<input type="checkbox" class="form-check-input rp-nom-checkbox mt-1" id="${inputId}"
         data-entry-code="${esc(entry.code)}" data-team-code="${esc(entry.team_code)}"
         data-category="${esc(categoryValue)}">`
    : "";
  return `
    <label class="d-flex align-items-start gap-2 border rounded p-2 mb-2" for="${interactive ? inputId : ""}">
      ${checkbox}
      <div>
        <div class="fw-medium">${esc(entry.label)}</div>
        ${entry.description ? `<div class="rp-help">${esc(entry.description)}</div>` : ""}
      </div>
    </label>
  `;
}

/**
 * Renders a read-only (preview) or interactive (survey/override) nomination
 * form into `container`. Shared by the admin preview drawer, the admin
 * override drawer, and the public survey page.
 *
 * @param {HTMLElement} container
 * @param {object} data - { entries, categories, existing_nominations }
 * @param {object} opts - { interactive, maxPerGroup, groupByTeam }
 * @returns {{ getNominations: () => Array, markExisting: () => void } | null}
 */
export function renderNominationForm(container, data, opts = {}) {
  const { interactive = false, maxPerGroup = 2, groupByTeam = false } = opts;
  const entries = data.entries || [];
  const categories = data.categories || [];
  const existing = new Set(
    (data.existing_nominations || []).map((n) => `${n.entry_code}|${n.category}`),
  );

  const sections = categories
    .map((cat) => {
      const icon = CATEGORY_ICON[cat.value] || "bi-star";
      const color = CATEGORY_COLOR[cat.value] || "primary";
      const borderVar = CATEGORY_BORDER_VAR[cat.value] || "var(--rp-primary)";

      let body;
      if (groupByTeam) {
        const byTeam = new Map();
        entries.forEach((e) => {
          if (!byTeam.has(e.team_code)) {
            byTeam.set(e.team_code, { name: e.team_name, entries: [] });
          }
          byTeam.get(e.team_code).entries.push(e);
        });
        body = Array.from(byTeam.values())
          .map(
            (group) => `
              <div class="rp-help text-uppercase fw-semibold mt-2 mb-1">${esc(group.name)}</div>
              ${group.entries.map((e) => renderEntryCard(e, cat.value, interactive)).join("")}
            `,
          )
          .join("");
      } else {
        body = entries.map((e) => renderEntryCard(e, cat.value, interactive)).join("");
      }

      return `
        <div class="mb-4" style="border-left: 3px solid ${borderVar}; padding-left: 12px;">
          <div class="d-flex align-items-center gap-2 mb-1">
            <icon-field icon="${icon}" color="${color}"></icon-field>
            <strong>${esc(cat.label)} Wins</strong>
          </div>
          <div class="rp-help mb-2">Select up to ${maxPerGroup}${groupByTeam ? " per team" : ""}.</div>
          ${body || `<p class="rp-muted">No wins available.</p>`}
        </div>
      `;
    })
    .join("");

  container.innerHTML =
    sections || `<p class="rp-muted">No wins are available for this survey.</p>`;

  if (!interactive) return null;

  const checkboxes = Array.from(container.querySelectorAll(".rp-nom-checkbox"));

  function applyLimits() {
    const checkedCategoryByEntry = new Map();
    checkboxes.forEach((cb) => {
      if (cb.checked) checkedCategoryByEntry.set(cb.dataset.entryCode, cb.dataset.category);
    });

    const groupCounts = new Map();
    checkboxes.forEach((cb) => {
      if (!cb.checked) return;
      const key = groupByTeam
        ? `${cb.dataset.category}|${cb.dataset.teamCode}`
        : cb.dataset.category;
      groupCounts.set(key, (groupCounts.get(key) || 0) + 1);
    });

    checkboxes.forEach((cb) => {
      if (cb.checked) return;
      const otherCategory = checkedCategoryByEntry.get(cb.dataset.entryCode);
      const crossCategoryBlocked = !!otherCategory && otherCategory !== cb.dataset.category;
      const key = groupByTeam
        ? `${cb.dataset.category}|${cb.dataset.teamCode}`
        : cb.dataset.category;
      const groupFull = (groupCounts.get(key) || 0) >= maxPerGroup;
      cb.disabled = crossCategoryBlocked || groupFull;
    });
  }

  checkboxes.forEach((cb) => {
    cb.checked = existing.has(`${cb.dataset.entryCode}|${cb.dataset.category}`);
    cb.addEventListener("change", applyLimits);
  });
  applyLimits();

  return {
    getNominations() {
      return checkboxes
        .filter((cb) => cb.checked)
        .map((cb) => ({ entry_code: cb.dataset.entryCode, category: cb.dataset.category }));
    },
  };
}
