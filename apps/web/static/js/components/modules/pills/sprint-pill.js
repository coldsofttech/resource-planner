import { esc } from "../../utils.js";

/* SprintPill: <sprint-pill>
 *
 * Displays the active sprint name and a live countdown to its end date.
 * The element itself carries the .rp-sprint-pill CSS class.
 *
 * Attributes:
 *   name    – sprint label (e.g. "S24.10"); element hides when omitted
 *   end     – ISO-8601 datetime of the sprint end (e.g. "2026-05-30T17:00:00")
 *   status  – "active" (default) | "warning" | "inactive" — controls dot colour
 *
 * Example:
 *   <sprint-pill name="S24.10" end="2026-05-30T17:00:00" status="active"></sprint-pill>
 */
class SprintPill extends HTMLElement {
  static get observedAttributes() {
    return ["name", "end", "status"];
  }

  connectedCallback() {
    this._connected = true;
    this._render();
    this._startTimer();
  }

  disconnectedCallback() {
    this._stopTimer();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._connected && oldVal !== newVal) {
      this._stopTimer();
      this._render();
      this._startTimer();
    }
  }

  get _sprintName() {
    return this.getAttribute("name") || "";
  }
  get _end() {
    return this.getAttribute("end") || "";
  }
  get _status() {
    return this.getAttribute("status") || "active";
  }

  _dotColor() {
    return (
      {
        active: "var(--rp-success)",
        warning: "var(--rp-warning)",
        inactive: "var(--rp-text-subtle)",
      }[this._status] ?? "var(--rp-success)"
    );
  }

  _countdown() {
    if (!this._end) return "";
    const diff = new Date(this._end).getTime() - Date.now();
    if (diff <= 0) return "Ended";
    const days = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    if (days > 0) return `${days}d ${hours}h`;
    const mins = Math.floor((diff % 3600000) / 60000);
    return `${hours}h ${mins}m`;
  }

  _render() {
    if (!this._sprintName) {
      this.style.display = "none";
      this.innerHTML = "";
      return;
    }

    this.style.display = "";
    this.className = "rp-sprint-pill";

    this.innerHTML = `
      <span class="rp-sprint-dot" style="background:${this._dotColor()}"></span>
      <span class="rp-sprint-name">${esc(this._sprintName)}</span>
      ${this._end ? `<span class="rp-sprint-time" data-sprint-time>${this._countdown()}</span>` : ""}
    `;
  }

  _tick() {
    const el = this.querySelector("[data-sprint-time]");
    if (el) el.textContent = this._countdown();
  }

  _startTimer() {
    if (!this._end || !this._sprintName) return;
    this._timer = setInterval(() => this._tick(), 60000);
  }

  _stopTimer() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }
}

customElements.define("sprint-pill", SprintPill);
