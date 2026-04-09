from typing import Optional

import streamlit as st

# Theme-specific base styles applied across all pages. CSS is appended on
# every rerun so the latest selection overrides the previous theme without
# extra state handling.
BASE_THEME_CSS = {
    "Dark High-Contrast": """
    <style>
    :root {
        color-scheme: dark;
        --primary-bg: #121212;
        --secondary-bg: rgba(18, 18, 18, 0.95);
        --accent: #00ff41;
        --accent-strong: #00e5ff;
        --text-color: #f0f0f0;
        --muted-text: #b0b0b0;
        --border-color: rgba(80, 80, 80, 0.6);
        --card-bg: rgba(28, 28, 28, 0.95);
        --card-border: rgba(80, 80, 80, 0.4);
        --card-shadow: 0 8px 24px rgba(0, 0, 0, 0.8);
        --input-bg: rgba(32, 32, 32, 0.95);
        --input-border: rgba(100, 100, 100, 0.6);
        --chip-bg: rgba(0, 255, 65, 0.15);
        --chip-text: #00ff41;
        --grid-color: rgba(80, 80, 80, 0.3);
        --neon-green: #00ff41;
        --neon-yellow: #ffea00;
        --neon-red: #ff0040;
        --neon-cyan: #00e5ff;
    }

    /* Professional Glassmorphism Dashboard */
    .hero-wrapper {
        position: relative;
        padding: 4rem 0 3rem;
    }
    
    .glass-panel {
        position: relative;
        z-index: 1;
        padding: clamp(2.5rem, 4vw, 3.5rem);
        border-radius: 32px;
        background: rgba(30, 30, 30, 0.7);
        backdrop-filter: blur(24px) saturate(160%);
        -webkit-backdrop-filter: blur(24px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 22px 46px rgba(0, 0, 0, 0.4);
        margin-bottom: 3rem;
        overflow: hidden;
    }
    
    .glass-panel::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
    }

    .hero-eyebrow {
        color: var(--neon-cyan);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
    }

    .hero-title {
        font-size: clamp(2.5rem, 5vw, 4rem);
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #b0b0b0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }

    .hero-lead {
        font-size: 1.25rem;
        line-height: 1.6;
        color: var(--muted-text);
        max-width: 65ch;
        margin-bottom: 2.5rem;
    }

    .hero-metrics {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .metric-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        background: rgba(0, 255, 65, 0.1);
        border: 1px solid rgba(0, 255, 65, 0.2);
        color: var(--neon-green);
        font-size: 0.9rem;
        font-weight: 500;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
    }

    /* Bento Grid */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3rem;
    }

    .bento-card {
        display: block;
        padding: 2rem;
        border-radius: 24px;
        background: rgba(30, 30, 30, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        text-decoration: none !important;
        position: relative;
        overflow: hidden;
    }

    .bento-card:hover {
        transform: translateY(-5px);
        background: rgba(30, 30, 30, 0.8);
        border-color: var(--neon-cyan);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
    }

    .bento-card h3 {
        color: #fff;
        font-size: 1.5rem;
        margin: 1rem 0 0.5rem 0;
        font-weight: 600;
    }

    .bento-card p {
        color: var(--muted-text);
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }

    .inline-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.8);
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .card-actions {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--neon-cyan);
        font-weight: 600;
        font-size: 0.9rem;
    }

    .note-footer {
        text-align: center;
        color: var(--muted-text);
        font-size: 0.85rem;
        margin-top: 4rem;
        opacity: 0.6;
    }

    /* Floating Layers for Atmosphere */
    .floating-layer {
        position: absolute;
        filter: blur(80px);
        z-index: 0;
        opacity: 0.4;
        pointer-events: none;
    }

    .floating-layer.one {
        top: -100px;
        left: -100px;
        width: 400px;
        height: 400px;
        background: var(--neon-green);
        border-radius: 50%;
        opacity: 0.15;
    }

    .floating-layer.two {
        bottom: 0;
        right: -100px;
        width: 300px;
        height: 300px;
        background: var(--neon-cyan);
        border-radius: 50%;
        opacity: 0.15;
    }

    .stApp {
        background: #121212;
        background-image: 
            repeating-linear-gradient(0deg, transparent, transparent 49px, var(--grid-color) 49px, var(--grid-color) 50px),
            repeating-linear-gradient(90deg, transparent, transparent 49px, var(--grid-color) 49px, var(--grid-color) 50px),
            radial-gradient(circle at 15% 25%, rgba(0, 255, 65, 0.08), transparent 40%),
            radial-gradient(circle at 85% 15%, rgba(0, 229, 255, 0.06), transparent 35%);
        color: var(--text-color);
        font-family: "JetBrains Mono", "Roboto Mono", "Fira Code", monospace, "Prompt", sans-serif;
    }

    .block-container {
        max-width: 1200px;
        padding: 2.5rem 3.5rem 4rem;
        color: var(--text-color);
    }

    section[data-testid="stSidebar"] {
        background: rgba(18, 18, 18, 0.98);
        backdrop-filter: blur(8px);
        border-right: 2px solid var(--neon-cyan);
        box-shadow: 2px 0 8px rgba(0, 229, 255, 0.3);
        color: var(--text-color);
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-color) !important;
    }

    div[data-testid="stMarkdown"], label, .stTooltip, .stText, .stNumberInput label {
        color: var(--text-color);
    }

    div[data-testid="stMetricValue"] {
        color: var(--neon-cyan);
        font-weight: 700;
        text-shadow: 0 0 8px rgba(0, 229, 255, 0.5);
    }

    div[data-testid="stMetricDelta"] {
        color: var(--neon-green);
        font-weight: 600;
        text-shadow: 0 0 6px rgba(0, 255, 65, 0.5);
    }

    /* Status Colors - Neon */
    .status-pass {
        color: var(--neon-green) !important;
        text-shadow: 0 0 8px rgba(0, 255, 65, 0.6);
    }

    .status-warning {
        color: var(--neon-yellow) !important;
        text-shadow: 0 0 8px rgba(255, 234, 0, 0.6);
    }

    .status-fail {
        color: var(--neon-red) !important;
        text-shadow: 0 0 8px rgba(255, 0, 64, 0.6);
    }

    div[data-baseweb="input"],
    div[data-baseweb="textarea"],
    div[data-baseweb="select"] > div {
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 0.75rem;
        color: var(--text-color) !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] input {
        color: var(--text-color) !important;
        background-color: var(--input-bg) !important;
    }

    /* Number Input Fields */
    input[type="number"],
    input[type="text"] {
        color: var(--text-color) !important;
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
    }

    /* Streamlit Number Input */
    .stNumberInput input {
        color: var(--text-color) !important;
        background-color: var(--input-bg) !important;
    }

    .stTextInput input {
        color: var(--text-color) !important;
        background-color: var(--input-bg) !important;
    }

    .stSelectbox > div > div {
        color: var(--text-color) !important;
        background-color: var(--input-bg) !important;
    }

    .stButton > button,
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        color: #121212;
        border: 2px solid var(--neon-cyan);
        border-radius: 8px;
        font-weight: 700;
        padding: 0.7rem 1.6rem;
        box-shadow: 0 0 16px rgba(0, 255, 65, 0.4), 0 0 32px rgba(0, 229, 255, 0.2);
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stButton > button:hover,
    button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 0 24px rgba(0, 255, 65, 0.6), 0 0 48px rgba(0, 229, 255, 0.3);
        border-color: var(--neon-green);
    }

    .stButton > button:focus-visible {
        outline: 2px solid rgba(148, 163, 184, 0.45);
        outline-offset: 2px;
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        background: rgba(28, 28, 28, 0.95);
        border-radius: 8px;
        border: 1px solid var(--border-color);
        padding: 0.5rem;
        box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.6);
    }

    table {
        color: var(--text-color);
    }

    .stAlert > div {
        background-color: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(148, 163, 184, 0.35);
        color: var(--text-color);
    }

    .stProgress > div > div {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
    }

    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
        margin: 1.5rem 0;
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.4);
    }

    /* Technical Vector Icons */
    .stMarkdown svg,
    .stImage svg {
        filter: drop-shadow(0 0 4px rgba(0, 255, 65, 0.3));
    }

    /* Input focus states with neon glow */
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within {
        border-color: var(--neon-cyan) !important;
        box-shadow: 0 0 12px rgba(0, 229, 255, 0.5) !important;
    }

    /* Crisp lines for all borders */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    </style>
    """,
    "Light": """
    <style>
    :root {
        color-scheme: light;
        --primary-bg: #f8fafc;
        --secondary-bg: rgba(255, 255, 255, 0.8);
        --accent: #2563eb;
        --accent-strong: #1d4ed8;
        --text-color: #0f172a;
        --muted-text: #475569;
        --border-color: rgba(148, 163, 184, 0.45);
        --card-bg: rgba(255, 255, 255, 0.9);
        --card-border: rgba(148, 163, 184, 0.25);
        --card-shadow: 0 24px 48px rgba(15, 23, 42, 0.12);
        --input-bg: rgba(255, 255, 255, 0.95);
        --input-border: rgba(148, 163, 184, 0.35);
        --chip-bg: rgba(37, 99, 235, 0.15);
        --chip-text: #1e3a8a;
    }

    .stApp {
        background: radial-gradient(circle at 15% 20%, rgba(59, 130, 246, 0.12), transparent 45%),
                    radial-gradient(circle at 85% 15%, rgba(249, 168, 212, 0.16), transparent 50%),
                    linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 45%, #e2e8f0 100%);
        color: var(--text-color);
        font-family: "Prompt", "Sarabun", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .block-container {
        max-width: 1200px;
        padding: 2.5rem 3.5rem 4rem;
        color: var(--text-color);
    }

    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(148, 163, 184, 0.35);
        color: var(--text-color);
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-color) !important;
    }

    div[data-testid="stMarkdown"], label, .stTooltip, .stText, .stNumberInput label {
        color: var(--text-color);
    }

    div[data-testid="stMetricValue"] {
        color: #1d4ed8;
    }

    div[data-testid="stMetricDelta"] {
        color: #15803d;
    }

    div[data-baseweb="input"],
    div[data-baseweb="textarea"],
    div[data-baseweb="select"] > div {
        background-color: var(--input-bg);
        border: 1px solid var(--input-border);
        border-radius: 0.75rem;
        color: var(--text-color);
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] input {
        color: var(--text-color);
    }

    .stButton > button,
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        color: #f8fafc;
        border: none;
        border-radius: 999px;
        font-weight: 600;
        padding: 0.6rem 1.4rem;
        box-shadow: 0 12px 26px rgba(37, 99, 235, 0.22);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }

    .stButton > button:hover,
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 18px 30px rgba(29, 78, 216, 0.28);
    }

    .stButton > button:focus-visible {
        outline: 2px solid rgba(59, 130, 246, 0.35);
        outline-offset: 2px;
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 1rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 0.5rem;
    }

    table {
        color: var(--text-color);
    }

    .stAlert > div {
        background-color: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.35);
        color: var(--text-color);
    }

    .stProgress > div > div {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
    }

    hr {
        border: none;
        height: 1px;
        background: rgba(148, 163, 184, 0.35);
        margin: 1.5rem 0;
    }
    </style>
    """
}


