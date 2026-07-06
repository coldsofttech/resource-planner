import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProgrammeField  <programme-field>
 *
 * Dropdown field pre-wired to the programmes API. Active programmes are fetched
 * from GET /api/v1/programmes/options/ on connect, and retried on reconnect until
 * the fetch succeeds at least once. Inherits all attributes and public API from
 * DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Programme"
 *   placeholder → "Select programme..."
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Programmes" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Programme" as the visible field label
 *
 * Usage:
 *   <programme-field id="project-programme" required col="col-md-6"></programme-field>
 *
 *   <!-- With pre-selected value (programme code) -->
 *   <programme-field id="project-programme" value="PROG-1"></programme-field>
 *
 *   <!-- Filter context: shows "All Programmes" as the default selection -->
 *   <programme-field id="filter-programme" name="programme" allow-all></programme-field>
 */
class ProgrammeField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Programme";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select programme...");

    if (this._initialOptions === undefined) this._initialOptions = [];

    super.connectedCallback();

    // Fetch whenever options haven't successfully loaded yet — not just on the very first
    // connect. Containers like <tab-panel> capture and re-insert child nodes on their own
    // initial render, which disconnects/reconnects this element before its first fetch
    // resolves; gating on "first connect" alone would then discard that in-flight result
    // and never retry, leaving the dropdown stuck on its placeholder.
    if (!this._loaded) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._loadId = Symbol();
      this._fetchOptions(this._loadId);
    }
  }

  disconnectedCallback() {
    // Invalidate any in-flight fetch so its result is discarded on reconnect.
    this._loadId = Symbol();
  }

  refresh() {
    this._loaded = false;
    this._loadId = Symbol();
    this._fetchOptions(this._loadId);
  }

  // Preserve the typed text on blur when no existing option was selected.
  // This allows free-form programme creation via the inputText property.
  _doComboBlur(input) {
    this._closeComboDropdown();
    if (this._comboValue) input.value = this._comboLabel || "";
    // else: leave input.value unchanged so inputText reflects what the user typed
    this._touched = true;
    this._updateError();
  }

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.programmes.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const programmes = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Programmes", value: "", selected: true, disabled: false }]
          : []),
        ...programmes.map((p) => ({
          id: p.code,
          label: p.name,
          value: p.code,
          selected: false,
          disabled: false,
        })),
      ];

      this._loaded = true;
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
      select.innerHTML = '<option value="" disabled selected>Could not load programmes</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load programmes. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("programme-field", ProgrammeField);
