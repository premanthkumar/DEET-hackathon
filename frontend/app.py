import logging
import html as html_lib

import requests
import streamlit as st

logger = logging.getLogger(__name__)

API = "http://localhost:8000"

COMPANY_URLS = {
    "TCS": "https://www.tcs.com/careers/tcs-careers-apply-for-jobs",
    "Infosys": "https://www.infosys.com/careers/apply-jobs.html",
    "Internshala": "https://internshala.com/internships",
}

st.set_page_config(
    page_title="DEET AutoMatch",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg-base:        #111318;
  --bg-surface:     #1a1d24;
  --bg-elevated:    #22262f;
  --bg-hover:       #292d38;

  --border-subtle:  rgba(255,255,255,0.06);
  --border-mid:     rgba(255,255,255,0.11);
  --border-accent:  rgba(32,201,151,0.30);

  --text-primary:   #eef0f6;
  --text-secondary: #9ba3b8;
  --text-muted:     #555e74;

  --accent:         #20c997;
  --accent-soft:    rgba(32,201,151,0.10);
  --accent-glow:    rgba(32,201,151,0.22);

  --good:           #34d399;
  --good-soft:      rgba(52,211,153,0.10);
  --warn:           #fbbf24;
  --warn-soft:      rgba(251,191,36,0.10);
  --bad:            #f87171;
  --bad-soft:       rgba(248,113,113,0.10);

  --radius-sm:   8px;
  --radius-md:   12px;
  --radius-lg:   16px;

  --shadow-sm:   0 1px 3px rgba(0,0,0,0.45);
  --shadow-md:   0 4px 16px rgba(0,0,0,0.35);
  --shadow-lg:   0 8px 32px rgba(0,0,0,0.40);
}

* { font-family: 'Sora', system-ui, sans-serif; }
code, .mono { font-family: 'JetBrains Mono', monospace; font-size: 0.85em; }

