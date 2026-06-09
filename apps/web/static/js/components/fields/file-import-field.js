import { BaseField } from "./base-field.js";

/* FileImportField  <file-import-field>
 *
 * Drag-and-drop / click-to-browse file import field.
 * Renders a drop zone with file tags for each selected file.
 * Participates in the wizard validation lifecycle via BaseField.
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Additional attributes:
 *   accept       – comma-separated extensions or MIME types (default ".csv,.xlsx")
 *   max-size     – maximum file size in bytes (default 26214400 = 25 MB)
 *   multiple     – boolean; allows selecting more than one file
 *   icon         – Bootstrap Icon class for the drop zone icon (default "bi-cloud-upload")
 *   drop-label   – primary drop zone heading text (default "Drop files here")
 *   browse-label – text for the browse link (default "browse from your computer")
 *   sub-text     – small caption below browse link (e.g. "Max 25 MB · UTF-8 · headers on row 1")
 *
 * Public API:
 *   field.files         – getter: array of selected File objects
 *   field.value         – getter: name of the first selected file, or ""
 *   field.clear()       – removes all selected files
 *
 * Events:
 *   rp:change           – fires (bubbles) whenever the file selection changes;
 *                         detail: { files: File[] }
 *
 * Validation:
 *   - required: at least one file must be selected
 *   - accept: files not matching the accept list are silently rejected on drop/select
 *   - max-size: files exceeding the limit are silently rejected on drop/select
 *
 * Examples:
 *   <file-import-field id="import-file" label="Import file" required
 *     accept=".csv,.xlsx" max-size="26214400"
 *     drop-label="Drop CSV or XLSX here"
 *     sub-text="Max 25 MB · UTF-8 · headers on row 1">
 *   </file-import-field>
 *
 *   <file-import-field id="attachments" label="Attachments" multiple
 *     accept=".pdf,.xlsx" drop-label="Drop files here">
 *   </file-import-field>
 */

const FILE_ICONS = {
  csv: "bi-filetype-csv",
  xlsx: "bi-file-earmark-spreadsheet",
  xls: "bi-file-earmark-spreadsheet",
  pdf: "bi-file-earmark-pdf",
};

class FileImportField extends BaseField {
  constructor() {
    super();
    this._files = [];
  }

  static get observedAttributes() {
    return [
      ...super.observedAttributes,
      "accept",
      "max-size",
      "multiple",
      "icon",
      "drop-label",
      "browse-label",
      "sub-text",
    ];
  }

  // --- Attribute getters ---

  get _accept() {
    return this.getAttribute("accept") || ".csv,.xlsx";
  }

  get _maxSize() {
    return parseInt(this.getAttribute("max-size") || "26214400", 10);
  }

  get _multiple() {
    return this.hasAttribute("multiple");
  }

  get _icon() {
    const raw = this.getAttribute("icon") || "bi-cloud-upload";
    return raw.startsWith("bi-") ? raw : `bi-${raw}`;
  }

  get _dropLabel() {
    return this.getAttribute("drop-label") || "Drop files here";
  }

  get _browseLabel() {
    return this.getAttribute("browse-label") || "browse from your computer";
  }

  get _subText() {
    return this.getAttribute("sub-text") || "";
  }

  // --- Value / files ---

  get _value() {
    return this._files.length ? this._files[0].name : "";
  }

  get files() {
    return [...this._files];
  }

  clear() {
    this._files = [];
    const input = this.querySelector(".rp-file-hidden");
    if (input) input.value = "";
    this._renderTags();
    if (this._touched) this._updateError();
  }

  // Files cannot be serialised across re-renders — suppress save/restore.
  _savedValue() {
    return null;
  }

  _restoreValue() {}

  // --- Render ---

