"""
Custom CSS Styles — Dark Mode Professional UI
"""

def load_css():
    """Load custom CSS for the application (dark mode)"""
    return """
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    /* ── CSS VARIABLES (Dark Palette) ── */
    :root {
        --bg-main:        #0e1117;
        --bg-card:        #1a1f2e;
        --bg-card-hover:  #222840;
        --bg-input:       #1e2436;
        --border:         rgba(255,255,255,0.08);
        --border-focus:   #667eea;
        --text-primary:   #e8eaf6;
        --text-secondary: #9aa0b4;
        --accent:         #667eea;
        --accent2:        #764ba2;
        --success:        #27ae60;
        --warning:        #f39c12;
        --danger:         #e74c3c;
        --info:           #3498db;
        --shadow:         0 4px 24px rgba(0,0,0,0.4);
        --shadow-hover:   0 8px 32px rgba(0,0,0,0.55);
        --radius:         12px;
        --radius-sm:      8px;
    }

    /* ── GLOBAL ── */
    * { font-family: 'Inter', sans-serif; }

    /* Main area background */
    .main, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], section.main {
        background: var(--bg-main) !important;
        color: var(--text-primary) !important;
    }

    /* Block container */
    [data-testid="block-container"] {
        background: transparent !important;
    }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #1a2540 100%) !important;
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] * { color: var(--text-primary) !important; }
    [data-testid="stSidebar"] h3 { color: #a5b4fc !important; }

    /* ── LOGO ── */
    .logo-container {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 2rem;
    }
    .logo-container img { max-width: 180px; filter: brightness(1.15); }

    /* ── KPI CARDS ── */
    .kpi-card {
        background: var(--bg-card);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        border-left: 4px solid;
        border-top: 1px solid var(--border);
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
        background: var(--bg-card-hover);
    }
    .kpi-card.total    { border-left-color: #4a90e2; }
    .kpi-card.overdue  { border-left-color: #e74c3c; }
    .kpi-card.due-soon { border-left-color: #f39c12; }
    .kpi-card.active   { border-left-color: #27ae60; }

    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
        color: var(--text-primary);
    }
    .kpi-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ── BUTTONS ── */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
        color: white !important;
        border: none;
        border-radius: var(--radius-sm);
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(102,126,234,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(102,126,234,0.45);
        filter: brightness(1.1);
    }
    .stButton > button[kind="secondary"] {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        box-shadow: none;
    }
    .stButton > button[kind="secondary"]:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--accent) !important;
    }

    /* ── DOWNLOAD BUTTON ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: #0e1117 !important;
        border: none;
        border-radius: var(--radius-sm);
        padding: 0.6rem 1.5rem;
        font-weight: 700;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(56,239,125,0.25);
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(56,239,125,0.4);
        filter: brightness(1.1);
    }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: var(--bg-card);
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        padding: 6px 6px 0 6px;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
        font-weight: 600;
        color: var(--text-secondary) !important;
        border: none;
        transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--bg-card-hover);
        color: var(--text-primary) !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%) !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--bg-card);
        border-radius: 0 0 var(--radius-sm) var(--radius-sm);
        padding: 1.5rem;
        border: 1px solid var(--border);
        border-top: none;
    }

    /* ── INPUTS ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        transition: border-color 0.2s;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.2) !important;
    }

    /* ── SELECTBOX / MULTISELECT ── */
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background: var(--bg-input) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }

    /* ── DATAFRAME / TABLE ── */
    [data-testid="stDataFrame"] > div,
    .dataframe {
        background: var(--bg-card) !important;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }

    /* ── METRIC ── */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }
    [data-testid="stMetricDelta"] svg { display: none; }

    /* ── ALERT BOXES ── */
    .alert-box {
        padding: 1rem;
        border-radius: var(--radius-sm);
        margin: 1rem 0;
        border-left: 4px solid;
    }
    .alert-box.warning {
        background-color: rgba(243,156,18,0.15);
        border-left-color: var(--warning);
        color: #fde68a;
    }
    .alert-box.danger {
        background-color: rgba(231,76,60,0.15);
        border-left-color: var(--danger);
        color: #fca5a5;
    }
    .alert-box.success {
        background-color: rgba(39,174,96,0.15);
        border-left-color: var(--success);
        color: #86efac;
    }

    /* ── EXPANDER ── */
    .streamlit-expanderHeader,
    [data-testid="stExpander"] summary {
        background: var(--bg-card) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        font-weight: 600;
        border: 1px solid var(--border) !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
    }

    /* ── HEADERS ── */
    h1 { color: var(--text-primary) !important; font-weight: 700; margin-bottom: 1.5rem; }
    h2 { color: var(--text-primary) !important; font-weight: 600; margin-top: 2rem; }
    h3 { color: var(--text-secondary) !important; font-weight: 600; }

    /* ── DIVIDER ── */
    hr { border-color: var(--border) !important; }

    /* ── RADIO / CHECKBOX ── */
    .stRadio > div, .stCheckbox > div {
        color: var(--text-primary) !important;
    }

    /* ── FILE UPLOADER ── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius) !important;
    }

    /* ── PROGRESS BAR ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent) 0%, var(--accent2) 100%);
    }

    /* ── QR CONTAINER ── */
    .qr-container {
        background: var(--bg-card);
        padding: 2rem;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        text-align: center;
        border: 1px solid var(--border);
    }

    /* ── CHART CONTAINER ── */
    .chart-container {
        background: var(--bg-card);
        padding: 1.5rem;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        margin: 1rem 0;
        border: 1px solid var(--border);
    }

    /* ── TOAST / SUCCESS / INFO native ── */
    [data-testid="stAlert"] {
        border-radius: var(--radius-sm) !important;
    }

    /* ── DATA EDITOR ── */
    [data-testid="stDataEditor"] {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border) !important;
        overflow: hidden;
    }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-main); }
    ::-webkit-scrollbar-thumb { background: #3a4060; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent); }

    </style>
    """
