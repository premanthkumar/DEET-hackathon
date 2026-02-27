import streamlit as st
import requests
import logging

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
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    * { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background: #080c14; color: #e2e8f0; }
    .block-container { padding: 2rem 3rem; max-width: 1400px; }
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    .deet-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 1.2rem 2rem;
        background: linear-gradient(135deg, #0d1117 0%, #161b27 100%);
        border: 1px solid #1e2d40; border-radius: 16px; margin-bottom: 2rem;
        box-shadow: 0 0 40px rgba(0, 120, 255, 0.08);
    }
    .deet-logo {
        font-size: 1.8rem; font-weight: 700; letter-spacing: -0.04em;
        background: linear-gradient(135deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .deet-tagline {
        font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
        color: #4a9eff; letter-spacing: 0.15em; text-transform: uppercase;
    }
    .live-badge {
        display: flex; align-items: center; gap: 8px;
        background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 14px; border-radius: 100px; font-size: 0.72rem; color: #10b981;
        font-family: 'JetBrains Mono', monospace; letter-spacing: 0.1em;
    }
    .offline-badge {
        display: flex; align-items: center; gap: 8px;
        background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 6px 14px; border-radius: 100px; font-size: 0.72rem; color: #ef4444;
        font-family: 'JetBrains Mono', monospace; letter-spacing: 0.1em;
    }
    .live-dot {
        width: 7px; height: 7px; background: #10b981; border-radius: 50%;
        animation: pulse 1.5s ease-in-out infinite; display: inline-block;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(1.3); }
    }
    .stats-row {
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #0d1117, #161b27);
        border: 1px solid #1e2d40; border-radius: 12px; padding: 1.2rem 1.5rem;
        position: relative; overflow: hidden;
    }
    .stat-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    }
    .stat-number {
        font-size: 2rem; font-weight: 700; letter-spacing: -0.04em;
        background: linear-gradient(135deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 0.72rem; color: #64748b; text-transform: uppercase;
        letter-spacing: 0.1em; margin-top: 2px; font-family: 'JetBrains Mono', monospace;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: #0d1117; border-radius: 12px; padding: 4px;
        border: 1px solid #1e2d40; gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #64748b; border-radius: 8px;
        font-weight: 500; font-size: 0.85rem; padding: 8px 20px; border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1d4ed8, #6d28d9) !important; color: white !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem; }
    .job-card {
        background: linear-gradient(135deg, #0d1117 0%, #111827 100%);
        border: 1px solid #1e2d40; border-radius: 14px; padding: 1.4rem 1.6rem;
        margin-bottom: 0.5rem; transition: all 0.2s ease; position: relative; overflow: hidden;
    }
    .job-card:hover {
        border-color: #3b82f6; box-shadow: 0 0 20px rgba(59,130,246,0.1); transform: translateY(-1px);
    }
    .job-card::after {
        content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
        background: linear-gradient(180deg, #3b82f6, #8b5cf6); border-radius: 3px 0 0 3px;
    }
    .job-title { font-size: 1rem; font-weight: 600; color: #e2e8f0; margin-bottom: 4px; }
    .job-company { font-size: 0.82rem; color: #60a5fa; font-weight: 500; }
    .job-meta { font-size: 0.75rem; color: #475569; font-family: 'JetBrains Mono', monospace; margin-top: 6px; }
    .skill-tag {
        display: inline-block; background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.2);
        color: #60a5fa; padding: 2px 10px; border-radius: 100px; font-size: 0.7rem; margin: 2px;
        font-family: 'JetBrains Mono', monospace;
    }
    .verified-badge {
        background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.25);
        color: #10b981; padding: 3px 10px; border-radius: 100px;
        font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
    }
    .applied-badge {
        background: rgba(139,92,246,0.1); border: 1px solid rgba(139,92,246,0.3);
        color: #a78bfa; padding: 3px 10px; border-radius: 100px;
        font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
    }
    .match-high { font-size: 1.8rem; font-weight: 700; background: linear-gradient(135deg, #10b981, #059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .match-mid  { font-size: 1.8rem; font-weight: 700; background: linear-gradient(135deg, #f59e0b, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .match-low  { font-size: 1.8rem; font-weight: 700; background: linear-gradient(135deg, #ef4444, #dc2626); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .profile-card {
        background: linear-gradient(135deg, #0d1117, #111827);
        border: 1px solid #1e2d40; border-radius: 14px; padding: 1.6rem 2rem; margin-bottom: 1.5rem;
    }
    .profile-name { font-size: 1.4rem; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
    .profile-meta { font-size: 0.8rem; color: #64748b; font-family: 'JetBrains Mono', monospace; }
    .stButton > button {
        background: linear-gradient(135deg, #1d4ed8, #6d28d9); color: white; border: none;
        border-radius: 10px; padding: 0.6rem 1.4rem; font-weight: 600; font-size: 0.85rem;
        transition: all 0.2s ease; width: 100%;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(29,78,216,0.4); }
    .section-header {
        font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; color: #3b82f6;
        text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 1rem;
        display: flex; align-items: center; gap: 8px;
    }
    .section-header::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, #1e2d40, transparent); }
    .rank-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 28px; height: 28px; background: linear-gradient(135deg, #1d4ed8, #6d28d9);
        border-radius: 8px; font-size: 0.75rem; font-weight: 700; color: white; margin-right: 8px;
    }
    [data-testid="stFileUploader"] { background: #0d1117; border: 1px solid #1e2d40; border-radius: 12px; }
    .stSpinner > div { border-top-color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def check_api_health() -> bool:
    try:
        r = requests.get(f"{API}/docs", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def safe_api_get(url: str, timeout: int = 10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Is uvicorn running on port 8000?"
    except requests.exceptions.Timeout:
        return None, "Request timed out. Backend may be overloaded."
    except requests.exceptions.HTTPError as e:
        return None, f"API error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, f"Unexpected error: {e}"

def safe_api_post(url: str, **kwargs):
    try:
        r = requests.post(url, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Is uvicorn running on port 8000?"
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except requests.exceptions.HTTPError as e:
        return None, f"API error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, f"Unexpected error: {e}"

def skills_html(skills: list) -> str:
    return "".join(f'<span class="skill-tag">{s}</span>' for s in skills)

def is_applied(job_title: str, job_company: str) -> bool:
    return any(
        a["title"] == job_title and a["company"] == job_company
        for a in st.session_state.get("applications", [])
    )


# ── SESSION STATE INIT ────────────────────────────────────────────────────────

if "applications" not in st.session_state:
    st.session_state["applications"] = []
if "cached_jobs" not in st.session_state:
    st.session_state["cached_jobs"] = []


# ── HEADER ────────────────────────────────────────────────────────────────────

api_online = check_api_health()
badge_html = (
    '<div class="live-badge"><span class="live-dot"></span> SYSTEM LIVE</div>'
    if api_online else
    '<div class="offline-badge">⚠ BACKEND OFFLINE</div>'
)

st.markdown(f"""
<div class="deet-header">
    <div>
        <div class="deet-logo">⚡ DEET AutoMatch</div>
        <div class="deet-tagline">AI-Powered Job Discovery &amp; Talent Registration</div>
    </div>
    {badge_html}
</div>
""", unsafe_allow_html=True)

if not api_online:
    st.error("⚠️ Backend is offline. Start it with: `uvicorn main:app --reload --port 8000`")


# ── STATS ─────────────────────────────────────────────────────────────────────

job_count = len(st.session_state["cached_jobs"]) or "—"
profile_skills = len(st.session_state["profile"].get("skills", [])) if "profile" in st.session_state else "—"
applied_count = len(st.session_state["applications"])

st.markdown(f"""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-number">3</div>
        <div class="stat-label">Employers Crawled</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{job_count}</div>
        <div class="stat-label">Jobs Discovered</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{applied_count}</div>
        <div class="stat-label">Applications Sent</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{profile_skills}</div>
        <div class="stat-label">Your Skills Found</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── TABS ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["⚡  Live Job Listings", "🧠  Register via Resume", "📋  My Applications"])


# ════════════════════════════════
# TAB 1 — JOB LISTINGS
# ════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Auto-Discovered Vacancies</div>', unsafe_allow_html=True)

    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        fetch = st.button("🔄  Fetch Latest Jobs")
    with col_info:
        st.markdown(
            "<p style='color:#475569;font-size:0.8rem;padding-top:0.6rem;"
            "font-family:JetBrains Mono,monospace;'>Crawled live from TCS · Infosys · Internshala</p>",
            unsafe_allow_html=True
        )

    if fetch:
        with st.spinner("Crawling employer career pages..."):
            jobs, error = safe_api_get(f"{API}/jobs", timeout=15)
        if error:
            st.error(f"❌ {error}")
        elif jobs:
            st.session_state["cached_jobs"] = jobs
            st.rerun()

    # ── JOB CARDS LOOP ── (apply form is BELOW this, outside the loop)
    if st.session_state["cached_jobs"]:
        st.success(f"✓ Showing {len(st.session_state['cached_jobs'])} vacancies")
        st.markdown("<br>", unsafe_allow_html=True)

        for job in st.session_state["cached_jobs"]:
            already_applied = is_applied(job.get("title"), job.get("company"))
            verified = "✓ Verified" if job.get("verified") else "Mock Data"
            verified_color = "#10b981" if job.get("verified") else "#475569"
            applied = "✓ Applied" if already_applied else ""

            st.markdown(f"""
            <div class="job-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                        <div class="job-title">{job.get('title', 'Unknown Role')}</div>
                        <div class="job-company">{job.get('company', '')}</div>
                        <div class="job-meta">📍 {job.get('location', '')} · 💼 {job.get('type', '')}</div>
                        <div style="margin-top:10px;">{skills_html(job.get('skills', []))}</div>
                    </div>
                    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;min-width:90px;">
                        <span style="color:{verified_color};font-size:0.7rem;font-family:'JetBrains Mono',monospace;">{verified}</span>
                        <span style="color:#a78bfa;font-size:0.7rem;font-family:'JetBrains Mono',monospace;">{applied}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not already_applied:
                company_url = COMPANY_URLS.get(job.get("company", ""), "#")
                col_open, col_apply = st.columns([1, 1])
                with col_open:
                    st.link_button("🌐 Open Job Page", company_url)
                with col_apply:
                    if st.button("📨 Apply Now", key=f"apply_{job.get('company')}_{job.get('title')}"):
                        st.session_state["apply_target"] = job
                        st.rerun()

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── APPLY FORM — outside the for loop, still inside tab1 ──────────────────
if "apply_target" in st.session_state:
        job = st.session_state["apply_target"]
        profile = st.session_state.get("profile", {})

        st.markdown("---")
        st.markdown(f'<div class="section-header">Apply — {job.get("title")} at {job.get("company")}</div>', unsafe_allow_html=True)

        with st.form("apply_form"):
            name  = st.text_input("Your Name",  value=profile.get("name", ""))
            email = st.text_input("Your Email", value=profile.get("email", ""))
            cover = st.text_area(
                "Cover Note",
                value=(
                    f"I am excited to apply for the {job.get('title')} position at {job.get('company')}. "
                    f"With {profile.get('experience_years', 0)} years of experience and skills in "
                    f"{', '.join(profile.get('skills', [])[:5])}, I believe I am a strong fit for this role."
                ),
                height=150
            )
            col_submit, col_cancel = st.columns([1, 1])
            with col_submit:
                submitted = st.form_submit_button("📨 Send Application")
            with col_cancel:
                cancelled = st.form_submit_button("✕ Cancel")

        if submitted:
            if not name or not email:
                st.error("Please fill in your name and email.")
            else:
                result, err = safe_api_post(f"{API}/apply", json={
                    "applicant_name": name,
                    "applicant_email": email,
                    "cover_note": cover,
                    "job_title": job.get("title"),
                    "job_company": job.get("company"),
                })
                if err:
                    st.warning(f"⚠️ Email could not be sent: {err} — application is still tracked.")
                else:
                    st.success("✅ Application email sent!")

                st.session_state["applications"].append({
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "name": name,
                    "email": email,
                    "cover": cover,
                    "status": "Sent" if not err else "Tracked (email failed)",
                })
                del st.session_state["apply_target"]
                st.rerun()

        if cancelled:
            del st.session_state["apply_target"]
            st.rerun()


# ════════════════════════════════
# TAB 2 — RESUME REGISTRATION
# ════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Instant Profile Creation</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"],
        help="Your DEET profile will be created automatically using AI"
    )

    if uploaded:
        with st.spinner("⚡ AI engine parsing your resume..."):
            profile, error = safe_api_post(
                f"{API}/parse-resume",
                files={"file": ("resume.pdf", uploaded.getvalue(), "application/pdf")},
                timeout=30
            )

        if error:
            st.error(f"❌ Parser error: {error}")
            profile = None

        if profile:
            parse_failed = "Could not parse" in profile.get("name", "")
            if parse_failed:
                st.error(f"❌ {profile.get('name')} — Try uploading a cleaner, text-based PDF.")
            else:
                st.success("✅ DEET Profile Created Successfully")
                st.session_state["profile"] = profile
                st.markdown("<br>", unsafe_allow_html=True)

                all_skills = profile.get("skills", [])
                hidden = max(0, len(all_skills) - 10)
                skill_preview = skills_html(all_skills[:10])
                if hidden:
                    skill_preview += f'<span style="color:#64748b;font-size:0.7rem;margin-left:4px;">+{hidden} more</span>'

                # Social links (LinkedIn / GitHub)
                social_bits = []
                if profile.get("linkedin"):
                    social_bits.append(f'<a href="{profile["linkedin"]}" target="_blank" style="color:#60a5fa;text-decoration:none;">LinkedIn</a>')
                if profile.get("github"):
                    sep = " · " if social_bits else ""
                    social_bits.append(sep + f'<a href="{profile["github"]}" target="_blank" style="color:#60a5fa;text-decoration:none;">GitHub</a>')
                social_html = "".join(social_bits)

                st.markdown(f"""
                <div class="profile-card">
                    <div class="profile-name">{profile.get('name', '—')}</div>
                    <div class="profile-meta">
                        {profile.get('email', '')}
                        {' · ' if profile.get('email') and profile.get('phone') else ''}
                        {profile.get('phone', '')}
                        {' · ' if (profile.get('email') or profile.get('phone')) and social_html else ''}
                        {social_html}
                    </div>
                    <div class="profile-meta" style="margin-top:4px;">📍 {profile.get('location', '—')}  ·  🎓 {profile.get('education', '—')}</div>
                    <div style="margin-top:14px;">{skill_preview}</div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Experience", f"{profile.get('experience_years', 0)} yrs")
                with col2:
                    st.metric("Skills Found", len(all_skills))
                with col3:
                    st.metric("Previous Roles", len(profile.get("previous_roles", [])))

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("🎯  Find My Matching Jobs"):
                    with st.spinner("🧠 Fetching jobs and calculating matches..."):
                        jobs, jobs_err = safe_api_get(f"{API}/jobs", timeout=15)
                        if jobs_err:
                            st.error(f"❌ Could not fetch jobs: {jobs_err}")
                        else:
                            matches, match_err = safe_api_post(
                                f"{API}/match",
                                json={"profile": profile, "jobs": jobs},
                                timeout=45
                            )
                            if match_err:
                                st.error(f"❌ Matching failed: {match_err}")
                            elif matches:
                                st.session_state["cached_jobs"] = jobs
                                st.markdown("<br>", unsafe_allow_html=True)
                                st.markdown('<div class="section-header">Top Matches for You</div>', unsafe_allow_html=True)

                                for i, job in enumerate(matches[:5]):
                                    score = job.get("match_score", 0)
                                    score_class = "match-high" if score >= 70 else "match-mid" if score >= 40 else "match-low"
                                    already_applied = is_applied(job.get("title"), job.get("company"))
                                    applied_html = '<span class="applied-badge">✓ Applied</span>' if already_applied else ""

                                    st.markdown(f"""
                                    <div class="job-card">
                                        <div style="display:flex;justify-content:space-between;align-items:center;">
                                            <div style="flex:1;">
                                                <div style="display:flex;align-items:center;">
                                                    <span class="rank-badge">#{i+1}</span>
                                                    <span class="job-title">{job.get('title')}</span>
                                                </div>
                                                <div class="job-company" style="margin-left:36px;">{job.get('company')}  ·  📍 {job.get('location')}</div>
                                                <div style="margin:10px 0 6px 36px;font-size:0.78rem;color:#94a3b8;font-style:italic;">"{job.get('match_reason', '')}"</div>
                                                <div style="margin-left:36px;">{skills_html(job.get('skills', []))}</div>
                                            </div>
                                            <div style="text-align:center;min-width:80px;">
                                                <div class="{score_class}">{score}%</div>
                                                <div style="font-size:0.65rem;color:#475569;font-family:JetBrains Mono,monospace;">MATCH</div>
                                                <div style="margin-top:6px;">{applied_html}</div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    if not already_applied:
                                        company_url = COMPANY_URLS.get(job.get("company", ""), "#")
                                        col_open, col_apply = st.columns([1, 1])
                                        with col_open:
                                            st.link_button("🌐 Open Job Page", company_url)
                                        with col_apply:
                                            if st.button("📨 Apply Now", key=f"match_apply_{i}_{job.get('company')}"):
                                                st.session_state["apply_target"] = job
                                                st.rerun()


# ════════════════════════════════
# TAB 3 — APPLICATIONS TRACKER
# ════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Your Applications This Session</div>', unsafe_allow_html=True)

    apps = st.session_state.get("applications", [])

    if not apps:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#475569;">
            <div style="font-size:2rem;margin-bottom:1rem;">📋</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;">
                No applications yet. Apply to jobs from the listings tab.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success(f"✓ {len(apps)} application(s) tracked this session")
        st.markdown("<br>", unsafe_allow_html=True)

        for i, app in enumerate(apps):
            status_color = "#10b981" if app["status"] == "Sent" else "#f59e0b"
            st.markdown(f"""
            <div class="job-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div class="job-title">{app['title']}</div>
                        <div class="job-company">{app['company']}  ·  📍 {app.get('location', '')}</div>
                        <div class="job-meta" style="margin-top:6px;">
                            Applied as: {app['name']}  ·  {app['email']}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:{status_color};font-size:0.8rem;font-family:'JetBrains Mono',monospace;font-weight:600;">
                            ● {app['status']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"View Cover Note — {app['title']}"):
                st.write(app["cover"])