/* ── APP BG ── */
.stApp { background: var(--bg-base); min-height: 100vh; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 1400px; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stSidebar"] { display: none; }

/* ── TOP BAR ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1.8rem;
  padding-bottom: 1.2rem;
  border-bottom: 1px solid var(--border-subtle);
}
.brand {
  font-weight: 800; font-size: 1.18rem;
  color: var(--text-primary); letter-spacing: -0.03em;
}
.brand em { font-style: normal; color: var(--accent); }
.pill {
  display: inline-flex; align-items: center; gap: 7px;
  background: var(--bg-surface);
  border: 1px solid var(--border-mid);
  color: var(--text-secondary);
  padding: 5px 13px; border-radius: 999px;
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
}
.pill-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--good); box-shadow: 0 0 7px var(--good);
  animation: pulse 2s ease-in-out infinite;
}
.pill-dot.off { background: var(--bad); box-shadow: 0 0 7px var(--bad); animation: none; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }

/* ── STAT CARD ── */
.stat {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  margin-bottom: 10px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.stat:hover {
  border-color: var(--border-accent);
  transform: translateY(-3px);
  box-shadow: var(--shadow-md), 0 0 20px var(--accent-glow);
}
.stat-num  { font-size: 2rem; font-weight: 800; color: var(--accent); line-height: 1.1; margin-bottom: 3px; }
.stat-label { font-size: 0.68rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; }

/* ── GENERIC CARD ── */
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 20px 22px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.card:hover { border-color: var(--border-mid); transform: translateY(-2px); box-shadow: var(--shadow-md); }
.card-title {
  font-size: 0.72rem; font-weight: 700; color: var(--text-muted);
  letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 9px;
}
.muted { color: var(--text-secondary); font-size: 0.83rem; line-height: 1.65; }

/* ── PROFILE CARD ── */
.profile-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 20px 22px; margin-bottom: 12px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s;
}
.profile-card:hover { border-color: var(--border-mid); }
.profile-avatar {
  width: 42px; height: 42px; border-radius: 10px;
  background: var(--accent-soft);
  border: 1px solid var(--border-accent);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 800; color: var(--accent);
  margin-right: 12px; flex-shrink: 0;
}
.profile-name { font-size: 0.95rem; font-weight: 700; color: var(--text-primary); line-height: 1.25; }
.profile-sub  { font-size: 0.72rem; color: var(--text-muted); margin-top: 2px; line-height: 1.5; }
.profile-detail { font-size: 0.78rem; color: var(--text-secondary); margin-top: 6px; line-height: 1.65; }

/* ── JOB CARD ── */
.job-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-md);
  padding: 16px 18px; margin-bottom: 10px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s, transform 0.22s, box-shadow 0.22s;
}
.job-card:hover {
  border-color: var(--border-accent);
  border-left-color: var(--accent);
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.job-title   { font-size: 0.9rem; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }
.job-company { font-size: 0.75rem; color: var(--accent); font-weight: 600; }
.job-meta    { font-size: 0.7rem; color: var(--text-muted); margin-top: 4px; }

/* ── SKILL TAGS ── */
.skill-tag {
  display: inline-block;
  background: var(--bg-elevated);
  border: 1px solid var(--border-mid);
  color: var(--text-secondary);
  padding: 2px 9px; border-radius: 5px;
  font-size: 0.66rem; margin: 2px; font-weight: 500;
  transition: color 0.18s, border-color 0.18s;
}
.skill-tag:hover { color: var(--accent); border-color: var(--border-accent); }

/* ── BADGES ── */
.verified-badge {
  background: var(--good-soft); border: 1px solid rgba(52,211,153,0.28);
  color: var(--good); padding: 3px 9px; border-radius: 5px;
  font-size: 0.66rem; font-weight: 700;
}
.applied-badge {
  background: var(--accent-soft); border: 1px solid var(--border-accent);
  color: var(--accent); padding: 3px 9px; border-radius: 5px;
  font-size: 0.66rem; font-weight: 700;
}

/* ── MATCH SCORES ── */
.match-high { font-size: 1.5rem; font-weight: 800; color: var(--good); }
.match-mid  { font-size: 1.5rem; font-weight: 800; color: var(--warn); }
.match-low  { font-size: 1.5rem; font-weight: 800; color: var(--bad); }

/* ── RANK BADGE ── */
.rank-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  background: var(--accent-soft); border: 1px solid var(--border-accent);
  border-radius: 7px; font-size: 0.64rem; font-weight: 700;
  color: var(--accent); margin-right: 8px; flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
}

/* ── BUTTONS ── */
.stButton > button {
  background: var(--accent) !important;
  border: none !important; color: #0d1117 !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.5rem 1.1rem !important;
  font-weight: 700 !important; font-size: 0.82rem !important;
  box-shadow: 0 2px 10px var(--accent-glow) !important;
  transition: transform 0.18s, box-shadow 0.18s, background 0.18s !important;
}
.stButton > button:hover {
  background: #2dd4a8 !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px var(--accent-glow) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── NAV RADIO ── */
.stRadio > div { display: flex; gap: 6px; flex-wrap: wrap; }
.stRadio label {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-mid) !important;
  color: var(--text-secondary) !important;
  border-radius: var(--radius-sm) !important;
  padding: 6px 16px !important; font-weight: 600 !important;
  font-size: 0.8rem !important; cursor: pointer !important;
  transition: color 0.18s, border-color 0.18s, background 0.18s !important;
}
.stRadio label:hover {
  color: var(--accent) !important;
  border-color: var(--border-accent) !important;
  background: var(--accent-soft) !important;
}