  _buildHTML() {
    const acceptAttr = this._accept ? ` accept="${this._esc(this._accept)}"` : "";
    const multipleAttr = this._multiple ? " multiple" : "";
    const subText = this._subText
      ? `<div class="rp-mono mt-2" style="font-size:11px;color:var(--rp-text-subtle)">${this._esc(this._subText)}</div>`
      : "";

    return `
      <div class="rp-field">
        ${this._label ? this._labelHTML() : ""}
        <input
          type="file"
          class="rp-file-hidden visually-hidden"
          id="${this._esc(this._fieldId)}-input"
          name="${this._esc(this._name)}"
          tabindex="-1"
          aria-hidden="true"
          ${acceptAttr}${multipleAttr}
        />
        <div
          class="rp-drop"
          data-drop-zone
          role="button"
          tabindex="0"
          aria-label="${this._esc(this._dropLabel)}"
        >
          <i class="bi ${this._esc(this._icon)}" aria-hidden="true"></i>
          <div style="font-weight:600;color:var(--rp-text)">${this._esc(this._dropLabel)}</div>
          <div>or <a class="rp-link" href="#" data-browse-link>${this._esc(this._browseLabel)}</a></div>
          ${subText}
        </div>
        <div class="d-flex flex-wrap gap-2 mt-3" data-file-tags hidden></div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    const input = this.querySelector(".rp-file-hidden");
    const dropZone = this.querySelector("[data-drop-zone]");
    const browseLink = this.querySelector("[data-browse-link]");

    if (!input || !dropZone) return;

    // Browse link opens file picker without triggering the drop zone click handler.
    browseLink?.addEventListener("click", (e) => {
      e.preventDefault();
      input.click();
    });

    // Drop zone click (excluding the link itself) opens file picker.
    dropZone.addEventListener("click", (e) => {
      if (browseLink && (e.target === browseLink || browseLink.contains(e.target))) return;
      input.click();
    });

    // Keyboard activation of the drop zone.
    dropZone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        input.click();
      }
    });

    // Drag & drop
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("is-over");
    });

    dropZone.addEventListener("dragleave", (e) => {
      if (!dropZone.contains(e.relatedTarget)) {
        dropZone.classList.remove("is-over");
      }
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("is-over");
      this._processFiles(Array.from(e.dataTransfer.files));
    });

    // File input change
    input.addEventListener("change", () => {
      this._processFiles(Array.from(input.files));
      // Reset so the same file can be re-selected after removal.
      input.value = "";
    });
  }

  // --- File processing ---

  _processFiles(incoming) {
    const valid = incoming.filter((f) => this._isAccepted(f));
    if (this._multiple) {
      this._files = [...this._files, ...valid];
    } else {
      this._files = valid.slice(0, 1);
    }
    this._renderTags();
    if (this._touched) this._updateError();
    this.dispatchEvent(
      new CustomEvent("rp:change", { bubbles: true, detail: { files: this.files } }),
    );
  }

  _isAccepted(file) {
    if (file.size > this._maxSize) return false;
    const accept = this._accept;
    if (!accept) return true;
    const ext = "." + file.name.split(".").pop().toLowerCase();
    const mime = file.type.toLowerCase();
    return accept
      .split(",")
      .map((s) => s.trim().toLowerCase())
      .some(
        (p) => p === ext || p === mime || (p.endsWith("/*") && mime.startsWith(p.slice(0, -1))),
      );
  }

  _renderTags() {
    const container = this.querySelector("[data-file-tags]");
    if (!container) return;

    if (!this._files.length) {
      container.hidden = true;
      container.innerHTML = "";
      return;
    }

    container.hidden = false;
    container.innerHTML = this._files
      .map((f, i) => {
        const icon = FILE_ICONS[f.name.split(".").pop().toLowerCase()] || "bi-file-earmark";
        return `<span class="rp-tag">
          <i class="bi ${icon}" aria-hidden="true"></i>
          ${this._esc(f.name)} · ${this._formatSize(f.size)}
          <button type="button" data-remove-idx="${i}" aria-label="Remove ${this._esc(f.name)}">
            <i class="bi bi-x" aria-hidden="true"></i>
          </button>
        </span>`;
      })
      .join("");

    container.querySelectorAll("[data-remove-idx]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.dataset.removeIdx, 10);
        this._files.splice(idx, 1);
        this._renderTags();
        if (this._touched) this._updateError();
        this.dispatchEvent(
          new CustomEvent("rp:change", { bubbles: true, detail: { files: this.files } }),
        );
      });
    });
  }

  _formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }

  // --- Validation ---

  _validate() {
    if (this._required && !this._files.length) return "Please select a file.";
    return "";
  }

  _updateError() {
    const err = this._validate();
    const errEl = this.querySelector("[data-rp-error]");
    if (errEl) {
      errEl.textContent = err;
      errEl.hidden = !err;
    }
  }
}

customElements.define("file-import-field", FileImportField);
