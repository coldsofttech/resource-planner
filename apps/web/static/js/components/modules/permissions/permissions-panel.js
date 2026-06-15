"use strict";

import { esc } from "../../utils.js";
import { apiFetch } from "../../../modules/utils/utils.js";

/* PermissionsPanel  <permissions-panel>
 *
 * Self-contained component for displaying and editing permission category
 * assignments. Handles both group and user subjects in edit or view modes.
 *
 * Attributes:
 *   subject-type  – "group" | "user"
 *
 * Public API:
 *   panel.load(subjectCode)         – load categories + assignments for editing
 *   panel.save()                    – diff and persist changes; returns a Promise
 *   panel.loadAssigned(subjectCode) – load current assignments as a read-only list
 *   panel.loadEffective(userCode)   – load effective (group + direct) permissions
 *                                     as a read-only list (user only)
 *
 * Events (bubble):
 *   rp:permissions:saved  – after a successful save(); detail: { code }
 */
class PermissionsPanel extends HTMLElement {
  connectedCallback() {
    if (this._connected) return;
    this._connected = true;
    this._original = {};
    this._subjectCode = null;
    this.innerHTML = `<div class="rp-perm-panel-content"></div>`;
    this._content = this.querySelector(".rp-perm-panel-content");

    // Toggle scope dropdown enabled/disabled with its checkbox
    this.addEventListener("change", (e) => {
      if (e.target.classList.contains("rp-perm-toggle")) {
        const code = e.target.dataset.permCode;
        const sel = this.querySelector(`.rp-perm-scope[data-perm-code="${code}"]`);
        if (sel) sel.disabled = !e.target.checked;
      }
    });
  }

  async load(subjectCode) {
    this._subjectCode = subjectCode;
    this._original = {};
    this._show(`<p class="rp-subtle mb-0 px-3 py-2">Loading permissions…</p>`);

    const subjectType = this.getAttribute("subject-type");
    const catsUrl = `/api/v1/permissions/categories/?page_size=200`;
    const assignUrl = `/api/v1/permissions/${subjectType}s/${subjectCode}/?page_size=200`;

    try {
      const [catResp, assignResp] = await Promise.all([
        apiFetch(catsUrl, { method: "GET" }),
        apiFetch(assignUrl, { method: "GET" }),
      ]);

      const cats = catResp?.data?.results ?? [];
      const assigns = assignResp?.data?.results ?? [];

      for (const a of assigns) {
        if (a.category?.code) {
          this._original[a.category.code] = { code: a.code, scope: a.scope };
        }
      }

      this._show(this._editHtml(cats, this._original));
    } catch {
      this._show(`<p class="rp-subtle mb-0 px-3 py-2">Could not load permissions.</p>`);
    }
  }

  async save() {
    const subjectType = this.getAttribute("subject-type");
    const baseUrl = `/api/v1/permissions/${subjectType}s/${this._subjectCode}/`;

    const errors = [];
    const ops = [];

    this.querySelectorAll(".rp-perm-toggle").forEach((toggle) => {
      const catCode = toggle.dataset.permCode;
      const scopeEl = this.querySelector(`.rp-perm-scope[data-perm-code="${catCode}"]`);
      const scope = parseInt(scopeEl?.value ?? "3", 10);
      const orig = this._original[catCode];

      if (toggle.checked && !orig) {
        ops.push(
          apiFetch(baseUrl, {
            method: "POST",
            body: JSON.stringify({ category_code: catCode, scope }),
          }).catch((e) => errors.push(e?.data?.error?.message ?? "Failed to assign permission.")),
        );
      } else if (!toggle.checked && orig) {
        ops.push(
          apiFetch(`${baseUrl}${orig.code}/`, { method: "DELETE" }).catch((e) =>
            errors.push(e?.data?.error?.message ?? "Failed to remove permission."),
          ),
        );
      } else if (toggle.checked && orig && scope !== orig.scope) {
        ops.push(
          apiFetch(`${baseUrl}${orig.code}/`, {
            method: "PATCH",
            body: JSON.stringify({ scope }),
          }).catch((e) => errors.push(e?.data?.error?.message ?? "Failed to update permission.")),
        );
      }
    });

    await Promise.all(ops);

    if (errors.length > 0) throw new Error(errors[0]);

    this.dispatchEvent(
      new CustomEvent("rp:permissions:saved", {
        bubbles: true,
        detail: { code: this._subjectCode },
      }),
    );
  }

  async loadAssigned(subjectCode) {
    this._subjectCode = subjectCode;
    this._show(`<p class="rp-subtle mb-0">Loading permissions…</p>`);

    const subjectType = this.getAttribute("subject-type");
    const url = `/api/v1/permissions/${subjectType}s/${subjectCode}/?page_size=100`;

    try {
      const resp = await apiFetch(url, { method: "GET" });
      const items = resp?.data?.results ?? [];
      this._show(this._assignedHtml(items));
    } catch {
      this._show(`<p class="rp-subtle mb-0">Could not load permissions.</p>`);
    }
  }

