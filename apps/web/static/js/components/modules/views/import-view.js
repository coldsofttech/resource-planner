import { esc } from "../../utils.js";
import {
  apiFetch,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../../../modules/utils/utils.js";
import { toast } from "../../../modules/utils/toast.js";

/* ImportView  <import-view>
 *
 * Self-contained import workflow rendered inside a large <drawer-modal>.
 * On open: fetches specs-url to populate the file specification card.
 * Validate button: POST import-url?validate=true (dry run) — populates results tabs.
 * Import button:   POST import-url               (commit)  — populates results tabs.
 * Sample link:     direct navigation to sample-url (Content-Disposition: attachment).
 *
 * Attributes:
 *   title        – drawer title (default: "Import")
 *   eyebrow      – drawer eyebrow text (optional)
 *   specs-url    – GET endpoint that returns { data: { max_file_size_mb, max_rows,
 *                  supported_formats, fields, notes } }
 *   sample-url   – GET endpoint returning a CSV attachment (used as link href)
 *   import-url   – POST endpoint; accepts multipart/form-data with field "file";
 *                  append ?validate=true for dry run
 *   accept       – file extension filter for <file-import-field> (default: ".csv")
 *   max-size     – max file size in bytes forwarded to <file-import-field> (default: 5242880)
 *
 * Public API:
 *   view.show()  – opens the drawer
 *   view.hide()  – closes the drawer
 *
 * Data-attribute hooks (available after connect for external JS):
 *   [data-import-file]      – <file-import-field>
 *   [data-footer-secondary] – Validate button (managed by <drawer-modal> footer)
 *   [data-footer-primary]   – Import button (managed by <drawer-modal> footer)
 *   [data-results]          – results <tab-panel>
 *   [data-table-created]    – <data-table> (Created tab)
 *   [data-table-errors]     – <data-table> (Errors tab)
 *
 * Usage:
 *   <import-view id="teams-import"
 *     title="Import Teams"
 *     eyebrow="Teams"
 *     specs-url="/api/v1/teams/import/specs/"
 *     sample-url="/api/v1/teams/import/sample/"
 *     import-url="/api/v1/teams/import/">
 *   </import-view>
 *
 *   <secondary-button id="open-import" label="Import"></secondary-button>
 *
 *   document.getElementById("open-import").addEventListener("click", () => {
 *     document.getElementById("teams-import").show();
 *   });
 */
class ImportView extends HTMLElement {
  connectedCallback() {
    if (this._connected) return;
    this._connected = true;
    this._render();
    this._bindEvents();
  }

  show() {
    this.querySelector("drawer-modal")?.show();
  }

  hide() {
    this.querySelector("drawer-modal")?.hide();
  }

  // --- Render ---

  _render() {
    const title = esc(this.getAttribute("title") || "Import");
    const eyebrow = this.getAttribute("eyebrow");
    const accept = esc(this.getAttribute("accept") || ".csv");
    const maxSize = esc(this.getAttribute("max-size") || "5242880");

    const eyebrowAttr = eyebrow ? ` eyebrow="${esc(eyebrow)}"` : "";

    this.innerHTML = `
      <drawer-modal width="900">
        <drawer-header${eyebrowAttr} title="${title}" no-sizes></drawer-header>
        <drawer-panel name="main">
          <div class="row g-4 align-items-start">
            <div class="col-12 col-md-6 order-2 order-md-1">
              <section-panel>
                <panel-body>
                  <file-import-field
                    data-import-file
                    label="Import file"
                    required
                    accept="${accept}"
                    max-size="${maxSize}"
                    drop-label="Drop your CSV file here"
                    sub-text="Max 5 MB · CSV format · headers on row 1">
                  </file-import-field>
                </panel-body>
              </section-panel>
            </div>

            <div class="col-12 col-md-6 order-1 order-md-2">
              <card-panel variant="sunken">
                <panel-header>
                  <span class="rp-card-title">File specification</span>
                </panel-header>
                <panel-body>
                  <div data-specs>
                    <span style="font-size:13px;color:var(--rp-text-muted)">Loading specifications…</span>
                  </div>
                </panel-body>
              </card-panel>
            </div>
          </div>

          <div class="mt-4">
          <tab-panel data-results>
            <tab-items>
              <tab-item id="created" active>
                <tab-header title="Created" icon="bi-check-circle"></tab-header>
                <tab-content>
                  <data-table data-table-created empty-message="No rows created.">
                    <table-columns>
                      <table-column label="Row" key="row" width="80px" mono></table-column>
                      <table-column label="Field" key="field"></table-column>
                      <table-column label="Message" key="message"></table-column>
                    </table-columns>
                  </data-table>
                </tab-content>
              </tab-item>
              <tab-item id="errors">
                <tab-header title="Errors" icon="bi-exclamation-circle"></tab-header>
                <tab-content>
                  <data-table data-table-errors empty-message="No errors.">
                    <table-columns>
                      <table-column label="Row" key="row" width="80px" mono></table-column>
                      <table-column label="Field" key="field"></table-column>
                      <table-column label="Message" key="message"></table-column>
                    </table-columns>
                  </data-table>
                </tab-content>
              </tab-item>
            </tab-items>
          </tab-panel>
          </div>
        </drawer-panel>
        <drawer-footer
          close="Cancel"
          secondary="Validate"
          secondary-icon="bi-check2-circle"
          primary="Import"
          primary-icon="bi-cloud-upload">
        </drawer-footer>
      </drawer-modal>
    `;
  }

  // --- Event binding ---

  _bindEvents() {
    const drawer = this.querySelector("drawer-modal");
    const fileField = this.querySelector("[data-import-file]");

    // Footer buttons are rendered by drawer-modal; initialize both as disabled.
    const validateBtn = this.querySelector("[data-footer-secondary]");
    const importBtn = this.querySelector("[data-footer-primary]");
    validateBtn?.setAttribute("disabled", "");
    importBtn?.setAttribute("disabled", "");

    // Load specs each time the drawer opens.
    drawer?.addEventListener("rp:open", () => this._loadSpecs());

    // Enable Validate when a file is selected; reset Import until re-validated.
    fileField?.addEventListener("rp:change", (e) => {
      const hasFile = e.detail.files.length > 0;
      this.querySelector("[data-footer-secondary]")?.toggleAttribute("disabled", !hasFile);
      this.querySelector("[data-footer-primary]")?.setAttribute("disabled", "");
      this._validated = false;
    });

    drawer?.addEventListener("rp:footer-secondary", () => this._runImport(true));
    drawer?.addEventListener("rp:footer-primary", () => this._runImport(false));
  }

  // --- Specs ---

  async _loadSpecs() {
    const specsUrl = this.getAttribute("specs-url");
    if (!specsUrl) return;

    try {
      const res = await apiFetch(specsUrl);
      this._renderSpecs(res?.data ?? res);
    } catch {
      const specsEl = this.querySelector("[data-specs]");
      if (specsEl) {
        specsEl.innerHTML = `<span style="font-size:13px;color:var(--rp-text-muted)">Unable to load specifications.</span>`;
      }
    }
  }

  _renderSpecs(specs) {
    const specsEl = this.querySelector("[data-specs]");
    if (!specsEl || !specs) return;

    const sampleUrl = esc(this.getAttribute("sample-url") || "#");

    const TYPE_ICONS = {
      string: "bi-fonts",
      text: "bi-fonts",
      char: "bi-fonts",
      integer: "bi-123",
      int: "bi-123",
      number: "bi-123",
      float: "bi-123",
      decimal: "bi-123",
      boolean: "bi-toggle-on",
      bool: "bi-toggle-on",
      date: "bi-calendar",
      datetime: "bi-calendar-event",
      email: "bi-envelope",
      url: "bi-link-45deg",
    };

    const fieldsHTML = specs.fields?.length
      ? `<table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid var(--rp-border)">
           <thead>
             <tr style="background:var(--rp-bg-sunken)">
               <th style="padding:6px 8px;font-weight:600;color:var(--rp-text-muted);border:1px solid var(--rp-border)">Field</th>
               <th style="padding:6px 8px;font-weight:600;color:var(--rp-text-muted);border:1px solid var(--rp-border)">Type</th>
               <th style="padding:6px 8px;font-weight:600;color:var(--rp-text-muted);border:1px solid var(--rp-border);text-align:center">Req.</th>
               <th style="padding:6px 8px;font-weight:600;color:var(--rp-text-muted);border:1px solid var(--rp-border)">Description</th>
             </tr>
           </thead>
           <tbody>
             ${specs.fields
               .map((f) => {
                 const typeKey = String(f.type ?? "").toLowerCase();
                 const typeIcon = TYPE_ICONS[typeKey] ?? "bi-circle";
                 const reqIcon = f.required
                   ? `<i class="bi bi-check-circle-fill text-success" title="Required"></i>`
                   : `<i class="bi bi-dash-circle" style="color:var(--rp-text-subtle)" title="Optional"></i>`;
                 return `<tr>
                   <td style="padding:6px 8px;border:1px solid var(--rp-border);font-weight:500;color:var(--rp-text)">${esc(f.name)}</td>
                   <td style="padding:6px 8px;border:1px solid var(--rp-border);color:var(--rp-text-muted);white-space:nowrap">
                     <i class="bi ${esc(typeIcon)}" style="margin-right:3px"></i>${esc(f.type ?? "—")}
                   </td>
                   <td style="padding:6px 8px;border:1px solid var(--rp-border);text-align:center">${reqIcon}</td>
                   <td style="padding:6px 8px;border:1px solid var(--rp-border);color:var(--rp-text-muted)">${esc(f.description ?? "")}</td>
                 </tr>`;
               })
               .join("")}
           </tbody>
         </table>`
      : "";

    const notesHTML = specs.notes?.length
      ? `<ul class="mt-2 ps-3" style="font-size:12px;color:var(--rp-text-subtle);line-height:1.7">
           ${specs.notes.map((n) => `<li>${esc(n)}</li>`).join("")}
         </ul>`
      : "";

    specsEl.innerHTML = `
      ${fieldsHTML}
      ${notesHTML}
      <div class="mt-3">
        <link-field href="${sampleUrl}" icon="bi-download" style="font-size:13px">Download sample import file</link-field>
      </div>
    `;
  }

  // --- Import / Validate ---

  async _runImport(dryRun) {
    const fileField = this.querySelector("[data-import-file]");
    const files = fileField?.files;
    if (!files?.length) return;

    const importUrl = this.getAttribute("import-url");
    if (!importUrl) return;

    const validateBtn = this.querySelector("[data-footer-secondary]");
    const importBtn = this.querySelector("[data-footer-primary]");
    const btn = dryRun ? validateBtn : importBtn;

    const snap = snapshotButton(btn);
    setBusyButton(btn, dryRun ? "Validating…" : "Importing…");
    validateBtn?.setAttribute("disabled", "");
    importBtn?.setAttribute("disabled", "");

    const url = dryRun ? `${importUrl}?validate=true` : importUrl;
    const body = new FormData();
    body.append("file", files[0]);

    try {
      // Content-Type must not be set to application/json for multipart uploads —
      // passing undefined removes the apiFetch default so the browser sets the
      // correct multipart/form-data boundary automatically.
      const res = await apiFetch(url, {
        method: "POST",
        body,
        headers: { "Content-Type": undefined },
      });
      const result = res?.data ?? res;

      restoreButton(btn, snap);
      this._renderResults(result);

      if (dryRun) {
        this._validated = true;
        const hasErrors = (result.errors?.length ?? 0) > 0;
        importBtn?.toggleAttribute("disabled", hasErrors);
        validateBtn?.toggleAttribute("disabled", !files.length);
        toast({
          type: hasErrors ? "warning" : "success",
          title: "Validation complete",
          message: `${result.created_rows?.length ?? 0} rows ready · ${result.errors?.length ?? 0} errors.`,
        });
      } else {
        toast({
          type: "success",
          title: "Import complete",
          message: `${result.created_rows?.length ?? 0} rows imported.`,
        });
        this.hide();
        this.dispatchEvent(
          new CustomEvent("rp:import:complete", { bubbles: true, detail: { result } }),
        );
      }
    } catch (err) {
      restoreButton(btn, snap);
      const hasFile = (fileField?.files?.length ?? 0) > 0;
      validateBtn?.toggleAttribute("disabled", !hasFile);
      if (!dryRun && this._validated) {
        importBtn?.toggleAttribute("disabled", false);
      }
      const msg = err?.data?.error?.message ?? (dryRun ? "Validation failed." : "Import failed.");
      toast({ type: "error", title: dryRun ? "Validation error" : "Import error", message: msg });
    }
  }

  // --- Results ---

  _renderResults(result) {
    const tabPanel = this.querySelector("[data-results]");
    const tableCreated = this.querySelector("[data-table-created]");
    const tableErrors = this.querySelector("[data-table-errors]");

    const errors = result.errors ?? [];

    tabPanel?.updateCount?.("created", result.created_rows?.length || null);
    tabPanel?.updateCount?.("errors", errors.length || null);

    if (tableCreated) tableCreated.rows = result.created_rows ?? [];
    if (tableErrors) tableErrors.rows = errors;

    tabPanel?.setTab?.(errors.length > 0 ? "errors" : "created");
  }
}

customElements.define("import-view", ImportView);
