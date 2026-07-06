import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* PriorityField  <priority-field>
 *
 * Dropdown field pre-wired to the project priority options API.
 * Options are fetched from GET /api/v1/projects/options/?fields=priority on
 * connect, and retried on reconnect until the fetch succeeds at least once.
 * Inherits all attributes and public API from DropdownField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Priority"
 *   placeholder → "Select priority..."
 *
 * Attributes:
 *   allow-all  – prepends an "All Priority Levels" option (value="")
 *                selected by default; used in filter contexts.
 *   inherit    – prepends an "Inherit" option (value="") selected by
 *                default; used for override fields that fall back to a
 *                snapshotted/parent value when left unset.
 *   show-label – when present, renders "Priority" as the visible field label.
 *
 * Usage:
 *   <priority-field id="proj-priority" required col="col-md-6"></priority-field>
 *
 *   <!-- Filter context -->
 *   <priority-field id="filter-priority" name="priority" allow-all></priority-field>
 *
 *   <!-- Override context -->
 *   <priority-field id="override-priority" inherit show-label></priority-field>
 */
class PriorityField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Priority";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select priority...");

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
    this._loadId = Symbol();
  }

  refresh() {
    this._loaded = false;
    this._loadId = Symbol();
    this._fetchOptions(this._loadId);
  }

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.projects.priorityOptions();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const items = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      const hasNotSet = this.hasAttribute("not-set");
      const hasInherit = this.hasAttribute("inherit");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Priority Levels", value: "", selected: true, disabled: false }]
          : []),
        ...(hasNotSet
          ? [{ id: "", label: "Not Set", value: "", selected: true, disabled: false }]
          : []),
        ...(hasInherit
          ? [{ id: "", label: "Inherit", value: "", selected: true, disabled: false }]
          : []),
        ...items.map((t) => ({
          id: t.code,
          label: t.name,
          value: t.code,
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
      select.innerHTML =
        '<option value="" disabled selected>Could not load priority options</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load priority options. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("priority-field", PriorityField);
