import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* PredecessorPhaseField  <predecessor-phase-field>
 *
 * Searchable single-select field for picking a "predecessor phase" when
 * configuring a PlanPhaseDependency. Options span every phase in the plan
 * version (any team/project), grouped by project name — matching the GH #173
 * UI mockup. Always renders in DropdownField's `searchable` combobox mode.
 *
 * Unlike other async-fetch fields, this one has no single natural attribute
 * to scope its fetch by (it needs plan/version/project/team/phase codes —
 * five path segments). Call `setScope(...)` to provide them and trigger the
 * fetch; it returns the fetch promise so callers can await it before setting
 * `.value` (needed so the label lookup in the base class has options loaded).
 *
 * Usage:
 *   const field = document.getElementById("rp-dependency-predecessor");
 *   await field.setScope({ planCode, version, projectVersionCode, teamVersionCode, phaseVersionCode });
 *   field.value = existingPredecessorCode; // optional, for edit mode
 */
class PredecessorPhaseField extends DropdownField {
  connectedCallback() {
    if (!this.hasAttribute("searchable")) this.setAttribute("searchable", "");
    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Select predecessor phase…");
    }
    if (this._initialOptions === undefined) this._initialOptions = [];
    super.connectedCallback();
  }

  disconnectedCallback() {
    super.disconnectedCallback?.();
    this._loadId = Symbol();
  }

  setScope({ planCode, version, projectVersionCode, teamVersionCode, phaseVersionCode }) {
    this._scope = { planCode, version, projectVersionCode, teamVersionCode, phaseVersionCode };
    this._loadId = Symbol();
    return this._fetchOptions(this._loadId);
  }

  async _fetchOptions(id) {
    if (!this._scope) return;
    try {
      const { href, method } =
        API_URLS.resourcePlans.versionProjectTeamPhaseDependencyAvailablePredecessors(
          this._scope.planCode,
          this._scope.version,
          this._scope.projectVersionCode,
          this._scope.teamVersionCode,
          this._scope.phaseVersionCode,
        );
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const phases = res?.data ?? [];
      this._initialOptions = phases.map((p) => ({
        id: p.code,
        value: p.code,
        label: `${p.name} (${p.team_name})`,
        group: p.project_name,
        selected: false,
        disabled: false,
      }));
      this._loaded = true;
      this._doRender();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    }
  }

  // Groups the (already project-ordered) option list by inserting non-selectable
  // header rows whenever the group changes — mirrors DropdownField._buildComboItems()
  // but with headers interleaved. Click/keyboard handlers in the base class only
  // ever target ".rp-ms-option", so header rows are automatically unreachable.
  _buildComboItems(query) {
    const q = (query || "").toLowerCase();
    const filtered = q
      ? this._options.filter(
          (o) => o.label.toLowerCase().includes(q) || (o.group || "").toLowerCase().includes(q),
        )
      : this._options;

    if (!filtered.length) {
      return `<div class="rp-ms-empty">No options found</div>`;
    }

    let html = "";
    let lastGroup;
    filtered.forEach((o) => {
      if (o.group !== lastGroup) {
        html += `<div class="rp-ms-group-header">${this._esc(o.group)}</div>`;
        lastGroup = o.group;
      }
      const isSel = o.value === this._comboValue;
      html += `<div class="rp-ms-option${isSel ? " is-highlighted" : ""}" role="option" data-combo-val="${this._esc(o.value)}" data-combo-label="${this._esc(o.label)}">${this._esc(o.label)}</div>`;
    });
    return html;
  }

  _setFetchError() {
    const input = this.querySelector(".rp-combobox-search");
    const errEl = this.querySelector("[data-rp-error]");
    if (input) {
      input.disabled = true;
      input.placeholder = "";
    }
    if (errEl) {
      errEl.textContent = "Could not load phases. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("predecessor-phase-field", PredecessorPhaseField);
