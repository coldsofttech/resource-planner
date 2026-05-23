/* Wizard: <rp-wizard> */
class Wizard extends HTMLElement {
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
        <span class="meta">${this._esc(s.navTitle)}${s.navSubtitle ? `<small>${this._esc(s.navSubtitle)}</small>` : ""}</span>
      </button>`,
      )
      .join("");

    const panelsHTML = steps
      .map(
        (s, i) => `
      <div class="rp-setup-panel" data-wiz-panel data-panel-slot="${i}">
        <div class="rp-setup-head">
          <div class="rp-step-icon"><i class="bi ${this._esc(s.icon)}"></i></div>
          <div>
            <div class="step-of"></div>
            <h3>${this._esc(s.title)}</h3>
            <div class="rp-setup-sub">${this._esc(s.subtitle)}</div>
          </div>
        </div>
        <div class="rp-setup-body">
          <div class="row g-3" data-body-slot="${i}"></div>
        </div>
        <div class="rp-setup-foot">
          <rp-button-muted data-wiz-back prefix-icon="bi-arrow-left" label="${this._esc(this._backLabel)}"></rp-button-muted>
          <rp-button-primary data-wiz-next suffix-icon="bi-arrow-right" label="${this._esc(this._nextLabel)}"></rp-button-primary>
        </div>
      </div>`,
      )
      .join("");

    this.innerHTML = `
      <div class="rp-setup-grid">
        <aside class="rp-setup-side">
          <div class="label">${this._esc(sideLabel)}</div>
          ${navHTML}
          ${
            showProgress
              ? `<div class="rp-setup-side-foot">
            <div class="d-flex justify-content-between" style="font-size:12px;color:var(--rp-text-muted)">
              <span>Progress</span>
              <span><strong class="cur" style="color:var(--rp-text)">1</strong> / <span class="total">${total}</span></span>
            </div>
            <div class="rp-progress rp-wiz-progress"><span></span></div>
            ${estTime ? `<div class="subtle" style="font-size:11px">Estimated time · ${this._esc(estTime)}</div>` : ""}
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

  _esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  _collect() {
    this.navButtons = Array.from(this.querySelectorAll("[data-wiz-step]"));
    this.panels = Array.from(this.querySelectorAll(".rp-setup-panel"));
    this.curEl = this.querySelector(".cur");
    this.totalEl = this.querySelector(".total");
    this.progressBar = this.querySelector(".rp-wiz-progress span");
  }

  _initState() {
    this.fieldId = this.getAttribute("field-id");
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
        if (!nextEl.querySelector("button")?.disabled) this.next();
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

customElements.define("rp-wizard", Wizard);

/* WizardSteps: <wizard-steps> */
class WizardSteps extends HTMLElement {}

customElements.define("wizard-steps", WizardSteps);

/* WizardStep: <wizard-step> */
class WizardStep extends HTMLElement {}

customElements.define("wizard-step", WizardStep);

/* WizardStepHeader: <wizard-step-header> */
class WizardStepHeader extends HTMLElement {}

customElements.define("wizard-step-header", WizardStepHeader);

/* WizardStepBody: <wizard-step-body> */
class WizardStepBody extends HTMLElement {}

customElements.define("wizard-step-body", WizardStepBody);

/* WizardStepFooter: <wizard-step-footer> */
class WizardStepFooter extends HTMLElement {}

customElements.define("wizard-step-footer", WizardStepFooter);