LANDING_THEME_CSS = {
    "Dark": """
    <style>
    .hero-wrapper {
        position: relative;
        padding: 4rem 0 3rem;
    }

    .hero-wrapper::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 36px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.18), rgba(236, 72, 153, 0.12));
        filter: blur(120px);
        z-index: 0;
    }

    .floating-layer {
        position: absolute;
        pointer-events: none;
        border-radius: 32px;
        backdrop-filter: blur(24px) saturate(160%);
        -webkit-backdrop-filter: blur(24px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 24px 48px rgba(15, 23, 42, 0.32);
        opacity: 0.85;
    }

    .floating-layer.one {
        inset-block-start: -60px;
        right: 6%;
        inline-size: 240px;
        height: 240px;
        background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.65), transparent 70%);
    }

    .floating-layer.two {
        inset-block-end: -40px;
        left: 4%;
        inline-size: 180px;
        height: 180px;
        background: radial-gradient(circle at 70% 30%, rgba(148, 163, 184, 0.6), transparent 70%);
    }

    .glass-panel {
        position: relative;
        z-index: 1;
        padding: clamp(2.5rem, 4vw, 3.5rem);
        border-radius: 32px;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(26px) saturate(160%);
        -webkit-backdrop-filter: blur(26px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 24px 48px rgba(15, 23, 42, 0.38);
        color: #e2e8f0;
    }

    .hero-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.3em;
        font-size: 0.75rem;
        font-weight: 600;
        color: #93c5fd;
        margin-bottom: 0.75rem;
    }

    .hero-title {
        font-size: clamp(2.4rem, 5vw, 3.4rem);
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 1rem;
        color: #f8fafc;
    }

    .hero-lead {
        font-size: clamp(1.05rem, 2vw, 1.2rem);
        color: rgba(226, 232, 240, 0.85);
        max-width: 680px;
        margin-bottom: 1.5rem;
    }

    .hero-metrics {
        display: flex;
        gap: clamp(16px, 3vw, 28px);
        flex-wrap: wrap;
        margin-top: 2rem;
    }

    .metric-chip {
        padding: 0.75rem 1.25rem;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.35);
        font-weight: 600;
        color: rgba(226, 232, 240, 0.92);
    }

    .bento-grid {
        position: relative;
        z-index: 1;
        margin-top: clamp(2.5rem, 4vw, 3.5rem);
        display: grid;
        gap: clamp(12px, 2vw, 24px);
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }

    .bento-card {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: clamp(1.8rem, 3vw, 2.4rem);
        border-radius: 28px;
        background: rgba(15, 23, 42, 0.68);
        color: #f8fafc;
        box-shadow: 0 18px 36px rgba(8, 25, 56, 0.36);
        border: 1px solid rgba(255, 255, 255, 0.08);
        position: relative;
        overflow: hidden;
        text-decoration: none;
        transition: transform 0.35s ease, box-shadow 0.35s ease;
    }

    .bento-card::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: inherit;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.18), transparent 65%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .bento-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 28px 60px rgba(15, 23, 42, 0.42);
    }

    .bento-card:hover::after {
        opacity: 1;
    }

    .bento-card h3 {
        font-size: 1.35rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .bento-card p {
        color: rgba(203, 213, 225, 0.88);
        margin-bottom: 0.85rem;
        font-size: 0.98rem;
    }

    .inline-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.22);
        color: rgba(226, 232, 240, 0.95);
        font-size: 0.78rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .card-actions {
        margin-top: auto;
        font-weight: 600;
        color: #bae6fd;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }

    .card-actions span {
        transition: transform 0.3s ease;
    }

    .bento-card:hover .card-actions span {
        transform: translateX(4px);
    }

    .note-footer {
        margin-top: clamp(1.8rem, 3vw, 2.6rem);
        font-size: 0.95rem;
        color: rgba(148, 163, 184, 0.85);
    }

    @media (max-width: 1100px) {
        .floating-layer.one {
            inset-block-start: -40px;
            right: 2%;
            width: 200px;
            height: 200px;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 1.8rem 1.4rem 3rem;
        }

        .hero-wrapper {
            padding: 3rem 0 2rem;
        }

        .hero-metrics {
            gap: 12px;
        }

        .floating-layer.one,
        .floating-layer.two {
            display: none;
        }
    }
    </style>
    """,
    "Light": """
    <style>
    .hero-wrapper {
        position: relative;
        padding: 4rem 0 3rem;
    }

    .hero-wrapper::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 36px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.16), rgba(236, 72, 153, 0.1));
        filter: blur(110px);
        z-index: 0;
    }

    .floating-layer {
        position: absolute;
        pointer-events: none;
        border-radius: 32px;
        backdrop-filter: blur(20px) saturate(160%);
        -webkit-backdrop-filter: blur(20px) saturate(160%);
        border: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: 0 22px 48px rgba(15, 23, 42, 0.18);
        opacity: 0.9;
    }

    .floating-layer.one {
        inset-block-start: -60px;
        right: 6%;
        width: 240px;
        height: 240px;
        background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.85), transparent 70%);
    }

    .floating-layer.two {
        bottom: -40px;
        left: 4%;
        width: 180px;
        height: 180px;
        background: radial-gradient(circle at 70% 30%, rgba(191, 219, 254, 0.75), transparent 72%);
    }

    .glass-panel {
        position: relative;
        z-index: 1;
        padding: clamp(2.5rem, 4vw, 3.5rem);
        border-radius: 32px;
        background: rgba(255, 255, 255, 0.78);
        backdrop-filter: blur(24px) saturate(160%);
        -webkit-backdrop-filter: blur(24px) saturate(160%);
        border: 1px solid rgba(148, 163, 184, 0.28);
        box-shadow: 0 22px 46px rgba(15, 23, 42, 0.18);
        color: #0f172a;
    }

    .hero-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.3em;
        font-size: 0.75rem;
        font-weight: 600;
        color: #2563eb;
        margin-bottom: 0.75rem;
    }

    .hero-title {
        font-size: clamp(2.4rem, 5vw, 3.4rem);
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 1rem;
        color: #0f172a;
    }

    .hero-lead {
        font-size: clamp(1.05rem, 2vw, 1.2rem);
        color: #334155;
        max-width: 680px;
        margin-bottom: 1.5rem;
    }

    .hero-metrics {
        display: flex;
        gap: clamp(16px, 3vw, 28px);
        flex-wrap: wrap;
        margin-top: 2rem;
    }

    .metric-chip {
        padding: 0.75rem 1.25rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.14);
        border: 1px solid rgba(37, 99, 235, 0.28);
        font-weight: 600;
        color: #1f2937;
    }

    .bento-grid {
        position: relative;
        z-index: 1;
        margin-top: clamp(2.5rem, 4vw, 3.5rem);
        display: grid;
        gap: clamp(12px, 2vw, 24px);
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }

    .bento-card {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: clamp(1.8rem, 3vw, 2.4rem);
        border-radius: 28px;
        background: linear-gradient(135deg, rgba(239, 246, 255, 0.95), rgba(224, 242, 254, 0.92));
        color: #1e293b;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
        border: 1px solid rgba(148, 163, 184, 0.22);
        position: relative;
        overflow: hidden;
        text-decoration: none;
        transition: transform 0.35s ease, box-shadow 0.35s ease;
    }

    .bento-card::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: inherit;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.28), transparent 65%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .bento-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 26px 60px rgba(15, 23, 42, 0.24);
    }

    .bento-card:hover::after {
        opacity: 1;
    }

    .bento-card h3 {
        font-size: 1.35rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        color: #1e293b;
    }

    .bento-card p {
        color: #475569;
        margin-bottom: 0.85rem;
        font-size: 0.98rem;
    }

    .inline-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.15);
        color: #1d4ed8;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .card-actions {
        margin-top: auto;
        font-weight: 600;
        color: #2563eb;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }

    .card-actions span {
        transition: transform 0.3s ease;
    }

    .bento-card:hover .card-actions span {
        transform: translateX(4px);
    }

    .note-footer {
        margin-top: clamp(1.8rem, 3vw, 2.6rem);
        font-size: 0.95rem;
        color: #475569;
    }

    @media (max-width: 1100px) {
        .floating-layer.one {
            top: -40px;
            right: 2%;
            width: 200px;
            height: 200px;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 1.8rem 1.4rem 3rem;
        }

        .hero-wrapper {
            padding: 3rem 0 2rem;
        }

        .hero-metrics {
            gap: 12px;
        }

        .floating-layer.one,
        .floating-layer.two {
            display: none;
        }
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
    current = _init_theme_state("Dark High-Contrast")
    options = ("Dark High-Contrast", "Light")
    index = options.index(current) if current in options else 0

    selected = st.sidebar.radio("Appearance", options, index=index, key="_theme_toggle")
    if selected != st.session_state["_ui_theme"]:
        st.session_state["_ui_theme"] = selected

    active_theme = st.session_state["_ui_theme"]
    st.markdown(BASE_THEME_CSS[active_theme], unsafe_allow_html=True)

    if page == "landing":
        st.markdown(LANDING_THEME_CSS.get(active_theme, LANDING_THEME_CSS["Light"]), unsafe_allow_html=True)

    return active_theme
