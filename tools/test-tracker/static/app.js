/* ── State ───────────────────────────────────────────────────────────────────── */
const S = {
  modules: [],
  activeSlug: null,
  view: "cases", // "cases" | "summary"
  suites: [],
  summary: null,
  customCases: [],
  filter: { search: "", status: "all", severity: "all" },
};

/* ── API ─────────────────────────────────────────────────────────────────────── */
async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(path, opts);
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}

/* ── Utilities ───────────────────────────────────────────────────────────────── */
function timeAgo(iso) {
  if (!iso) return null;
  const ms = Date.now() - new Date(iso.includes("Z") ? iso : iso + "Z").getTime();
  const m = Math.floor(ms / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function fmtFull(iso) {
  if (!iso) return "";
  return new Date(iso.includes("Z") ? iso : iso + "Z").toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function passRate(s) {
  return s.total ? Math.round((s.pass / s.total) * 100) : 0;
}

function esc(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function statusLabel(s) {
  return { pass: "Pass", fail: "Fail", blocked: "Blocked", skip: "Skip" }[s] || "Not Run";
}
function statusCls(s) {
  return s ? `s-${s}` : "s-not-run";
}

/* ── Sidebar ─────────────────────────────────────────────────────────────────── */
function renderSidebar() {
  const list = document.getElementById("module-list");
  if (!S.modules.length) {
    list.innerHTML = `<div style="padding:16px;color:var(--text-m);font-size:12px">No modules found.</div>`;
    return;
  }

  // Group modules by parent, preserving the server-supplied order
  const parentOrder = [];
  const groups = {};
  for (const m of S.modules) {
    const pk = m.parent_slug || "";
    if (!groups[pk]) {
      groups[pk] = { name: m.parent_name || null, modules: [] };
      parentOrder.push(pk);
    }
    groups[pk].modules.push(m);
  }

  list.innerHTML = parentOrder
    .map((pk) => {
      const g = groups[pk];
      const items = g.modules
        .map((m) => {
          const pct = passRate(m.stats);
          const active = m.slug === S.activeSlug ? " active" : "";
          return `
          <div class="mod-item${active}" data-slug="${esc(m.slug)}">
            <div class="mod-name">${esc(m.name)}</div>
            <div class="mod-stats">
              <span class="mod-stat ms-total">${m.stats.total} cases</span>
              ${m.stats.pass ? `<span class="mod-stat ms-pass">✓${m.stats.pass}</span>` : ""}
              ${m.stats.fail ? `<span class="mod-stat ms-fail">✗${m.stats.fail}</span>` : ""}
              ${m.stats.blocked ? `<span class="mod-stat ms-blk">⊘${m.stats.blocked}</span>` : ""}
              ${m.stats.total !== m.stats.not_run ? `<span class="mod-stat ms-pct">${pct}%</span>` : ""}
            </div>
          </div>`;
        })
        .join("");

      return g.name
        ? `<div class="mod-group"><div class="mod-group-hdr">${esc(g.name)}</div>${items}</div>`
        : items;
    })
    .join("");

  list
    .querySelectorAll(".mod-item")
    .forEach((el) => el.addEventListener("click", () => selectModule(el.dataset.slug)));
}

/* ── Module header (shared) ──────────────────────────────────────────────────── */
function moduleHeader(name) {
  return `
    <div class="mod-hdr">
      <div class="mod-hdr-title">${esc(name)}</div>
      <div class="mod-hdr-actions">
        <div class="tabs">
          <button class="tab${S.view === "cases" ? " active" : ""}" data-view="cases">Test Cases</button>
          <button class="tab${S.view === "summary" ? " active" : ""}" data-view="summary">Summary</button>
        </div>
        <button class="btn-add-case" id="btn-add-case" title="Log a new test scenario found during testing">+ Add Test Case</button>
        <button class="btn-clear-module" id="btn-clear-module" title="Reset all results to Not Run">Clear Results</button>
      </div>
    </div>`;
}

function bindTabs() {
  document
    .querySelectorAll(".tab[data-view]")
    .forEach((btn) => btn.addEventListener("click", () => switchView(btn.dataset.view)));
  const clearBtn = document.getElementById("btn-clear-module");
  if (clearBtn) clearBtn.addEventListener("click", clearModule);
  const addBtn = document.getElementById("btn-add-case");
  if (addBtn) addBtn.addEventListener("click", openAddModal);
}

async function switchView(view) {
  if (view === S.view) return;
  S.view = view;
  if (view === "summary") {
    await loadSummary();
  } else {
    renderCases();
  }
}

/* ── Summary view ────────────────────────────────────────────────────────────── */
async function loadSummary() {
  setMainLoading();
  S.summary = await api("GET", `/api/modules/${S.activeSlug}/summary`);
  renderSummary();
}

function renderSummary() {
  const { module: mod, overall: o, suites } = S.summary;
  const pct = passRate(o);
  const exec = o.total - o.not_run;
  const W = o.total;

  const seg = (val, cls) =>
    val
      ? `<div class="prog-seg prog-${cls}" style="width:${((val / W) * 100).toFixed(1)}%"></div>`
      : "";

  document.getElementById("main").innerHTML = `
    ${moduleHeader(mod.name)}

    <div class="cards">
      <div class="card total">  <div class="card-val">${o.total}</div>   <div class="card-lbl">Total</div>   </div>
      <div class="card pass">   <div class="card-val">${o.pass}</div>    <div class="card-lbl">Pass</div>    </div>
      <div class="card fail">   <div class="card-val">${o.fail}</div>    <div class="card-lbl">Fail</div>    </div>
      <div class="card blocked"><div class="card-val">${o.blocked}</div> <div class="card-lbl">Blocked</div> </div>
      <div class="card skip">   <div class="card-val">${o.skip}</div>    <div class="card-lbl">Skip</div>    </div>
      <div class="card not-run"><div class="card-val">${o.not_run}</div> <div class="card-lbl">Not Run</div> </div>
    </div>

    <div class="prog-wrap">
      <div class="prog-meta">
        <span class="prog-meta-lbl">Pass Rate — ${pct}%</span>
        <span class="prog-meta-val">
          ${exec} of ${o.total} executed
          ${o.last_tested ? ` · Last run ${timeAgo(o.last_tested)}` : ""}
        </span>
      </div>
      <div class="prog-track">
        ${seg(o.pass, "pass")}${seg(o.fail, "fail")}${seg(o.blocked, "blocked")}${seg(o.skip, "skip")}
      </div>
    </div>

    <div class="sum-tbl-wrap">
      <table class="sum-tbl">
        <thead>
          <tr>
            <th>Suite</th><th>Total</th><th>Pass</th><th>Fail</th>
            <th>Blocked</th><th>Skip</th><th>Not Run</th><th>Rate</th>
          </tr>
        </thead>
        <tbody>
          ${suites
            .map(
              (s) => `
            <tr>
              <td><strong>${esc(s.id)}</strong> — ${esc(s.name)}</td>
              <td>${s.total}</td>
              <td class="${s.pass ? "c-pass" : "c-muted"}">${s.pass || "—"}</td>
              <td class="${s.fail ? "c-fail" : "c-muted"}">${s.fail || "—"}</td>
              <td class="${s.blocked ? "c-blocked" : "c-muted"}">${s.blocked || "—"}</td>
              <td class="c-muted">${s.skip || "—"}</td>
              <td class="c-muted">${s.not_run || "—"}</td>
              <td>${s.total ? Math.round((s.pass / s.total) * 100) + "%" : "—"}</td>
            </tr>`,
            )
            .join("")}
        </tbody>
      </table>
    </div>`;

  bindTabs();
  updateHdrMeta();
}

/* ── Cases view ──────────────────────────────────────────────────────────────── */
function renderCases() {
  const mod = S.modules.find((m) => m.slug === S.activeSlug);
  if (!mod) return;

  document.getElementById("main").innerHTML = `
    ${moduleHeader(mod.name)}
    ${filterBar()}
    <div id="suites-container">
      ${S.suites.map((suite) => renderSuite(suite)).join("")}
    </div>
    <div id="empty-filter" style="display:none; padding:40px; text-align:center; color:var(--text-m)">
      No test cases match the current filters.
    </div>
    <div id="custom-section" class="custom-section"></div>`;

  bindTabs();
  bindFilterBar();
  bindSuites();
  resizeAllTextareas();
  applyFilters();
  renderCustomSection();
}

function filterBar() {
  return `
    <div class="filter-bar">
      <input class="filter-search" type="search" placeholder="Search scenarios…"
             value="${esc(S.filter.search)}" id="f-search" />
      <select class="filter-select" id="f-status">
        <option value="all"     ${S.filter.status === "all" ? "selected" : ""}>All statuses</option>
        <option value="not_run" ${S.filter.status === "not_run" ? "selected" : ""}>Not Run</option>
        <option value="pass"    ${S.filter.status === "pass" ? "selected" : ""}>Pass</option>
        <option value="fail"    ${S.filter.status === "fail" ? "selected" : ""}>Fail</option>
        <option value="blocked" ${S.filter.status === "blocked" ? "selected" : ""}>Blocked</option>
        <option value="skip"    ${S.filter.status === "skip" ? "selected" : ""}>Skip</option>
      </select>
      <select class="filter-select" id="f-sev">
        <option value="all" ${S.filter.severity === "all" ? "selected" : ""}>All severities</option>
        <option value="P0"  ${S.filter.severity === "P0" ? "selected" : ""}>P0 — Critical</option>
        <option value="P1"  ${S.filter.severity === "P1" ? "selected" : ""}>P1 — High</option>
        <option value="P2"  ${S.filter.severity === "P2" ? "selected" : ""}>P2 — Medium</option>
        <option value="P3"  ${S.filter.severity === "P3" ? "selected" : ""}>P3 — Low</option>
      </select>
      <span class="filter-count" id="f-count"></span>
      <button class="filter-reset" id="f-reset">Reset</button>
    </div>`;
}

function bindFilterBar() {
  const s = document.getElementById("f-search");
  const st = document.getElementById("f-status");
  const sv = document.getElementById("f-sev");
  const rs = document.getElementById("f-reset");

  s.addEventListener("input", () => {
    S.filter.search = s.value;
    applyFilters();
  });
  st.addEventListener("change", () => {
    S.filter.status = st.value;
    applyFilters();
  });
  sv.addEventListener("change", () => {
    S.filter.severity = sv.value;
    applyFilters();
  });
  rs.addEventListener("click", () => {
    S.filter = { search: "", status: "all", severity: "all" };
    s.value = "";
    st.value = "all";
    sv.value = "all";
    applyFilters();
  });
}

function applyFilters() {
  const { search, status, severity } = S.filter;
  let visible = 0;

  document.querySelectorAll(".tc-tbl tbody tr[data-tc-id]").forEach((row) => {
    const id = row.dataset.tcId;
    const tc = findTc(id);
    if (!tc) return;

    const matchSearch =
      !search ||
      tc.scenario.toLowerCase().includes(search.toLowerCase()) ||
      id.toLowerCase().includes(search.toLowerCase());
    const matchStatus =
      status === "all" || (status === "not_run" ? !tc.status : tc.status === status);
    const matchSev = severity === "all" || tc.severity === severity;

    const show = matchSearch && matchStatus && matchSev;
    row.classList.toggle("hidden", !show);
    if (show) visible++;
  });

  // Update suite mini-bar counts & hide empty suites
  S.suites.forEach((suite) => {
    const sec = document.querySelector(`.suite[data-sid="${suite.id}"]`);
    if (!sec) return;
    const shown = sec.querySelectorAll(".tc-tbl tbody tr[data-tc-id]:not(.hidden)").length;
    sec.style.display = shown === 0 ? "none" : "";

    // Mini progress bar
    const run = suite.cases.filter((c) => c.status).length;
    const fill = sec.querySelector(".suite-mini-fill");
    if (fill) fill.style.width = suite.cases.length ? `${(run / suite.cases.length) * 100}%` : "0%";

    const cnt = sec.querySelector(".suite-count");
    if (cnt) cnt.textContent = `${run}/${suite.cases.length}`;
  });

  const fc = document.getElementById("f-count");
  if (fc) fc.textContent = `${visible} case${visible !== 1 ? "s" : ""}`;
  const ef = document.getElementById("empty-filter");
  if (ef) ef.style.display = visible === 0 ? "" : "none";
}

function findTc(id) {
  for (const s of S.suites) {
    const tc = s.cases.find((c) => c.id === id);
    if (tc) return tc;
  }
  return null;
}

/* ── Suite rendering ─────────────────────────────────────────────────────────── */
function renderSuite(suite) {
  const run = suite.cases.filter((c) => c.status).length;
  const pct = suite.cases.length ? (run / suite.cases.length) * 100 : 0;
  return `
    <div class="suite" data-sid="${esc(suite.id)}">
      <div class="suite-hdr">
        <span class="suite-chev">▶</span>
        <span class="suite-id">${esc(suite.id)}</span>
        <span class="suite-name">${esc(suite.name)}</span>
        <div class="suite-prog">
          <div class="suite-mini-bar"><div class="suite-mini-fill" style="width:${pct.toFixed(1)}%"></div></div>
          <span class="suite-count">${run}/${suite.cases.length}</span>
        </div>
      </div>
      <div class="suite-body">
        <table class="tc-tbl">
          <thead>
            <tr>
              <th>ID</th><th>Scenario</th><th>Sev</th>
              <th>Status</th><th>Notes</th><th>Last Tested</th><th></th>
            </tr>
          </thead>
          <tbody>
            ${suite.cases.map((tc) => renderTcRow(tc)).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
}

function renderTcRow(tc) {
  const ago = tc.tested_at ? timeAgo(tc.tested_at) : null;
  const hasDetail = tc.steps || tc.expected;
  const sel = (val, lbl, cur) =>
    `<option value="${val}"${cur === val ? " selected" : ""}>${lbl}</option>`;

  return `
    <tr data-tc-id="${esc(tc.id)}">
      <td class="tc-id-cell" data-label="ID">
        <div class="tc-id-content">
          <span class="tc-id-val">${esc(tc.id)}</span>
          <button class="tc-id-hist" data-tc="${esc(tc.id)}">history</button>
        </div>
      </td>
      <td class="tc-scen-cell" data-label="Scenario">
        <div class="tc-scen-content">
          <div class="tc-scen-text">${esc(tc.scenario)}</div>
          ${
            hasDetail
              ? `
            <button class="tc-detail-btn" data-tc="${esc(tc.id)}">▸ steps &amp; expected</button>
            <div class="tc-detail" id="det-${esc(tc.id)}">
              ${tc.steps ? `<div class="tc-detail-row"><div class="tc-detail-lbl">Steps</div><div class="tc-detail-val">${esc(tc.steps)}</div></div>` : ""}
              ${tc.expected ? `<div class="tc-detail-row"><div class="tc-detail-lbl">Expected</div><div class="tc-detail-val">${esc(tc.expected)}</div></div>` : ""}
            </div>`
              : ""
          }
        </div>
      </td>
      <td class="tc-sev-cell" data-label="Sev"><span class="sev sev-${esc(tc.severity)}">${esc(tc.severity)}</span></td>
      <td class="tc-status-cell" data-label="Status">
        <select class="status-sel ${statusCls(tc.status)}" data-tc="${esc(tc.id)}">
          ${sel("", "Not Run", tc.status || "")}
          ${sel("pass", "Pass", tc.status)}
          ${sel("fail", "Fail", tc.status)}
          ${sel("blocked", "Blocked", tc.status)}
          ${sel("skip", "Skip", tc.status)}
        </select>
      </td>
      <td class="tc-notes-cell" data-label="Notes">
        <textarea class="notes-ta" data-tc="${esc(tc.id)}"
                  placeholder="Add notes…" rows="1">${esc(tc.notes || "")}</textarea>
      </td>
      <td class="tc-ts-cell" id="ts-${esc(tc.id)}" data-label="Tested">
        ${
          ago
            ? `<span title="${fmtFull(tc.tested_at)}">${ago}</span>`
            : `<span class="ts-never">—</span>`
        }
      </td>
      <td class="tc-ind-cell"><span class="ind" id="ind-${esc(tc.id)}"></span></td>
    </tr>`;
}

/* ── Suite interaction ───────────────────────────────────────────────────────── */
function bindSuites() {
  // Collapse / expand
  document.querySelectorAll(".suite-hdr").forEach((hdr) => {
    hdr.addEventListener("click", () => hdr.classList.toggle("collapsed"));
  });

  // Detail expand
  document.querySelectorAll(".tc-detail-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const det = document.getElementById(`det-${btn.dataset.tc}`);
      const open = det.classList.toggle("open");
      btn.textContent = (open ? "▾" : "▸") + " steps & expected";
    });
  });

  // History
  document.querySelectorAll(".tc-id-hist").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openHistory(btn.dataset.tc);
    });
  });

  // Status select → save, or clear when set back to Not Run
  document.querySelectorAll(".status-sel").forEach((sel) => {
    sel.addEventListener("change", async () => {
      const notes = document.querySelector(`.notes-ta[data-tc="${sel.dataset.tc}"]`)?.value || "";
      if (!sel.value) {
        await doClear(sel.dataset.tc);
      } else {
        await doSave(sel.dataset.tc, sel.value, notes);
      }
    });
  });

  // Notes textarea → save on blur when status is set
  document.querySelectorAll(".notes-ta").forEach((ta) => {
    ta.addEventListener("input", () => autoResize(ta));
    ta.addEventListener("blur", async () => {
      const sel = document.querySelector(`.status-sel[data-tc="${ta.dataset.tc}"]`);
      if (sel?.value) await doSave(ta.dataset.tc, sel.value, ta.value);
    });
  });
}

function autoResize(ta) {
  ta.style.height = "auto";
  ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
}

function resizeAllTextareas() {
  document.querySelectorAll(".notes-ta").forEach((ta) => {
    if (ta.value) autoResize(ta);
  });
}

/* ── Save ────────────────────────────────────────────────────────────────────── */
async function doSave(tcId, status, notes) {
  const ind = document.getElementById(`ind-${tcId}`);
  const sel = document.querySelector(`.status-sel[data-tc="${tcId}"]`);
  const tsEl = document.getElementById(`ts-${tcId}`);
  if (ind) {
    ind.className = "ind saving";
    ind.textContent = "…";
  }

  try {
    const res = await api("POST", `/api/test-cases/${encodeURIComponent(tcId)}/result`, {
      status,
      notes,
    });

    // Update status select colour
    if (sel) sel.className = `status-sel s-${status}`;

    // Update timestamp cell
    if (tsEl) {
      const ago = timeAgo(res.tested_at);
      tsEl.innerHTML = `<span title="${fmtFull(res.tested_at)}">${ago}</span>`;
    }

    // Update in-memory suite data
    const tc = findTc(tcId);
    if (tc) {
      tc.status = status;
      tc.notes = notes;
      tc.tested_at = res.tested_at;
    }

    // Update suite mini progress
    updateSuiteProgress(tcId);

    // Refresh sidebar stats silently
    refreshSidebarStats();

    if (ind) {
      ind.className = "ind saved";
      ind.textContent = "✓";
      setTimeout(() => {
        if (ind) {
          ind.className = "ind";
          ind.textContent = "";
        }
      }, 2000);
    }
  } catch {
    if (ind) {
      ind.className = "ind err";
      ind.textContent = "✗";
    }
  }
}

async function doClear(tcId) {
  const ind = document.getElementById(`ind-${tcId}`);
  const sel = document.querySelector(`.status-sel[data-tc="${tcId}"]`);
  const notesEl = document.querySelector(`.notes-ta[data-tc="${tcId}"]`);
  const tsEl = document.getElementById(`ts-${tcId}`);
  if (ind) {
    ind.className = "ind saving";
    ind.textContent = "…";
  }

  try {
    await api("DELETE", `/api/test-cases/${encodeURIComponent(tcId)}/result`);

    if (sel) sel.className = "status-sel s-not-run";
    if (notesEl) {
      notesEl.value = "";
      autoResize(notesEl);
    }
    if (tsEl) tsEl.innerHTML = `<span class="ts-never">—</span>`;

    const tc = findTc(tcId);
    if (tc) {
      tc.status = null;
      tc.notes = "";
      tc.tested_at = null;
    }

    updateSuiteProgress(tcId);
    refreshSidebarStats();

    if (ind) {
      ind.className = "ind saved";
      ind.textContent = "✓";
      setTimeout(() => {
        if (ind) {
          ind.className = "ind";
          ind.textContent = "";
        }
      }, 2000);
    }
  } catch {
    if (ind) {
      ind.className = "ind err";
      ind.textContent = "✗";
    }
  }
}

function updateSuiteProgress(tcId) {
  for (const suite of S.suites) {
    if (!suite.cases.find((c) => c.id === tcId)) continue;
    const run = suite.cases.filter((c) => c.status).length;
    const sec = document.querySelector(`.suite[data-sid="${suite.id}"]`);
    if (!sec) break;
    const cnt = sec.querySelector(".suite-count");
    const fill = sec.querySelector(".suite-mini-fill");
    if (cnt) cnt.textContent = `${run}/${suite.cases.length}`;
    if (fill) fill.style.width = `${(run / suite.cases.length) * 100}%`;
    break;
  }
}

async function clearModule() {
  if (!S.activeSlug) return;
  const mod = S.modules.find((m) => m.slug === S.activeSlug);
  const name = mod ? mod.name : S.activeSlug;
  if (
    !confirm(
      `Reset all test results for "${name}"?\n\nAll recorded results will be deleted and every test case will return to Not Run.`,
    )
  )
    return;

  const btn = document.getElementById("btn-clear-module");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Clearing…";
  }

  try {
    await api("POST", `/api/modules/${encodeURIComponent(S.activeSlug)}/clear`);
    S.suites = await api("GET", `/api/modules/${encodeURIComponent(S.activeSlug)}/test-cases`);
    S.summary = null;
    S.view = "cases";
    renderCases();
    await refreshSidebarStats();
  } catch (err) {
    alert(`Failed to clear results: ${err.message}`);
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Clear Results";
    }
  }
}

async function refreshSidebarStats() {
  try {
    S.modules = await api("GET", "/api/modules");
    renderSidebar();
    updateHdrMeta();
  } catch {
    /* silent */
  }
}

function updateHdrMeta() {
  const el = document.getElementById("hdr-meta");
  if (!el || !S.modules.length) return;

  let total = 0,
    pass = 0,
    fail = 0,
    blocked = 0,
    not_run = 0;
  for (const m of S.modules) {
    total += m.stats.total;
    pass += m.stats.pass;
    fail += m.stats.fail;
    blocked += m.stats.blocked;
    not_run += m.stats.not_run;
  }

  if (not_run === total) {
    el.innerHTML = `<span class="hdr-ov-muted">${total} cases · not started</span>`;
    return;
  }

  const pct = total ? Math.round((pass / total) * 100) : 0;
  const parts = [
    `<span class="hdr-ov-pct">${pct}%</span>`,
    pass ? `<span class="hdr-ov-pass">${pass} pass</span>` : null,
    fail ? `<span class="hdr-ov-fail">${fail} fail</span>` : null,
    blocked ? `<span class="hdr-ov-blk">${blocked} blocked</span>` : null,
    `<span class="hdr-ov-muted">${total} total</span>`,
  ].filter(Boolean);

  el.innerHTML = parts.join('<span class="hdr-ov-sep"> · </span>');
}

/* ── History drawer ──────────────────────────────────────────────────────────── */
async function openHistory(tcId) {
  const overlay = document.getElementById("drawer-overlay");
  const drawer = document.getElementById("history-drawer");
  const titleEl = document.getElementById("drawer-tc-id");
  const body = document.getElementById("drawer-body");

  titleEl.textContent = tcId;
  body.innerHTML = `<div class="spinner-wrap"><div class="spinner"></div></div>`;
  overlay.classList.add("open");
  drawer.classList.add("open");

  try {
    const history = await api("GET", `/api/test-cases/${encodeURIComponent(tcId)}/history`);
    if (!history.length) {
      body.innerHTML = `<div class="drawer-empty">No results recorded yet.</div>`;
      return;
    }
    body.innerHTML = history
      .map(
        (h) => `
      <div class="hist-item">
        <div class="hist-dot ${h.status}"></div>
        <div class="hist-body">
          <div class="hist-status ${h.status}">${statusLabel(h.status)}</div>
          ${h.notes ? `<div class="hist-notes">${esc(h.notes)}</div>` : ""}
          <div class="hist-ts">${fmtFull(h.tested_at)}</div>
        </div>
      </div>`,
      )
      .join("");
  } catch {
    body.innerHTML = `<div class="drawer-empty">Failed to load history.</div>`;
  }
}

function closeHistory() {
  document.getElementById("drawer-overlay").classList.remove("open");
  document.getElementById("history-drawer").classList.remove("open");
}

document.getElementById("drawer-close").addEventListener("click", closeHistory);
document.getElementById("drawer-overlay").addEventListener("click", closeHistory);

/* ── Module selection ────────────────────────────────────────────────────────── */
async function selectModule(slug) {
  if (S.activeSlug === slug && S.view === "cases") return;
  S.activeSlug = slug;
  S.view = "cases";
  S.filter = { search: "", status: "all", severity: "all" };
  S.customCases = [];
  closeMobileSidebar();
  renderSidebar();
  setMainLoading();
  try {
    const [suites, customCases] = await Promise.all([
      api("GET", `/api/modules/${encodeURIComponent(slug)}/test-cases`),
      api("GET", `/api/modules/${encodeURIComponent(slug)}/custom-test-cases`),
    ]);
    S.suites = suites;
    S.customCases = customCases;
    renderCases();
    updateHdrMeta();
  } catch (err) {
    document.getElementById("main").innerHTML =
      `<div class="welcome"><h2>Error</h2><p>${esc(err.message)}</p></div>`;
  }
}

function setMainLoading() {
  document.getElementById("main").innerHTML =
    `<div class="loading-main"><div class="spinner"></div> Loading…</div>`;
}

/* ── Custom test cases ───────────────────────────────────────────────────────── */
function renderCustomSection() {
  const container = document.getElementById("custom-section");
  if (!container) return;

  const total = S.customCases.length;
  const unreviewed = S.customCases.filter((tc) => !tc.is_reviewed).length;

  let badgeHTML = total > 0 ? `<span class="custom-hdr-badge badge-count">${total}</span>` : "";
  if (unreviewed > 0) {
    badgeHTML += `<span class="custom-hdr-badge badge-pending">⏳ ${unreviewed} pending review</span>`;
  } else if (total > 0) {
    badgeHTML += `<span class="custom-hdr-badge badge-reviewed">✓ All reviewed</span>`;
  }

  const bodyHTML =
    total === 0
      ? `<div class="custom-empty">No custom test cases added yet.<br>Use <strong>+ Add Test Case</strong> above to log a scenario discovered during testing.</div>`
      : `<table class="custom-tbl">
        <thead>
          <tr>
            <th>ID</th><th>Scenario</th><th>Sev</th>
            <th>Status</th><th>Notes</th><th style="text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${S.customCases.map((tc) => renderCustomRow(tc)).join("")}
        </tbody>
      </table>`;

  container.innerHTML = `
    <div class="custom-hdr" id="custom-hdr">
      <span class="custom-hdr-title">Custom Test Cases</span>
      ${badgeHTML}
    </div>
    <div class="custom-body" id="custom-body">${bodyHTML}</div>`;

  bindCustomRows();
}

function renderCustomRow(tc) {
  const sevBadge = tc.severity
    ? `<span class="sev sev-${esc(tc.severity)}">${esc(tc.severity)}</span>`
    : `<span style="color:var(--border-s)">—</span>`;

  const sel = (val, lbl, cur) =>
    `<option value="${val}"${cur === val ? " selected" : ""}>${lbl}</option>`;

  const reviewCls = tc.is_reviewed ? "reviewed" : "pending";
  const reviewLbl = tc.is_reviewed ? "✓ Reviewed" : "Mark Reviewed";
  const rowCls = tc.is_reviewed ? " custom-reviewed" : "";

  return `
    <tr data-cid="${tc.id}"${rowCls ? ` class="${rowCls}"` : ""}>
      <td class="ctc-id">
        <span class="ctc-id-val">${tc.custom_id ? esc(tc.custom_id) : '<span style="color:var(--border-s)">—</span>'}</span>
      </td>
      <td class="ctc-scen">${esc(tc.scenario)}</td>
      <td class="ctc-sev">${sevBadge}</td>
      <td class="ctc-status">
        <select class="status-sel ${statusCls(tc.status || null)}" data-cid="${tc.id}">
          ${sel("", "Not Run", tc.status || "")}
          ${sel("pass", "Pass", tc.status)}
          ${sel("fail", "Fail", tc.status)}
          ${sel("blocked", "Blocked", tc.status)}
          ${sel("skip", "Skip", tc.status)}
        </select>
      </td>
      <td class="ctc-notes">
        <textarea class="notes-ta" data-cid="${tc.id}"
                  placeholder="Add notes…" rows="1">${esc(tc.notes || "")}</textarea>
      </td>
      <td class="ctc-actions">
        <button class="btn-tc-review ${reviewCls}" data-cid="${tc.id}">${reviewLbl}</button>
        <button class="btn-tc-delete" data-cid="${tc.id}">Delete</button>
      </td>
    </tr>`;
}

function bindCustomRows() {
  document.querySelectorAll(".status-sel[data-cid]").forEach((sel) => {
    sel.addEventListener("change", async () => {
      const id = parseInt(sel.dataset.cid, 10);
      const notes = document.querySelector(`.notes-ta[data-cid="${id}"]`)?.value || "";
      await saveCustomUpdate(id, { status: sel.value, notes });
      sel.className = `status-sel ${statusCls(sel.value || null)}`;
    });
  });

  document.querySelectorAll(".notes-ta[data-cid]").forEach((ta) => {
    ta.addEventListener("input", () => autoResize(ta));
    ta.addEventListener("blur", async () => {
      const id = parseInt(ta.dataset.cid, 10);
      const sel = document.querySelector(`.status-sel[data-cid="${id}"]`);
      await saveCustomUpdate(id, { status: sel?.value || "", notes: ta.value });
    });
    if (ta.value) autoResize(ta);
  });

  document.querySelectorAll(".btn-tc-review[data-cid]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = parseInt(btn.dataset.cid, 10);
      const tc = S.customCases.find((c) => c.id === id);
      const newVal = tc && tc.is_reviewed ? 0 : 1;
      const result = await saveCustomUpdate(id, { is_reviewed: newVal });
      if (result) {
        const found = S.customCases.find((c) => c.id === id);
        if (found) found.is_reviewed = result.is_reviewed;
        renderCustomSection();
      }
    });
  });

  document.querySelectorAll(".btn-tc-delete[data-cid]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = parseInt(btn.dataset.cid, 10);
      const tc = S.customCases.find((c) => c.id === id);
      if (!confirm(`Delete custom test case?\n\n"${tc?.scenario || ""}"`)) return;
      try {
        await api("DELETE", `/api/custom-test-cases/${id}`);
        S.customCases = S.customCases.filter((c) => c.id !== id);
        renderCustomSection();
      } catch (err) {
        alert(`Failed to delete: ${err.message}`);
      }
    });
  });
}

async function saveCustomUpdate(id, data) {
  try {
    const result = await api("PATCH", `/api/custom-test-cases/${id}`, data);
    const tc = S.customCases.find((c) => c.id === id);
    if (tc) Object.assign(tc, result);
    return result;
  } catch {
    return null;
  }
}

/* ── Add custom test case modal ──────────────────────────────────────────────── */
function openAddModal() {
  document.getElementById("nc-id").value = "";
  document.getElementById("nc-scenario").value = "";
  document.getElementById("nc-sev").value = "";
  document.getElementById("nc-status").value = "";
  document.getElementById("nc-notes").value = "";
  document.getElementById("nc-scenario-err").hidden = true;
  document.getElementById("nc-scenario").classList.remove("is-invalid");
  document.getElementById("modal-overlay").classList.add("open");
  setTimeout(() => document.getElementById("nc-scenario").focus(), 60);
}

function closeModal() {
  document.getElementById("modal-overlay").classList.remove("open");
}

async function submitCustomCase() {
  const scenarioEl = document.getElementById("nc-scenario");
  const errEl = document.getElementById("nc-scenario-err");
  const scenario = scenarioEl.value.trim();

  if (!scenario) {
    scenarioEl.classList.add("is-invalid");
    errEl.hidden = false;
    scenarioEl.focus();
    return;
  }
  scenarioEl.classList.remove("is-invalid");
  errEl.hidden = true;

  const btn = document.getElementById("modal-submit");
  btn.disabled = true;
  btn.textContent = "Adding…";

  try {
    const result = await api(
      "POST",
      `/api/modules/${encodeURIComponent(S.activeSlug)}/custom-test-cases`,
      {
        custom_id: document.getElementById("nc-id").value.trim(),
        scenario,
        severity: document.getElementById("nc-sev").value,
        status: document.getElementById("nc-status").value,
        notes: document.getElementById("nc-notes").value.trim(),
      },
    );
    S.customCases.push(result);
    closeModal();
    renderCustomSection();
  } catch (err) {
    alert(`Failed to add test case: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = "Add Test Case";
  }
}

/* ── Init ────────────────────────────────────────────────────────────────────── */
async function init() {
  try {
    S.modules = await api("GET", "/api/modules");
    renderSidebar();
    // Auto-select first module if only one
    if (S.modules.length === 1) selectModule(S.modules[0].slug);
  } catch (err) {
    document.getElementById("module-list").innerHTML =
      `<div style="padding:16px;color:var(--fail);font-size:12px">Server error: ${esc(err.message)}</div>`;
  }
}

/* ── Mobile sidebar ──────────────────────────────────────────────────────────── */
function openMobileSidebar() {
  document.getElementById("sidebar").classList.add("open");
  document.getElementById("sidebar-overlay").classList.add("open");
}

function closeMobileSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebar-overlay").classList.remove("open");
}

document.getElementById("sidebar-toggle").addEventListener("click", () => {
  document.getElementById("sidebar").classList.contains("open")
    ? closeMobileSidebar()
    : openMobileSidebar();
});
document.getElementById("sidebar-overlay").addEventListener("click", closeMobileSidebar);

/* ── Modal events ────────────────────────────────────────────────────────────── */
document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("modal-cancel").addEventListener("click", closeModal);
document.getElementById("modal-submit").addEventListener("click", submitCustomCase);
document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target === document.getElementById("modal-overlay")) closeModal();
});
document.getElementById("nc-scenario").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submitCustomCase();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && document.getElementById("modal-overlay").classList.contains("open")) {
    closeModal();
  }
});

init();
