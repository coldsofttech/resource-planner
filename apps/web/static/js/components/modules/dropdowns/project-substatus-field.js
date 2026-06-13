import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProjectSubStatusField  <project-substatus-field>
 *
 * Dropdown field pre-wired to the project sub-statuses API.
 *
 * When used standalone (no status-id), fetches all active sub-statuses from
 * GET /api/v1/projects/sub-statuses/options/.
 *
 * When status-id is provided, it watches the referenced field element for
 * value changes and fetches sub-statuses scoped to the selected main status
 * from GET /api/v1/projects/statuses/<code>/substatus/options/. The field is
 * disabled when no main status is selected.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Project Sub-Status"
 *   placeholder → "Select project sub-status..."
 *
 * Attributes:
 *   status-id  – id of a <project-status-field> (or any dropdown) whose value
 *                provides the main status code to scope sub-status options.
 *   allow-all  – when present, prepends an "All Sub-Statuses" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Project Sub-Status" as the visible label.
 *
 * Usage:
 *   <!-- Standalone: loads all sub-statuses -->
 *   <project-substatus-field id="sub-status" required col="col-md-6"></project-substatus-field>
 *
 *   <!-- Scoped: reacts to the status field's value -->
 *   <project-status-field id="status-field" required></project-status-field>
 *   <project-substatus-field id="sub-status-field" status-id="status-field" required></project-substatus-field>
 *
 *   <!-- Filter context -->
 *   <project-substatus-field id="filter-sub" name="sub_status" allow-all status-id="filter-status"></project-substatus-field>
 */
class ProjectSubStatusField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "status-id"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Project Sub-Status";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder"))
      this.setAttribute("placeholder", "Select project sub-status...");

    const firstConnect = this._initialOptions === undefined;
    if (firstConnect) {
      this._initialOptions = [];
      this._loadId = Symbol();
      this._statusChangeHandler = null;
      this._watchedStatusEl = null;
    }

    super.connectedCallback();

    if (firstConnect) {
      this._attachStatusWatcher();
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
    this._detachStatusWatcher();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    super.attributeChangedCallback(name, oldVal, newVal);
    if (name === "status-id" && oldVal !== newVal && this.isConnected) {
      this._detachStatusWatcher();
      this._attachStatusWatcher();
    }
  }

  _attachStatusWatcher() {
    const statusId = this.getAttribute("status-id");
    if (!statusId) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(null, this._loadId);
      return;
    }

    const statusEl = document.getElementById(statusId);
    if (!statusEl) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      return;
    }

    this._watchedStatusEl = statusEl;
    this._statusChangeHandler = () => {
      const code = this._getStatusValue(statusEl);
      this._onStatusChange(code);
    };

    statusEl.addEventListener("change", this._statusChangeHandler);

    const currentCode = this._getStatusValue(statusEl);
    if (currentCode) {
      this._fetchOptions(currentCode, this._loadId);
    } else {
      this._clearOptions();
    }
  }

  _detachStatusWatcher() {
    if (this._watchedStatusEl && this._statusChangeHandler) {
      this._watchedStatusEl.removeEventListener("change", this._statusChangeHandler);
    }
    this._watchedStatusEl = null;
    this._statusChangeHandler = null;
  }

  _getStatusValue(el) {
    const select = el.querySelector?.(".rp-input") ?? el.querySelector?.("select");
    if (select) return select.value || "";
    if (el.value !== undefined) return el.value || "";
    return "";
  }

  _onStatusChange(statusCode) {
    this._loadId = Symbol();
    const id = this._loadId;
    if (statusCode) {
      this._fetchOptions(statusCode, id);
    } else {
      this._clearOptions();
    }
  }

  _clearOptions() {
    this._initialOptions = [];
    const select = this.querySelector(".rp-input");
    if (select) {
      select.disabled = true;
      select.innerHTML = `<option value="" disabled selected>${this.getAttribute("placeholder") || "Select project sub-status..."}</option>`;
    }
  }

  async _fetchOptions(statusCode, id) {
    const select = this.querySelector(".rp-input");
    if (select) select.disabled = true;

    try {
      let href, method;
      if (statusCode) {
        ({ href, method } = API_URLS.projectSubStatuses.options(statusCode));
      } else {
        ({ href, method } = API_URLS.projectSubStatuses.allOptions());
      }

      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const items = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Sub-Statuses", value: "", selected: true, disabled: false }]
          : []),
        ...items.map((s) => ({
          id: s.code,
          label: s.name,
          value: s.code,
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
      select.innerHTML = '<option value="" disabled selected>Could not load sub-statuses</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load sub-statuses. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("project-substatus-field", ProjectSubStatusField);
