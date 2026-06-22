"use strict";

/* CommentsPager  <comments-pager>
 *
 * Pagination control for the comment list. Re-renders when attributes change.
 * Hidden automatically when total-pages <= 1.
 *
 * Attributes:
 *   current-page  — active page number (integer)
 *   total-pages   — total page count (integer)
 *
 * Events dispatched:
 *   rp:pager:change  — { page } — bubbles to <comments-panel>
 */
class CommentsPager extends HTMLElement {
  static get observedAttributes() {
    return ["current-page", "total-pages"];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(attr, oldVal, newVal) {
    if (oldVal !== newVal) this._render();
  }

  _render() {
    const cur = parseInt(this.getAttribute("current-page"), 10) || 1;
    const total = parseInt(this.getAttribute("total-pages"), 10) || 1;

    if (total <= 1) {
      this.innerHTML = "";
      this.hidden = true;
      return;
    }

    this.hidden = false;
    let btns = `<button class="rp-comment-pager-btn" data-page="${cur - 1}" ${cur === 1 ? "disabled" : ""} type="button">
      <i class="bi bi-chevron-left"></i>
    </button>`;

    let last = 0;
    for (let i = 1; i <= total; i++) {
      const inWindow = i >= cur - 2 && i <= cur + 2;
      if (i === 1 || i === total || inWindow) {
        if (last && i - last > 1) {
          btns += `<button class="rp-comment-pager-btn" disabled type="button">…</button>`;
        }
        btns += `<button
          class="rp-comment-pager-btn${i === cur ? " is-active" : ""}"
          data-page="${i}"
          type="button"
        >${i}</button>`;
        last = i;
      }
    }

    btns += `<button class="rp-comment-pager-btn" data-page="${cur + 1}" ${cur === total ? "disabled" : ""} type="button">
      <i class="bi bi-chevron-right"></i>
    </button>`;

    this.innerHTML = `<div class="rp-comment-pager">${btns}</div>`;

    this.querySelectorAll("[data-page]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const page = parseInt(btn.dataset.page, 10);
        if (!isNaN(page) && page >= 1 && page <= total) {
          this.dispatchEvent(
            new CustomEvent("rp:pager:change", { bubbles: true, detail: { page } }),
          );
        }
      });
    });
  }
}

if (!customElements.get("comments-pager")) {
  customElements.define("comments-pager", CommentsPager);
}
