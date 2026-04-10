from typing import Optional

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Google Fonts — loaded once via CSS @import so both themes share the same font.
# IBM Plex Sans Thai: covers Thai script + Latin + excellent tabular numerals.
# ─────────────────────────────────────────────────────────────────────────────
_FONT_IMPORT = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&display=swap');
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Shared design tokens that don't change between themes (structure only).
# Each theme block below overrides the CSS custom-property values.
# ─────────────────────────────────────────────────────────────────────────────
_SHARED_CSS = """
<style>
/* ── Shared structural rules ───────────────────────────────────────────── */

/* Typography base */
html, body, .stApp {
    font-family: 'IBM Plex Sans Thai', 'Inter', system-ui, -apple-system, sans-serif;
    letter-spacing: 0.01em;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Numbers and units: always tabular so columns align */
.stNumberInput input,
input[type="number"],
div[data-testid="stMetricValue"],
div[data-testid="stMetricDelta"],
table td, table th,
.tabular {
    font-feature-settings: "tnum" 1, "salt" 0;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.02em;
}

/* Layout */
.block-container {
    max-width: 1280px;
    padding: 2rem 2.5rem 4rem;
}

/* ── Status indicators ─────────────────────────────────────────────────── */
.status-pass    { color: var(--pass) !important; font-weight: 600; }
.status-warning { color: var(--warn) !important; font-weight: 600; }
.status-fail    { color: var(--fail) !important; font-weight: 600; }

/* ── Divider ───────────────────────────────────────────────────────────── */
hr {
    border: none;
    height: 1px;
    background: var(--border);
    margin: 1.5rem 0;
}

/* ── Metrics ───────────────────────────────────────────────────────────── */
div[data-testid="stMetricValue"] {
    color: var(--text);
    font-weight: 700;
    font-size: 1.8rem;
}
div[data-testid="stMetricDelta"] {
    color: var(--text-muted);
    font-size: 0.85rem;
}

/* ── Inputs ────────────────────────────────────────────────────────────── */
div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] > div {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    transition: border-color 0.15s ease;
}
div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"]:focus-within {
    border-color: var(--accent) !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] input,
.stNumberInput input,
.stTextInput input,
input[type="number"],
input[type="text"] {
    color: var(--text) !important;
    background-color: var(--surface) !important;
}
.stSelectbox > div > div {
    color: var(--text) !important;
    background-color: var(--surface) !important;
}

/* ── Buttons ───────────────────────────────────────────────────────────── */
.stButton > button,
button[kind="primary"] {
    background: var(--text);
    color: var(--bg);
    border: none;
    border-radius: 6px;
    font-family: inherit;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 0.55rem 1.4rem;
    letter-spacing: 0.02em;
    transition: opacity 0.15s ease, transform 0.1s ease;
}
.stButton > button:hover,
button[kind="primary"]:hover {
    opacity: 0.85;
    transform: translateY(-1px);
}
.stButton > button:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
}

/* ── Tables / DataFrames ───────────────────────────────────────────────── */
div[data-testid="stDataFrame"],
div[data-testid="stTable"] {
    background: var(--surface);
    border-radius: 8px;
    border: 1px solid var(--border);
}
table { color: var(--text); }

/* ── Alerts ────────────────────────────────────────────────────────────── */
.stAlert > div {
    background-color: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 6px;
}

/* ── Progress bar ──────────────────────────────────────────────────────── */
.stProgress > div > div {
    background: var(--pass);
}

/* ── Sidebar ───────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* ── Labels / markdown text ────────────────────────────────────────────── */
div[data-testid="stMarkdown"],
label,
.stTooltip,
.stText,
.stNumberInput label,
p, li, span {
    color: var(--text);
}
.stApp { color: var(--text); }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Per-theme token overrides
# ─────────────────────────────────────────────────────────────────────────────
BASE_THEME_CSS = {
    "Dark": """
