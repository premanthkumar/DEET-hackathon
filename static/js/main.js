/**
 * main.js — Shared utilities: toast, file upload, demo, stats loader.
 */

// ── Toast helper ──────────────────────────────────────────
function showToast(msg, type = 'success') {
  const toast    = document.getElementById('toast');
  const toastMsg = document.getElementById('toastMsg');
  const icon     = document.getElementById('toastIcon');
  if (!toast) return;
  icon.textContent  = type === 'success' ? '✅' : '❌';
  toastMsg.textContent = msg;
  toast.className = `toast ${type}`;
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 4000);
}

// ── Upload zone ───────────────────────────────────────────
const resumeInput = document.getElementById('resumeInput');
const uploadZone  = document.getElementById('uploadZone');
const processBtn  = document.getElementById('processBtn');

if (uploadZone) {
  uploadZone.addEventListener('dragover', e => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
  });
  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
  uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const f = e.dataTransfer.files[0];
    if (f) handleFileSelected(f);
  });
}

if (resumeInput) {
  resumeInput.addEventListener('change', () => {
    if (resumeInput.files[0]) handleFileSelected(resumeInput.files[0]);
  });
}

function handleFileSelected(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  const allowed = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'];
  if (!allowed.includes(ext)) {
    showToast('Unsupported file type. Use PDF, DOCX, or image.', 'error');
    return;
  }
  const icons = { pdf: '📄', doc: '📝', docx: '📝', png: '🖼️', jpg: '🖼️', jpeg: '🖼️' };
  document.getElementById('fileIcon').textContent  = icons[ext] || '📄';
  document.getElementById('fileName').textContent  = file.name;
  document.getElementById('fileSize').textContent  = formatBytes(file.size);
  document.getElementById('selectedFile').style.display = 'block';
  if (processBtn) processBtn.disabled = false;

  // Store file reference
  window._selectedFile = file;
}

function clearFile() {
  window._selectedFile = null;
  document.getElementById('selectedFile').style.display = 'none';
  if (processBtn) processBtn.disabled = true;
  if (resumeInput) resumeInput.value = '';
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Process resume ────────────────────────────────────────
async function processResume() {
  if (!window._selectedFile) {
    showToast('Please select a file first', 'error'); return;
  }

  const overlay = document.getElementById('processingOverlay');
  if (overlay) overlay.classList.add('active');
  if (processBtn) processBtn.disabled = true;

  const steps = ['step-ocr', 'step-nlp', 'step-score', 'step-done'];
  let stepIdx = 0;

  // Animate steps
  const stepInterval = setInterval(() => {
    if (stepIdx > 0) {
      const prev = document.getElementById(steps[stepIdx - 1]);
      if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
    }
    const curr = document.getElementById(steps[stepIdx]);
    if (curr) curr.classList.add('active');
    stepIdx++;
    if (stepIdx >= steps.length) clearInterval(stepInterval);
  }, 900);

  try {
    const formData = new FormData();
    formData.append('resume', window._selectedFile);

    const res = await fetch('/api/resume/upload', { method: 'POST', body: formData });
    const data = await res.json();

    clearInterval(stepInterval);
    // Mark all done
    steps.forEach(s => {
      const el = document.getElementById(s);
      if (el) { el.classList.remove('active'); el.classList.add('done'); }
    });

    await new Promise(r => setTimeout(r, 600));
    if (overlay) overlay.classList.remove('active');

    if (data.success) {
      sessionStorage.setItem('deetProfile', JSON.stringify(data.profile));
      showToast('Profile extracted! Redirecting to preview…');
      setTimeout(() => window.location.href = '/preview', 1000);
    } else {
      showToast(data.error || 'Extraction failed', 'error');
      if (processBtn) processBtn.disabled = false;
    }
  } catch (err) {
    clearInterval(stepInterval);
    if (overlay) overlay.classList.remove('active');
    showToast('Network error — is the server running?', 'error');
    if (processBtn) processBtn.disabled = false;
  }
}

// ── Demo data ─────────────────────────────────────────────
function loadDemoData() {
  const demo = {
    full_name: 'Alex Johnson',
    email: 'alex.johnson@email.com',
    phone: '+1 (555) 123-4567',
    address: 'San Francisco, CA, USA',
    linkedin: 'https://linkedin.com/in/alexjohnson',
    github: 'https://github.com/alexjohnson',
    summary: 'Results-driven Software Engineer with 5+ years of experience building scalable web applications. Proficient in Python, React, and cloud infrastructure. Passionate about AI/ML solutions.',
    education: [
      { institution: 'University of California, Berkeley', degree: 'Bachelor', field: 'Computer Science', year: '2018' }
    ],
    skills: ['Python', 'JavaScript', 'React', 'Node.Js', 'Aws', 'Docker', 'Machine Learning', 'Sql', 'Git'],
    certifications: [
      { name: 'AWS Certified Solutions Architect', issuer: 'Amazon Web Services', year: '2022' },
      { name: 'Google Professional ML Engineer', issuer: 'Google Cloud', year: '2023' }
    ],
    work_experience: [
      { role: 'Senior Software Engineer', company: 'TechCorp Inc.', dates: 'Jan 2021 – Present', description: 'Led backend development of microservices architecture serving 2M+ users. Reduced API latency by 40%.' },
      { role: 'Software Engineer', company: 'StartupXYZ', dates: 'Jun 2018 – Dec 2020', description: 'Full-stack development using React and Django. Built real-time chat feature used by 500k users.' }
    ],
    projects: [
      { name: 'AI Resume Parser', description: 'Developed an NLP-based resume parsing system using spaCy and Transformers with 95% field extraction accuracy.', technologies: 'Python, spaCy, Flask, React' },
      { name: 'Job Recommendation Engine', description: 'Built collaborative filtering recommendation system for job matching using Scikit-learn.', technologies: 'Python, Scikit-learn, PostgreSQL' }
    ],
    confidence_scores: {
      full_name: 0.88, email: 1.0, phone: 1.0, address: 0.72, summary: 0.80,
      education: 0.85, skills: 0.85, certifications: 0.70, work_experience: 0.75, projects: 0.70, overall: 0.83
    },
    confidence_labels: {
      full_name: 'high', email: 'high', phone: 'high', address: 'medium',
      summary: 'high', education: 'high', skills: 'high', certifications: 'medium',
      work_experience: 'medium', projects: 'medium', overall: 'high'
    }
  };
  sessionStorage.setItem('deetProfile', JSON.stringify(demo));
  showToast('Demo profile loaded! Redirecting…');
  setTimeout(() => window.location.href = '/preview', 900);
}

// ── Stats loader ──────────────────────────────────────────
async function loadStats() {
  try {
    const res  = await fetch('/api/dashboard/stats');
    const data = await res.json();
    if (data.success) {
      const s = data.stats;
      const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
      set('statProfiles', s.total_profiles ?? '—');
      set('statJobs',     s.total_jobs     ?? '—');
      set('statVerified', s.verified_jobs  ?? '—');
      set('jobCount',     s.total_jobs     ?? '0');
    }
  } catch (_) {}
}

document.addEventListener('DOMContentLoaded', loadStats);