  async loadEffective(userCode) {
    this._subjectCode = userCode;
    this._show(`<p class="rp-subtle mb-0">Loading permissions…</p>`);

    try {
      const resp = await apiFetch(`/api/v1/permissions/users/${userCode}/effective/`, {
        method: "GET",
      });
      const items = resp?.data ?? [];
      this._show(this._effectiveHtml(items));
    } catch {
      this._show(`<p class="rp-subtle mb-0">Could not load permissions.</p>`);
    }
  }

  _show(html) {
    if (this._content) this._content.innerHTML = html;
  }

  _fmtModule(mod) {
    return (mod || "other").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  _editHtml(cats, original) {
    if (!cats.length) {
      return `<p class="rp-subtle mb-0 px-3 py-2">No permission categories available.</p>`;
    }

    const byModule = {};
    for (const cat of cats) {
      const mod = cat.module || "other";
      if (!byModule[mod]) byModule[mod] = [];
      byModule[mod].push(cat);
    }

    return Object.entries(byModule)
      .map(([mod, entries]) => {
        const rows = entries
          .map((cat) => {
            const assigned = original[cat.code];
            const checked = !!assigned;
            const scope = assigned?.scope ?? 3;
            return `
              <div class="d-flex align-items-center justify-content-between py-2 border-bottom px-3" style="gap:1rem">
                <div class="d-flex align-items-center gap-2" style="flex:1 1 auto">
                  <input type="checkbox" class="form-check-input rp-perm-toggle mt-0"
                         data-perm-code="${esc(cat.code)}" ${checked ? "checked" : ""}>
                  <span style="font-size:0.875rem">${esc(cat.label || cat.name)}</span>
                </div>
                <select class="form-select form-select-sm rp-perm-scope"
                        data-perm-code="${esc(cat.code)}"
                        style="width:110px"
                        ${checked ? "" : "disabled"}>
                  <option value="1" ${scope === 1 ? "selected" : ""}>Self</option>
                  <option value="2" ${scope === 2 ? "selected" : ""}>Team</option>
                  <option value="3" ${scope === 3 ? "selected" : ""}>All</option>
                </select>
              </div>`;
          })
          .join("");
        return `<accordion-panel label="${esc(this._fmtModule(mod))}"><accordion-body>${rows}</accordion-body></accordion-panel>`;
      })
      .join("");
  }

  _assignedHtml(items) {
    if (!items.length) {
      return `<p class="rp-subtle mb-0">No permissions assigned.</p>`;
    }

    const byModule = {};
    for (const item of items) {
      const mod = item.category?.module || "other";
      if (!byModule[mod]) byModule[mod] = [];
      byModule[mod].push(item);
    }

    let html = "";
    for (const [mod, entries] of Object.entries(byModule)) {
      html += `<p class="fw-semibold rp-subtle mb-1 text-uppercase" style="font-size:0.7rem;letter-spacing:.05em">${esc(this._fmtModule(mod))}</p>`;
      html += `<ul class="list-unstyled mb-3">`;
      for (const entry of entries) {
        const label = entry.category?.label || entry.category?.name || "—";
        const scope = entry.scope_display || "—";
        html += `
          <li class="d-flex justify-content-between align-items-center py-1 border-bottom" style="font-size:0.875rem">
            <span>${esc(label)}</span>
            <span class="rp-badge rp-badge-soft rp-badge-info ms-2">${esc(scope)}</span>
          </li>`;
      }
      html += `</ul>`;
    }
    return html;
  }

  _effectiveHtml(items) {
    if (!items.length) {
      return `<p class="rp-subtle mb-0">No permissions assigned.</p>`;
    }

    const byModule = {};
    for (const item of items) {
      const mod = item.category?.module || "other";
      if (!byModule[mod]) byModule[mod] = [];
      byModule[mod].push(item);
    }

    const viaBadge = (via) => {
      if (via === "both")
        return `<span class="rp-badge rp-badge-soft rp-badge-warning ms-1">Group + Direct</span>`;
      if (via === "group") return `<span class="rp-badge rp-badge-soft ms-1">Group</span>`;
      return `<span class="rp-badge rp-badge-soft rp-badge-success ms-1">Direct</span>`;
    };

    let html = "";
    for (const [mod, entries] of Object.entries(byModule)) {
      html += `<p class="fw-semibold rp-subtle mb-1 text-uppercase" style="font-size:0.7rem;letter-spacing:.05em">${esc(this._fmtModule(mod))}</p>`;
      html += `<ul class="list-unstyled mb-3">`;
      for (const entry of entries) {
        const label = entry.category?.label || entry.category?.name || "—";
        const scope = entry.scope_display || "—";
        html += `
          <li class="d-flex justify-content-between align-items-center py-1 border-bottom" style="font-size:0.875rem">
            <span>${esc(label)}</span>
            <div class="d-flex align-items-center gap-1">
              <span class="rp-badge rp-badge-soft rp-badge-info">${esc(scope)}</span>
              ${viaBadge(entry.via)}
            </div>
          </li>`;
      }
      html += `</ul>`;
    }
    return html;
  }
}

customElements.define("permissions-panel", PermissionsPanel);
