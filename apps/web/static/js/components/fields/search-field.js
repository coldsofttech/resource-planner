/* SearchField: <search-field>
 *
 * A search input with prefix icon, optional suffix, and a Ctrl+K / ⌘K shortcut
 * that focuses the input from anywhere on the page.
 *
 * Attributes:
 *   id           – gives the inner <input> the id "{id}-input"
 *   name         – name attribute on the inner <input>
 *   placeholder  – default "Search…"
 *   prefix-icon  – Bootstrap icon class (default "bi-search")
 *   suffix-icon  – Bootstrap icon class; omit to show the ⌘ K hint text
 *   width        – CSS width of the control (default "240px")
 *   show-label   – when present, renders a label above the input (default text "Search")
 *   label        – overrides the default label text when used with show-label
 *
 * Public API:
 *   el.value        – read current input value
 *   el.value = ""   – set input value
 *   el.focus()      – focus and select the input
 *
 * Emits:
 *   rp:search (bubbles) – on Enter keypress; detail: { value }
 */
import { esc } from "../utils.js";

class SearchField extends HTMLElement {
  static get observedAttributes() {
    return [
      "placeholder",
      "prefix-icon",
      "suffix-icon",
      "width",
      "name",
      "shortcut",
      "show-label",
      "label",
    ];
  }

  connectedCallback() {
    this._connected = true;
    this._render();
    this._bindShortcut();
  }

  disconnectedCallback() {
    if (this._onKeyDown) document.removeEventListener("keydown", this._onKeyDown);
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._connected && oldVal !== newVal) {
      const saved = this._input?.value ?? "";
      this._render();
      if (saved && this._input) this._input.value = saved;
    }
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "Search…";
  }
  get _prefixIcon() {
    return this.getAttribute("prefix-icon") || "bi-search";
  }
  get _hasSuffixIcon() {
    return this.hasAttribute("suffix-icon");
  }
  get _suffixIcon() {
    return this.getAttribute("suffix-icon") || "";
  }
  get _width() {
    return this.getAttribute("width") || "240px";
  }
  get _name() {
    return this.getAttribute("name") || "";
  }
  get _shortcut() {
    return this.getAttribute("shortcut") || "k";
  }
  get _fieldId() {
    return this.id || "";
  }

  get _input() {
    return this.querySelector(".rp-input");
  }

  get value() {
    return this._input?.value ?? "";
  }

  set value(v) {
    if (this._input) this._input.value = v;
  }

  focus() {
    this._input?.focus();
    this._input?.select();
  }

  _render() {
    const prefixHTML = `<i class="bi ${esc(this._prefixIcon)} rp-prefix"></i>`;
    const shortcut = this._shortcut;
    const noShortcut = shortcut === "none";
    const shortcutHint = noShortcut
      ? ""
      : `<span class="rp-suffix rp-mono rp-subtle" style="font-size:11px">&#8984;&thinsp;${esc(shortcut.toUpperCase())}</span>`;
    const suffixHTML = this._hasSuffixIcon
      ? `<i class="bi ${esc(this._suffixIcon)} rp-suffix"></i>`
      : shortcutHint;
    const idAttr = this._fieldId ? ` id="${esc(this._fieldId)}-input"` : "";
    const nameAttr = this._name ? ` name="${esc(this._name)}"` : "";
    const widthStyle = this.hasAttribute("width") ? ` style="width:${esc(this._width)}"` : "";
    const forAttr = this._fieldId ? ` for="${esc(this._fieldId)}-input"` : "";
    const labelHTML = this.hasAttribute("show-label")
      ? `<label class="rp-label"${forAttr}>${esc(this.getAttribute("label") || "Search")}</label>`
      : "";

    this.innerHTML = `<div class="rp-field">${labelHTML}<div class="rp-input-affix"${widthStyle}>
        ${prefixHTML}
        <input
          class="rp-input has-prefix has-suffix"
          type="search"
          placeholder="${esc(this._placeholder)}"
          autocomplete="off"
          spellcheck="false"${idAttr}${nameAttr}
        />
        ${suffixHTML}
      </div></div>`;

    this.querySelector(".rp-input")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        this.dispatchEvent(
          new CustomEvent("rp:search", { bubbles: true, detail: { value: this.value } }),
        );
      }
    });
  }

  _bindShortcut() {
    const shortcut = this._shortcut;
    if (shortcut === "none") return;
    this._onKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === shortcut) {
        e.preventDefault();
        this.focus();
      }
    };
    document.addEventListener("keydown", this._onKeyDown);
  }
}

customElements.define("search-field", SearchField);
