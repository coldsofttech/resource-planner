import { MultiSelectField } from "../../fields/multi-select-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* SkillsField  <skills-field>
 *
 * Multi-select field pre-wired to the skills API. Active skills are fetched
 * from GET /api/v1/skills/options/ on first connect and cached for the
 * lifetime of the element. Inherits all attributes and public API from
 * MultiSelectField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Skills"
 *   placeholder → "Select skill…"
 *
 * All other MultiSelectField attributes work as-is:
 *   required, max, free-form, col, hint, hint-type, value, name, id
 *
 * Usage:
 *   <skills-field id="member-skills" required col="col-md-12"></skills-field>
 *
 *   <!-- With pre-selected values (codes as JSON array) -->
 *   <skills-field id="member-skills" value='["SKILL-0001","SKILL-0003"]'></skills-field>
 *
 * Attributes:
 *   show-label – when present, renders "Skills" as the visible field label.
 *
 * Reading the value in JS:
 *   JSON.parse(field.value)  // → ["SKILL-0001", "SKILL-0003"]
 *   field.values             // → [{id, label, value}, …]
 */
class SkillsField extends MultiSelectField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Skills";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select skill…");

    const firstConnect = this._initialOptions === undefined;
    let pending = [];

    if (firstConnect) {
      pending = this._parseValueCodes(this.getAttribute("value") || "");
      // Seed with placeholder chips (code as label) so pre-selected values are
      // visible immediately. Labels are updated once options finish loading.
      this._initialOptions = [];
      this._selectedValues = pending.map((code) => ({ id: code, label: code, value: code }));
      this._loadId = Symbol();
    }

    super.connectedCallback();

    // Re-fetch if this is the first connect OR if options never loaded (e.g. the
    // element was disconnected mid-fetch by section-panel._render() which uses innerHTML).
    const shouldFetch = firstConnect || this._initialOptions.length === 0;
    if (shouldFetch) {
      this._loadId = Symbol();
      this._fetchOptions(this._loadId, pending);
    }
  }

  disconnectedCallback() {
    // Invalidate any in-flight fetch so its result is discarded on reconnect.
    this._loadId = Symbol();
    super.disconnectedCallback();
  }

  // ── Private ──────────────────────────────────────────────────────────────

  async _fetchOptions(id, pending) {
    const hasPending = pending.length > 0;
    if (hasPending) this._setLoadingState(true);

    try {
      const { href, method } = API_URLS.skills.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const skills = res?.data ?? [];
      this._initialOptions = skills.map((s) => ({
        id: s.code,
        label: s.skill,
        value: s.code,
      }));

      // Update any selected values (placeholder or pre-loaded) with proper labels.
      if (this._selectedValues && this._selectedValues.length > 0) {
        this._selectedValues = this._selectedValues.map((sv) => {
          const opt = this._initialOptions.find((o) => o.value === sv.value);
          return opt ? { ...opt } : sv;
        });
        this._refreshChipsAndInput();
      } else if (hasPending) {
        this._selectedValues = this._initialOptions.filter((o) => pending.includes(o.value));
        this._refreshChipsAndInput();
      }

      // Refresh dropdown if the user opened it before options arrived.
      const dropdown = this.querySelector(".rp-ms-dropdown");
      if (dropdown && !dropdown.hidden) this._updateDropdown();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    } finally {
      if (this._loadId === id && hasPending) this._setLoadingState(false);
    }
  }

  _parseValueCodes(val) {
    if (!val) return [];
    try {
      const parsed = JSON.parse(val);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return val
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
    }
  }

  _setLoadingState(on) {
    const input = this.querySelector(".rp-ms-input");
    if (!input) return;
    input.disabled = on;
    input.placeholder = on ? "Loading…" : this._isAtMax() ? "" : this._placeholder;
  }

  _setFetchError() {
    const input = this.querySelector(".rp-ms-input");
    const errEl = this.querySelector("[data-rp-error]");
    const ms = this.querySelector(".rp-multiselect");
    if (input) {
      input.disabled = true;
      input.placeholder = "";
    }
    if (errEl) {
      errEl.textContent = "Could not load skills. Refresh the page to retry.";
      errEl.hidden = false;
    }
    if (ms) ms.classList.add("is-invalid");
  }
}

customElements.define("skills-field", SkillsField);
