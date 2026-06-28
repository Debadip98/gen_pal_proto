"""GenPal Question Bank Factory — Enterprise UI (FastAPI-backed)."""
from __future__ import annotations

import time

import streamlit as st

import api_client as _api

# Keep backward-compatible imports for page functions that still reference
# plan/config constants directly (display only — no LLM calls via services).
try:
    from services import plan, config
except ImportError:
    from backend.core import constants as plan, config

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# ─── Mock data ────────────────────────────────────────────────────────────────
MOCK_QUESTIONS = [
    {"title": "Q001", "topic": "SharePoint Farm Architecture", "career_level": "ASE",
     "complexity": "Basic", "status": "Accepted", "duplicate_warning": False,
     "doc_alignment": "ALIGNED", "last_sme_action": "Accepted",
     "question": "What is a SharePoint Server farm and what are its primary components?",
     "answer": "A SharePoint Server farm is a collection of servers providing SharePoint services. Primary components include web front-end servers, application servers, database servers, and the Central Administration server.",
     "reference_url": "https://learn.microsoft.com/en-us/sharepoint/", "sme_feedback": ""},
    {"title": "Q002", "topic": "SharePoint Security", "career_level": "ASE",
     "complexity": "Basic", "status": "Rejected", "duplicate_warning": False,
     "doc_alignment": "ALIGNED", "last_sme_action": "Rejected",
     "question": "Explain the difference between SharePoint permission levels and permission groups.",
     "answer": "Permission levels define what actions a user can perform. Permission groups are collections of users assigned a permission level.",
     "reference_url": "https://learn.microsoft.com/en-us/sharepoint/",
     "sme_feedback": "Make more specific to SharePoint 2019 governance scenario."},
    {"title": "Q003", "topic": "SharePoint Search", "career_level": "SE",
     "complexity": "Intermediate", "status": "Regenerated", "duplicate_warning": True,
     "doc_alignment": "PARTIALLY_ALIGNED", "last_sme_action": "Regenerated",
     "question": "How does SharePoint Server search handle content crawling and indexing?",
     "answer": "SharePoint search uses a crawl component to traverse content sources, processes documents through content processing, and stores indexed data for fast retrieval.",
     "reference_url": "https://learn.microsoft.com/en-us/sharepoint/", "sme_feedback": ""},
    {"title": "Q004", "topic": "SharePoint Object Model", "career_level": "SE",
     "complexity": "Intermediate", "status": "Pending", "duplicate_warning": False,
     "doc_alignment": "ALIGNED", "last_sme_action": "—",
     "question": "What is the SPWeb object in SharePoint Server Object Model?",
     "answer": "SPWeb represents a SharePoint site. It provides access to lists, document libraries, subsites, users, and configuration settings for a single site.",
     "reference_url": "https://learn.microsoft.com/en-us/sharepoint/", "sme_feedback": ""},
    {"title": "Q005", "topic": "SharePoint Farm Architecture", "career_level": "SSE",
     "complexity": "Advanced", "status": "Pending", "duplicate_warning": False,
     "doc_alignment": "ALIGNED", "last_sme_action": "—",
     "question": "Describe HA configuration options for a SharePoint Server 2019 farm.",
     "answer": "High availability in SharePoint 2019 includes SQL Server AlwaysOn Availability Groups, multiple WFE servers with load balancing, and redundant application servers.",
     "reference_url": "https://learn.microsoft.com/en-us/sharepoint/", "sme_feedback": ""},
]

MOCK_NOTIFICATIONS = [
    {"id": 1, "time": "2 min ago", "action": "accepted", "question": "Q001",
     "message": "SME accepted question Q001 — SharePoint Farm Architecture.", "read": False},
    {"id": 2, "time": "15 min ago", "action": "rejected", "question": "Q002",
     "message": "SME rejected Q002 with feedback: 'Make more specific to SP2019'.", "read": False},
    {"id": 3, "time": "32 min ago", "action": "regenerated", "question": "Q003",
     "message": "SME regenerated Q003. Pending your approval.", "read": True},
    {"id": 4, "time": "1 hr ago", "action": "started", "question": None,
     "message": "SME review session started for SharePoint Server Development.", "read": True},
]

MOCK_DOCS = [
    {"use": True, "title": "Microsoft SharePoint Server Documentation", "domain": "learn.microsoft.com",
     "url": "https://learn.microsoft.com/en-us/sharepoint/", "relevance": "High",
     "source_type": "Official", "summary": "Official Microsoft documentation covering SharePoint Server architecture, administration, and development."},
    {"use": True, "title": "SharePoint Dev Center", "domain": "learn.microsoft.com",
     "url": "https://learn.microsoft.com/en-us/sharepoint/dev/", "relevance": "High",
     "source_type": "Official", "summary": "Developer-focused documentation including CSOM, REST API, and SharePoint Framework guidance."},
    {"use": False, "title": "SharePoint Community Blog", "domain": "techcommunity.microsoft.com",
     "url": "https://techcommunity.microsoft.com/", "relevance": "Medium",
     "source_type": "Community", "summary": "Community articles and best practices for SharePoint administrators and developers."},
]

# ─── CSS ─────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
:root {
    --purple: #A100FF; --purple-light: #F3E6FF; --purple-dark: #7B00C4;
    --dark: #1F1F29; --bg: #FFFFFF; --surface: #F7F7FA; --border: #D9D9E3;
    --success: #1E8E3E; --success-bg: #E6F4EA;
    --warning: #B45309; --warning-bg: #FEF3C7;
    --error: #D93025; --error-bg: #FEE2E2;
    --info: #1D4ED8; --info-bg: #EFF6FF;
    --muted: #6B7280; --secondary: #374151;
}

