/**
 * preview.js — DEET Profile preview/edit page logic.
 */

let _profile = null;

document.addEventListener('DOMContentLoaded', () => {
    const raw = sessionStorage.getItem('deetProfile');
    if (!raw) {
        document.getElementById('noDataMsg').style.display = 'block';
        return;
    }
    _profile = JSON.parse(raw);
    document.getElementById('noDataMsg').style.display = 'none';
    document.getElementById('profileForm').style.display = 'block';
    document.getElementById('overallConfCard').style.display = 'block';
    populateForm(_profile);
});

// ── Tab switching ──────────────────────────────────────────
function showTab(name, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).style.display = 'block';
    btn.classList.add('active');
}

// ── Populate form from profile ─────────────────────────────
function populateForm(p) {
    const scores = p.confidence_scores || {};
    const labels = p.confidence_labels || {};

    // Overall bar
    const overall = Math.round((scores.overall || 0) * 100);
    document.getElementById('overallBar').style.width = overall + '%';
    document.getElementById('overallPct').textContent = overall + '%';

    // Simple text fields
    const textFields = ['full_name', 'email', 'phone', 'address', 'linkedin', 'github', 'summary'];
    textFields.forEach(f => {
        const el = document.getElementById('field-' + f);
        if (el) el.value = p[f] || '';
        const badge = document.getElementById('conf-' + f);
        if (badge) applyConfBadge(badge, labels[f] || 'missing', scores[f]);
    });

    // Apply score to skills and top-level badges
    ['skills', 'education', 'certifications', 'work_experience', 'projects'].forEach(f => {
        const badge = document.getElementById('conf-' + f);
        if (badge) applyConfBadge(badge, labels[f] || 'missing', scores[f]);
    });

    // Skills chips
    renderSkills(p.skills || []);

    // Education entries
    renderEducation(p.education || []);

    // Experience entries
    renderExperience(p.work_experience || []);

    // Certifications
    renderCerts(p.certifications || []);

    // Projects
    renderProjects(p.projects || []);
}

function applyConfBadge(el, label, score) {
    const pct = score !== undefined ? ` ${Math.round(score * 100)}%` : '';
    el.textContent = label.toUpperCase() + pct;
    el.className = `conf-badge conf-${label}`;
}

// ── Skills ────────────────────────────────────────────────
function renderSkills(skills) {
    const list = document.getElementById('skillsList');
    list.innerHTML = '';
    skills.forEach(skill => list.appendChild(makeChip(skill)));
}

function makeChip(text) {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.innerHTML = `${text} <span class="chip-remove" onclick="removeSkill('${text}')">✕</span>`;
    return chip;
}

function addSkill() {
    const inp = document.getElementById('skillInput');
    const val = inp.value.trim();
    if (!val) return;
    if (!_profile.skills) _profile.skills = [];
    if (_profile.skills.includes(val)) { showToast('Skill already added', 'error'); return; }
    _profile.skills.push(val);
    renderSkills(_profile.skills);
    inp.value = '';
}

function removeSkill(name) {
    _profile.skills = (_profile.skills || []).filter(s => s !== name);
    renderSkills(_profile.skills);
}

// ── Education ─────────────────────────────────────────────
function renderEducation(list) {
    const container = document.getElementById('educationList');
    const empty = document.getElementById('eduEmpty');
    container.innerHTML = '';
    empty.style.display = list.length === 0 ? 'block' : 'none';
    list.forEach((e, i) => container.appendChild(makeEducationCard(e, i)));
}

function makeEducationCard(e, i) {
    const d = document.createElement('div');
    d.className = 'card card-sm mb-2';
    d.innerHTML = `
    <div class="flex-between mb-2">
      <span style="font-weight:600; color: var(--accent-blue);">Education Entry ${i + 1}</span>
      <button class="btn btn-danger btn-sm" onclick="removeEntry('education',${i})">✕ Remove</button>
    </div>
    <div class="grid-2">
      <div class="form-group">
        <label class="form-label">Institution</label>
        <input class="form-control" value="${escHtml(e.institution || '')}" oninput="_profile.education[${i}].institution=this.value"/>
      </div>
      <div class="form-group">
        <label class="form-label">Degree</label>
        <input class="form-control" value="${escHtml(e.degree || '')}" oninput="_profile.education[${i}].degree=this.value"/>
      </div>
      <div class="form-group">
        <label class="form-label">Field of Study</label>
        <input class="form-control" value="${escHtml(e.field || '')}" oninput="_profile.education[${i}].field=this.value"/>
      </div>
      <div class="form-group">
        <label class="form-label">Year</label>
        <input class="form-control" value="${escHtml(e.year || '')}" oninput="_profile.education[${i}].year=this.value"/>
      </div>
    </div>`;
    return d;
}

function addEducationEntry() {
    if (!_profile.education) _profile.education = [];
    _profile.education.push({ institution: '', degree: '', field: '', year: '' });
    renderEducation(_profile.education);
}

// ── Work Experience ────────────────────────────────────────
function renderExperience(list) {
    const container = document.getElementById('experienceList');
    const empty = document.getElementById('expEmpty');
    container.innerHTML = '';
    empty.style.display = list.length === 0 ? 'block' : 'none';
    list.forEach((e, i) => container.appendChild(makeExpCard(e, i)));
}