<style>
:root {
    color-scheme: dark;
    --bg:          #0a0a0a;
    --surface:     #141414;
    --surface-2:   #1c1c1c;
    --border:      #2a2a2a;
    --text:        #ededed;
    --text-muted:  #737373;
    --accent:      #d4d4d4;
    --pass:        #22c55e;
    --fail:        #ef4444;
    --warn:        #f59e0b;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

/* Sidebar bg already set in shared, ensure bg var used */
section[data-testid="stSidebar"] {
    background: #111111 !important;
}

div[data-testid="stMetricValue"] { color: var(--text); }
div[data-testid="stMetricDelta"] { color: var(--text-muted); }
</style>
""",
    "Light": """
<style>
:root {
    color-scheme: light;
    --bg:          #ffffff;
    --surface:     #f5f5f5;
    --surface-2:   #ebebeb;
    --border:      #e0e0e0;
    --text:        #0a0a0a;
    --text-muted:  #737373;
    --accent:      #404040;
    --pass:        #16a34a;
    --fail:        #dc2626;
    --warn:        #d97706;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

section[data-testid="stSidebar"] {
    background: #f5f5f5 !important;
}

div[data-testid="stMetricValue"] { color: var(--text); }
div[data-testid="stMetricDelta"] { color: var(--text-muted); }
</style>
"""
}

# ─────────────────────────────────────────────────────────────────────────────
# Landing page styles (app.py hero + bento grid)
# ─────────────────────────────────────────────────────────────────────────────
LANDING_THEME_CSS = {
    "Dark": """
<style>
/* ── Hero wrapper ──────────────────────────────────────────────────────── */
.hero-wrapper {
    padding: 3.5rem 0 2.5rem;
}

/* Subtle decorative orbs — neutral, not neon */
.floating-layer {
    position: absolute;
    pointer-events: none;
    border-radius: 50%;
    filter: blur(72px);
    opacity: 0.06;
}
.floating-layer.one {
    top: -80px; left: -80px;
    width: 320px; height: 320px;
    background: #ffffff;
}
.floating-layer.two {
    bottom: -60px; right: -60px;
    width: 240px; height: 240px;
    background: #ffffff;
}

/* ── Glass panel (hero card) ───────────────────────────────────────────── */
.glass-panel {
    position: relative;
    z-index: 1;
    padding: clamp(2rem, 4vw, 3rem);
    border-radius: 16px;
    background: #141414;
    border: 1px solid #2a2a2a;
    margin-bottom: 2.5rem;
}

.hero-eyebrow {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #737373;
    margin-bottom: 0.75rem;
}

.hero-title {
    font-size: clamp(2rem, 4.5vw, 3.2rem);
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 1rem;
    color: #ededed;
    letter-spacing: -0.01em;
}

.hero-lead {
    font-size: 1.05rem;
    line-height: 1.65;
    color: #737373;
    max-width: 68ch;
    margin-bottom: 2rem;
}

.hero-metrics {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.metric-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.9rem;
    border-radius: 4px;
    background: #1c1c1c;
    border: 1px solid #2a2a2a;
    color: #a3a3a3;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.01em;
}

/* ── Bento grid ────────────────────────────────────────────────────────── */
.bento-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
    margin-bottom: 2.5rem;
}

.bento-card {
    display: flex;
    flex-direction: column;
    padding: 1.75rem;
    border-radius: 12px;
    background: #141414;
    border: 1px solid #2a2a2a;
    text-decoration: none !important;
    transition: border-color 0.15s ease, background 0.15s ease;
    color: #ededed;
}

.bento-card:hover {
    border-color: #525252;
    background: #1c1c1c;
}

.bento-card h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #ededed;
    margin: 0.75rem 0 0.5rem;
}

.bento-card p {
    color: #737373;
    font-size: 0.9rem;
    line-height: 1.6;
    flex: 1;
    margin-bottom: 1.25rem;
}

.inline-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: #1c1c1c;
    color: #737373;
    border: 1px solid #2a2a2a;
}

.card-actions {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    color: #a3a3a3;
    font-weight: 600;
    font-size: 0.85rem;
    margin-top: auto;
    transition: color 0.15s ease;
}

.bento-card:hover .card-actions {
    color: #ededed;
}

