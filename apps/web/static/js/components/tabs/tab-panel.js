import { esc } from "../utils.js";

/* TabPanel  <tab-panel>
 *
 * Declarative tab component. Declarative children are parsed once on connect, then replaced
 * with rendered HTML. Panel content nodes are captured and re-inserted into slots so that
 * nested component state is preserved.
 *
 * Declarative children (captured before first render):
 *   <tab-items>
 *     <tab-item [id="…"] [active]>
 *       <tab-header title="…" [icon="bi-…"] [count="…"]>
 *       <tab-content>  ← arbitrary panel body content
 *     </tab-item>
 *   </tab-items>
 *
 * Public API:
 *   panel.setTab(id)              – switch to tab by id
 *   panel.updateCount(id, count)  – update a tab's count badge; pass "" or null to remove
 *   panel.activeTab               – getter: currently active tab id
 *
 * Events fired (all bubble):
 *   rp:tab-change  – tab switched; detail: { tab: id }
 */
class TabPanel extends HTMLElement {
  connectedCallback() {
    this._capture();
    this._render();
    this._bind();
  }

  // ── Public API ───────────────────────────────────────────────────────────

  setTab(id) {
    this._activeId = id;
    const url = new URL(window.location.href);
    url.searchParams.set("tab", id);
    history.replaceState(null, "", url);
    this.querySelectorAll("[data-tab]").forEach((btn) => {
      const active = btn.dataset.tab === id;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active);
    });
    this.querySelectorAll("[data-tab-panel]").forEach((panel) => {
      panel.hidden = panel.dataset.tabPanel !== id;
    });
    this.dispatchEvent(new CustomEvent("rp:tab-change", { bubbles: true, detail: { tab: id } }));
  }

  updateCount(id, count) {
    const btn = this.querySelector(`[data-tab="${CSS.escape(id)}"]`);
    if (!btn) return;
    let span = btn.querySelector(".rp-tab-count");
    if (count === null || count === undefined || count === "") {
      span?.remove();
    } else {
      if (!span) {
        span = document.createElement("span");
        span.className = "rp-tab-count";
        btn.appendChild(span);
      }
      span.textContent = count;
    }
  }

  get activeTab() {
    return this._activeId ?? null;
  }

  // ── Internals ────────────────────────────────────────────────────────────

  _capture() {
    this._tabs = Array.from(this.querySelectorAll("tab-item")).map((item, i) => {
      const hdr = item.querySelector("tab-header");
      const content = item.querySelector("tab-content");
      return {
        id: item.id || `tab-${i}`,
        icon: hdr?.getAttribute("icon") || "",
        title: hdr?.getAttribute("title") || `Tab ${i + 1}`,
        count: hdr?.getAttribute("count") || "",
        active: item.hasAttribute("active"),
        nodes: content ? Array.from(content.childNodes) : [],
      };
    });
  }

  _render() {
    if (!this._tabs.length) return;

    const urlTab = new URLSearchParams(window.location.search).get("tab");
    const matchedTab = urlTab && this._tabs.find((t) => t.id === urlTab);
    const activeId = (matchedTab ?? this._tabs.find((t) => t.active) ?? this._tabs[0]).id;
    this._activeId = activeId;

    const tabsBarHTML = `<div class="rp-tabs" role="tablist">${this._tabs
      .map((t) => {
        const iconHTML = t.icon ? `<i class="bi ${esc(t.icon)}" aria-hidden="true"></i>` : "";
        const countHTML = t.count ? `<span class="rp-tab-count">${esc(t.count)}</span>` : "";
        const isActive = t.id === activeId;
        return `<button class="rp-tab${isActive ? " is-active" : ""}" role="tab" aria-selected="${isActive}" aria-controls="rp-tabpanel-${esc(t.id)}" data-tab="${esc(t.id)}">${iconHTML}${esc(t.title)}${countHTML}</button>`;
      })
      .join("")}</div>`;

    const panelsHTML = this._tabs
      .map(
        (t) =>
          `<div id="rp-tabpanel-${esc(t.id)}" role="tabpanel" data-tab-panel="${esc(t.id)}"${t.id !== activeId ? " hidden" : ""}></div>`,
      )
      .join("");

    this.innerHTML = tabsBarHTML + panelsHTML;

    // Re-insert captured panel content into slots
    this._tabs.forEach((t) => {
      const slot = this.querySelector(`[data-tab-panel="${t.id}"]`);
      if (slot) t.nodes.forEach((node) => slot.appendChild(node));
    });
  }

  _bind() {
    this.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-tab]");
      if (btn) this.setTab(btn.dataset.tab);
    });

    // Arrow key navigation between tabs
    this.addEventListener("keydown", (e) => {
      const btn = e.target.closest("[data-tab]");
      if (!btn) return;
      const tabs = [...this.querySelectorAll("[data-tab]")];
      const idx = tabs.indexOf(btn);
      if (e.key === "ArrowRight" && idx < tabs.length - 1) {
        tabs[idx + 1].focus();
        this.setTab(tabs[idx + 1].dataset.tab);
        e.preventDefault();
      } else if (e.key === "ArrowLeft" && idx > 0) {
        tabs[idx - 1].focus();
        this.setTab(tabs[idx - 1].dataset.tab);
        e.preventDefault();
      }
    });
  }
}

customElements.define("tab-panel", TabPanel);
