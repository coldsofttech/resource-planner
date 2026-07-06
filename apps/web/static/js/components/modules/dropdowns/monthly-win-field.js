import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* MonthlyWinField  <monthly-win-field>
 *
 * Dropdown field pre-wired to the Monthly Wins options API. Rounds are
 * fetched from GET /api/v1/wins/monthly/options/ on connect, and retried on
 * reconnect until the fetch succeeds at least once. Inherits all attributes
 * and public API from DropdownField / BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Monthly Win"
 *   placeholder → "Select monthly win…"
 *
 * Attributes:
 *   show-label – when present, renders "Monthly Win" as the visible field label.
 *
 * Usage:
 *   <monthly-win-field id="report-monthly-win" show-label required></monthly-win-field>
 */
class MonthlyWinField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Monthly Win";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select monthly win…");

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
      const { href, method } = API_URLS.wins.monthly.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const monthlyWins = res?.data ?? [];
      this._initialOptions = monthlyWins.map((mw) => ({
        id: mw.code,
        label: mw.name,
        value: mw.code,
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

  _setFetchError() {
    const select = this.querySelector(".rp-input");
    const errEl = this.querySelector("[data-rp-error]");
    if (select) {
      select.disabled = true;
      select.innerHTML = '<option value="" disabled selected>Could not load monthly wins</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load monthly wins. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("monthly-win-field", MonthlyWinField);
