import { esc } from "../utils.js";

/* ─────────────────────────────────────────────────────────────────────────
 * EmailView  <email-view>
 *
 * Read-only email preview component. Renders To, Cc, Subject metadata rows
 * followed by the HTML body of the email. All child elements are captured
 * once on connect, then replaced by the rendered output.
 *
 * Declarative children (read before first render, then discarded):
 *   <email-to-items [icon]>           – To recipients container
 *     <email-to-item value="">        – individual recipient (one per address)
 *   <email-cc-items [icon]>           – Cc recipients container (omit to hide row)
 *     <email-cc-item value="">        – individual recipient
 *   <email-subject [icon]>            – text content becomes the subject line
 *   <email-body>                      – innerHTML is the email body (trusted HTML)
 *
 * Child attributes:
 *   icon  – Bootstrap Icon class for the row label (e.g. "bi-person-fill").
 *           Defaults: To→bi-person-fill  Cc→bi-people-fill  Subject→bi-tag
 *
 * Notes:
 *   - <email-body> accepts arbitrary HTML; content must be trusted/application-generated.
 *   - The Cc row is omitted entirely when <email-cc-items> is absent.
 *   - Recipient values are escaped; subject text is escaped.
 * ───────────────────────────────────────────────────────────────────────── */
class EmailView extends HTMLElement {
  connectedCallback() {
    if (this._rendered) return;
    this._rendered = true;
    this._capture();
    this._render();
  }

  _capture() {
    const toEl = this.querySelector("email-to-items");
    const ccEl = this.querySelector("email-cc-items");
    const subjectEl = this.querySelector("email-subject");
    const bodyEl = this.querySelector("email-body");

    this._toIcon = toEl?.getAttribute("icon") || "bi-person-fill";
    this._toValues = toEl
      ? Array.from(toEl.querySelectorAll("email-to-item"))
          .map((el) => el.getAttribute("value") || "")
          .filter(Boolean)
      : [];

    this._hasCc = !!ccEl;
    this._ccIcon = ccEl?.getAttribute("icon") || "bi-people-fill";
    this._ccValues = ccEl
      ? Array.from(ccEl.querySelectorAll("email-cc-item"))
          .map((el) => el.getAttribute("value") || "")
          .filter(Boolean)
      : [];

    this._subjectIcon = subjectEl?.getAttribute("icon") || "bi-tag";
    this._subject = subjectEl?.textContent?.trim() || "";

    this._bodyHTML = bodyEl?.innerHTML || "";
  }

  _buildRecipientRow(icon, label, values) {
    if (!values.length) return "";
    const tags = values.map((v) => `<span class="rp-email-recipient">${esc(v)}</span>`).join("");
    return `<div class="rp-email-row">
      <div class="rp-email-row-label"><i class="bi ${esc(icon)}"></i>${esc(label)}</div>
      <div class="rp-email-row-value">${tags}</div>
    </div>`;
  }

  _buildSubjectRow() {
    if (!this._subject) return "";
    return `<div class="rp-email-row">
      <div class="rp-email-row-label"><i class="bi ${esc(this._subjectIcon)}"></i>Subject</div>
      <div class="rp-email-row-value rp-email-row-value--subject">${esc(this._subject)}</div>
    </div>`;
  }

  _render() {
    const toRow = this._buildRecipientRow(this._toIcon, "To", this._toValues);
    const ccRow = this._hasCc ? this._buildRecipientRow(this._ccIcon, "Cc", this._ccValues) : "";
    const subjectRow = this._buildSubjectRow();

    this.innerHTML = `<div class="rp-email-view">
      <div class="rp-email-meta">${toRow}${ccRow}${subjectRow}</div>
      <div class="rp-email-body">${this._bodyHTML}</div>
    </div>`;
  }
}

customElements.define("email-view", EmailView);
