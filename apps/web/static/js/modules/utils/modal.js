const TYPE_CONFIG = {
  info: { cssClass: "info", icon: "bi-info-circle" },
  success: { cssClass: "success", icon: "bi-check-circle" },
  warning: { cssClass: "warning", icon: "bi-exclamation-triangle" },
  error: { cssClass: "danger", icon: "bi-x-circle" },
};

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

class StatusModal {
  constructor() {
    this._el = null;
    this._cfg = {};
  }

  open(config = {}) {
    this._cfg = { ...config };
    if (!this._el) this._mount();
    this._el.style.display = "grid";
    this._el.style.placeItems = "center";
    this._render();
  }

  update(patch = {}) {
    this._cfg = { ...this._cfg, ...patch };
    if (this._el) this._render();
  }

  close() {
    if (this._el) this._el.style.display = "none";
  }

  _mount() {
    this._el = document.createElement("div");
    this._el.id = "rp-modal-status-overlay";

    // Apply backdrop layout inline so positioning works before modals.css is built.
    const s = this._el.style;
    s.position = "fixed";
    s.inset = "0";
    s.zIndex = "100";
    s.padding = "20px";
    s.background = "rgba(15,23,42,0.45)";
    s.backdropFilter = "blur(2px)";
    s.placeItems = "center";
    s.display = "none";

    document.body.appendChild(this._el);
    this._el.addEventListener("click", (e) => {
      if (e.target === this._el && this._cfg.closeable !== false) this.close();
    });
  }

  _btnHTML(cfg, slot, variant) {
    if (!cfg) return "";
    const icon = cfg.icon ? `<i class="bi ${esc(cfg.icon)}"></i>` : "";
    const disabled = cfg.disabled ? " disabled" : "";
    return `<button class="rp-btn ${variant}" data-modal-btn="${slot}"${disabled}>${icon}${esc(cfg.label ?? "")}</button>`;
  }

  _render() {
    const {
      iconType = "info",
      icon,
      iconBgColor,
      title = "",
      body = "",
      additionalBody = "",
      closeable = true,
      dismissBtn,
      secondaryBtn,
      primaryBtn,
    } = this._cfg;

    const t = TYPE_CONFIG[iconType] ?? TYPE_CONFIG.info;
    const iconCls = icon ?? t.icon;
    const iconStyle = iconBgColor ? ` style="background:${esc(iconBgColor)}"` : "";

    const closeBtn = closeable
      ? `<button class="rp-iconbtn" data-modal-btn="close" style="position:absolute;top:10px;right:10px;z-index:1"><i class="bi bi-x-lg"></i></button>`
      : "";

    const foot = [
      this._btnHTML(dismissBtn, "dismiss", "rp-btn-muted"),
      this._btnHTML(secondaryBtn, "secondary", "rp-btn-secondary"),
      this._btnHTML(primaryBtn, "primary", "rp-btn-primary"),
    ].join("");

    this._el.className = `rp-modal-back rp-status-modal ${t.cssClass}`;
    this._el.innerHTML = `
      <div class="rp-modal" style="position:relative">
        ${closeBtn}
        <div class="rp-status-hero">
          <div class="rp-status-icon"${iconStyle}><i class="bi ${esc(iconCls)}"></i></div>
          <h3>${esc(title)}</h3>
          ${body ? `<p>${esc(body)}</p>` : ""}
        </div>
        ${additionalBody ? `<div class="rp-status-additional">${additionalBody}</div>` : ""}
        ${foot ? `<div class="rp-modal-foot">${foot}</div>` : ""}
      </div>`;

    this._el
      .querySelector('[data-modal-btn="close"]')
      ?.addEventListener("click", () => this.close());

    this._el
      .querySelector('[data-modal-btn="dismiss"]')
      ?.addEventListener("click", () =>
        dismissBtn?.onClick ? dismissBtn.onClick() : this.close(),
      );

    this._el
      .querySelector('[data-modal-btn="secondary"]')
      ?.addEventListener("click", () => secondaryBtn?.onClick?.());

    const primaryEl = this._el.querySelector('[data-modal-btn="primary"]');
    if (primaryEl) {
      primaryEl.addEventListener("click", () => {
        if (primaryBtn?.href) window.location.href = primaryBtn.href;
        else primaryBtn?.onClick?.();
      });
    }
  }
}

export const rpStatusModal = new StatusModal();
