import { esc } from "../utils.js";

/* StepWizard  <step-wizard>
 *
 * Multi-step form wizard with a sidebar step navigator and panel layout. Declarative child
 * structure is parsed once on connect, then replaced with rendered HTML. Body child nodes are
 * captured and re-inserted into panel slots so their component state is preserved.
 * Current step is synced to the URL via a query param (e.g. `?step=2`).
 *
 * Declarative children (captured before first render):
 *   <wizard-steps
 *     [title="…"]            – sidebar heading (default "Setup Steps")
 *     [estimated-time="…"]   – estimated time string shown in sidebar footer
 *     [show-progress]        – boolean; shows a progress bar in the sidebar
 *     [back-label="…"]       – Back button label (default "Back")
 *     [next-label="…"]       – Next button label (default "Next")
 *     [finish-label="…"]     – Finish button label on the last step (default "Finish")
 *   >
 *     <wizard-step
 *       nav-title="…"        – step label in the sidebar navigator
 *       [nav-subtitle="…"]   – secondary line in the sidebar navigator
 *     >
 *       <wizard-step-header icon="bi-…" title="…" subtitle="…">
 *       <wizard-step-body>   – child elements become the step's form fields
 *     </wizard-step>
 *   </wizard-steps>
 *
 * Attributes on <step-wizard>:
 *   name              – logical wizard name (used externally to identify the wizard)
 *   navigation        – "sequential" (default) | "free"; in sequential mode, steps can only be
 *                       accessed in order; in free mode, any step can be jumped to
 *   route-prefix      – query param name used for URL step sync (default "step")
 *   validate-on-next  – boolean; when present, fires `rp:validate` on the current panel before
 *                       advancing and blocks navigation if any field reports an error
 *
 * Public API:
 *   wizard.next()          – advance to the next step (validates if validate-on-next is set)
 *   wizard.back()          – go to the previous step
 *   wizard.goTo(index)     – jump to a step by 0-based index (sequential rules apply)
 *   wizard.currentIndex    – current active step index (read/write)
 *
 * Events fired (all bubble):
 *   rp:finish  – fired when the Finish button is clicked on the last step
 */
class StepWizard extends HTMLElement {
  connectedCallback() {
    this._build();
    this._collect();
    this._initState();
    this._applyRoute();
    this._render();
    this._bind();
  }

  _build() {
    const stepsEl = this.querySelector("wizard-steps");
    const stepEls = Array.from(this.querySelectorAll("wizard-step"));
    const total = stepEls.length;

    const steps = stepEls.map((el, i) => {
      const hdr = el.querySelector("wizard-step-header");
      const body = el.querySelector("wizard-step-body");
      return {
        navTitle: el.getAttribute("nav-title") || `Step ${i + 1}`,
        navSubtitle: el.getAttribute("nav-subtitle") || "",
        icon: hdr?.getAttribute("icon") || "",
        title: hdr?.getAttribute("title") || "",
        subtitle: hdr?.getAttribute("subtitle") || "",
        bodyNodes: body ? Array.from(body.children) : [],
      };
    });

    const sideLabel = stepsEl?.getAttribute("title") || "Setup Steps";
    const estTime = stepsEl?.getAttribute("estimated-time") || "";
    const showProgress = stepsEl?.hasAttribute("show-progress") ?? false;
    this._backLabel = stepsEl?.getAttribute("back-label") || "Back";
    this._nextLabel = stepsEl?.getAttribute("next-label") || "Next";
    this._finishLabel = stepsEl?.getAttribute("finish-label") || "Finish";

    const navHTML = steps
      .map(
        (s, i) => `
      <button class="rp-wiz-step" data-wiz-step data-wiz-go="${i}">
        <span class="num">${i + 1}</span>
        <span class="meta">${esc(s.navTitle)}${s.navSubtitle ? `<small>${esc(s.navSubtitle)}</small>` : ""}</span>
      </button>`,
      )
      .join("");

    const panelsHTML = steps
      .map(
        (s, i) => `
      <div class="rp-setup-panel" data-wiz-panel data-panel-slot="${i}">
        <div class="rp-setup-head">
          <div class="rp-step-icon"><i class="bi ${esc(s.icon)}"></i></div>
          <div>
            <div class="step-of"></div>
            <h3>${esc(s.title)}</h3>
            <div class="rp-setup-sub">${esc(s.subtitle)}</div>
          </div>
        </div>
        <div class="rp-setup-body">
          <div class="row g-3" data-body-slot="${i}"></div>
        </div>
        <div class="rp-setup-foot">
          <muted-button data-wiz-back prefix-icon="bi-arrow-left" label="${esc(this._backLabel)}"></muted-button>
          <primary-button data-wiz-next suffix-icon="bi-arrow-right" label="${esc(this._nextLabel)}"></primary-button>
        </div>
      </div>`,
      )
      .join("");

    this.innerHTML = `
      <div class="rp-setup-grid">
        <aside class="rp-setup-side">
          <div class="label">${esc(sideLabel)}</div>
          ${navHTML}
          ${
            showProgress
              ? `<div class="rp-setup-side-foot">
            <div class="d-flex justify-content-between" style="font-size:12px;color:var(--rp-text-muted)">
              <span>Progress</span>
              <span><strong class="cur" style="color:var(--rp-text)">1</strong> / <span class="total">${total}</span></span>
            </div>
            <div class="rp-progress rp-wiz-progress"><span></span></div>
            ${estTime ? `<div class="subtle" style="font-size:11px">Estimated time · ${esc(estTime)}</div>` : ""}
          </div>`
              : ""
          }
        </aside>
        <main class="rp-setup-main">${panelsHTML}</main>
      </div>`;

    steps.forEach((s, i) => {
      const row = this.querySelector(`[data-body-slot="${i}"]`);
      if (row) s.bodyNodes.forEach((node) => row.appendChild(node));
    });
  }