/* ── INPUTS ── */
.stTextInput input, .stTextArea textarea {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-mid) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.86rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ── MISC STREAMLIT ── */
[data-testid="stFileUploader"] {
  background: var(--bg-elevated) !important;
  border: 1px dashed var(--border-mid) !important;
  border-radius: var(--radius-md) !important;
}
[data-testid="stExpander"] {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-sm) !important;
}
.stAlert { border-radius: var(--radius-sm) !important; }
</style>
""", unsafe_allow_html=True)


# ── MOUSE-TRACKING TILT ───────────────────────────────────────────────────────
import streamlit.components.v1 as components

components.html("""
<script>
(function() {
  function applyTilt() {
    const cards = window.parent.document.querySelectorAll(
      '.job-card, .card, .stat, .profile-card'
    );
    cards.forEach(card => {
      card.addEventListener('mousemove', function(e) {
        const rect = card.getBoundingClientRect();
        const cx = rect.left + rect.width  / 2;
        const cy = rect.top  + rect.height / 2;
        const dx = (e.clientX - cx) / (rect.width  / 2);
        const dy = (e.clientY - cy) / (rect.height / 2);
        card.style.transform =
          `perspective(900px) rotateX(${(-dy * 4).toFixed(2)}deg) rotateY(${(dx * 4).toFixed(2)}deg) translateY(-4px)`;
        card.style.transition = 'box-shadow 0.1s ease';
      });
      card.addEventListener('mouseleave', function() {
        card.style.transform = '';
        card.style.transition = 'transform 0.4s ease, box-shadow 0.4s ease';
      });
    });
  }
  setTimeout(applyTilt, 800);
  new MutationObserver(() => setTimeout(applyTilt, 800))
    .observe(window.parent.document.body, { childList: true, subtree: true });
})();
</script>
""", height=0)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def check_api_health() -> bool:
    try:
        r = requests.get(f"{API}/docs", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def safe_api_get(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend."
    except Exception as e:
        return None, str(e)

def safe_api_post(url, **kwargs):
    try:
        r = requests.post(url, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend."
    except Exception as e:
        return None, str(e)

def skills_html(skills):
    return "".join(f'<span class="skill-tag">{s}</span>' for s in skills)

def is_applied(title, company):
    return any(
        a["title"] == title and a["company"] == company
        for a in st.session_state.get("applications", [])
    )


# ── SESSION STATE ─────────────────────────────────────────────────────────────

if "applications" not in st.session_state:
    st.session_state["applications"] = []
if "cached_jobs" not in st.session_state:
    st.session_state["cached_jobs"] = []


# ── TOP BAR ───────────────────────────────────────────────────────────────────

api_online = check_api_health()
st.markdown(f"""
<div class="topbar">
  <div class="brand">⚡ DEET <em>AutoMatch</em></div>
  <div class="pill">
    <span class="pill-dot {'off' if not api_online else ''}"></span>
    {'SYSTEM LIVE' if api_online else 'BACKEND OFFLINE'}
  </div>
</div>
""", unsafe_allow_html=True)

if not api_online:
    st.warning("Backend offline. Run: `uvicorn main:app --reload --port 8000`")


# ── LAYOUT ────────────────────────────────────────────────────────────────────

left, main = st.columns([1.1, 3.2], gap="large")

job_count      = len(st.session_state["cached_jobs"])
applied_count  = len(st.session_state["applications"])
profile_skills = len(st.session_state.get("profile", {}).get("skills", []))


# ── LEFT COLUMN ───────────────────────────────────────────────────────────────

with left:
    st.markdown(f"""
<div class="stat"><div class="stat-num">{job_count}</div><div class="stat-label">Jobs Discovered</div></div>
<div class="stat"><div class="stat-num">{applied_count}</div><div class="stat-label">Applications Sent</div></div>
<div class="stat"><div class="stat-num">{profile_skills}</div><div class="stat-label">Skills Found</div></div>
""", unsafe_allow_html=True)

    profile    = st.session_state.get("profile", {})
    name_val   = profile.get("name") or "No profile yet"
    avatar_ch  = name_val[0].upper() if name_val != "No profile yet" else "?"
    email_safe = html_lib.escape(profile.get("email", ""))
    phone_safe = html_lib.escape(profile.get("phone", ""))
    loc_safe   = html_lib.escape(profile.get("location", "—"))
    edu_safe   = html_lib.escape((profile.get("education") or "—")[:60])
    contact    = " · ".join(filter(None, [email_safe, phone_safe]))

    st.markdown(f"""