function makeExpCard(e, i) {
    const d = document.createElement('div');
    d.className = 'card card-sm mb-2';
    d.innerHTML = `
    <div class="flex-between mb-2">
      <span style="font-weight:600; color: var(--accent-blue);">Experience Entry ${i + 1}</span>
      <button class="btn btn-danger btn-sm" onclick="removeEntry('work_experience',${i})">✕ Remove</button>
    </div>
    <div class="grid-2">
      <div class="form-group">
        <label class="form-label">Job Title / Role</label>
        <input class="form-control" value="${escHtml(e.role || '')}" oninput="_profile.work_experience[${i}].role=this.value"/>
      </div>
      <div class="form-group">
        <label class="form-label">Company</label>
        <input class="form-control" value="${escHtml(e.company || '')}" oninput="_profile.work_experience[${i}].company=this.value"/>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Dates</label>
      <input class="form-control" value="${escHtml(e.dates || '')}" placeholder="e.g. Jan 2020 – Dec 2022"
             oninput="_profile.work_experience[${i}].dates=this.value"/>
    </div>
    <div class="form-group">
      <label class="form-label">Description / Responsibilities</label>
      <textarea class="form-control" rows="3" oninput="_profile.work_experience[${i}].description=this.value">${escHtml(e.description || '')}</textarea>
    </div>`;
    return d;
}

function addExperienceEntry() {
    if (!_profile.work_experience) _profile.work_experience = [];
    _profile.work_experience.push({ role: '', company: '', dates: '', description: '' });
    renderExperience(_profile.work_experience);
}

// ── Certifications ─────────────────────────────────────────
function renderCerts(list) {
    const container = document.getElementById('certList');
    const empty = document.getElementById('certEmpty');
    container.innerHTML = '';
    empty.style.display = list.length === 0 ? 'block' : 'none';
    list.forEach((c, i) => {
        const d = document.createElement('div');
        d.className = 'card card-sm mb-2';
        d.innerHTML = `
      <div class="flex-between mb-2">
        <span style="font-weight:600; color:var(--accent-purple);">Certification ${i + 1}</span>
        <button class="btn btn-danger btn-sm" onclick="removeEntry('certifications',${i})">✕ Remove</button>
      </div>
      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Certification Name</label>
          <input class="form-control" value="${escHtml(c.name || '')}" oninput="_profile.certifications[${i}].name=this.value"/>
        </div>
        <div class="form-group">
          <label class="form-label">Issuing Organization</label>
          <input class="form-control" value="${escHtml(c.issuer || '')}" oninput="_profile.certifications[${i}].issuer=this.value"/>
        </div>
        <div class="form-group">
          <label class="form-label">Year</label>
          <input class="form-control" value="${escHtml(c.year || '')}" oninput="_profile.certifications[${i}].year=this.value"/>
        </div>
      </div>`;
        container.appendChild(d);
    });
}

function addCertEntry() {
    if (!_profile.certifications) _profile.certifications = [];
    _profile.certifications.push({ name: '', issuer: '', year: '' });
    renderCerts(_profile.certifications);
}

// ── Projects ─────────────────────────────────────────────
function renderProjects(list) {
    const container = document.getElementById('projectList');
    const empty = document.getElementById('projEmpty');
    container.innerHTML = '';
    empty.style.display = list.length === 0 ? 'block' : 'none';
    list.forEach((p, i) => {
        const d = document.createElement('div');
        d.className = 'card card-sm mb-2';
        d.innerHTML = `
      <div class="flex-between mb-2">
        <span style="font-weight:600; color:var(--accent-cyan);">Project ${i + 1}</span>
        <button class="btn btn-danger btn-sm" onclick="removeEntry('projects',${i})">✕ Remove</button>
      </div>
      <div class="form-group">
        <label class="form-label">Project Name</label>
        <input class="form-control" value="${escHtml(p.name || '')}" oninput="_profile.projects[${i}].name=this.value"/>
      </div>
      <div class="form-group">
        <label class="form-label">Description</label>
        <textarea class="form-control" rows="2" oninput="_profile.projects[${i}].description=this.value">${escHtml(p.description || '')}</textarea>
      </div>
      <div class="form-group">
        <label class="form-label">Technologies Used</label>
        <input class="form-control" value="${escHtml(p.technologies || '')}" oninput="_profile.projects[${i}].technologies=this.value"/>
      </div>`;
        container.appendChild(d);
    });
}

function addProjectEntry() {
    if (!_profile.projects) _profile.projects = [];
    _profile.projects.push({ name: '', description: '', technologies: '' });
    renderProjects(_profile.projects);
}

// ── Generic remove ────────────────────────────────────────
function removeEntry(field, idx) {
    if (!_profile[field]) return;
    _profile[field].splice(idx, 1);
    const renderFns = {
        education: renderEducation, work_experience: renderExperience,
        certifications: renderCerts, projects: renderProjects
    };
    if (renderFns[field]) renderFns[field](_profile[field]);
}

// ── Submit ────────────────────────────────────────────────
async function submitProfile() {
    // Collect current values from text fields
    const textFields = ['full_name', 'email', 'phone', 'address', 'linkedin', 'github', 'summary'];
    textFields.forEach(f => {
        const el = document.getElementById('field-' + f);
        if (el) _profile[f] = el.value;
    });

    if (!_profile.full_name || !_profile.email) {
        showToast('Full name and email are required.', 'error'); return;
    }

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Submitting…';

    try {
        const res = await fetch('/api/resume/submit', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(_profile)
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Profile saved! ID: #${data.profile_id}`);
            btn.textContent = '✅ Submitted!';
            sessionStorage.removeItem('deetProfile');
        } else {
            showToast(data.error || 'Submit failed', 'error');
            btn.disabled = false; btn.textContent = '✅ Submit to DEET';
        }
    } catch (err) {
        showToast('Network error', 'error');
        btn.disabled = false; btn.textContent = '✅ Submit to DEET';
    }
}

function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