  _collect() {
    this.navButtons = Array.from(this.querySelectorAll("[data-wiz-step]"));
    this.panels = Array.from(this.querySelectorAll(".rp-setup-panel"));
    this.curEl = this.querySelector(".cur");
    this.totalEl = this.querySelector(".total");
    this.progressBar = this.querySelector(".rp-wiz-progress span");
  }

  _initState() {
    this.name = this.getAttribute("name");
    this.navigation = this.getAttribute("navigation") || "sequential";
    this.routePrefix = this.getAttribute("route-prefix") || "step";
    this.validateOnNext = this.hasAttribute("validate-on-next");
    this.currentIndex = 0;
    this._done = new Set(); // indices of steps that have been successfully passed
  }

  _applyRoute() {
    const raw = new URL(window.location).searchParams.get(this.routePrefix);
    if (raw !== null) {
      const i = parseInt(raw, 10);
      if (!isNaN(i) && i >= 0 && i < this.panels.length) this.currentIndex = i;
    }
  }

  _updateRoute() {
    const url = new URL(window.location);
    url.searchParams.set(this.routePrefix, this.currentIndex);
    window.history.replaceState({}, "", url);
  }

  next() {
    if (this.validateOnNext && !this._validateStep()) return;
    if (this.currentIndex < this.panels.length - 1) {
      this._done.add(this.currentIndex);
      this.currentIndex++;
      this._sync();
    }
  }

  back() {
    if (this.currentIndex > 0) {
      this._done.delete(this.currentIndex - 1);
      this.currentIndex--;
      this._sync();
    }
  }

  goTo(index) {
    if (this.navigation === "sequential" && index > this.currentIndex + 1) return;
    if (index < 0 || index >= this.panels.length) return;
    if (this.validateOnNext && index > this.currentIndex && !this._validateStep()) return;
    if (index > this.currentIndex) {
      this._done.add(this.currentIndex);
    } else {
      for (let j = index; j < this.currentIndex; j++) this._done.delete(j);
    }
    this.currentIndex = index;
    this._sync();
  }

  _sync() {
    this._render();
    this._updateRoute();
  }