<div class="profile-card">
  <div class="card-title">👤 Profile</div>
  <div style="display:flex;align-items:center;margin-bottom:10px;">
    <div class="profile-avatar">{avatar_ch}</div>
    <div>
      <div class="profile-name">{html_lib.escape(name_val)}</div>
      <div class="profile-sub">{contact}</div>
    </div>
  </div>
  <div class="profile-detail">📍 {loc_safe}</div>
  <div class="profile-detail">🎓 {edu_safe}</div>
</div>
<div class="card">
  <div class="card-title">💡 Tips</div>
  <div class="muted">Upload a clean text-based PDF. Fetch jobs then run matching.</div>
</div>
""", unsafe_allow_html=True)

    if st.button("🔄 Fetch Latest Jobs"):
        with st.spinner("Crawling..."):
            jobs, error = safe_api_get(f"{API}/jobs", timeout=15)
        if error:
            st.error(error)
        elif jobs:
            st.session_state["cached_jobs"] = jobs
            st.rerun()


# ── MAIN COLUMN ───────────────────────────────────────────────────────────────

with main:
    nav = st.radio(
        "",
        ["🏠 Dashboard", "💼 Jobs", "🧠 Register", "📋 Applications"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # ── DASHBOARD ──
    if nav == "🏠 Dashboard":
        st.markdown("""
<div class="card">
  <div class="card-title">🏠 Dashboard</div>
  <div class="muted">Fetch jobs, upload your resume, then run matching to see results here.</div>
</div>
""", unsafe_allow_html=True)

        if "profile" in st.session_state and st.session_state["cached_jobs"]:
            if st.button("🎯 Run Matching Now"):
                with st.spinner("AI matching in progress..."):
                    matches, err = safe_api_post(
                        f"{API}/match",
                        json={"profile": st.session_state["profile"], "jobs": st.session_state["cached_jobs"]},
                        timeout=45,
                    )
                if err:
                    st.error(err)
                else:
                    st.session_state["latest_matches"] = matches

        matches = st.session_state.get("latest_matches", [])
        if matches:
            st.markdown('<div class="card"><div class="card-title">🏆 Your Top Matches</div>', unsafe_allow_html=True)
            for i, job in enumerate(matches[:5], 1):
                score = job.get("match_score", 0)
                sc = "match-high" if score >= 70 else "match-mid" if score >= 40 else "match-low"
                st.markdown(f"""
