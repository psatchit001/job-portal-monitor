/* ── State ─────────────────────────────────────────────────────────────── */
let selectedCompanyId = null;
let currentPage = 0;
const PAGE_SIZE = 25;
let searchTimer = null;

/* ── Boot ──────────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadCompanies();
  loadJobs();
});

/* ── Stats ─────────────────────────────────────────────────────────────── */
async function loadStats() {
  const data = await api("/api/stats");
  document.getElementById("stat-new").textContent = data.new ?? "—";
  document.getElementById("stat-saved").textContent = data.saved ?? "—";
  document.getElementById("stat-applied").textContent = data.applied ?? "—";
  document.getElementById("stat-total").textContent = data.total_matched_jobs ?? "—";

  const el = document.getElementById("last-run-info");
  if (data.last_run) {
    const d = new Date(data.last_run);
    el.textContent = `Last run: ${d.toLocaleString()} · Next: every ${data.next_run_hours}h`;
  } else {
    el.textContent = "Not run yet — click ▶ Run Now";
  }
}

/* ── Companies sidebar ─────────────────────────────────────────────────── */
async function loadCompanies() {
  const companies = await api("/api/companies");
  const list = document.getElementById("company-list");
  const companyFilter = document.getElementById("filter-company");

  list.innerHTML = "";
  companyFilter.innerHTML = '<option value="">All companies</option>';

  for (const c of companies) {
    // Sidebar item
    const li = document.createElement("li");
    li.className = `company-item ${!c.enabled ? "disabled" : ""} ${selectedCompanyId === c.id ? "selected" : ""}`;
    li.dataset.id = c.id;

    const dotClass = c.last_scrape_status === "ok" ? "dot-ok"
                   : c.last_scrape_status === "error" ? "dot-error" : "dot-never";

    li.innerHTML = `
      <div>
        <div class="company-name">${c.name}</div>
        <div class="company-meta">${c.jobs_found_last_run ?? 0} found last run</div>
      </div>
      <div class="company-status-dot ${dotClass}"></div>
    `;

    li.addEventListener("click", () => selectCompany(c.id, li));
    list.appendChild(li);

    // Filter dropdown
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.name;
    companyFilter.appendChild(opt);
  }
}

function selectCompany(id, el) {
  document.querySelectorAll(".company-item").forEach(i => i.classList.remove("selected"));
  if (selectedCompanyId === id) {
    selectedCompanyId = null;
    document.getElementById("filter-company").value = "";
  } else {
    selectedCompanyId = id;
    el.classList.add("selected");
    document.getElementById("filter-company").value = id;
  }
  currentPage = 0;
  loadJobs();
}

/* ── Jobs ──────────────────────────────────────────────────────────────── */
async function loadJobs() {
  const status    = document.getElementById("filter-status").value;
  const seniority = document.getElementById("filter-seniority").value;
  const company   = document.getElementById("filter-company").value;
  const search    = document.getElementById("search-input").value.trim();
  const matched   = document.getElementById("matched-only").checked;

  const params = new URLSearchParams({
    limit: PAGE_SIZE,
    offset: currentPage * PAGE_SIZE,
    matched_only: matched,
  });
  if (status)    params.set("status", status);
  if (seniority) params.set("seniority", seniority);
  if (company)   params.set("company_id", company);
  if (search)    params.set("search", search);

  const data = await api(`/api/jobs?${params}`);
  renderJobs(data.jobs, data.total);
}

function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { currentPage = 0; loadJobs(); }, 350);
}

function renderJobs(jobs, total) {
  const list = document.getElementById("job-list");
  const meta = document.getElementById("results-meta");
  const pag  = document.getElementById("pagination");

  meta.textContent = `${total} job${total !== 1 ? "s" : ""} found`;

  if (!jobs.length) {
    list.innerHTML = '<div class="empty-state">No jobs match your filters.</div>';
    pag.innerHTML = "";
    return;
  }

  list.innerHTML = jobs.map(j => jobCardHTML(j)).join("");

  // Pagination
  const totalPages = Math.ceil(total / PAGE_SIZE);
  pag.innerHTML = "";
  if (totalPages <= 1) return;

  if (currentPage > 0) {
    const prev = btn("← Prev", () => { currentPage--; loadJobs(); });
    pag.appendChild(prev);
  }
  for (let i = 0; i < totalPages; i++) {
    const b = btn(i + 1, () => { currentPage = i; loadJobs(); });
    if (i === currentPage) b.classList.add("current");
    pag.appendChild(b);
  }
  if (currentPage < totalPages - 1) {
    const next = btn("Next →", () => { currentPage++; loadJobs(); });
    pag.appendChild(next);
  }
}

