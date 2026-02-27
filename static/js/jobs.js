/**
 * jobs.js — Job board: load, filter, paginate, crawl, manual add.
 */

let _currentPage = 1;
let _totalPages = 1;
let _searchTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    loadJobs(1);
    loadJobStats();
});

// ── Debounced search ──────────────────────────────────────
function debounceSearch() {
    clearTimeout(_searchTimer);
    _searchTimer = setTimeout(() => loadJobs(1), 400);
}

// ── Load jobs ─────────────────────────────────────────────
async function loadJobs(page = 1) {
    _currentPage = page;
    const grid = document.getElementById('jobGrid');
    const empty = document.getElementById('emptyState');
    const pag = document.getElementById('pagination');

    grid.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto;"></div><p style="margin-top:1rem;">Loading jobs…</p></div>';
    if (empty) empty.style.display = 'none';

    const search = document.getElementById('searchInput')?.value || '';
    const category = document.getElementById('categoryFilter')?.value || '';
    const exp = document.getElementById('expFilter')?.value || '';

    const params = new URLSearchParams({ page, per_page: 12 });
    if (search) params.set('search', search);
    if (category) params.set('category', category);
    if (exp) params.set('experience_level', exp);

    try {
        const res = await fetch(`/api/jobs/list?${params}`);
        const data = await res.json();

        if (!data.success) { throw new Error(data.error); }

        _totalPages = data.pages || 1;
        grid.innerHTML = '';

        if (!data.jobs || data.jobs.length === 0) {
            if (empty) empty.style.display = 'block';
            if (pag) pag.innerHTML = '';
            return;
        }

        data.jobs.forEach(job => grid.appendChild(makeJobCard(job)));
        renderPagination(data.total, data.page, data.pages);

    } catch (err) {
        grid.innerHTML = `<div class="card" style="grid-column:1/-1; text-align:center; padding:3rem;">
      <div style="font-size:2.5rem;">⚠️</div>
      <p style="color:var(--accent-yellow); margin-top:1rem;">${err.message || 'Failed to load jobs. Is the server running?'}</p>
      <button class="btn btn-secondary mt-2" onclick="loadJobs(1)">Retry</button>
    </div>`;
    }
}

// ── Job card ──────────────────────────────────────────────
function makeJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';

    const skills = Array.isArray(job.skills_required)
        ? job.skills_required.slice(0, 5)
        : (typeof job.skills_required === 'string'
            ? tryParseJson(job.skills_required).slice(0, 5)
            : []);

    const skillsHtml = skills.length
        ? skills.map(s => `<span class="skill-tag">${escHtml(s)}</span>`).join('')
        : '<span class="text-muted text-sm">No skills listed</span>';

    const trustScore = job.employer_score || 0;
    const trustClass = trustScore >= 0.7 ? 'trust-high' : trustScore >= 0.4 ? 'trust-medium' : 'trust-low';
    const trustIcon = trustScore >= 0.7 ? '✅' : trustScore >= 0.4 ? '⚠️' : '❌';
    const trustLabel = trustScore >= 0.7 ? 'Verified' : trustScore >= 0.4 ? 'Partial' : 'Unverified';

    const discoveredDate = job.discovered_at
        ? new Date(job.discovered_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
        : 'Unknown';

    card.innerHTML = `
    <div class="job-card-header">
      <div>
        <div class="job-title">${escHtml(job.title || 'Unknown Title')}</div>
        <div class="job-company">${escHtml(job.company || 'Unknown Company')}</div>
      </div>
      <div style="display:flex; flex-direction:column; align-items:flex-end; gap:5px;">
        <span class="category-pill">${escHtml(job.category || 'Other')}</span>
        <span class="exp-badge">${escHtml(job.experience_level || 'Not Specified')}</span>
      </div>
    </div>
    <div class="job-meta">
      ${job.location ? `<span>📍 ${escHtml(job.location)}</span>` : ''}
      <span>📅 ${discoveredDate}</span>
    </div>
    <div class="job-skills">${skillsHtml}</div>
    ${job.description ? `<p style="color:var(--text-secondary); font-size:0.82rem; line-height:1.5; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;">${escHtml(job.description.slice(0, 200))}…</p>` : ''}
    <div class="job-card-footer">
      <div class="trust-badge ${trustClass}">${trustIcon} ${trustLabel} (${Math.round(trustScore * 100)}%)</div>
      ${job.application_link
            ? `<a class="btn btn-primary btn-sm" href="${escHtml(job.application_link)}" target="_blank" rel="noopener">Apply →</a>`
            : `<span class="text-muted text-sm">No link</span>`
        }
    </div>`;

    return card;
}