/* Force light background everywhere */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"],
.main, .block-container { background-color: #FFFFFF !important; color: #1F1F29 !important; }
[data-testid="stMain"] { background-color: #FFFFFF !important; }

#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; max-width: 1400px !important; }

/* Sidebar — always dark */
[data-testid="stSidebar"] {
    background: #1F1F29 !important;
    border-right: 1px solid #2D2D3A !important;
    min-width: 220px !important;
}
[data-testid="stSidebar"] > div { background: #1F1F29 !important; }
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.8rem !important; padding: 0.3rem 0 !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
[data-testid="stSidebar"] [data-baseweb="radio"] { background: transparent !important; }
/* Sidebar collapse button */
[data-testid="collapsedControl"] { color: #CBD5E1 !important; }

/* Buttons */
.stButton > button { border-radius: 6px !important; font-weight: 600 !important; font-size: 0.825rem !important; transition: all 0.15s !important; }
.stButton > button[kind="primary"] { background: var(--purple) !important; border: none !important; color: #FFFFFF !important; }
.stButton > button[kind="primary"]:hover { background: var(--purple-dark) !important; box-shadow: 0 4px 12px rgba(161,0,255,0.3) !important; }
.stButton > button[kind="secondary"] { background: #FFFFFF !important; border: 1.5px solid var(--border) !important; color: var(--dark) !important; }

/* Inputs — light bg */
.stTextInput input, .stTextArea textarea {
    background: #FFFFFF !important; color: #1F1F29 !important;
    border: 1.5px solid #D9D9E3 !important; border-radius: 6px !important;
    font-size: 0.875rem !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #9CA3AF !important; }
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--purple) !important;
    box-shadow: 0 0 0 3px rgba(161,0,255,0.08) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label, .stSlider label, .stCheckbox label {
    font-weight: 500 !important; font-size: 0.875rem !important; color: #1F1F29 !important;
}
/* Radio / checkbox labels */
.stRadio label, .stCheckbox label { color: #1F1F29 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 2px solid var(--border); background: transparent !important; }
.stTabs [data-baseweb="tab"] { border-radius: 6px 6px 0 0 !important; font-weight: 500 !important; font-size: 0.825rem !important; background: transparent !important; color: #6B7280 !important; }
.stTabs [aria-selected="true"] { background: var(--purple-light) !important; color: var(--purple) !important; }
.stTabs [data-baseweb="tab-panel"] { background: #FFFFFF !important; }

/* Containers / borders */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border: 1px solid #D9D9E3 !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    padding: 1rem !important;
}

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 8px !important; overflow: hidden; }

/* Metric */
[data-testid="stMetric"] label { color: #6B7280 !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: #1F1F29 !important; }

/* Alerts */
.stAlert { border-radius: 8px !important; }
[data-testid="stNotification"] { border-radius: 8px !important; }

/* Expander */
.streamlit-expanderHeader { font-weight: 600 !important; color: #1F1F29 !important; background: #F7F7FA !important; border-radius: 6px !important; }

/* Download button */
.stDownloadButton > button { border-radius: 6px !important; font-weight: 600 !important; }
.stDownloadButton > button[kind="primary"] { background: var(--purple) !important; color: white !important; border: none !important; }

/* Custom components */
.gp-header {
    background: #1F1F29 !important; color: white !important;
    padding: 0.875rem 1.5rem !important;
    margin: -1rem -1rem 1rem -1rem !important;
    display: flex !important; align-items: center !important;
    justify-content: space-between !important;
    border-bottom: 3px solid #A100FF !important;
}
.gp-header-left { display: flex; flex-direction: column; }
.gp-header-title { font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em; color: #FFFFFF !important; }
.gp-header-sub { font-size: 0.72rem; color: #94A3B8 !important; margin-top: 3px; }
.gp-header-right { display: flex; gap: 0.5rem; align-items: center; }

.badge {
    display: inline-flex; align-items: center; padding: 2px 9px;
    border-radius: 999px; font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.04em; text-transform: uppercase; white-space: nowrap;
}
.b-purple { background: var(--purple-light); color: var(--purple); }
.b-success { background: var(--success-bg); color: var(--success); }
.b-warning { background: var(--warning-bg); color: var(--warning); }
.b-error { background: var(--error-bg); color: var(--error); }
.b-info { background: var(--info-bg); color: var(--info); }
.b-gray { background: #F3F4F6; color: #6B7280; }
.b-dark { background: #1F1F29; color: white; }

.flow-strip {
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 0.7rem 1.25rem; display: flex; align-items: center; gap: 0.4rem;
    margin-bottom: 1.25rem; overflow-x: auto; flex-wrap: nowrap;
}
.fs { font-size: 0.72rem; font-weight: 500; color: var(--muted); white-space: nowrap; }
.fs.active { color: var(--purple); font-weight: 700; }
.fs.done { color: var(--success); }
.fa { color: #C4C4D4; font-size: 0.8rem; }

.card {
    background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.25rem; margin-bottom: 1rem;
}
.card.accent-purple { border-left: 4px solid var(--purple); }
.card.accent-success { border-left: 4px solid #1E8E3E; }
.card.accent-warning { border-left: 4px solid #F9AB00; }
.card.accent-error { border-left: 4px solid var(--error); }
.card-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--muted); margin-bottom: 0.6rem; }
.card-value { font-size: 1.75rem; font-weight: 700; color: var(--dark); line-height: 1; }
.card-label { font-size: 0.7rem; color: var(--muted); margin-top: 0.2rem; }

.metric-row { display: grid; gap: 0.75rem; margin-bottom: 1.25rem; }
.metric-box { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; }
.m-value { font-size: 1.75rem; font-weight: 700; color: var(--dark); }
.m-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin-top: 0.2rem; }

.section-title { font-size: 1.2rem; font-weight: 700; color: var(--dark); margin: 0 0 0.25rem 0; }
.section-sub { font-size: 0.85rem; color: var(--muted); margin-bottom: 1.25rem; }

.prog-bar-wrap { background: #F3F4F6; border-radius: 999px; height: 8px; overflow: hidden; margin: 0.4rem 0 0.25rem; }
.prog-bar-fill { height: 100%; border-radius: 999px; background: var(--purple); }

.notif-card {
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    padding: 0.75rem 1rem; margin-bottom: 0.5rem; display: flex; gap: 0.75rem;
}
.notif-card.unread { border-left: 3px solid var(--purple); background: #FCFAFF; }
.notif-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--purple); flex-shrink: 0; margin-top: 5px; }
.notif-dot.read { background: #D1D5DB; }
.notif-msg { font-size: 0.8rem; color: var(--secondary); line-height: 1.45; }
.notif-time { font-size: 0.7rem; color: var(--muted); margin-top: 2px; }

.step-row { display: flex; align-items: flex-start; gap: 0; margin-bottom: 1.5rem; overflow-x: auto; }
.step-wrap { display: flex; flex-direction: column; align-items: center; flex: 1; }
.step-circle {
    width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 0.75rem; font-weight: 700; z-index: 1;
    border: 2px solid var(--border); background: var(--bg); color: var(--muted);
}
.step-circle.done { border-color: var(--success); background: var(--success); color: white; }
.step-circle.active { border-color: var(--purple); background: var(--purple); color: white; }
.step-circle.warn { border-color: #F9AB00; background: #F9AB00; color: white; }
.step-lbl { font-size: 0.65rem; font-weight: 600; color: var(--muted); margin-top: 0.3rem; text-align: center; }
.step-lbl.done { color: var(--success); }
.step-lbl.active { color: var(--purple); }
.step-conn { height: 2px; background: var(--border); flex: 1; margin-top: 17px; }
.step-conn.done { background: var(--success); }

.level-card {
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    padding: 1rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 1rem;
}
.level-name { font-weight: 700; font-size: 0.95rem; color: var(--dark); min-width: 40px; }

.q-card { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; }
.q-text { font-size: 0.95rem; font-weight: 500; color: var(--dark); line-height: 1.6; margin-bottom: 0.75rem; }
.a-text { font-size: 0.85rem; color: var(--secondary); line-height: 1.7; padding: 0.75rem; background: var(--surface); border-radius: 6px; border-left: 3px solid var(--border); }

.llm-box { background: #F9F5FF; border: 1.5px solid #DDD6FE; border-radius: 10px; padding: 1.25rem; margin: 1rem 0; }
.llm-title { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--purple); margin-bottom: 0.75rem; }
.llm-row { display: flex; gap: 1rem; margin-bottom: 0.5rem; }
.llm-key { font-size: 0.75rem; font-weight: 600; color: var(--secondary); min-width: 140px; }
.llm-val { font-size: 0.75rem; color: var(--secondary); }

.compare-panel { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; }
.compare-panel.orig { border-top: 3px solid var(--error); }
.compare-panel.prop { border-top: 3px solid var(--success); }
.compare-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.75rem; }
.compare-label.orig { color: var(--error); }
.compare-label.prop { color: var(--success); }

.check-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0; font-size: 0.8rem; color: var(--secondary); }

.timeline { border-left: 2px solid var(--border); padding-left: 1rem; margin-left: 0.25rem; }
.tl-item { position: relative; padding: 0.4rem 0 0.4rem 0.25rem; }
.tl-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--purple); position: absolute; left: -1.4rem; top: 0.55rem; }
.tl-msg { font-size: 0.8rem; color: var(--secondary); }
.tl-time { font-size: 0.7rem; color: var(--muted); }

.dl-card { background: var(--bg); border: 1.5px solid var(--border); border-radius: 12px; padding: 1.5rem; text-align: center; }
.dl-card.ready { border-color: var(--success); }
.dl-card.draft { border-color: #F9AB00; }
.dl-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.dl-title { font-weight: 700; font-size: 1rem; color: var(--dark); margin-bottom: 0.4rem; }
.dl-desc { font-size: 0.78rem; color: var(--muted); line-height: 1.5; margin-bottom: 1rem; }

.flow-overview { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.fo-card { background: var(--bg); border: 1.5px solid var(--border); border-radius: 10px; padding: 1.25rem; text-align: center; transition: all 0.2s; cursor: pointer; }
.fo-card:hover { border-color: var(--purple); box-shadow: 0 4px 16px rgba(161,0,255,0.1); }
.fo-icon { font-size: 1.75rem; margin-bottom: 0.5rem; }
.fo-title { font-size: 0.85rem; font-weight: 700; color: var(--dark); margin-bottom: 0.3rem; }
.fo-desc { font-size: 0.72rem; color: var(--muted); line-height: 1.5; }
.fo-arrow { text-align: center; font-size: 1.25rem; color: var(--border); margin: 0.5rem 0; }

.gp-footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: 0.7rem; color: var(--muted); text-align: center; }
.sep { width: 100%; height: 1px; background: var(--border); margin: 1.25rem 0; }
</style>
"""

# ─── Helpers ──────────────────────────────────────────────────────────────────
def h(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)

def badge(text: str, style: str = "gray") -> str:
    return f'<span class="badge b-{style}">{text}</span>'

def status_badge(status: str) -> str:
    MAP = {
        "Pending": ("gray", "Pending"), "Accepted": ("success", "Accepted"),
        "Rejected": ("error", "Rejected"), "Regenerated": ("info", "Regenerated"),
        "Manual Review Required": ("warning", "Manual Review"),
        "Generating": ("purple", "Generating"), "Locked": ("success", "Locked"),
        "Warning": ("warning", "Warning"), "Export Ready": ("success", "Export Ready"),
        "Duplicate Check Running": ("purple", "Dup Check"), "Pending": ("gray", "Pending"),
        "Mock Mode": ("warning", "Mock Mode"), "Real API Mode": ("success", "Real API Mode"),
        "SME": ("info", "SME"), "Requestor": ("purple", "Requestor"),
        "Enabled": ("success", "Enabled"), "Not Configured": ("gray", "Not Configured"),
    }
    s, label = MAP.get(status, ("gray", status))
    return badge(label, s)

def progress_bar(pct: float, color: str = "var(--purple)") -> str:
    return f"""<div class="prog-bar-wrap"><div class="prog-bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div>"""

def section(title: str, subtitle: str = "") -> None:
    h(f'<div class="section-title">{title}</div>')
    if subtitle:
        h(f'<div class="section-sub">{subtitle}</div>')

def render_header() -> None:
    page = st.session_state.get("page", "input")
    user_type = "SME" if page.startswith("sme") else "Requestor"
    is_mock = st.session_state.get("_genpal_mock_mode", config.use_mock_data())
    mode_label = "Mock Mode" if is_mock else "Real API Mode"
    mode_style = "warning" if is_mock else "success"
    h(f"""
    <div class="gp-header">
        <div class="gp-header-left">
            <div class="gp-header-title">GenPal Question Bank Factory</div>
            <div class="gp-header-sub">AI-assisted question bank generation · SME review · GenPal-ready Excel export</div>
        </div>
        <div class="gp-header-right">
            {badge(mode_label, mode_style)}
            {badge(user_type, "info")}
        </div>
    </div>
    """)

def render_sidebar() -> None:
    NAV = [
        ("input",        "01  Input Form"),
        ("docs",         "02  Documentation"),
        ("progress",     "03  Generation Progress"),
        ("dashboard",    "04  Requestor Dashboard"),
        ("sme_send",     "05  Send to SME"),
        ("sme_review",   "06  SME Review Queue"),
        ("sme_question", "07  Question Review"),
        ("regenerate",   "08  Regenerate"),
        ("comparison",   "09  Version Compare"),
        ("docs_check",   "10  Doc Alignment"),
        ("sme_complete", "11  Review Complete"),
        ("export",       "12  Export Center"),
        ("cost",         "13  Cost & Traceability"),
        ("flow",         "14  Business Flow"),
    ]
    with st.sidebar:
        h("""<div style="padding:1rem 0.5rem 0.75rem;border-bottom:1px solid #2D2D3A;margin-bottom:0.75rem;">
            <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;color:#64748B;text-transform:uppercase;">Navigation</div>
        </div>""")
        labels = [label for _, label in NAV]
        keys   = [key for key, _ in NAV]
        current = st.session_state.get("page", "input")
        current_idx = keys.index(current) if current in keys else 0
        choice = st.radio("", labels, index=current_idx, key="_nav_radio",
                          label_visibility="collapsed")
        chosen_key = keys[labels.index(choice)]
        if chosen_key != current:
            st.session_state["page"] = chosen_key
            st.rerun()

        h('<div style="height:1px;background:#2D2D3A;margin:0.75rem 0;"></div>')
        ls_ok = st.session_state.get("_genpal_langsmith_configured", False)
        h(f"""<div style="padding:0 0.5rem;">
            <div style="font-size:0.68rem;color:#94A3B8;margin-bottom:4px;">
                {'● LangSmith ON' if ls_ok else '○ LangSmith off'}
            </div>
            <div style="font-size:0.68rem;color:#94A3B8;">
                Threshold: {config.get_duplicate_similarity_threshold()}
            </div>
        </div>""")

# ─── Pipeline (API-backed) ────────────────────────────────────────────────────
def _reset_pipeline() -> None:
    for key in ("_genpal_locked", "_genpal_level_dups", "_genpal_pending_level",
                "_genpal_pending_count", "_genpal_merged", "_genpal_final_status",
                "_genpal_final_report", "_genpal_override", "_genpal_errors",
                "_genpal_xlsx", "_genpal_filename", "_genpal_job_id",
                "_genpal_job_token", "_genpal_review_link", "_genpal_review_token"):
        st.session_state.pop(key, None)
    st.session_state["_genpal_locked"] = {}


def _create_job_via_api() -> bool:
    """Create a job in the backend. Returns True on success."""
    inputs = st.session_state.get("_genpal_inputs")
    if not inputs:
        return False
    try:
        level_counts = inputs.get("level_counts", {})
        career_levels = [
            {
                "career_level": lvl,
                "enabled": True,
                "question_count": level_counts.get(lvl, 40),
            }
            for lvl in inputs["levels"]
        ]
        payload = {
            "skill_name": inputs["skill"],
            "ssid": inputs["ssid"],
            "requestor_email": inputs.get("req_email", ""),
            "sme_email": inputs.get("sme_email") or None,
            "topics": inputs["topics"],
            "manual_urls": inputs["urls"],
            "generation_mode": inputs.get("mode", "Dynamic Count"),
            "career_levels": career_levels,
            "duplicate_threshold": inputs.get("threshold", 0.85),
        }
        result = _api.create_job(payload)
        st.session_state["_genpal_job_id"] = result["job_id"]
        st.session_state["_genpal_job_token"] = result["job_token"]
        return True
    except Exception as exc:
        st.session_state["_genpal_errors"] = [f"Failed to create job: {exc}"]
        return False


def _run_pipeline() -> None:
    """Start generation via API and poll for completion."""
    job_id = st.session_state.get("_genpal_job_id")
    if not job_id:
        if not _create_job_via_api():
            return
        job_id = st.session_state.get("_genpal_job_id")

    progress = st.progress(0.0, text="Starting generation via API...")
    try:
        _api.start_generation(job_id)
    except Exception as exc:
        err_msg = str(exc)
        if "409" in err_msg or "already in progress" in err_msg.lower():
            pass  # already generating, continue to poll
        else:
            st.session_state["_genpal_errors"] = [f"Generation failed to start: {exc}"]
            progress.empty()
            return

    poll_count = 0
    while poll_count < 120:  # max ~10 minutes at 5s intervals
        time.sleep(5)
        poll_count += 1
        try:
            job = _api.get_job(job_id)
        except Exception:
            continue

        status = job.get("status", "")
        if status == "GENERATING":
            progress.progress(
                min(0.1 + poll_count * 0.007, 0.9),
                text=f"Generating questions… ({poll_count * 5}s elapsed)",
            )
        elif status == "GENERATED":
            progress.progress(1.0, text="Generation complete!")
            time.sleep(0.5)
            try:
                questions = _api.get_questions(job_id)
                st.session_state["_genpal_merged"] = [
                    {
                        "title": q.get("title"),
                        "ssid": q.get("ssid"),
                        "skill": q.get("skill"),
                        "topic": q.get("topic"),
                        "question_type": q.get("question_type"),
                        "career_level": q.get("career_level"),
                        "complexity": q.get("complexity"),
                        "question": q.get("question"),
                        "answer": q.get("answer"),
                        "options": q.get("options", ""),
                        "reference_url": q.get("reference_url"),
                    }
                    for q in questions
                ]
                st.session_state["_genpal_final_status"] = "FINAL_DUPLICATE_CHECK_PASSED"
                xlsx_bytes = _api.get_export_bytes(job_id, "draft")
                if xlsx_bytes:
                    inputs = st.session_state.get("_genpal_inputs", {})
                    skill = inputs.get("skill", "")
                    ssid = inputs.get("ssid", "")
                    st.session_state["_genpal_xlsx"] = xlsx_bytes
                    st.session_state["_genpal_filename"] = plan.build_filename(skill, ssid)
            except Exception as exc:
                st.session_state["_genpal_errors"] = [f"Failed to fetch results: {exc}"]
            break
        elif status == "FAILED":
            st.session_state["_genpal_errors"] = [
                job.get("error_message") or "Generation failed. Check backend logs."
            ]
            break
        else:
            progress.progress(0.05, text=f"Status: {status}…")

    progress.empty()

# ─── PAGE 1: Input Form ───────────────────────────────────────────────────────
def page_input() -> None:
    h("""<div class="flow-strip">
        <span class="fs active">Input</span><span class="fa">›</span>
        <span class="fs">Generate</span><span class="fa">›</span>
        <span class="fs">Validate</span><span class="fa">›</span>
        <span class="fs">SME Review</span><span class="fa">›</span>
        <span class="fs">Export Excel</span>
    </div>""")

    left, right = st.columns([2, 1])

    with left:
        section("Requestor Input", "Define the skill, topics, career levels, and SME details for question bank generation.")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                skill = st.text_input("Skill Name", placeholder="Microsoft SharePoint Server Development",
                    help="Enter the skill name exactly as it should appear in the Excel file.",
                    key="inp_skill")
            with c2:
                ssid = st.text_input("Skill ID / SSID", placeholder="80002591",
                    help="This value will be repeated in every Excel row.", key="inp_ssid")
            c3, c4 = st.columns(2)
            with c3:
                req_email = st.text_input("Requestor Email", placeholder="requestor@example.com",
                    help="Notifications will be sent to this email after SME actions.", key="inp_req_email")
            with c4:
                sme_email = st.text_input("SME Email", placeholder="sme@example.com",
                    help="The SME review link will be sent to this email.", key="inp_sme_email")
            topics_raw = st.text_area("Topic List", height=130,
                help="Paste one topic per line.",
                placeholder="SharePoint Server Farm Architecture\nSharePoint Server Object Model\nSharePoint Search Configuration\nSharePoint Security and Permissions",
                key="inp_topics")
            urls_raw = st.text_area("Reference URL List", height=110,
                help="Paste one reference URL per line.",
                placeholder="https://learn.microsoft.com/\nhttps://support.microsoft.com/",
                key="inp_urls")
            auto_docs = st.checkbox("Auto-find latest documentation from web based on Skill Name",
                key="inp_auto_docs",
                help="The system will search official/latest docs and suggest additional references.")

        h('<div style="height:0.5rem"></div>')
        with st.container(border=True):
            h('<div class="card-title">Generation Configuration</div>')
            mode = st.radio("Generation Mode", options=[plan.PROTOTYPE_MODE, plan.FULL_MODE],
                index=0, horizontal=True, key="inp_mode")
            if mode == plan.FULL_MODE:
                st.info("Full GenPal Mode enables all 7 career levels. Adjust questions per level below.")

            h('<div style="height:0.5rem"></div>')
            h('<div style="font-size:0.8rem;font-weight:600;color:var(--dark);margin-bottom:0.5rem;">Career Level Configuration</div>')
            all_levels = list(plan.CAREER_LEVELS)
            default_levels = list(plan.DEFAULT_PROTOTYPE_LEVELS) if mode == plan.PROTOTYPE_MODE else all_levels
            if mode == plan.FULL_MODE:
                st.multiselect("Career Levels", options=all_levels, default=all_levels,
                    disabled=True, key="inp_levels_full")
                levels = all_levels
            else:
                levels = st.multiselect("Career Levels", options=all_levels,
                    default=default_levels, key="inp_levels_proto")

            if levels:
                h('<div style="font-size:0.78rem;color:var(--muted);font-weight:600;margin:0.5rem 0 0.25rem;">Questions per Career Level</div>')
                count_cols = st.columns(min(len(levels), 4))
                level_counts: dict[str, int] = {}
                for i, lvl in enumerate(levels):
                    with count_cols[i % len(count_cols)]:
                        level_counts[lvl] = st.number_input(
                            lvl, min_value=5, max_value=200, value=40, step=5,
                            key=f"inp_count_{lvl}",
                        )
            else:
                level_counts = {}

            h('<div style="height:0.5rem"></div>')
            dup_threshold = st.slider("Duplicate Similarity Threshold", 0.70, 1.00,
                value=config.get_duplicate_similarity_threshold(), step=0.01, key="inp_threshold")

        col_a, col_b = st.columns(2)
        with col_a:
            generate_clicked = st.button("Generate Question Bank", type="primary", use_container_width=True)
        with col_b:
            reset_clicked = st.button("Reset Form", type="secondary", use_container_width=True)

        if reset_clicked:
            for k in ["inp_skill","inp_ssid","inp_req_email","inp_sme_email","inp_topics","inp_urls"]:
                st.session_state.pop(k, None)
            st.rerun()

        if generate_clicked:
            topics = plan.parse_lines(topics_raw)
            urls   = plan.parse_lines(urls_raw)
            errors: list[str] = []
            if not skill.strip():   errors.append("Skill Name is required.")
            if not ssid.strip():    errors.append("Skill ID / SSID is required.")
            if not topics:          errors.append("At least one topic is required.")
            if not levels:          errors.append("Select at least one career level.")
            if not urls:            errors.append("At least one reference URL is required.")
            elif not all(plan.looks_like_url(u) for u in urls):
                errors.append("All URLs must start with http:// or https://")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                resolved = plan.build_plan(mode, levels)
                resolved_counts = {lvl: level_counts.get(lvl, 40) for lvl in resolved.levels}
                _reset_pipeline()
                st.session_state["_genpal_inputs"] = {
                    "skill": skill.strip(), "ssid": ssid.strip(),
                    "topics": topics, "urls": urls, "req_email": req_email.strip(),
                    "sme_email": sme_email.strip(), "mode": resolved.mode,
                    "levels": resolved.levels,
                    "level_counts": resolved_counts,
                    "total": sum(resolved_counts.values()),
                }
                st.session_state["_genpal_should_run"] = True
                if auto_docs:
                    st.session_state["page"] = "docs"
                else:
                    st.session_state["page"] = "progress"
                st.rerun()

    with right:
        inp = st.session_state.get("_genpal_inputs", {})
        skill_r   = inp.get("skill") or skill if "inp_skill" in st.session_state else (inp.get("skill") or "—")
        ssid_r    = inp.get("ssid") or (st.session_state.get("inp_ssid") or "—")
        skill_r   = st.session_state.get("inp_skill") or inp.get("skill") or "—"
        ssid_r    = st.session_state.get("inp_ssid") or inp.get("ssid") or "—"
        with st.container(border=True):
            h('<div class="card-title">Expected Output Summary</div>')
            dynamic_total = sum(level_counts.get(lvl, 40) for lvl in levels) if levels else 0
            counts_label = (
                ", ".join(f"{lvl}={level_counts.get(lvl, 40)}" for lvl in levels)
                if levels else "—"
            )
            rows_data = {
                "Skill Name": skill_r, "Skill ID / SSID": ssid_r,
                "Requestor Email": st.session_state.get("inp_req_email") or "—",
                "SME Email": st.session_state.get("inp_sme_email") or "—",
                "Career Levels": ", ".join(levels) if levels else "—",
                "Total Questions": str(dynamic_total) if levels else "—",
                "Questions / Level": counts_label,
            }
            for k, v in rows_data.items():
                h(f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid var(--border);font-size:0.78rem;">'
                  f'<span style="color:var(--muted);font-weight:500;">{k}</span>'
                  f'<span style="color:var(--dark);font-weight:600;text-align:right;max-width:60%;">{v}</span></div>')
            fname = plan.build_filename(skill_r, ssid_r) if skill_r != "—" and ssid_r != "—" else "—"
            h(f'<div style="margin-top:0.75rem;padding:0.6rem;background:var(--surface);border-radius:6px;">'
              f'<div style="font-size:0.68rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">Output File</div>'
              f'<div style="font-size:0.8rem;color:var(--dark);font-weight:600;margin-top:2px;">{fname}</div>'
              f'<div style="font-size:0.7rem;color:var(--muted);margin-top:2px;">Sheet: Sheet1 · Columns: 11</div></div>')

        with st.container(border=True):
            h('<div class="card-title">Complexity Distribution</div>')
            sample_count = level_counts.get(levels[0], 40) if levels else 40
            try:
                from backend.core.constants import calculate_complexity_distribution
                sample_dist = calculate_complexity_distribution(sample_count)
            except ImportError:
                sample_dist = plan.COMPLEXITY_DISTRIBUTION
            for comp, count in sample_dist.items():
                pct = int(count / sample_count * 100) if sample_count else 0
                h(f'<div style="margin-bottom:0.5rem;">'
                  f'<div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:2px;">'
                  f'<span style="color:var(--secondary);">{comp}</span>'
                  f'<span style="color:var(--muted);">{count} / {sample_count}</span></div>'
                  f'{progress_bar(pct)}</div>')

        mode_style = "warning" if config.use_mock_data() else "success"
        mode_label = "Mock Mode" if config.use_mock_data() else "Real API Mode"
        h(f'<div style="text-align:center;margin-top:0.75rem;">{badge(mode_label, mode_style)}</div>')

    h('<div class="gp-footer">Prototype design. Official brand assets should be applied only from approved internal sources.</div>')

# ─── PAGE 2: Documentation Discovery ─────────────────────────────────────────
def page_docs() -> None:
    h("""<div class="flow-strip">
        <span class="fs done">Input</span><span class="fa">›</span>
        <span class="fs active">Documentation</span><span class="fa">›</span>
        <span class="fs">Generate</span><span class="fa">›</span>
        <span class="fs">SME Review</span><span class="fa">›</span>
        <span class="fs">Export Excel</span>
    </div>""")

    inp = st.session_state.get("_genpal_inputs", {})
    skill = inp.get("skill", "the selected skill")
    section("Documentation Discovery", f"Searching latest official documentation for: {skill}")

    tab1, tab2, tab3 = st.tabs(["Auto-Discovered Docs", "Manual URLs", "Selected for Generation"])

    with tab1:
        st.info("Searching the web for official documentation related to this skill...")
        for i, doc in enumerate(MOCK_DOCS):
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    use = st.checkbox(f"**{doc['title']}**", value=doc["use"], key=f"doc_{i}")
                    h(f'<div style="font-size:0.78rem;color:var(--muted);margin-top:2px;">{doc["url"]}</div>')
                    h(f'<div style="font-size:0.78rem;color:var(--secondary);margin-top:4px;">{doc["summary"]}</div>')
                with c2:
                    st.markdown(f"**Relevance:** {doc['relevance']}")
                    h(f'{badge(doc["source_type"], "success" if doc["source_type"]=="Official" else "gray")}')

    with tab2:
        urls_raw = inp.get("urls", [])
        if urls_raw:
            for url in urls_raw:
                h(f'<div style="display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0;border-bottom:1px solid var(--border);">'
                  f'{badge("Manual","purple")}'
                  f'<span style="font-size:0.8rem;color:var(--info);">{url}</span></div>')
        else:
            st.info("No manual URLs provided. Add them on the Input page.")

    with tab3:
        h(f'<div style="margin-bottom:0.75rem;">{badge("3 documents selected for generation","success")}</div>')
        selected = [d for d in MOCK_DOCS if d["use"]]
        for doc in selected:
            h(f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border);">'
              f'{badge("In Use","success")}'
              f'<span style="font-size:0.8rem;font-weight:500;color:var(--dark);">{doc["title"]}</span>'
              f'<span style="font-size:0.75rem;color:var(--muted);">{doc["domain"]}</span></div>')

    h('<div style="height:0.5rem"></div>')
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Use Selected Docs & Continue", type="primary", use_container_width=True):
            st.session_state["page"] = "progress"
            st.session_state["_genpal_should_run"] = True
            st.rerun()
    with c2:
        if st.button("Back to Input", type="secondary", use_container_width=True):
            st.session_state["page"] = "input"
            st.rerun()
    with c3:
        st.button("Skip Documentation", type="secondary", use_container_width=True)

# ─── PAGE 3: Generation Progress ─────────────────────────────────────────────
def page_progress() -> None:
    h("""<div class="flow-strip">
        <span class="fs done">Input</span><span class="fa">›</span>
        <span class="fs done">Documentation</span><span class="fa">›</span>
        <span class="fs active">Generate</span><span class="fa">›</span>
        <span class="fs">Validate</span><span class="fa">›</span>
        <span class="fs">SME Review</span><span class="fa">›</span>
        <span class="fs">Export Excel</span>
    </div>""")

    inp = st.session_state.get("_genpal_inputs")
    if not inp:
        st.warning("No generation inputs found. Please complete the Input Form first.")
        if st.button("Go to Input Form", type="primary"):
            st.session_state["page"] = "input"
            st.rerun()
        return

    levels   = inp["levels"]
    total    = inp["total"]
    skill    = inp["skill"]
    ssid     = inp["ssid"]

    section("Generation Progress", f"{skill} · SSID: {ssid}")

    # Stepper
    stepper_html = '<div class="step-row">'
    locked = st.session_state.get("_genpal_locked", {})
    pending = st.session_state.get("_genpal_pending_level")
    for i, lv in enumerate(levels):
        if i > 0:
            done_conn = lv in locked or (i < levels.index(pending) if pending else False)
            stepper_html += f'<div class="step-conn {"done" if done_conn else ""}"></div>'
        if lv in locked:
            state = "done"
        elif lv == pending:
            state = "warn"
        else:
            state = ""
        stepper_html += (f'<div class="step-wrap">'
                         f'<div class="step-circle {state}">{"✓" if lv in locked else lv[0]}</div>'
                         f'<div class="step-lbl {state}">{lv}</div></div>')
    stepper_html += '</div>'
    h(stepper_html)

    # Run pipeline if triggered
    if st.session_state.pop("_genpal_should_run", False):
        _run_pipeline()

    locked = st.session_state.get("_genpal_locked", {})
    pending = st.session_state.get("_genpal_pending_level")
    errors  = st.session_state.get("_genpal_errors")
    final_status = st.session_state.get("_genpal_final_status")
    final_report = st.session_state.get("_genpal_final_report") or {}
    merged  = st.session_state.get("_genpal_merged")
    xlsx    = st.session_state.get("_genpal_xlsx")

    # Metrics
    done_count = sum(len(v) for v in locked.values())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Expected", total)
    c2.metric("Generated", done_count)
    c3.metric("Dup Pairs", final_report.get("initial_pair_count", 0))
    c4.metric("Reworked", final_report.get("reworked_count", 0))
    c5.metric("Levels Done", len(locked))

    h(progress_bar(done_count / total * 100 if total else 0))
    h(f'<div style="font-size:0.75rem;color:var(--muted);margin-bottom:1rem;">Generated {done_count} / {total} rows</div>')

    # Level status cards
    with st.container(border=True):
        h('<div class="card-title">Career Level Status</div>')
        for lv in levels:
            if lv in locked:
                sb = badge("Locked", "success")
                count_txt = f"{len(locked[lv])} rows"
            elif lv == pending:
                sb = badge("Duplicate Block", "error")
                count_txt = "Action required"
            else:
                sb = badge("Pending", "gray")
                count_txt = "—"
            h(f'<div class="level-card">'
              f'<div class="level-name">{lv}</div>'
              f'{sb}'
              f'<div style="flex:1"></div>'
              f'<div style="font-size:0.78rem;color:var(--muted);">{count_txt}</div></div>')

    # Error / duplicate block
    if pending and st.session_state.get("_genpal_level_dups", {}).get(pending):
        dups = st.session_state["_genpal_level_dups"][pending]
        st.error(f"Career level {pending} has {len(dups)} similar question pair(s) after auto-regeneration.")
        with st.expander("View duplicate pairs", expanded=True):
            for f in dups:
                st.markdown(f"- Rows **{f['row1']}** & **{f['row2']}** · similarity **{f['similarity']}**")
                st.caption(f"Q{f['row1']}: {f['question1']}")
                st.caption(f"Q{f['row2']}: {f['question2']}")
        if st.button(f"Regenerate {pending}", type="primary"):
            st.session_state["_genpal_should_run"] = True
            st.rerun()
        return

    if errors:
        st.error("Validation failed. Export is blocked.")
        for msg in errors[:20]:
            st.warning(msg)
        if st.button("Clear and Regenerate", type="secondary"):
            _reset_pipeline()
            st.session_state["_genpal_should_run"] = True
            st.rerun()
        return

    if final_status == genpal.FINAL_MANUAL_REVIEW_REQUIRED:
        st.warning("Final duplicate repair reached the automatic limit. Manual review required.")
        override = st.checkbox("I confirm these pairs are acceptable or will be reviewed manually.", key="_genpal_override")
        if override and xlsx and merged:
            st.success(f"Override accepted. {len(merged)} questions ready for export.")
            st.download_button("Download Draft Excel", data=xlsx,
                file_name=st.session_state.get("_genpal_filename","genpal.xlsx"),
                mime=XLSX_MIME, type="primary")
        return

    if final_status == genpal.FINAL_DUPLICATE_CHECK_PASSED and xlsx and merged:
        rw = final_report.get("reworked_count", 0)
        st.success(f"Generation complete! {len(merged)} questions ready.{f' ({rw} rows reworked)' if rw else ''}")
        st.session_state["_genpal_sme_questions"] = None  # reset SME mock state
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button("Download Draft Excel", data=xlsx,
                file_name=st.session_state.get("_genpal_filename","genpal.xlsx"),
                mime=XLSX_MIME, type="secondary", use_container_width=True)
        with col_b:
            if st.button("Proceed to Requestor Dashboard", type="primary", use_container_width=True):
                st.session_state["page"] = "dashboard"
                st.rerun()
        with st.expander("Preview first 10 rows"):
            st.dataframe(merged[:10], use_container_width=True, hide_index=True)
        return

    # Nothing generated yet
    if st.button("Start Generation", type="primary"):
        st.session_state["_genpal_should_run"] = True
        st.rerun()

# ─── PAGE 4: Requestor Dashboard ─────────────────────────────────────────────
def page_dashboard() -> None:
    h("""<div class="flow-strip">
        <span class="fs done">Input</span><span class="fa">›</span>
        <span class="fs done">Generate</span><span class="fa">›</span>
        <span class="fs active">Dashboard</span><span class="fa">›</span>
        <span class="fs">SME Review</span><span class="fa">›</span>
        <span class="fs">Export Excel</span>
    </div>""")

    inp = st.session_state.get("_genpal_inputs", {})
    section("Requestor Dashboard", "Monitor SME review progress, notifications, and download options.")

    skill  = inp.get("skill", "Microsoft SharePoint Server Development")
    ssid   = inp.get("ssid", "80002591")
    total  = inp.get("total", 80)
    sme_email = inp.get("sme_email", "sme@example.com")
    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
    notifs    = st.session_state.get("_genpal_notifications", MOCK_NOTIFICATIONS)

    accepted  = sum(1 for q in questions if q["status"] == "Accepted")
    rejected  = sum(1 for q in questions if q["status"] == "Rejected")
    regen     = sum(1 for q in questions if q["status"] == "Regenerated")
    pending   = sum(1 for q in questions if q["status"] == "Pending")
    dup_warns = sum(1 for q in questions if q.get("duplicate_warning"))
    unread    = sum(1 for n in notifs if not n["read"])
    review_pct = int(accepted / len(questions) * 100) if questions else 0

    # Summary metrics
    cols = st.columns(5)
    metrics = [
        ("Skill", skill[:20]+"…" if len(skill)>20 else skill),
        ("SSID", ssid), ("SME Email", sme_email[:18]+"…" if len(sme_email)>18 else sme_email),
        ("Total Questions", str(total)), ("SME Email Sent", "Yes"),
    ]
    for col, (lbl, val) in zip(cols, metrics):
        with col:
            h(f'<div class="metric-box"><div class="m-value" style="font-size:1rem;word-break:break-all;">{val}</div><div class="m-label">{lbl}</div></div>')

    h('<div style="height:0.5rem"></div>')
    cols2 = st.columns(6)
    m2 = [
        ("Accepted",  str(accepted),  "success"),
        ("Rejected",  str(rejected),  "error"),
        ("Regenerated", str(regen),   "info"),
        ("Pending",   str(pending),   "gray"),
        ("Dup Warnings", str(dup_warns), "warning"),
        ("Unread Notifs", str(unread), "purple"),
    ]
    for col, (lbl, val, style) in zip(cols2, m2):
        with col:
            color_map = {"success":"#1E8E3E","error":"#D93025","info":"#1D4ED8","gray":"#6B7280","warning":"#B45309","purple":"#A100FF"}
            h(f'<div class="metric-box"><div class="m-value" style="color:{color_map[style]};">{val}</div><div class="m-label">{lbl}</div></div>')

    h('<div style="height:0.5rem"></div>')
    h(f'<div style="font-size:0.8rem;font-weight:600;color:var(--dark);">SME Review Progress — {accepted} / {len(questions)} Accepted</div>')
    h(progress_bar(review_pct))
    h(f'<div style="font-size:0.72rem;color:var(--muted);margin-bottom:1.25rem;">{review_pct}% complete</div>')

    left, right = st.columns([3, 2])

    with left:
        with st.container(border=True):
            h('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">'
              '<div class="card-title">SME Review Notifications</div>'
              f'<span>{badge(str(unread)+" unread","purple") if unread else badge("All read","success")}</span></div>')
            for notif in notifs[:6]:
                style = "error" if notif["action"]=="rejected" else ("success" if notif["action"]=="accepted" else "info")
                h(f'<div class="notif-card {"unread" if not notif["read"] else ""}">'
                  f'<div class="notif-dot {"read" if notif["read"] else ""}"></div>'
                  f'<div style="flex:1;">'
                  f'<div class="notif-msg">{badge(notif["action"].upper(), style)} {notif["message"]}</div>'
                  f'<div class="notif-time">{notif["time"]}</div>'
                  f'</div></div>')
            if st.button("Mark All as Read", type="secondary"):
                for n in notifs:
                    n["read"] = True
                st.session_state["_genpal_notifications"] = notifs
                st.rerun()

    with right:
        with st.container(border=True):
            h('<div class="card-title">Actions</div>')
            xlsx = st.session_state.get("_genpal_xlsx")
            fname = st.session_state.get("_genpal_filename", "genpal.xlsx")
            all_accepted = all(q["status"] in ("Accepted","Regenerated") for q in questions)

            h('<div class="dl-card draft" style="margin-bottom:0.75rem;">'
              '<div class="dl-icon">📥</div>'
              '<div class="dl-title">Download Draft Excel</div>'
              '<div class="dl-desc">Always available once rows exist. May include pending questions.</div></div>')
            if xlsx:
                st.download_button("Download Draft Excel", data=xlsx, file_name=fname,
                    mime=XLSX_MIME, type="secondary", use_container_width=True)
            else:
                st.button("Draft Excel (generate first)", type="secondary",
                    use_container_width=True, disabled=True)

            h('<div style="height:0.5rem"></div>')
            h(f'<div class="dl-card {"ready" if all_accepted else ""}" style="margin-bottom:0.75rem;">'
              f'<div class="dl-icon">✅</div>'
              f'<div class="dl-title">Download Approved Excel</div>'
              f'<div class="dl-desc">{"All questions approved. Ready for export." if all_accepted else "Available after all questions are accepted."}</div></div>')
            if all_accepted and xlsx:
                st.download_button("Download Approved Excel", data=xlsx, file_name=fname,
                    mime=XLSX_MIME, type="primary", use_container_width=True)
            else:
                st.button("Approved Excel (pending review)", type="secondary",
                    use_container_width=True, disabled=not all_accepted)

            h('<div style="height:0.5rem"></div>')
            if st.button("Send to SME Review", type="primary", use_container_width=True):
                st.session_state["page"] = "sme_send"
                st.rerun()
            if st.button("View SME Review Queue", type="secondary", use_container_width=True):
                st.session_state["page"] = "sme_review"
                st.rerun()

    h('<div style="height:0.5rem"></div>')
    with st.container(border=True):
        h('<div class="card-title">Question Status</div>')
        table_data = [
            {"Title": q["title"], "Topic": q["topic"], "Level": q["career_level"],
             "Complexity": q["complexity"], "Status": q["status"],
             "SME Action": q["last_sme_action"],
             "Dup Warning": "⚠ Yes" if q.get("duplicate_warning") else "—",
             "Doc Alignment": q.get("doc_alignment","—")}
            for q in questions
        ]
        st.dataframe(table_data, use_container_width=True, hide_index=True)

# ─── PAGE 5: Send to SME ─────────────────────────────────────────────────────
def page_sme_send() -> None:
    h("""<div class="flow-strip">
        <span class="fs done">Generate</span><span class="fa">›</span>
        <span class="fs done">Dashboard</span><span class="fa">›</span>
        <span class="fs active">Send to SME</span><span class="fa">›</span>
        <span class="fs">SME Review</span><span class="fa">›</span>
        <span class="fs">Export</span>
    </div>""")

    inp  = st.session_state.get("_genpal_inputs", {})
    skill = inp.get("skill","Microsoft SharePoint Server Development")
    ssid  = inp.get("ssid","80002591")
    sme   = inp.get("sme_email","sme@example.com")
    total = inp.get("total",80)
    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
    dup_warns = sum(1 for q in questions if q.get("duplicate_warning"))

    section("Send to SME Review", "Review the summary and send the review link to the SME.")

    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True):
            h('<div class="card-title">Review Summary</div>')
            rows = [("Skill Name",skill),("Skill ID / SSID",ssid),("Total Questions",str(total)),
                    ("SME Email",sme),("Duplicate Warnings",str(dup_warns)),
                    ("Documentation Used","Yes — 3 sources"),("Estimated Cost","$0.12 (mock)")]
            for k,v in rows:
                h(f'<div style="display:flex;justify-content:space-between;padding:0.35rem 0;border-bottom:1px solid var(--border);font-size:0.8rem;">'
                  f'<span style="color:var(--muted);font-weight:500;">{k}</span>'
                  f'<span style="color:var(--dark);font-weight:600;">{v}</span></div>')

        with st.container(border=True):
            h('<div class="card-title">Review Link Preview</div>')
            review_token = "abc123xyz"
            h(f'<div style="background:var(--surface);border-radius:6px;padding:0.6rem 0.75rem;font-size:0.78rem;color:var(--info);word-break:break-all;">'
              f'https://genpal-app.example.com/review?token={review_token}&skill={ssid}</div>')

        with st.container(border=True):
            h('<div class="card-title">Email Preview</div>')
            h(f'''<div style="background:var(--surface);border-radius:8px;padding:1rem;font-size:0.8rem;">
                <div style="margin-bottom:0.5rem;"><strong>To:</strong> {sme}</div>
                <div style="margin-bottom:0.5rem;"><strong>Subject:</strong> GenPal Question Bank Review Required — {skill}</div>
                <hr style="border-color:var(--border);margin:0.5rem 0;">
                <div style="color:var(--secondary);line-height:1.6;">
                A GenPal question bank has been generated and is ready for your review.<br><br>
                <strong>Skill:</strong> {skill}<br>
                <strong>SSID:</strong> {ssid}<br>
                <strong>Total Questions:</strong> {total}<br><br>
                Please use the secure review link below to accept, reject, or regenerate individual questions.<br><br>
                <span style="color:var(--info);">https://genpal-app.example.com/review?token={review_token}</span><br><br>
                Thank you.
                </div>
            </div>''')

    with right:
        if st.session_state.get("_sme_email_sent"):
            st.success("SME review link sent successfully.")
            h(f'<div style="margin:0.75rem 0;">{badge("Email Sent","success")}</div>')
            if st.button("View SME Review Queue", type="primary", use_container_width=True):
                st.session_state["page"] = "sme_review"
                st.rerun()
        else:
            if st.button("Send SME Review Email", type="primary", use_container_width=True):
                st.session_state["_sme_email_sent"] = True
                st.rerun()

        h('<div style="height:0.5rem"></div>')
        if st.button("Copy Review Link", type="secondary", use_container_width=True):
            st.toast("Review link copied to clipboard!", icon="📋")
        if st.button("Back to Dashboard", type="secondary", use_container_width=True):
            st.session_state["page"] = "dashboard"
            st.rerun()

# ─── PAGE 6: SME Review Queue ─────────────────────────────────────────────────
def page_sme_review() -> None:
    h("""<div class="flow-strip">
        <span class="fs done">Generate</span><span class="fa">›</span>
        <span class="fs active">SME Review</span><span class="fa">›</span>
        <span class="fs">Question Review</span><span class="fa">›</span>
        <span class="fs">Rework</span><span class="fa">›</span>
        <span class="fs">Export</span>
    </div>""")

    inp = st.session_state.get("_genpal_inputs", {})
    section("SME Review Workspace", "Review generated GenPal QnA questions — accept, reject, or regenerate.")

    skill = inp.get("skill","Microsoft SharePoint Server Development")
    ssid  = inp.get("ssid","80002591")
    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)

    accepted  = sum(1 for q in questions if q["status"]=="Accepted")
    rejected  = sum(1 for q in questions if q["status"]=="Rejected")
    regen     = sum(1 for q in questions if q["status"]=="Regenerated")
    pending   = sum(1 for q in questions if q["status"]=="Pending")

    # Job summary
    with st.container(border=True):
        cc = st.columns(6)
        summaries = [("Skill",skill[:22]+"…" if len(skill)>22 else skill),
                     ("SSID",ssid),("Total",str(len(questions))),
                     ("Accepted",str(accepted)),("Rejected",str(rejected)),("Pending",str(pending))]
        for col,(lbl,val) in zip(cc,summaries):
            with col:
                h(f'<div style="text-align:center;"><div style="font-size:1rem;font-weight:700;color:var(--dark);">{val}</div>'
                  f'<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.05em;color:var(--muted);margin-top:2px;">{lbl}</div></div>')

    h(progress_bar(accepted/len(questions)*100 if questions else 0))
    h(f'<div style="font-size:0.72rem;color:var(--muted);margin-bottom:1rem;">Review Progress: {accepted}/{len(questions)} accepted</div>')

    # Filters
    filter_opts = ["All","Pending","Accepted","Rejected","Regenerated","Duplicate Warning"]
    selected_filter = st.radio("Filter", filter_opts, horizontal=True, key="sme_filter", label_visibility="collapsed")

    filtered = questions
    if selected_filter == "Pending":        filtered = [q for q in questions if q["status"]=="Pending"]
    elif selected_filter == "Accepted":     filtered = [q for q in questions if q["status"]=="Accepted"]
    elif selected_filter == "Rejected":     filtered = [q for q in questions if q["status"]=="Rejected"]
    elif selected_filter == "Regenerated":  filtered = [q for q in questions if q["status"]=="Regenerated"]
    elif selected_filter == "Duplicate Warning": filtered = [q for q in questions if q.get("duplicate_warning")]

    with st.container(border=True):
        for i, q in enumerate(filtered):
            sb = status_badge(q["status"])
            dup = f' {badge("⚠ Dup Warning","warning")}' if q.get("duplicate_warning") else ""
            al  = q.get("doc_alignment","ALIGNED")
            al_style = "success" if al=="ALIGNED" else ("warning" if al=="PARTIALLY_ALIGNED" else "error")
            h(f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0;border-bottom:1px solid var(--border);">'
              f'<div style="font-weight:700;font-size:0.85rem;color:var(--dark);min-width:42px;">{q["title"]}</div>'
              f'<div style="flex:1;font-size:0.78rem;color:var(--secondary);line-height:1.4;">'
              f'<div style="font-weight:500;">{q["question"][:80]}{"…" if len(q["question"])>80 else ""}</div>'
              f'<div style="color:var(--muted);font-size:0.7rem;margin-top:2px;">{q["topic"]} · {q["career_level"]} · {q["complexity"]}</div></div>'
              f'{sb}{dup}{badge(al,al_style)}</div>')
            col_act1, col_act2, _ = st.columns([1,1,4])
            with col_act1:
                if st.button("Review", key=f"review_{i}", type="primary"):
                    st.session_state["_sme_selected_q_idx"] = questions.index(q)
                    st.session_state["page"] = "sme_question"
                    st.rerun()
            with col_act2:
                if q["status"]=="Pending":
                    if st.button("Quick Accept", key=f"qacc_{i}", type="secondary"):
                        q["status"] = "Accepted"
                        q["last_sme_action"] = "Accepted"
                        st.session_state["_genpal_sme_questions"] = questions
                        st.rerun()

    h('<div style="height:0.75rem"></div>')
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Complete Review", type="primary", use_container_width=True):
            st.session_state["page"] = "sme_complete"
            st.rerun()
    with c2:
        xlsx = st.session_state.get("_genpal_xlsx")
        fname = st.session_state.get("_genpal_filename","genpal.xlsx")
        if xlsx:
            st.download_button("Download Draft Excel", data=xlsx, file_name=fname,
                mime=XLSX_MIME, type="secondary", use_container_width=True)

# ─── PAGE 7: SME Question Review Detail ──────────────────────────────────────
def page_sme_question() -> None:
    h("""<div class="flow-strip">
        <span class="fs done">SME Review Queue</span><span class="fa">›</span>
        <span class="fs active">Question Review</span><span class="fa">›</span>
        <span class="fs">Rework</span>
    </div>""")

    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
    idx = st.session_state.get("_sme_selected_q_idx", 0)
    q = questions[idx]

    section(f"Question Review — {q['title']}", f"{q['topic']} · {q['career_level']} · {q['complexity']}")

    # Metadata strip
    h(f'<div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1rem;">'
      f'{badge(q["career_level"],"purple")}{badge(q["complexity"],"info")}'
      f'{badge(q["topic"],"gray")}{status_badge(q["status"])}'
      f'{""+badge("⚠ Duplicate Warning","warning") if q.get("duplicate_warning") else ""}'
      f'{badge(q.get("doc_alignment","ALIGNED"),"success" if q.get("doc_alignment","ALIGNED")=="ALIGNED" else "warning")}'
      f'</div>')

    left, right = st.columns([3, 2])

    with left:
        with st.container(border=True):
            h(f'<div class="card-title">Question</div>')
            h(f'<div class="q-text">{q["question"]}</div>')
            h(f'<div class="card-title" style="margin-top:0.75rem;">Answer</div>')
            h(f'<div class="a-text">{q["answer"]}</div>')
            h(f'<div style="margin-top:0.75rem;font-size:0.72rem;color:var(--info);">Reference: {q["reference_url"]}</div>')

        h(f'''<div class="llm-box">
            <div class="llm-title">LLM Review Suggestion</div>
            <div class="llm-row"><span class="llm-key">Quality Summary</span><span class="llm-val">Well-structured question aligned with the topic domain.</span></div>
            <div class="llm-row"><span class="llm-key">Possible Concern</span><span class="llm-val">{"Slight semantic overlap with another access-control question." if q.get("duplicate_warning") else "No major concerns identified."}</span></div>
            <div class="llm-row"><span class="llm-key">Doc Alignment</span><span class="llm-val">{q.get("doc_alignment","ALIGNED")}</span></div>
            <div class="llm-row"><span class="llm-key">Recommended Action</span><span class="llm-val">{"Consider regenerating with a more specific deployment scenario." if q.get("duplicate_warning") else "Accept — meets quality criteria."}</span></div>
            <div class="llm-row"><span class="llm-key">SME Message</span><span class="llm-val">{"This question resembles another. Consider regenerating with a governance or deployment angle." if q.get("duplicate_warning") else "This question is clear, relevant, and documentation-aligned."}</span></div>
        </div>''')

    with right:
        with st.container(border=True):
            h('<div class="card-title">SME Decision</div>')
            if q.get("sme_feedback"):
                h(f'<div style="background:var(--warning-bg,#FEF3C7);border-radius:6px;padding:0.6rem;font-size:0.78rem;color:#92400E;margin-bottom:0.75rem;">'
                  f'<strong>Previous feedback:</strong> {q["sme_feedback"]}</div>')
            feedback = st.text_area("SME Feedback / Review Instruction", key=f"sme_fb_{idx}",
                placeholder="Make this question more relevant to SharePoint farm recovery or deployment topology.",
                height=100, value=q.get("sme_feedback",""))

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Accept", type="primary", use_container_width=True, key=f"acc_{idx}"):
                    q["status"]="Accepted"; q["last_sme_action"]="Accepted"; q["sme_feedback"]=feedback
                    st.session_state["_genpal_sme_questions"]=questions
                    notifs = st.session_state.get("_genpal_notifications", MOCK_NOTIFICATIONS.copy())
                    notifs.insert(0,{"id":len(notifs)+1,"time":"Just now","action":"accepted",
                        "question":q["title"],"message":f"SME accepted {q['title']}.","read":False})
                    st.session_state["_genpal_notifications"]=notifs
                    st.success("Question accepted.")
                    st.rerun()
            with col_b:
                if st.button("Reject", type="secondary", use_container_width=True, key=f"rej_{idx}"):
                    q["status"]="Rejected"; q["last_sme_action"]="Rejected"; q["sme_feedback"]=feedback
                    st.session_state["_genpal_sme_questions"]=questions
                    st.warning("Question rejected.")
                    st.rerun()

            h('<div style="height:0.5rem"></div>')
            if st.button("Regenerate This Question", type="secondary", use_container_width=True, key=f"regen_{idx}"):
                q["sme_feedback"]=feedback
                st.session_state["_genpal_sme_questions"]=questions
                st.session_state["page"]="regenerate"
                st.rerun()
            if st.button("Use LLM Suggestion for Regen", type="secondary", use_container_width=True, key=f"llm_{idx}"):
                q["sme_feedback"]="Consider regenerating with a deployment or governance scenario."
                st.session_state["_genpal_sme_questions"]=questions
                st.session_state["page"]="regenerate"
                st.rerun()

        h('<div style="height:0.5rem"></div>')
        nav_c1, nav_c2 = st.columns(2)
        with nav_c1:
            if idx > 0:
                if st.button("← Previous", type="secondary", use_container_width=True):
                    st.session_state["_sme_selected_q_idx"]=idx-1; st.rerun()
        with nav_c2:
            if idx < len(questions)-1:
                if st.button("Next →", type="secondary", use_container_width=True):
                    st.session_state["_sme_selected_q_idx"]=idx+1; st.rerun()
        if st.button("Back to Review Queue", type="secondary", use_container_width=True):
            st.session_state["page"]="sme_review"; st.rerun()

# ─── PAGE 8: Regenerate Question ─────────────────────────────────────────────
def page_regenerate() -> None:
    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
    idx = st.session_state.get("_sme_selected_q_idx", 0)
    q = questions[idx]

    section("Regenerate Question", f"Only {q['title']} will be reworked. All other questions are unchanged.")
    st.info(f"Only **{q['title']}** will be regenerated. Other {len(questions)-1} questions are preserved.")

    left, right = st.columns([1,1])
    with left:
        with st.container(border=True):
            h('<div class="card-title">Preserved Fields</div>')
            preserved = [("title",q["title"]),("ssid",st.session_state.get("_genpal_inputs",{}).get("ssid","—")),
                         ("skill",st.session_state.get("_genpal_inputs",{}).get("skill","—")),
                         ("topic",q["topic"]),("question_type","QnA"),("career_level",q["career_level"]),
                         ("complexity",q["complexity"]),("reference_url",q["reference_url"])]
            for k,v in preserved:
                h(f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid var(--border);font-size:0.78rem;">'
                  f'<span style="color:var(--muted);font-family:monospace;">{k}</span>'
                  f'<span style="color:var(--dark);font-weight:500;text-align:right;max-width:65%;">{v[:40]+"…" if len(str(v))>40 else v}</span></div>')
    with right:
        with st.container(border=True):
            h('<div class="card-title">Current Question</div>')
            h(f'<div class="q-text">{q["question"]}</div>')
            h('<div class="card-title" style="margin-top:0.75rem;">Current Answer</div>')
            h(f'<div class="a-text">{q["answer"][:200]}{"…" if len(q["answer"])>200 else ""}</div>')

    h('<div style="height:0.5rem"></div>')
    with st.container(border=True):
        h('<div class="card-title">Regeneration Instruction</div>')
        instruction = st.text_area("Instruction (pre-filled from SME feedback / LLM suggestion)",
            value=q.get("sme_feedback",""),
            placeholder="Make this question more relevant to SharePoint farm recovery or a deployment governance scenario.",
            height=100, key="regen_instruction")
        if st.button("Regenerate This Question", type="primary", use_container_width=True):
            st.session_state["_regen_done"] = True
            st.session_state["_regen_instruction"] = instruction
            st.rerun()

    if st.session_state.get("_regen_done"):
        st.success("Question regenerated. Review the proposed change below.")
        h('<div style="height:0.5rem"></div>')
        cl, cr = st.columns(2)
        with cl:
            h('<div class="compare-panel orig"><div class="compare-label orig">Original Version</div>')
            h(f'<div class="q-text">{q["question"]}</div>')
            h(f'<div class="a-text">{q["answer"][:200]}</div></div>')
        with cr:
            new_q = f"[Regenerated] How does {q['topic']} relate to enterprise deployment and governance in {st.session_state.get('_genpal_inputs',{}).get('skill','SharePoint')}?"
            new_a = f"[Regenerated Answer] This question explores {q['topic']} from a deployment governance perspective, covering administration, configuration, and best practices relevant to {q['career_level']}-level practitioners."
            h('<div class="compare-panel prop"><div class="compare-label prop">Regenerated Version</div>')
            h(f'<div class="q-text">{new_q}</div>')
            h(f'<div class="a-text">{new_a}</div>')
            h(f'<div style="margin-top:0.75rem;">{badge("Doc Aligned","success")}{badge("Unique","success")}{badge("Topic Preserved","success")}</div></div>')

        h('<div style="height:0.75rem"></div>')
        ca, cb, cc = st.columns(3)
        with ca:
            if st.button("Accept Change", type="primary", use_container_width=True):
                q["question"]=new_q; q["answer"]=new_a; q["status"]="Accepted"
                q["last_sme_action"]="Accepted after regen"
                st.session_state["_genpal_sme_questions"]=questions
                st.session_state["_regen_done"]=False
                notifs = st.session_state.get("_genpal_notifications", [])
                notifs.insert(0,{"id":len(notifs)+1,"time":"Just now","action":"accepted",
                    "question":q["title"],"message":f"Regenerated {q['title']} was accepted.","read":False})
                st.session_state["_genpal_notifications"]=notifs
                st.session_state["page"]="sme_review"
                st.rerun()
        with cb:
            if st.button("Reject Change", type="secondary", use_container_width=True):
                q["status"]="Rejected"; st.session_state["_genpal_sme_questions"]=questions
                st.session_state["_regen_done"]=False; st.session_state["page"]="sme_review"; st.rerun()
        with cc:
            if st.button("Regenerate Again", type="secondary", use_container_width=True):
                st.session_state["_regen_done"]=False; st.rerun()

        if st.button("View Full Comparison", type="secondary"):
            st.session_state["page"]="comparison"; st.rerun()

# ─── PAGE 9: Version Comparison ──────────────────────────────────────────────
def page_comparison() -> None:
    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
    idx = st.session_state.get("_sme_selected_q_idx", 0)
    q = questions[idx]
    section("Review Proposed Change", f"Side-by-side comparison for {q['title']}")

    cl, cr = st.columns(2)
    with cl:
        with st.container(border=True):
            h('<div class="compare-panel orig"><div class="compare-label orig" style="margin-bottom:0.75rem;">Original Version</div>')
            h(f'<div class="q-text">{q["question"]}</div>')
            h(f'<div class="a-text">{q["answer"]}</div>')
            h(f'<div style="margin-top:0.75rem;">{status_badge("Rejected")}</div>')
            if q.get("sme_feedback"):
                h(f'<div style="font-size:0.75rem;color:var(--muted);margin-top:0.5rem;font-style:italic;">SME: {q["sme_feedback"]}</div>')
            h('</div>')
    with cr:
        new_q = f"[Regenerated] How does {q['topic']} relate to enterprise deployment governance in SharePoint?"
        new_a = "[Regenerated] This covers enterprise deployment patterns, governance frameworks, and best practices."
        with st.container(border=True):
            h('<div class="compare-panel prop"><div class="compare-label prop" style="margin-bottom:0.75rem;">New Proposed Version</div>')
            h(f'<div class="q-text">{new_q}</div>')
            h(f'<div class="a-text">{new_a}</div>')
            checks = [("Same topic preserved","success"),("Career level preserved","success"),
                      ("Complexity preserved","success"),("Doc alignment checked","success"),
                      ("Not similar to previous version","success"),("Duplicate check completed","success")]
            for label,style in checks:
                h(f'<div class="check-row"><span style="color:var(--{style});">✓</span><span>{label}</span></div>')
            h('</div>')

    h('<div style="height:0.75rem"></div>')
    with st.container(border=True):
        h('<div class="card-title">Audit Timeline</div>')
        h('<div class="timeline">')
        timeline = [("Generated","Original question generated by AI."),
                    ("SME Rejected","SME rejected with feedback."),
                    ("Regenerated","Question regenerated using SME instruction."),
                    ("Pending Decision","SME reviewing proposed change.")]
        for event, detail in timeline:
            h(f'<div class="tl-item"><div class="tl-dot"></div>'
              f'<div><div class="tl-msg"><strong>{event}</strong> — {detail}</div>'
              f'<div class="tl-time">GenPal Audit Log</div></div></div>')
        h('</div>')

    h('<div style="height:0.5rem"></div>')
    ca, cb, cc = st.columns(3)
    with ca:
        if st.button("Accept Change", type="primary", use_container_width=True):
            q["status"]="Accepted"; st.session_state["_genpal_sme_questions"]=questions
            st.session_state["page"]="sme_review"; st.rerun()
    with cb:
        if st.button("Reject Change", type="secondary", use_container_width=True):
            q["status"]="Rejected"; st.session_state["_genpal_sme_questions"]=questions
            st.session_state["page"]="sme_review"; st.rerun()
    with cc:
        if st.button("Regenerate Again", type="secondary", use_container_width=True):
            st.session_state["page"]="regenerate"; st.rerun()

# ─── PAGE 10: Doc Alignment Panel ────────────────────────────────────────────
def page_docs_check() -> None:
    section("Documentation Context and Alignment",
            "Review how questions are validated against reference documentation.")
    tab1, tab2, tab3, tab4 = st.tabs(["Manual URLs","Auto-Discovered","Uploaded Docs","Used Context"])

    with tab1:
        inp = st.session_state.get("_genpal_inputs",{})
        urls = inp.get("urls",["https://learn.microsoft.com/en-us/sharepoint/"])
        for url in urls:
            h(f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border);">'
              f'{badge("Manual","purple")}<span style="font-size:0.8rem;color:var(--info);">{url}</span>'
              f'{badge("Active","success")}</div>')

    with tab2:
        for doc in MOCK_DOCS:
            h(f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border);">'
              f'{badge("Auto","info")}'
              f'<div style="flex:1;"><div style="font-size:0.8rem;font-weight:500;">{doc["title"]}</div>'
              f'<div style="font-size:0.72rem;color:var(--muted);">{doc["url"]}</div></div>'
              f'{badge(doc["relevance"],"success" if doc["relevance"]=="High" else "gray")}'
              f'{badge(doc["source_type"],"success" if doc["source_type"]=="Official" else "gray")}</div>')

    with tab3:
        st.info("No documents uploaded. Use manual URLs or auto-discovery.")

    with tab4:
        st.caption("Context used for the currently selected question.")
        questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
        idx = st.session_state.get("_sme_selected_q_idx", 0)
        q = questions[idx]
        al = q.get("doc_alignment","ALIGNED")
        al_style = "success" if al=="ALIGNED" else ("warning" if al=="PARTIALLY_ALIGNED" else "error")
        h(f'<div style="background:var(--surface);border-radius:8px;padding:1rem;margin-bottom:1rem;">'
          f'<div style="font-size:0.75rem;font-weight:600;color:var(--muted);margin-bottom:0.4rem;">QUESTION</div>'
          f'<div style="font-size:0.85rem;color:var(--dark);">{q["question"]}</div></div>')
        h(f'<div style="display:flex;gap:1rem;align-items:center;margin-bottom:0.75rem;">'
          f'<div style="font-size:0.8rem;"><strong>Alignment Status:</strong></div>'
          f'{badge(al,al_style)}</div>')
        h(f'<div style="font-size:0.8rem;color:var(--secondary);line-height:1.6;">'
          f'{"The question is aligned with the selected SharePoint documentation." if al=="ALIGNED" else "The question is partially aligned. Consider regenerating with more specific documentation context."}'
          f'</div>')
        h('<div style="height:0.5rem"></div>')
        if st.button("Use Selected Docs for Rework", type="primary"):
            st.session_state["page"]="regenerate"; st.rerun()

# ─── PAGE 11: SME Review Complete ────────────────────────────────────────────
def page_sme_complete() -> None:
    section("Review Complete", "SME review session summary and final export options.")
    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
    accepted  = sum(1 for q in questions if q["status"]=="Accepted")
    rejected  = sum(1 for q in questions if q["status"]=="Rejected")
    regen     = sum(1 for q in questions if q["status"]=="Regenerated")
    pending   = sum(1 for q in questions if q["status"]=="Pending")
    all_done  = pending == 0

    cols = st.columns(5)
    for col,(lbl,val,style) in zip(cols,[
        ("Total",str(len(questions)),"dark"),("Accepted",str(accepted),"success"),
        ("Rejected",str(rejected),"error"),("Regenerated",str(regen),"info"),
        ("Pending",str(pending),"warning" if pending else "success")]):
        with col:
            color_map={"dark":"var(--dark)","success":"#1E8E3E","error":"#D93025","info":"#1D4ED8","warning":"#B45309"}
            h(f'<div class="metric-box"><div class="m-value" style="color:{color_map[style]};">{val}</div><div class="m-label">{lbl}</div></div>')

    h('<div style="height:0.75rem"></div>')
    xlsx  = st.session_state.get("_genpal_xlsx")
    fname = st.session_state.get("_genpal_filename","genpal.xlsx")

    if all_done:
        st.success("All questions have been reviewed. The approved Excel file is ready for export.")
        h(f'<div style="margin:0.75rem 0;">{badge("Review Complete","success")}{badge("Export Ready","success")}</div>')
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if xlsx:
                st.download_button("Download GenPal Import Excel", data=xlsx,
                    file_name=fname, mime=XLSX_MIME, type="primary", use_container_width=True)
        with col_b:
            if st.button("Notify Requestor", type="secondary", use_container_width=True):
                st.toast("Requestor notification sent!", icon="📧")
        with col_c:
            if st.button("Go to Export Center", type="secondary", use_container_width=True):
                st.session_state["page"]="export"; st.rerun()
    else:
        st.warning(f"{pending} question(s) are still pending review.")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Continue Review", type="primary", use_container_width=True):
                st.session_state["page"]="sme_review"; st.rerun()
        with col_b:
            if st.button("Use Final Override", type="secondary", use_container_width=True):
                for qq in questions:
                    if qq["status"]=="Pending": qq["status"]="Accepted"; qq["last_sme_action"]="Override"
                st.session_state["_genpal_sme_questions"]=questions; st.rerun()
        with col_c:
            if xlsx:
                st.download_button("Download Draft Excel", data=xlsx, file_name=fname,
                    mime=XLSX_MIME, type="secondary", use_container_width=True)

# ─── PAGE 12: Export Center ───────────────────────────────────────────────────
def page_export() -> None:
    section("Excel Download Center", "Download the GenPal-ready question bank Excel file.")
    questions = st.session_state.get("_genpal_sme_questions", MOCK_QUESTIONS)
    xlsx  = st.session_state.get("_genpal_xlsx")
    fname = st.session_state.get("_genpal_filename","genpal.xlsx")
    all_accepted = all(q["status"] in ("Accepted",) for q in questions)

    cl, cr = st.columns(2)
    with cl:
        with st.container(border=True):
            h('<div class="dl-card draft">'
              '<div class="dl-icon">📥</div>'
              '<div class="dl-title">Current Draft Excel</div>'
              '<div class="dl-desc">Available once generated rows exist. May include questions not fully accepted by SME.</div></div>')
            h('<div style="height:0.5rem"></div>')
            if xlsx:
                st.download_button("Download Draft Excel", data=xlsx, file_name=fname,
                    mime=XLSX_MIME, type="secondary", use_container_width=True)
                h(f'<div style="font-size:0.72rem;color:var(--muted);text-align:center;margin-top:0.5rem;">{badge("Always Available","warning")}</div>')
            else:
                st.button("Generate first to download", type="secondary", use_container_width=True, disabled=True)
    with cr:
        with st.container(border=True):
            h(f'<div class="dl-card {"ready" if all_accepted else ""}">'
              f'<div class="dl-icon">✅</div>'
              f'<div class="dl-title">Approved GenPal Excel</div>'
              f'<div class="dl-desc">{"All questions accepted. Ready for GenPal import." if all_accepted else "Available after all questions are accepted or override is used."}</div></div>')
            h('<div style="height:0.5rem"></div>')
            if xlsx and all_accepted:
                st.download_button("Download Approved Excel", data=xlsx, file_name=fname,
                    mime=XLSX_MIME, type="primary", use_container_width=True)
            else:
                st.button("Complete SME review first", type="primary",
                    use_container_width=True, disabled=True)

    h('<div style="height:0.75rem"></div>')
    with st.container(border=True):
        h('<div class="card-title">Excel Validation Checklist</div>')
        checks = [
            ("One workbook", True), ("Sheet named 'Sheet1'", True),
            ("11 columns exactly", True), ("title serial numbers present", True),
            ("ssid in every row", True), ("question_type = QnA", True),
            ("options column blank", True), ("No internal review metadata exported", True),
        ]
        for label, ok in checks:
            icon = "✓" if ok else "✗"
            color = "var(--success)" if ok else "var(--error)"
            h(f'<div class="check-row"><span style="color:{color};font-weight:700;">{icon}</span><span>{label}</span></div>')

    h('<div style="height:0.5rem"></div>')
    inp = st.session_state.get("_genpal_inputs",{})
    skill = inp.get("skill","[skill]")
    ssid  = inp.get("ssid","[ssid]")
    h(f'<div style="background:var(--surface);border-radius:8px;padding:0.75rem 1rem;font-size:0.8rem;">'
      f'<strong>Output file:</strong> <span style="color:var(--purple);font-family:monospace;">{plan.build_filename(skill,ssid)}</span>'
      f' · <strong>Sheet:</strong> Sheet1 · <strong>Columns:</strong> 11 · <strong>Format:</strong> .xlsx</div>')
    h('<div style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted);">'
      '<strong>GenPal columns exported:</strong> '
      + ', '.join(f'<code>{c}</code>' for c in plan.GENPAL_COLUMNS) + '</div>')

# ─── PAGE 13: Cost & Traceability ─────────────────────────────────────────────
def page_cost() -> None:
    section("Cost and Traceability Summary",
            "Estimated API usage, token consumption, and LangSmith trace status.")
    merged = st.session_state.get("_genpal_merged",[])
    inp    = st.session_state.get("_genpal_inputs",{})
    total  = inp.get("total",0)
    ls_ok  = st.session_state.get("_genpal_langsmith_configured",False)

    # Estimate costs (mock)
    gen_cost  = round(total * 0.0015, 4)
    emb_cost  = round(total * 0.0002, 4)
    regen_cost= round(0.005, 4)
    total_cost= round(gen_cost+emb_cost+regen_cost, 4)

    cols = st.columns(4)
    for col,(lbl,val) in zip(cols,[
        ("Total Est. Cost", f"${total_cost}"), ("Generation Cost", f"${gen_cost}"),
        ("Embedding Cost",  f"${emb_cost}"),  ("Regen Cost",       f"${regen_cost}")]):
        with col:
            h(f'<div class="metric-box"><div class="m-value" style="font-size:1.4rem;">{val}</div><div class="m-label">{lbl}</div></div>')

    h('<div style="height:0.5rem"></div>')
    c2 = st.columns(4)
    for col,(lbl,val) in zip(c2,[
        ("Total Questions",str(total)),("OpenAI Calls", str(total*2+5)),
        ("Est. Tokens",f"{total*800:,}"),("Web Search","0 (manual)")]):
        with col:
            h(f'<div class="metric-box"><div class="m-value" style="font-size:1.25rem;">{val}</div><div class="m-label">{lbl}</div></div>')

    h('<div style="height:0.75rem"></div>')
    with st.container(border=True):
        h('<div class="card-title">LangSmith Trace</div>')
        if ls_ok:
            st.success("LangSmith tracing is active. All pipeline calls are being traced.")
            h(f'{badge("Enabled","success")} <span style="font-size:0.8rem;color:var(--secondary);margin-left:0.5rem;">Project: {config.get_langsmith_project()}</span>')
            h('<div style="margin-top:0.75rem;"><a href="https://smith.langchain.com" target="_blank" style="font-size:0.8rem;color:var(--info);">View Trace Dashboard →</a></div>')
        else:
            st.info("LangSmith tracing is not configured. Set LANGSMITH_API_KEY and LANGSMITH_TRACING=true to enable.")
            h(f'{badge("Not Configured","gray")}')

    with st.container(border=True):
        h('<div class="card-title">Usage Breakdown</div>')
        tab1, tab2, tab3 = st.tabs(["Generation","Embedding","SME Regen"])
        with tab1:
            st.caption(f"Model: {config.get_openai_generation_model()} · Questions: {total} · Batches: {total//5 or 1}")
        with tab2:
            st.caption(f"Model: {config.get_openai_embedding_model()} · Vectors: {len(merged) if merged else 0}")
        with tab3:
            st.caption("Regeneration calls depend on duplicate resolution. Mock estimate: ~5 calls.")

# ─── PAGE 14: Business Flow Overview ─────────────────────────────────────────
def page_flow() -> None:
    section("Business Flow Overview",
            "End-to-end GenPal Question Bank Factory process — click any step to navigate.")

    steps = [
        ("input",       "📋", "Request Intake",
         "User enters skill, SSID, topics, URLs, career level counts, and SME email."),
        ("docs",        "🔍", "Documentation Enrichment",
         "System uses pasted URLs and optionally searches latest official docs."),
        ("progress",    "⚡", "AI Question Generation",
         "System generates QnA records by career level with complexity distribution."),
        ("progress",    "🛡", "Duplicate & Format Validation",
         "System checks schema, duplicates, and similarity above threshold."),
        ("sme_review",  "👁", "SME Review",
         "SME accepts, rejects, or regenerates each question via secure review link."),
        ("regenerate",  "🔁", "Question-Level Rework",
         "Only selected question is regenerated using SME feedback and docs."),
        ("export",      "📊", "GenPal Excel Export",
         "System creates one Sheet1 Excel file with 11 columns — GenPal-ready."),
        ("cost",        "📈", "Decision Evidence",
         "System shows cost, traceability, notifications, and review audit trail."),
    ]

    for i in range(0, len(steps), 4):
        row_steps = steps[i:i+4]
        cols = st.columns(len(row_steps))
        for col, (page_key, icon, title, desc) in zip(cols, row_steps):
            with col:
                with st.container(border=True):
                    h(f'<div style="text-align:center;">'
                      f'<div style="font-size:1.75rem;margin-bottom:0.4rem;">{icon}</div>'
                      f'<div style="font-size:0.85rem;font-weight:700;color:var(--dark);margin-bottom:0.3rem;">{title}</div>'
                      f'<div style="font-size:0.72rem;color:var(--muted);line-height:1.5;">{desc}</div></div>')
                    if st.button(f"Go →", key=f"fo_{i}_{title}", type="secondary", use_container_width=True):
                        st.session_state["page"] = page_key
                        st.rerun()
        if i + 4 < len(steps):
            h('<div style="text-align:center;font-size:1.25rem;color:var(--border);margin:0.25rem 0;">↓</div>')

    h('<div style="height:1rem"></div>')
    with st.container(border=True):
        h('<div class="card-title">GenPal Excel Contract</div>')
        h('<div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-top:0.25rem;">')
        for col in plan.GENPAL_COLUMNS:
            h(f'<code style="background:var(--purple-light);color:var(--purple);padding:2px 8px;border-radius:4px;font-size:0.78rem;">{col}</code>')
        h('</div>')
        h('<div style="margin-top:0.75rem;font-size:0.75rem;color:var(--muted);">'
          'Review metadata (status, SME feedback, duplicate warnings) is shown in the UI only — '
          'never exported to the Excel file.</div>')

# ─── Password Gate ────────────────────────────────────────────────────────────
def _password_gate() -> None:
    expected = config.get_app_password()
    if not expected:
        return
    if st.session_state.get("_genpal_authed"):
        return
    st.markdown("### GenPal Question Bank Factory")
    entered = st.text_input("Prototype access password", type="password")
    if not entered:
        st.stop()
    if entered != expected:
        st.warning("Incorrect password.")
        st.stop()
    st.session_state["_genpal_authed"] = True
    st.rerun()

# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="GenPal Question Bank Factory",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    _password_gate()

    if "_genpal_langsmith_configured" not in st.session_state:
        st.session_state["_genpal_langsmith_configured"] = config.configure_langsmith()

    # Check backend connectivity once per session
    if "_genpal_backend_checked" not in st.session_state:
        health = _api.health_check()
        st.session_state["_genpal_backend_ok"] = health.get("status") == "ok"
        st.session_state["_genpal_mock_mode"] = health.get("mock_mode", True)
        st.session_state["_genpal_backend_checked"] = True

    # Route SME review via URL query param
    params = st.query_params
    review_token = params.get("review_token")
    if review_token and not st.session_state.get("_genpal_review_token"):
        st.session_state["_genpal_review_token"] = review_token
        st.session_state["page"] = "sme_review"

    render_header()
    render_sidebar()

    page = st.session_state.get("page", "input")
    pages = {
        "input":        page_input,
        "docs":         page_docs,
        "progress":     page_progress,
        "dashboard":    page_dashboard,
        "sme_send":     page_sme_send,
        "sme_review":   page_sme_review,
        "sme_question": page_sme_question,
        "regenerate":   page_regenerate,
        "comparison":   page_comparison,
        "docs_check":   page_docs_check,
        "sme_complete": page_sme_complete,
        "export":       page_export,
        "cost":         page_cost,
        "flow":         page_flow,
    }
    pages.get(page, page_input)()


if __name__ == "__main__":
    main()
