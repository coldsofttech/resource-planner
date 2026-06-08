import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* TeamField  <team-field>
 *
 * Dropdown field pre-wired to the teams API. Active teams are fetched from
 * GET /api/v1/teams/options/ on first connect. Inherits all attributes and
 * public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Team"
 *   placeholder → "Select team…"
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Teams" option (value="")
 *                selected by default; used in filter contexts.
 *   unassign   – when present, prepends an "Unassign from current team" option
 *                (value="") selected by default; takes precedence over allow-all
 *                label when both are set. Used in reassignment contexts.
 *   show-label – when present, renders "Team" as the visible field label.
 *
 * Usage:
 *   <team-field id="member-team" required col="col-md-6"></team-field>
 *
 *   <!-- With pre-selected value (team code) -->
 *   <team-field id="member-team" value="TEAM-1"></team-field>
 *
 *   <!-- Filter context: shows "All Teams" as the default selection -->
 *   <team-field id="filter-team" name="team" allow-all></team-field>
 *
 *   <!-- Reassignment context: shows "Unassign from current team" -->
 *   <team-field id="reassign-team" name="team" unassign></team-field>
 */
class TeamField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Team";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select team…");

    const firstConnect = this._initialOptions === undefined;
    if (firstConnect) {
      this._initialOptions = [];
      this._loadId = Symbol();
    }

    super.connectedCallback();

    if (firstConnect) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(this._loadId);
    }
  }

  disconnectedCallback() {
    // Invalidate any in-flight fetch so its result is discarded on reconnect.
    this._loadId = Symbol();
  }

  // ── Private ──────────────────────────────────────────────────────────────

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.teams.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const teams = res?.data ?? [];
      const hasUnassign = this.hasAttribute("unassign");
      const hasAllOpt = hasUnassign || this.hasAttribute("allow-all");
      const allLabel = hasUnassign ? "Unassign from current team" : "All Teams";

      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: allLabel, value: "", selected: true, disabled: false }]
          : []),
        ...teams.map((t) => ({
          id: t.code,
          label: t.name,
          value: t.code,
          selected: false,
          disabled: false,
        })),
      ];

      this._doRender();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    }
  }

  _setFetchError() {
    const select = this.querySelector(".rp-input");
    const errEl = this.querySelector("[data-rp-error]");
    if (select) {
      select.disabled = true;
      select.innerHTML = '<option value="" disabled selected>Could not load teams</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load teams. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("team-field", TeamField);