// ── Pagination ─────────────────────────────────────────────
function renderPagination(total, page, pages) {
    const pag = document.getElementById('pagination');
    if (!pag || pages <= 1) { if (pag) pag.innerHTML = ''; return; }

    let html = `<button class="page-btn" onclick="loadJobs(${page - 1})" ${page <= 1 ? 'disabled' : ''}>‹</button>`;

    const range = 2;
    for (let i = 1; i <= pages; i++) {
        if (i === 1 || i === pages || Math.abs(i - page) <= range) {
            html += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="loadJobs(${i})">${i}</button>`;
        } else if (Math.abs(i - page) === range + 1) {
            html += `<span class="page-btn" style="cursor:default;">…</span>`;
        }
    }

    html += `<button class="page-btn" onclick="loadJobs(${page + 1})" ${page >= pages ? 'disabled' : ''}>›</button>`;
    pag.innerHTML = html;
}

// ── Load stats ─────────────────────────────────────────────
async function loadJobStats() {
    try {
        const res = await fetch('/api/dashboard/stats');
        const data = await res.json();
        if (data.success) {
            const s = data.stats;
            const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val ?? '—'; };
            set('totalJobsStat', s.total_jobs);
            set('verifiedJobsStat', s.verified_jobs);
            set('categoriesStat', Object.keys(s.categories || {}).length);
        }
    } catch (_) { }
}

// ── Crawl trigger ─────────────────────────────────────────
async function triggerCrawl() {
    const btn = document.getElementById('crawlBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Crawling…';
    try {
        const res = await fetch('/api/jobs/crawl', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            const r = data.result;
            showToast(`Crawl done! Found: ${r.found ?? 0}, Added: ${r.added ?? 0}`);
            loadJobs(1);
            loadJobStats();
        } else {
            showToast(data.error || 'Crawl failed', 'error');
        }
    } catch (_) {
        showToast('Could not reach server', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '⚡ Crawl Now';
    }
}

// ── Manual job submit ─────────────────────────────────────
async function submitManualJob() {
    const title = document.getElementById('manTitle')?.value.trim();
    const company = document.getElementById('manCompany')?.value.trim();
    if (!title || !company) { showToast('Title and Company are required', 'error'); return; }

    const payload = {
        title,
        company,
        location: document.getElementById('manLocation')?.value.trim() || '',
        experience_level: document.getElementById('manExp')?.value || 'Not Specified',
        application_link: document.getElementById('manLink')?.value.trim() || '',
        source_url: document.getElementById('manSource')?.value.trim() || '',
        description: document.getElementById('manDesc')?.value.trim() || '',
    };

    try {
        const res = await fetch('/api/jobs/add', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success || res.status === 201) {
            showToast('Job posted successfully!');
            // Clear form
            ['manTitle', 'manCompany', 'manLocation', 'manLink', 'manSource', 'manDesc']
                .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
            loadJobs(1); loadJobStats();
        } else if (res.status === 409) {
            showToast('This job already exists (duplicate detected)', 'error');
        } else {
            showToast(data.error || 'Failed to post job', 'error');
        }
    } catch (_) {
        showToast('Network error', 'error');
    }
}

// ── Utilities ─────────────────────────────────────────────
function escHtml(str) {
    return String(str ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function tryParseJson(str) {
    try { return JSON.parse(str); } catch (_) { return []; }
}
