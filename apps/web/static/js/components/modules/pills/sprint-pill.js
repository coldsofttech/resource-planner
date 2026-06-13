import { esc } from "../../utils.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* SprintPill: <sprint-pill>
 *
 * Displays the active (In Progress) sprint name and a live countdown to its
 * end date. Fetches GET /api/v1/sprints/active/ on every connect — no external
 * attributes required. The element hides itself when there is no active sprint
 * or when the request fails.
 *
 * The dot colour reflects sprint health:
 *   green  – in progress, more than 3 days remaining
 *   amber  – in progress, 3 days or fewer remaining
 *   muted  – sprint not in progress (should not normally be visible)
 *
 * Example:
 *   <sprint-pill id="active-sprint"></sprint-pill>
 */
class SprintPill extends HTMLElement {
  connectedCallback() {
    this._connected = true;
    this.style.display = "none";
    this._loadId = Symbol();
    this._fetchActive(this._loadId);
    this._startTimer();
  }

  disconnectedCallback() {
    this._connected = false;
    this._loadId = Symbol();
    this._stopTimer();
  }

  async _fetchActive(id) {
    try {
      const { href, method } = API_URLS.sprints.active();
      const res = await apiFetch(href, { method });
      if (!this._connected || this._loadId !== id) return;
      const sprint = res?.data;
      if (!sprint) {
        this._hide();
        return;
      }
      this._sprintData = {
        name: sprint.name,
        end: sprint.end_date,
        statusKey: sprint.status,
      };
      this._render();
    } catch {
      if (!this._connected || this._loadId !== id) return;
      this._hide();
    }
  }

  _dotColor() {
    const { statusKey, end } = this._sprintData ?? {};
    if (statusKey !== "in_progress") return "var(--rp-text-subtle)";
    const daysLeft = (new Date(end).getTime() - Date.now()) / 86400000;
    return daysLeft <= 3 ? "var(--rp-warning)" : "var(--rp-success)";
  }

  _countdown() {
    const end = this._sprintData?.end;
    if (!end) return "";
    const diff = new Date(end).getTime() - Date.now();
    if (diff <= 0) return "Ended";
    const days = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    if (days > 0) return `${days}d ${hours}h`;
    const mins = Math.floor((diff % 3600000) / 60000);
    return `${hours}h ${mins}m`;
  }

  _render() {
    const name = this._sprintData?.name;
    if (!name) {
      this._hide();
      return;
    }
    this.style.display = "";
    this.className = "rp-sprint-pill";
    const end = this._sprintData?.end;
    this.innerHTML = `
      <span class="rp-sprint-dot" style="background:${this._dotColor()}"></span>
      <span class="rp-sprint-name">${esc(name)}</span>
      ${end ? `<span class="rp-sprint-time" data-sprint-time>${this._countdown()}</span>` : ""}
    `;
  }

  _hide() {
    this.style.display = "none";
    this.innerHTML = "";
  }

  _tick() {
    const el = this.querySelector("[data-sprint-time]");
    if (el) el.textContent = this._countdown();
  }

  _startTimer() {
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
