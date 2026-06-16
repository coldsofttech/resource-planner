import { esc } from "../utils.js";

/* HistoryItems  <history-items>
 *
 * Scrollable container for <history-item> children. Shows a placeholder message
 * on connect when empty. Exposes state methods called by page JS to manage
 * loading, empty, error, and populated states without touching innerHTML directly.
 *
 * Attributes:
 *   placeholder  – text shown on connect when no items are present
 *                  (default "No history available.")
 *
 * Methods (called from page JS):
 *   loading(msg?)          – replace content with a "loading" message
 *   empty(msg?)            – replace content with the placeholder (or override)
 *   error(msg?)            – replace content with an "error" message
 *   setItems(elements)     – replace content with an array of <history-item> elements
 */
class HistoryItems extends HTMLElement {
  static get observedAttributes() {
    return ["placeholder"];
  }

  connectedCallback() {
    if (!this.classList.contains("mt-2") && !this.classList.contains("mt-3")) {
      this.classList.add("mt-2");
    }
    if (!this.children.length) this._showMessage(this._placeholder);
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "No history available.";
  }

  _showMessage(msg) {
    this.innerHTML = `<p class="text-muted rp-fs-13 mb-0">${esc(msg)}</p>`;
  }

  loading(msg = "Loading history…") {
    this._showMessage(msg);
  }

  empty(msg) {
    this._showMessage(msg ?? this._placeholder);
  }

  error(msg = "Failed to load history.") {
    this._showMessage(msg);
  }

  setItems(elements) {
    this.replaceChildren(...elements);
  }
}

customElements.define("history-items", HistoryItems);
