import { MultiSelectField } from "../../fields/multi-select-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProjectTagsField  <project-tags-field>
 *
 * Multi-select field pre-wired to the global tags list. Tags are fetched from
 * GET /api/v1/tags/ on first connect and cached for the lifetime of the element.
 * Inherits all attributes and public API from MultiSelectField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Tags"
 *   placeholder → "Select tag…"
 *
 * All other MultiSelectField attributes work as-is:
 *   required, max, free-form, col, hint, hint-type, value, name, id
 *
 * Usage:
 *   <project-tags-field id="project-tags" col="col-12"></project-tags-field>
 *
 *   <!-- With pre-selected values (codes as JSON array) -->
 *   <project-tags-field id="project-tags" value='["TAG-0001","TAG-0003"]'></project-tags-field>
 *
 * Attributes:
 *   show-label – when present, renders "Tags" as the visible field label.
 *
 * Reading the value in JS:
 *   JSON.parse(field.value)  // → ["TAG-0001", "TAG-0003"]
 *   field.values             // → [{id, label, value}, …]
 */
class ProjectTagsField extends MultiSelectField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Tags";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select tag…");

    const firstConnect = this._initialOptions === undefined;
    let pending = [];

    if (firstConnect) {
      pending = this._parseValueCodes(this.getAttribute("value") || "");
      this._initialOptions = [];
      this._selectedValues = pending.map((code) => ({ id: code, label: code, value: code }));
      this._loadId = Symbol();
    }

    super.connectedCallback();

    const shouldFetch = firstConnect || this._initialOptions.length === 0;
    if (shouldFetch) {
      this._loadId = Symbol();
      this._fetchOptions(this._loadId, pending);
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
    super.disconnectedCallback();
  }

  async _fetchOptions(id, pending) {
    const hasPending = pending.length > 0;
    if (hasPending) this._setLoadingState(true);

    try {
      const { href, method } = API_URLS.tags.list();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      // Handle paginated {data:{results:[...]}} and flat {data:[...]} response formats
      const raw = res?.data;
      const tags = Array.isArray(raw) ? raw : (raw?.results ?? []);
      this._initialOptions = tags.map((t) => ({
        id: t.code,
        label: t.name,
        value: t.code,
      }));

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

      const dropdown = this.querySelector(".rp-ms-dropdown");
      if (dropdown && !dropdown.hidden) this._updateDropdown();
    } catch {
      if (this._loadId !== id) return;
      // Treat fetch failure as empty list — no tags configured in this system yet.
      this._initialOptions = [];
    } finally {
      if (this._loadId === id && hasPending) this._setLoadingState(false);
    }
  }

  _addChip(opt) {
    const chipOpt = opt.id === "" ? { ...opt, label: `#${opt.label}` } : opt;
    super._addChip(chipOpt);
    this.dispatchEvent(
      new CustomEvent("rp:change", { bubbles: true, detail: { value: this.value } }),
    );
  }

  _removeChip(idx) {
    super._removeChip(idx);
    this.dispatchEvent(
      new CustomEvent("rp:change", { bubbles: true, detail: { value: this.value } }),
    );
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
      errEl.textContent = "Could not load tags. Refresh the page to retry.";
      errEl.hidden = false;
    }
    if (ms) ms.classList.add("is-invalid");
  }
}

customElements.define("project-tags-field", ProjectTagsField);