function btn(label, onClick) {
  const b = document.createElement("button");
  b.className = "page-btn";
  b.textContent = label;
  b.addEventListener("click", onClick);
  return b;
}

function jobCardHTML(j) {
  const scorePercent = Math.round(j.match_score * 100);
  const seniorityTag = seniorityLabel(j.seniority);
  const dateStr = j.first_seen ? new Date(j.first_seen).toLocaleDateString() : "";
  const activeTag = j.is_active ? "" : '<span class="tag tag-inactive">Inactive</span>';

  return `
    <div class="job-card status-${j.status}" id="job-${j.id}">
      <div class="job-header">
        <div>
          <a class="job-title" href="${j.url}" target="_blank" rel="noopener">${esc(j.title)}</a>
          <div class="job-company">${esc(j.company)}${j.location ? " · " + esc(j.location) : ""}</div>
        </div>
      </div>

      <div class="job-meta">
        ${seniorityTag}
        ${j.matched_role ? `<span class="tag tag-role">${esc(j.matched_role)}</span>` : ""}
        ${activeTag}
        <div class="match-bar-wrap">
          <div class="match-bar-bg"><div class="match-bar-fill" style="width:${scorePercent}%"></div></div>
          <span>${scorePercent}% match</span>
        </div>
        <span class="job-date">${dateStr}</span>
      </div>

      <div class="job-actions">
        <button class="action-btn ${j.status === 'saved' ? 'active-saved' : ''}"
                onclick="setStatus(${j.id}, 'saved')">🔖 Save</button>
        <button class="action-btn ${j.status === 'applied' ? 'active-applied' : ''}"
                onclick="setStatus(${j.id}, 'applied')">✅ Applied</button>
        <button class="action-btn ${j.status === 'not_interested' ? 'active-not_interested' : ''}"
                onclick="setStatus(${j.id}, 'not_interested')">✕ Not Interested</button>
      </div>
    </div>
  `;
}

function seniorityLabel(s) {
  const map = {
    internship:   ['tag-seniority-internship', '🎓 Internship'],
    new_grad:     ['tag-seniority-new_grad',   '🎓 New Grad'],
    entry_level:  ['tag-seniority-entry_level', '🟢 Entry Level'],
    junior:       ['tag-seniority-junior',      '🟢 Junior'],
    "senior+":    ['tag-seniority-senior+',     '🔴 Senior+'],
    unspecified:  ['tag-seniority-unspecified', '⚪ Level N/A'],
  };
  const [cls, label] = map[s] || ['tag-seniority-unspecified', '⚪ Level N/A'];
  return `<span class="tag ${cls}">${label}</span>`;
}

/* ── Actions ───────────────────────────────────────────────────────────── */
async function setStatus(jobId, status) {
  const current = document.querySelector(`#job-${jobId} .action-btn.active-${status}`);
  const newStatus = current ? "new" : status;

  await api(`/api/jobs/${jobId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: newStatus }),
  });

  loadJobs();
  loadStats();
}

async function triggerScrape() {
  const btn = document.getElementById("btn-scrape");
  btn.disabled = true;
  btn.textContent = "⏳ Running…";
  await api("/api/scrape", { method: "POST" });
  setTimeout(() => {
    btn.disabled = false;
    btn.textContent = "▶ Run Now";
    loadStats();
    loadCompanies();
    loadJobs();
  }, 3000);
}

/* ── Helpers ───────────────────────────────────────────────────────────── */
async function api(url, opts = {}) {
  try {
    const resp = await fetch(url, opts);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (e) {
    console.error("API error:", e);
    return {};
  }
}

function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