  _validateStep() {
    const panel = this.panels[this.currentIndex];
    panel.dispatchEvent(new CustomEvent("rp:validate", { bubbles: true }));
    const fields = panel.querySelectorAll("input, select, textarea, [data-validate]");
    let valid = true;
    fields.forEach((f) => {
      if (f.closest("[hidden]")) return;
      if (typeof f.reportValidity === "function" && !f.reportValidity()) valid = false;
    });
    return valid;
  }

  _render() {
    const total = this.panels.length;
    const i = this.currentIndex;

    this.panels.forEach((p, idx) => p.classList.toggle("is-active", idx === i));
    this.navButtons.forEach((btn, idx) => {
      btn.classList.toggle("is-active", idx === i);
      btn.classList.toggle("is-done", this._done.has(idx) && idx !== i);
    });

    if (this.curEl) this.curEl.textContent = i + 1;
    if (this.totalEl) this.totalEl.textContent = total;
    if (this.progressBar) {
      const pct = total > 1 ? Math.round(((i + 1) / total) * 100) : 100;
      this.progressBar.style.width = `${pct}%`;
    }

    // Sync "Step N of M · Title" in every panel head
    this.panels.forEach((panel, idx) => {
      const stepOfEl = panel.querySelector(".step-of");
      if (!stepOfEl) return;
      const meta = this.navButtons[idx]?.querySelector(".meta");
      const title = meta?.firstChild?.textContent?.trim() || "";
      stepOfEl.textContent = `Step ${idx + 1} of ${total}${title ? " · " + title : ""}`;
    });

    const panel = this.panels[i];
    if (!panel) return;

    const backBtn = panel.querySelector("[data-wiz-back]");
    if (backBtn) {
      if (i === 0) backBtn.setAttribute("disabled", "");
      else backBtn.removeAttribute("disabled");
    }

    const nextBtn = panel.querySelector("[data-wiz-next]");
    if (nextBtn) {
      const isLast = i === total - 1;
      nextBtn.setAttribute("label", isLast ? this._finishLabel : this._nextLabel);
      nextBtn.setAttribute("suffix-icon", isLast ? "bi-check2" : "bi-arrow-right");
    }

    this._applyMobileNav(i, total);
  }

  _applyMobileNav(i, total) {
    this.querySelectorAll(".rp-wiz-ellipsis").forEach((el) => el.remove());

    if (total <= 5) {
      this.navButtons.forEach((btn) => btn.removeAttribute("data-wiz-mobile-hidden"));
      return;
    }

    const visible = new Set([0, total - 1, i]);
    if (i - 1 >= 0) visible.add(i - 1);
    if (i + 1 < total) visible.add(i + 1);

    this.navButtons.forEach((btn, idx) => {
      if (visible.has(idx)) btn.removeAttribute("data-wiz-mobile-hidden");
      else btn.setAttribute("data-wiz-mobile-hidden", "");
    });

    const sorted = [...visible].sort((a, b) => a - b);
    for (let k = 0; k < sorted.length - 1; k++) {
      if (sorted[k + 1] - sorted[k] > 1) {
        const ellipsis = document.createElement("span");
        ellipsis.className = "rp-wiz-ellipsis";
        ellipsis.setAttribute("aria-hidden", "true");
        ellipsis.textContent = "…";
        this.navButtons[sorted[k]].after(ellipsis);
      }
    }
  }

  _bind() {
    this.addEventListener("click", (e) => {
      const navBtn = e.target.closest("button[data-wiz-go]");
      if (navBtn && !navBtn.disabled) {
        this.goTo(parseInt(navBtn.getAttribute("data-wiz-go"), 10));
        return;
      }

      const nextEl = e.target.closest("[data-wiz-next]");
      if (nextEl) {
        if (!nextEl.querySelector("button")?.disabled) {
          if (this.currentIndex === this.panels.length - 1) {
            this.dispatchEvent(new CustomEvent("rp:finish", { bubbles: true }));
          } else {
            this.next();
          }
        }
        return;
      }
      const backEl = e.target.closest("[data-wiz-back]");
      if (backEl) {
        if (!backEl.querySelector("button")?.disabled) this.back();
        return;
      }
    });

    window.addEventListener("popstate", () => {
      this._applyRoute();
      this._render();
    });
  }
}

customElements.define("step-wizard", StepWizard);