<div class="job-card">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div style="display:flex;align-items:center;">
        <span class="rank-badge">#{i}</span>
        <span class="job-title">{job.get('title','')}</span>
      </div>
      <div class="job-company" style="margin-left:32px;">{job.get('company','')} · 📍 {job.get('location','')}</div>
      <div style="margin:6px 0 4px 32px;font-size:0.73rem;color:#555e74;font-style:italic;">"{job.get('match_reason','')}"</div>
      <div style="margin-left:32px;">{skills_html(job.get('skills',[]))}</div>
    </div>
    <div style="text-align:center;min-width:70px;">
      <div class="{sc}">{score}%</div>
      <div style="font-size:0.59rem;color:#555e74;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;">Match</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── JOBS ──
    elif nav == "💼 Jobs":
        st.markdown("""
<div class="card">
  <div class="card-title">💼 Live Job Listings</div>
  <div class="muted">Auto-discovered from employer career pages. Click Apply to send your application.</div>
</div>
""", unsafe_allow_html=True)

        if not st.session_state["cached_jobs"]:
            st.info("No jobs yet. Click **Fetch Latest Jobs** on the left.")
        else:
            st.success(f"✓ Showing {len(st.session_state['cached_jobs'])} vacancies")
            for job in st.session_state["cached_jobs"]:
                already       = is_applied(job.get("title"), job.get("company"))
                salary        = job.get("salary", "")
                salary_html   = f'<span style="color:#34d399;font-size:0.72rem;font-weight:700;">{salary}</span>' if salary else ""
                verified_html = '<span class="verified-badge">✓ Verified</span>' if job.get("verified") else ""
                applied_html  = '<span class="applied-badge">✓ Applied</span>' if already else ""

                st.markdown(f"""
<div class="job-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div style="flex:1;">
      <div class="job-title">{job.get('title','')}</div>
      <div class="job-company">{job.get('company','')}</div>
      <div class="job-meta">📍 {job.get('location','')} · 💼 {job.get('type','')}</div>
      <div style="margin-top:8px;">{skills_html(job.get('skills',[]))}</div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;min-width:110px;padding-left:8px;">
      {verified_html}{salary_html}{applied_html}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

                if not already:
                    ca, cb = st.columns([1, 1])
                    with ca:
                        st.link_button("🌐 Open Job", COMPANY_URLS.get(job.get("company", ""), job.get("url", "#")))
                    with cb:
                        if st.button("📨 Apply", key=f"apply_{job.get('company')}_{job.get('title')}"):
                            st.session_state["apply_target"] = job
                            st.rerun()

        if "apply_target" in st.session_state:
            job = st.session_state["apply_target"]
            p   = st.session_state.get("profile", {})
            st.markdown("---")
            st.markdown(f'<div class="card"><div class="card-title">📨 Apply — {job.get("title")} at {job.get("company")}</div>', unsafe_allow_html=True)
            with st.form("apply_form"):
                name  = st.text_input("Your Name",  value=p.get("name", ""))
                email = st.text_input("Your Email", value=p.get("email", ""))
                cover = st.text_area("Cover Note", value=(
                    f"I am excited to apply for the {job.get('title')} position at {job.get('company')}. "
                    f"With {p.get('experience_years', 0)} years of experience and skills in "
                    f"{', '.join(p.get('skills', [])[:5])}, I believe I am a strong fit."
                ), height=140)
                cs, cc = st.columns([1, 1])
                with cs: submitted = st.form_submit_button("Send Application")
                with cc: cancelled = st.form_submit_button("✕ Cancel")

            if submitted:
                if not name or not email:
                    st.error("Fill in name and email.")
                else:
                    _, err = safe_api_post(f"{API}/apply", json={
                        "applicant_name": name, "applicant_email": email,
                        "cover_note": cover, "job_title": job.get("title"), "job_company": job.get("company"),
                    })
                    st.session_state["applications"].append({
                        "title": job.get("title"), "company": job.get("company"),
                        "location": job.get("location"), "name": name, "email": email,
                        "cover": cover, "status": "Sent" if not err else "Tracked",
                    })
                    del st.session_state["apply_target"]
                    st.rerun()
            if cancelled:
                del st.session_state["apply_target"]
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ── REGISTER ──
    elif nav == "🧠 Register":
        st.markdown("""
<div class="card">
  <div class="card-title">🧠 Register via Resume</div>
  <div class="muted">Upload your PDF resume. AI will extract your profile instantly.</div>
</div>
""", unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            with st.spinner("⚡ AI parsing your resume..."):
                profile, error = safe_api_post(
                    f"{API}/parse-resume",
                    files={"file": ("resume.pdf", uploaded.getvalue(), "application/pdf")},
                    timeout=30,
                )
            if error:
                st.error(error)
            elif profile:
                if "Could not parse" in profile.get("name", ""):
                    st.error(profile.get("name"))
                else:
                    st.session_state["profile"] = profile
                    st.success("✅ Profile created!")

        if "profile" in st.session_state:
            p = st.session_state["profile"]
            all_skills = p.get("skills", [])
            hidden = max(0, len(all_skills) - 12)
            sp = skills_html(all_skills[:12])
            if hidden:
                sp += f'<span style="color:#555e74;font-size:0.7rem;margin-left:4px;">+{hidden} more</span>'

            st.markdown(f"""
<div class="card">
  <div class="card-title">📋 Your DEET Profile</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
    <div>
      <div style="font-size:0.66rem;color:#555e74;text-transform:uppercase;letter-spacing:0.06em;">Name</div>
      <div style="font-size:0.88rem;font-weight:600;color:#eef0f6;margin-top:2px;">{html_lib.escape(p.get('name','—'))}</div>
    </div>
    <div>
      <div style="font-size:0.66rem;color:#555e74;text-transform:uppercase;letter-spacing:0.06em;">Email</div>
      <div style="font-size:0.88rem;color:#eef0f6;margin-top:2px;">{html_lib.escape(p.get('email','—'))}</div>
    </div>
    <div>
      <div style="font-size:0.66rem;color:#555e74;text-transform:uppercase;letter-spacing:0.06em;">Phone</div>
      <div style="font-size:0.88rem;color:#eef0f6;margin-top:2px;">{html_lib.escape(p.get('phone','—'))}</div>
    </div>
    <div>
      <div style="font-size:0.66rem;color:#555e74;text-transform:uppercase;letter-spacing:0.06em;">Location</div>
      <div style="font-size:0.88rem;color:#eef0f6;margin-top:2px;">{html_lib.escape(p.get('location','—'))}</div>
    </div>
    <div>
      <div style="font-size:0.66rem;color:#555e74;text-transform:uppercase;letter-spacing:0.06em;">Experience</div>
      <div style="font-size:0.88rem;font-weight:700;color:#20c997;margin-top:2px;">{p.get('experience_years',0)} yrs</div>
    </div>
    <div>
      <div style="font-size:0.66rem;color:#555e74;text-transform:uppercase;letter-spacing:0.06em;">Roles</div>
      <div style="font-size:0.88rem;font-weight:700;color:#20c997;margin-top:2px;">{len(p.get('previous_roles',[]))}</div>
    </div>
  </div>
  <div style="font-size:0.66rem;color:#555e74;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">Skills ({len(all_skills)})</div>
  <div>{sp}</div>
</div>
""", unsafe_allow_html=True)

            if st.button("🎯 Find My Matching Jobs"):
                with st.spinner("Matching..."):
                    jobs, je = safe_api_get(f"{API}/jobs", timeout=15)
                    if je:
                        st.error(je)
                    else:
                        matches, me = safe_api_post(
                            f"{API}/match", json={"profile": p, "jobs": jobs}, timeout=45,
                        )
                        if me:
                            st.error(me)
                        elif matches:
                            st.session_state["cached_jobs"] = jobs
                            st.session_state["latest_matches"] = matches
                            st.success("✅ Matches ready! Go to Dashboard.")

    # ── APPLICATIONS ──
    elif nav == "📋 Applications":
        apps = st.session_state.get("applications", [])
        st.markdown(f"""
<div class="card">
  <div class="card-title">📋 My Applications</div>
  <div class="muted">{len(apps)} application(s) tracked this session.</div>
</div>
""", unsafe_allow_html=True)

        if not apps:
            st.markdown("""
<div class="card" style="text-align:center;padding:2.5rem;">
  <div style="font-size:2rem;margin-bottom:8px;">📭</div>
  <div style="font-weight:700;color:#eef0f6;margin-bottom:4px;">No applications yet</div>
  <div class="muted">Apply to jobs from the Jobs tab.</div>
</div>
""", unsafe_allow_html=True)
        else:
            for app in apps:
                sc = "#34d399" if app["status"] == "Sent" else "#fbbf24"
                st.markdown(f"""
<div class="job-card">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div class="job-title">{app.get('title','')}</div>
      <div class="job-company">{app.get('company','')} · 📍 {app.get('location','')}</div>
      <div class="job-meta">Applied as: {app.get('name','')} · {app.get('email','')}</div>
    </div>
    <span style="color:{sc};font-size:0.76rem;font-weight:700;letter-spacing:0.04em;">● {app['status']}</span>
  </div>
</div>
""", unsafe_allow_html=True)
                with st.expander(f"Cover Note — {app.get('title','')}"):
                    st.write(app.get("cover", ""))