.note-footer {
    text-align: center;
    color: #525252;
    font-size: 0.82rem;
    margin-top: 3rem;
}

@media (max-width: 768px) {
    .floating-layer { display: none; }
    .block-container { padding: 1.5rem 1.25rem 3rem; }
}
</style>
""",
    "Light": """
<style>
.hero-wrapper {
    padding: 3.5rem 0 2.5rem;
}

.floating-layer {
    position: absolute;
    pointer-events: none;
    border-radius: 50%;
    filter: blur(72px);
    opacity: 0.06;
}
.floating-layer.one {
    top: -80px; left: -80px;
    width: 320px; height: 320px;
    background: #000000;
}
.floating-layer.two {
    bottom: -60px; right: -60px;
    width: 240px; height: 240px;
    background: #000000;
}

.glass-panel {
    position: relative;
    z-index: 1;
    padding: clamp(2rem, 4vw, 3rem);
    border-radius: 16px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    margin-bottom: 2.5rem;
}

.hero-eyebrow {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #737373;
    margin-bottom: 0.75rem;
}

.hero-title {
    font-size: clamp(2rem, 4.5vw, 3.2rem);
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 1rem;
    color: #0a0a0a;
    letter-spacing: -0.01em;
}

.hero-lead {
    font-size: 1.05rem;
    line-height: 1.65;
    color: #737373;
    max-width: 68ch;
    margin-bottom: 2rem;
}

.hero-metrics {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.metric-chip {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.9rem;
    border-radius: 4px;
    background: #f5f5f5;
    border: 1px solid #e0e0e0;
    color: #525252;
    font-size: 0.82rem;
    font-weight: 500;
}

.bento-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
    margin-bottom: 2.5rem;
}

.bento-card {
    display: flex;
    flex-direction: column;
    padding: 1.75rem;
    border-radius: 12px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    text-decoration: none !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
    color: #0a0a0a;
}

.bento-card:hover {
    border-color: #a3a3a3;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

.bento-card h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0a0a0a;
    margin: 0.75rem 0 0.5rem;
}

.bento-card p {
    color: #737373;
    font-size: 0.9rem;
    line-height: 1.6;
    flex: 1;
    margin-bottom: 1.25rem;
}

.inline-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: #f5f5f5;
    color: #525252;
    border: 1px solid #e0e0e0;
}

.card-actions {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    color: #737373;
    font-weight: 600;
    font-size: 0.85rem;
    margin-top: auto;
    transition: color 0.15s ease;
}

.bento-card:hover .card-actions {
    color: #0a0a0a;
}

.note-footer {
    text-align: center;
    color: #a3a3a3;
    font-size: 0.82rem;
    margin-top: 3rem;
}

@media (max-width: 768px) {
    .floating-layer { display: none; }
    .block-container { padding: 1.5rem 1.25rem 3rem; }
}
</style>
"""
}


def _init_theme_state(default: str = "Dark") -> str:
    """Ensure a theme option exists in session state and return it."""
    if "_ui_theme" not in st.session_state:
        st.session_state["_ui_theme"] = default
    return st.session_state["_ui_theme"]


def use_theme(page: Optional[str] = None) -> str:
    """Render the theme selector and apply CSS for the selected theme."""
    current = _init_theme_state("Dark")
    options = ("Dark", "Light")
    index = options.index(current) if current in options else 0

    selected = st.sidebar.radio("Appearance", options, index=index, key="_theme_toggle")
    if selected != st.session_state["_ui_theme"]:
        st.session_state["_ui_theme"] = selected

    active_theme = st.session_state["_ui_theme"]

    # Inject font first, then shared structural CSS, then per-theme tokens
    st.markdown(_FONT_IMPORT, unsafe_allow_html=True)
    st.markdown(_SHARED_CSS, unsafe_allow_html=True)
    st.markdown(BASE_THEME_CSS[active_theme], unsafe_allow_html=True)

    if page == "landing":
        landing_css = LANDING_THEME_CSS.get(active_theme, LANDING_THEME_CSS["Light"])
        st.markdown(landing_css, unsafe_allow_html=True)

    return active_theme
