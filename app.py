"""
╔══════════════════════════════════════════════════════════════════════╗
║                  FINANZZENTRALE — WORLD-CLASS EDITION               ║
║      Senior Full-Stack · Streamlit · Plotly · Private Finance       ║
║            FINANZZENTRALE — PRIVATBANK EDITION                      ║
║      Premium Design · Dark Mode · Glassmorphism · Plotly            ║
╚══════════════════════════════════════════════════════════════════════╝
Modulare Struktur:
  1.  Konfiguration & Design-System
  2.  Hilfsfunktionen (clean_betrag, clean_datum, …)
  3.  Google-Sheets-Anbindung (gspread, Cache)
  4.  Sidebar (Navigation, Zeitraum-Filter)
  5.  Datenaufbereitung (Skalierung, KPI-Berechnung)
  6.  Tab-Renderer:
        TAB 1 – 📊 Gesamtübersicht + KPI-Header
        TAB 2 – 💰 Einnahmen
        TAB 3 – 🏠 Fixkosten
        TAB 4 – 🛒 Variable Ausgaben
        TAB 5 – ⚖️  Saldo-Zeitstrahl & Sankey-Cashflow
        TAB 6 – 📈 Trends
        TAB 7 – 📐 Kennzahlen (Simon / Alisia)
        TAB 8 – 🤝 Lastenverteilung (Unsere Finanzen)
        TAB 9 – 💡 Optimierungspotenzial (alle)
"""

# ──────────────────────────────────────────────────────────────────────
@@ -39,16 +23,37 @@
initial_sidebar_state="expanded",
)

# ── Design-System ─────────────────────────────────────────────────────
# ── Design-System (Premium Dark Palette) ──────────────────────────────
COMPLEMENTARY_COLORS = [
    "#003f5c", "#ff7c43", "#2f4b7c", "#ffa600",
    "#665191", "#f95d6a", "#a05195", "#d45087",
    "#C9A84C",   # Gold
    "#4A90D9",   # Sapphire Blue
    "#7B68EE",   # Slate Purple
    "#50C878",   # Emerald
    "#E87040",   # Copper
    "#9BB8CD",   # Steel Blue
    "#D4AF7A",   # Champagne
    "#6EC6CA",   # Teal
]
COLOR_POSITIVE  = "#28a745"
COLOR_NEGATIVE  = "#dc3545"
COLOR_NEUTRAL   = "#6c757d"
COLOR_ACCENT    = "#003f5c"
COLOR_WARN      = "#ff7c43"
COLOR_POSITIVE  = "#50C878"
COLOR_NEGATIVE  = "#E05252"
COLOR_NEUTRAL   = "#8A9BAE"
COLOR_ACCENT    = "#C9A84C"
COLOR_WARN      = "#E87040"

# Plotly-Theme für alle Charts
PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(family="Georgia, 'Times New Roman', serif", color="#D4C5A0", size=12),
        title=dict(font=dict(color="#C9A84C", size=15, family="Georgia, serif")),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)", tickfont=dict(color="#8A9BAE")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)", tickfont=dict(color="#8A9BAE")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#D4C5A0")),
        colorway=COMPLEMENTARY_COLORS,
        margin=dict(t=50, b=30, l=10, r=10),
    )
)

# ── Deutsches Monats-Mapping ──────────────────────────────────────────
MONATE_DE = {
@@ -65,44 +70,474 @@
}


# ──────────────────────────────────────────────────────────────────────
# PREMIUM CSS INJECTION
# ──────────────────────────────────────────────────────────────────────
def inject_premium_css():
    st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=Jost:wght@300;400;500&display=swap');

/* ── Root Variables ── */
:root {
    --bg-primary:       #0D0F14;
    --bg-secondary:     #13161E;
    --bg-card:          rgba(255,255,255,0.04);
    --bg-card-hover:    rgba(255,255,255,0.07);
    --border-subtle:    rgba(201,168,76,0.15);
    --border-strong:    rgba(201,168,76,0.35);
    --gold:             #C9A84C;
    --gold-light:       #E8D4A0;
    --text-primary:     #E8E0D0;
    --text-secondary:   #8A9BAE;
    --text-muted:       #5A6A7A;
    --positive:         #50C878;
    --negative:         #E05252;
    --shadow-card:      0 4px 24px rgba(0,0,0,0.4), 0 1px 4px rgba(201,168,76,0.08);
    --shadow-elevated:  0 8px 40px rgba(0,0,0,0.6), 0 2px 8px rgba(201,168,76,0.12);
    --radius-card:      12px;
    --radius-sm:        8px;
    --font-display:     'Cormorant Garamond', Georgia, serif;
    --font-body:        'Jost', 'Helvetica Neue', sans-serif;
}

/* ── Global App Background ── */
.stApp {
    background: linear-gradient(160deg, #0D0F14 0%, #111420 50%, #0E1118 100%) !important;
    font-family: var(--font-body) !important;
}

/* ── Main content area ── */
.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1600px !important;
}

/* ── Sidebar — Glassmorphism + Geometric Pattern ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,
        rgba(15,18,26,0.98) 0%,
        rgba(13,15,20,0.99) 60%,
        rgba(11,13,18,1.0) 100%
    ) !important;
    border-right: 1px solid var(--border-subtle) !important;
    position: relative;
    overflow: hidden;
}

[data-testid="stSidebar"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(var(--border-subtle) 1px, transparent 1px),
        linear-gradient(90deg, var(--border-subtle) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
    opacity: 0.5;
}

[data-testid="stSidebar"]::after {
    content: "";
    position: absolute;
    top: -200px; right: -200px;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(201,168,76,0.06) 0%, transparent 65%);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stSidebar"] > div:first-child {
    position: relative;
    z-index: 1;
}

[data-testid="stSidebar"] .stImage img {
    border-radius: var(--radius-card) !important;
    border: 1px solid var(--border-subtle) !important;
}

/* ── Sidebar Header Text ── */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: var(--font-display) !important;
    color: var(--gold) !important;
    letter-spacing: 0.04em !important;
    font-weight: 500 !important;
}

/* ── Sidebar Buttons ── */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(201,168,76,0.2) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
    font-weight: 300 !important;
    letter-spacing: 0.06em !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(201,168,76,0.1) !important;
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
    transform: translateX(3px) !important;
    box-shadow: 0 0 20px rgba(201,168,76,0.1) !important;
}

/* ── Selectbox ── */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    font-size: 0.83rem !important;
}

/* ── Main Title ── */
h1 {
    font-family: var(--font-display) !important;
    font-size: 2.4rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    letter-spacing: 0.03em !important;
    line-height: 1.2 !important;
}
h1::after {
    content: "";
    display: block;
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent);
    margin-top: 0.4rem;
}

h2, h3 {
    font-family: var(--font-display) !important;
    color: var(--text-primary) !important;
    font-weight: 400 !important;
    letter-spacing: 0.02em !important;
}

h4 {
    font-family: var(--font-body) !important;
    color: var(--text-secondary) !important;
    font-weight: 400 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-size: 0.78rem !important;
}

/* ── KPI / Metric Cards ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    padding: 1.1rem 1.3rem !important;
    box-shadow: var(--shadow-card) !important;
    transition: all 0.3s ease !important;
    position: relative;
    overflow: hidden;
}
[data-testid="stMetric"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent 70%);
}
[data-testid="stMetric"]:hover {
    background: var(--bg-card-hover) !important;
    border-color: var(--border-strong) !important;
    box-shadow: var(--shadow-elevated) !important;
    transform: translateY(-2px) !important;
}

[data-testid="stMetricLabel"] {
    font-family: var(--font-body) !important;
    font-size: 0.7rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
}

[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-size: 1.65rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    letter-spacing: 0.01em !important;
    line-height: 1.2 !important;
}

[data-testid="stMetricDelta"] {
    font-family: var(--font-body) !important;
    font-size: 0.75rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.04em !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.02) !important;
    border-bottom: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    padding: 0 0.5rem !important;
    gap: 0 !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: var(--font-body) !important;
    font-size: 0.78rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1.1rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--gold) !important;
    background: rgba(201,168,76,0.05) !important;
}

.stTabs [aria-selected="true"] {
    color: var(--gold) !important;
    background: rgba(201,168,76,0.08) !important;
    border-bottom: 2px solid var(--gold) !important;
}

.stTabs [data-baseweb="tab-panel"] {
    background: rgba(255,255,255,0.01) !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-card) var(--radius-card) !important;
    padding: 1.5rem !important;
}

/* ── Dividers ── */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--border-subtle), transparent) !important;
    margin: 1.5rem 0 !important;
}

/* ── DataFrames / Tables ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
    background: rgba(201,168,76,0.08) !important;
    color: var(--gold) !important;
    font-family: var(--font-body) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
}
[data-testid="stDataFrame"] td {
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
    font-size: 0.82rem !important;
    background: rgba(255,255,255,0.01) !important;
}
[data-testid="stDataFrame"] tr:hover td {
    background: rgba(201,168,76,0.05) !important;
}

/* ── Plotly Charts Container ── */
[data-testid="stPlotlyChart"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-card) !important;
    padding: 0.3rem !important;
    background: rgba(255,255,255,0.02) !important;
    box-shadow: var(--shadow-card) !important;
}

/* ── Info / Success / Warning / Error boxes ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border-left-width: 3px !important;
    font-family: var(--font-body) !important;
    font-size: 0.83rem !important;
}

.stSuccess {
    background: rgba(80,200,120,0.08) !important;
    border-left-color: var(--positive) !important;
    color: var(--positive) !important;
}
.stInfo {
    background: rgba(74,144,217,0.08) !important;
    border-left-color: #4A90D9 !important;
}
.stWarning {
    background: rgba(232,112,64,0.08) !important;
    border-left-color: var(--negative) !important;
}
.stError {
    background: rgba(224,82,82,0.1) !important;
    border-left-color: var(--negative) !important;
}

/* ── Sliders ── */
[data-testid="stSlider"] > div > div > div {
    color: var(--gold) !important;
}
[data-testid="stSlider"] .stSlider > div {
    background: rgba(201,168,76,0.2) !important;
}

/* ── Multiselect ── */
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(201,168,76,0.15) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--gold-light) !important;
    font-family: var(--font-body) !important;
    font-size: 0.75rem !important;
    border-radius: 4px !important;
}

/* ── Subheader special styling ── */
.stSubheader, [data-testid="stMarkdown"] h3 {
    font-family: var(--font-display) !important;
    color: var(--text-primary) !important;
    padding-bottom: 0.3rem !important;
    border-bottom: 1px solid var(--border-subtle) !important;
    margin-bottom: 1rem !important;
}

/* ── Caption / small text ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.05em !important;
    font-family: var(--font-body) !important;
}

/* ── Number Input ── */
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-display) !important;
    font-size: 1rem !important;
}

/* ── Sidebar info/success boxes ── */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    font-size: 0.75rem !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Scrollbar styling ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: rgba(201,168,76,0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(201,168,76,0.45); }

/* ── Custom KPI card section header ── */
.kpi-section-label {
    font-family: var(--font-body);
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.7rem;
    padding-left: 2px;
}

/* ── Gold accent rule for sections ── */
.gold-rule {
    height: 1px;
    background: linear-gradient(90deg, var(--gold) 0%, rgba(201,168,76,0.1) 50%, transparent 100%);
    margin: 1.5rem 0;
    border: none;
}

/* ── Sidebar "active mode" pill ── */
.mode-pill {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 500;
    border: 1px solid var(--gold);
    color: var(--gold);
    background: rgba(201,168,76,0.07);
    margin-top: 0.3rem;
}

/* ── Logo / brand mark in sidebar ── */
.sidebar-brand {
    font-family: var(--font-display);
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--gold);
    letter-spacing: 0.1em;
    text-align: center;
    padding: 1rem 0 0.5rem 0;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1rem;
}
.sidebar-brand span {
    display: block;
    font-size: 0.62rem;
    letter-spacing: 0.25em;
    color: var(--text-muted);
    font-family: var(--font-body);
    font-weight: 300;
    text-transform: uppercase;
    margin-top: 0.15rem;
}
</style>
""", unsafe_allow_html=True)

inject_premium_css()


# ──────────────────────────────────────────────────────────────────────
# 2. HILFSFUNKTIONEN
# ──────────────────────────────────────────────────────────────────────

def clean_betrag(series: pd.Series) -> pd.Series:
    """
    Wandelt Betragsstrings aus Google Sheets zuverlässig in float um.
    Unterstützt: Buchhaltungsformat (1.234,56), Währung (1.234,56 €),
    englisches Format (1234.56) und Klammernotation (1.234,56).
    """
s = series.astype(str).str.strip()
s = s.str.replace("€", "", regex=False).str.strip()

    # Buchhaltungsformat: (1.234,56) → negativ
is_acc = s.str.startswith("(") & s.str.endswith(")")
s[is_acc] = "-" + s[is_acc].str[1:-1]

s = s.str.replace(" ", "", regex=False)
has_dot   = s.str.contains(r"\.", regex=True)
has_comma = s.str.contains(r",", regex=True)
result    = s.copy()

    # Deutsches Format: Punkt=Tausender, Komma=Dezimal
mask_de = has_dot & has_comma
result[mask_de] = (
s[mask_de].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
)
    # Nur Komma → Dezimalzeichen
mask_c = ~has_dot & has_comma
result[mask_c] = s[mask_c].str.replace(",", ".", regex=False)

return pd.to_numeric(result, errors="coerce").fillna(0.0)


def clean_datum(series: pd.Series) -> pd.Series:
    """
    Parst Datums-Strings aus Google Sheets (TT.MM.JJJJ priorisiert).
    """
result   = pd.to_datetime(series, format="%d.%m.%Y", errors="coerce")
mask_nat = result.isna()
if mask_nat.any():
@@ -113,37 +548,65 @@ def clean_datum(series: pd.Series) -> pd.Series:


def datum_zu_monat(x) -> str | None:
    """Datum → 'Monat Jahr'-String (NaT-sicher)."""
try:
return f"{MONATE_DE[x.strftime('%m')]} {x.year}"
except Exception:
return None


def hex_to_rgba(hex_val: str, opacity: float) -> str:
    """Konvertiert Hex-Farbe in rgba-String für Plotly-Links."""
h = hex_val.lstrip("#")
r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
return f"rgba({r},{g},{b},{opacity})"


def fmt_eur(val: float) -> str:
    """Formatiert einen Betrag als Euro-String."""
return f"{val:,.2f} €"


def delta_str(val: float) -> str:
    """Hilfsfunktion für st.metric delta (mit Vorzeichen)."""
return f"{val:+,.2f} €"


def apply_chart_theme(fig, height=None):
    """Applies the premium dark theme to any Plotly figure."""
    updates = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.025)",
        font=dict(family="Georgia, 'Times New Roman', serif", color="#D4C5A0", size=11),
        title=dict(font=dict(color="#C9A84C", size=14, family="Georgia, serif")),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#8A9BAE", size=10),
            zerolinecolor="rgba(255,255,255,0.1)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#8A9BAE", size=10),
            zerolinecolor="rgba(255,255,255,0.1)",
        ),
        legend=dict(
            bgcolor="rgba(13,15,20,0.85)",
            bordercolor="rgba(201,168,76,0.2)",
            borderwidth=1,
            font=dict(color="#D4C5A0", size=10),
        ),
        margin=dict(t=55, b=30, l=10, r=10),
    )
    if height:
        updates["height"] = height
    fig.update_layout(**updates)
    return fig


# ──────────────────────────────────────────────────────────────────────
# 3. GOOGLE SHEETS — VERBINDUNG & DATENLADEN
# ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_gspread_client():
    """Erstellt einen gspread-Client aus den Streamlit-Secrets."""
scopes = [
"https://www.googleapis.com/auth/spreadsheets.readonly",
"https://www.googleapis.com/auth/drive.readonly",
@@ -154,41 +617,29 @@ def get_gspread_client():


def sheet_to_df(worksheet) -> pd.DataFrame:
    """
    Liest ein Worksheet als rohe Strings (get_all_values) und gibt einen
    bereinigten DataFrame zurück. Vermeidet Typkonflikte bei Buchhaltungs-
    und Datumsformaten.
    """
all_values = worksheet.get_all_values()
if not all_values or len(all_values) < 2:
return pd.DataFrame()
headers = all_values[0]
rows    = all_values[1:]
df = pd.DataFrame(rows, columns=headers)
    # Leere Zeilen entfernen
df = df[df.apply(lambda r: r.str.strip().any(), axis=1)].reset_index(drop=True)
return df


@st.cache_data(ttl=600)
def load_data(sheet_id: str) -> tuple:
    """
    Lädt alle vier Worksheets, bereinigt Beträge und parst Daten.
    Rückgabe: (df_ausgaben, df_fixkosten, df_fix_einnahmen, df_einnahmen)
    """
client      = get_gspread_client()
spreadsheet = client.open_by_key(sheet_id)

    ausgaben     = sheet_to_df(spreadsheet.worksheet("Ausgaben"))
    fixkosten    = sheet_to_df(spreadsheet.worksheet("Fixkosten"))
    ausgaben      = sheet_to_df(spreadsheet.worksheet("Ausgaben"))
    fixkosten     = sheet_to_df(spreadsheet.worksheet("Fixkosten"))
fix_einnahmen = sheet_to_df(spreadsheet.worksheet("Fix_Einnahmen"))
    einnahmen    = sheet_to_df(spreadsheet.worksheet("Einnahmen"))
    einnahmen     = sheet_to_df(spreadsheet.worksheet("Einnahmen"))

    # Beträge bereinigen
for df in [ausgaben, fixkosten, fix_einnahmen, einnahmen]:
df["Betrag"] = clean_betrag(df["Betrag"]) if "Betrag" in df.columns else 0.0

    # Datum parsen
for df in [ausgaben, einnahmen]:
if "Datum" in df.columns:
df["Datum"] = clean_datum(df["Datum"])
@@ -201,11 +652,18 @@ def load_data(sheet_id: str) -> tuple:
# ──────────────────────────────────────────────────────────────────────

with st.sidebar:
    # ── Dashboard-Bild ─────────────────────────────────────────────
    # Brand header
    st.markdown("""
    <div class="sidebar-brand">
        FINANZZENTRALE
        <span>Private Wealth Management</span>
    </div>
    """, unsafe_allow_html=True)

if os.path.exists("Bild Dashboard.PNG"):
st.image("Bild Dashboard.PNG", use_container_width=True)

    st.header("👤 Dashboard wählen")
    st.markdown('<p class="kpi-section-label">Dashboard Auswahl</p>', unsafe_allow_html=True)

if "mode" not in st.session_state:
st.session_state.mode = "unser"
@@ -223,16 +681,16 @@ def load_data(sheet_id: str) -> tuple:
SHEET_ID = SHEET_IDS[mode]

if mode == "unser":
        st.success("✅ Unsere Finanzen")
        st.success("✅ Unsere Finanzen aktiv")
dashboard_title = "🚀 Unsere Finanzzentrale"
elif mode == "simon":
        st.info("✅ Simons Finanzen")
        st.info("✅ Simons Finanzen aktiv")
dashboard_title = "👤 Simons Finanzzentrale"
else:
        st.info("✅ Alisias Finanzen")
        st.info("✅ Alisias Finanzen aktiv")
dashboard_title = "👤 Alisias Finanzzentrale"

    st.divider()
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

# ── Daten laden ───────────────────────────────────────────────────────
st.title(dashboard_title)
@@ -267,8 +725,8 @@ def _sort_key(label):

# ── Zeitraum-Selektor in der Sidebar ─────────────────────────────────
with st.sidebar:
    st.header("🔍 Globaler Zeitfilter")
    selected_label = st.selectbox("Zeitraum wählen", month_options)
    st.markdown('<p class="kpi-section-label">Zeitraum-Filter</p>', unsafe_allow_html=True)
    selected_label = st.selectbox("Zeitraum wählen", month_options, label_visibility="collapsed")

# ── Filter anwenden ───────────────────────────────────────────────────
if selected_label == "Gesamter Zeitraum":
@@ -304,33 +762,30 @@ def _sort_key(label):
filtered_einnahmen = df_einnahmen[df_einnahmen["Monat_Jahr"] == tech_val].copy()

with st.sidebar:
    st.divider()
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
if selected_label == "Gesamter Zeitraum":
        st.info(f"📅 Gesamter Zeitraum ({num_months} Monat/e)")
        st.info(f"📅 Gesamter Zeitraum · {num_months} Monat/e")
elif selected_label != "Benutzerdefinierter Zeitraum":
        st.info(f"📅 Aktiver Monat: {selected_label}")
        st.info(f"📅 {selected_label}")
st.caption("⚡ Daten werden alle 10 Min. aktualisiert.")


# ──────────────────────────────────────────────────────────────────────
# 5. ZENTRALE KENNZAHLEN-BERECHNUNG
# ──────────────────────────────────────────────────────────────────────

# ── Skalierte Summen ──────────────────────────────────────────────────
fix_monat_summe       = df_fixkosten["Betrag"].sum() if not df_fixkosten.empty else 0.0
fix_summe_scaled      = fix_monat_summe * num_months
einn_fix_monat        = df_fix_einnahmen["Betrag"].sum() if not df_fix_einnahmen.empty else 0.0
einn_fix_summe_scaled = einn_fix_monat * num_months

# ── Gesamteinnahmen & -ausgaben ───────────────────────────────────────
var_ausgaben_summe = filtered_ausgaben["Betrag"].sum() if not filtered_ausgaben.empty else 0.0
var_ausgaben_summe  = filtered_ausgaben["Betrag"].sum() if not filtered_ausgaben.empty else 0.0
var_einnahmen_summe = filtered_einnahmen["Betrag"].sum() if not filtered_einnahmen.empty else 0.0

gesamt_einnahmen = var_einnahmen_summe + einn_fix_summe_scaled
gesamt_ausgaben  = var_ausgaben_summe  + fix_summe_scaled
saldo            = gesamt_einnahmen - gesamt_ausgaben

# ── Sparbetrag (Fix + Variabel) ───────────────────────────────────────
spar_fix = (
df_fixkosten[df_fixkosten["Unterkategorie"] == "Sparen"]["Betrag"].sum() * num_months
if not df_fixkosten.empty else 0.0
@@ -342,10 +797,6 @@ def _sort_key(label):
gesamt_spar = spar_fix + spar_var
sparquote   = (gesamt_spar / gesamt_einnahmen * 100) if gesamt_einnahmen > 0 else 0.0

# ── 50/30/20-Regel ────────────────────────────────────────────────────
# Fixkosten (ohne Sparen) → "50"-Bucket
# Variable Ausgaben (ohne Sparen) → "30"-Bucket (Wünsche/variabel)
# Sparen → "20"-Bucket
fix_ohne_spar = (
df_fixkosten[df_fixkosten["Unterkategorie"] != "Sparen"]["Betrag"].sum() * num_months
if not df_fixkosten.empty else 0.0
@@ -357,21 +808,12 @@ def _sort_key(label):
fix_quote = (fix_ohne_spar / gesamt_einnahmen * 100) if gesamt_einnahmen > 0 else 0.0
var_quote = (var_ohne_spar / gesamt_einnahmen * 100) if gesamt_einnahmen > 0 else 0.0

# ── Burn-Rate (Monate bis Ersparnis aufgebraucht, falls Einnahmen wegfallen) ──
# Ersparnisse = Sparbetrag im Zeitraum (als Proxy für akkumuliertes Vermögen
# falls keine Bestandsdaten vorhanden – kann bei Bedarf durch echte Daten ersetzt werden)
burn_rate_monate = (gesamt_spar / (gesamt_ausgaben / num_months)) if gesamt_ausgaben > 0 else 0.0

# ── Vormonat-Delta (für st.metric) ───────────────────────────────────
def _get_vormonat_daten(df: pd.DataFrame, target_monat: str | None) -> float:
    """
    Gibt die Betrag-Summe für den Vormonat zurück.
    target_monat: 'MM-YYYY' oder None (bei Gesamtzeitraum → letzter Monat - 1)
    """
if df.empty or "Monat_Jahr" not in df.columns:
return 0.0
if target_monat is None:
        # Letzter verfügbarer Monat
months = sorted(df["Monat_Jahr"].dropna().unique())
target_monat = months[-1] if months else None
if not target_monat:
@@ -384,7 +826,6 @@ def _get_vormonat_daten(df: pd.DataFrame, target_monat: str | None) -> float:
except Exception:
return 0.0

# Aktueller und Vormonats-Wert für Ausgaben (skaliert auf 1 Monat für Vergleich)
cur_monat_ausgaben  = var_ausgaben_summe / num_months if num_months > 1 else var_ausgaben_summe
prev_monat_ausgaben = _get_vormonat_daten(
df_ausgaben,
@@ -404,7 +845,8 @@ def _get_vormonat_daten(df: pd.DataFrame, target_monat: str | None) -> float:
# 6. KPI-HEADER (immer sichtbar, über den Tabs)
# ──────────────────────────────────────────────────────────────────────

st.divider()
st.markdown('<p class="kpi-section-label">Schlüsselkennzahlen — Ausgewählter Zeitraum</p>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
"💰 Gesamteinnahmen",
@@ -416,7 +858,7 @@ def _get_vormonat_daten(df: pd.DataFrame, target_monat: str | None) -> float:
"💸 Gesamtausgaben",
fmt_eur(gesamt_ausgaben),
delta_str(delta_ausgaben),
    delta_color="inverse",   # Anstieg = rot (schlechter)
    delta_color="inverse",
)
c3.metric(
"📈 Saldo",
@@ -434,7 +876,8 @@ def _get_vormonat_daten(df: pd.DataFrame, target_monat: str | None) -> float:
help="Wie viele Monate reichen die Ersparnisse im gewählten Zeitraum, falls alle Einnahmen wegfallen?",
delta_color="off",
)
st.divider()

st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
@@ -457,7 +900,6 @@ def _get_vormonat_daten(df: pd.DataFrame, target_monat: str | None) -> float:

tabs = st.tabs(tab_titles)

# Hilfsfunktion: Tab-Index sicher bestimmen
def tab_idx(name: str) -> int:
return tab_titles.index(name)

@@ -481,12 +923,9 @@ def tab_idx(name: str) -> int:
st.subheader(f"Gesamtausgaben im Zeitraum: {fmt_eur(gesamt_gesamt)}")

# ── 50/30/20-Analyse ─────────────────────────────────────────────
    st.write("#### 🎯 50/30/20-Regelanalyse")
    st.markdown('<p class="kpi-section-label">50 / 30 / 20 — Regelanalyse</p>', unsafe_allow_html=True)
r1, r2, r3 = st.columns(3)

    def _rule_color(actual, target):
        return COLOR_POSITIVE if actual <= target else COLOR_NEGATIVE

with r1:
st.metric(
"🏠 Fixkosten (Soll ≤ 50 %)",
@@ -522,34 +961,37 @@ def _rule_color(actual, target):
fig_rule.add_trace(go.Bar(
x=categories, y=actual_vals,
marker_color=bar_colors,
        marker_line=dict(color="rgba(255,255,255,0.1)", width=1),
name="Ist",
text=[f"{v:.1f} %" for v in actual_vals],
textposition="outside",
        textfont=dict(color="#D4C5A0"),
))
fig_rule.add_trace(go.Scatter(
x=categories, y=target_vals,
mode="markers+text",
        marker=dict(size=14, color=COLOR_ACCENT, symbol="diamond"),
        marker=dict(size=14, color=COLOR_ACCENT, symbol="diamond",
                    line=dict(color="rgba(255,255,255,0.3)", width=1)),
text=[f"Ziel: {v} %" for v in target_vals],
textposition="top center",
        textfont=dict(color=COLOR_ACCENT),
name="Zielwert",
))
    apply_chart_theme(fig_rule)
fig_rule.update_layout(
        title="50/30/20-Regelanalyse (Ist vs. Ziel)",
        title="50/30/20-Regelanalyse — Ist vs. Ziel",
yaxis_title="Anteil am Einkommen (%)",
yaxis_range=[0, max(max(actual_vals), 55)],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
legend=dict(orientation="h"),
)
st.plotly_chart(fig_rule, use_container_width=True)

    st.divider()
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

# ── Sunburst + Tabelle ────────────────────────────────────────────
col_l, col_r = st.columns([1.5, 1])
with col_r:
        st.write("**🔎 Tabellenfilter**")
        st.markdown('<p class="kpi-section-label">Tabellenfilter</p>', unsafe_allow_html=True)
if not df_all.empty:
f_kat = st.multiselect(
"Kategorie",
@@ -583,11 +1025,12 @@ def _rule_color(actual, target):
title="Ausgabenstruktur (Fix + Variabel)",
)
fig_sun.update_traces(textinfo="label+percent entry")
            apply_chart_theme(fig_sun, height=600)
st.plotly_chart(fig_sun, use_container_width=True)

# ── Fix vs. Variabel Donut ────────────────────────────────────────
    st.divider()
    st.write("#### 📐 Fixe vs. Variable Kostenstruktur")
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
    st.markdown('<p class="kpi-section-label">Fixe vs. Variable Kostenstruktur</p>', unsafe_allow_html=True)
ratio_col1, ratio_col2 = st.columns(2)
with ratio_col1:
fig_ratio = go.Figure(go.Pie(
@@ -596,14 +1039,17 @@ def _rule_color(actual, target):
hole=0.55,
marker_colors=[COMPLEMENTARY_COLORS[0], COMPLEMENTARY_COLORS[1], COLOR_POSITIVE],
textinfo="label+percent",
            textfont=dict(color="#D4C5A0"),
))
fig_ratio.update_layout(
title="Ausgabenstruktur Donut",
            annotations=[dict(text=fmt_eur(gesamt_ausgaben), x=0.5, y=0.5, showarrow=False, font_size=14)],
            annotations=[dict(text=fmt_eur(gesamt_ausgaben), x=0.5, y=0.5, showarrow=False,
                              font_size=13, font_color="#C9A84C", font_family="Georgia, serif")],
)
        apply_chart_theme(fig_ratio)
st.plotly_chart(fig_ratio, use_container_width=True)
with ratio_col2:
        st.write("**Interpretation**")
        st.markdown('<p class="kpi-section-label">Interpretation</p>', unsafe_allow_html=True)
st.markdown(f"""
| Kennzahl | Wert | Bewertung |
|----------|------|-----------|
@@ -632,7 +1078,7 @@ def _rule_color(actual, target):

col1, col2 = st.columns([1.5, 1])
with col2:
        st.write("**Einnahmenübersicht (monatlich)**")
        st.markdown('<p class="kpi-section-label">Einnahmenübersicht (monatlich)</p>', unsafe_allow_html=True)
if not df_fix_einnahmen.empty:
f_pers = st.multiselect(
"Person auswählen",
@@ -654,13 +1100,14 @@ def _rule_color(actual, target):
height=500,
color_discrete_sequence=COMPLEMENTARY_COLORS,
)
            fig_einn.update_traces(textinfo="label+percent+value")
            fig_einn.update_traces(textinfo="label+percent+value",
                                    textfont=dict(color="#D4C5A0"))
            apply_chart_theme(fig_einn, height=500)
st.plotly_chart(fig_einn, use_container_width=True)

    # Variable Einnahmen (falls vorhanden)
if not filtered_einnahmen.empty:
        st.divider()
        st.write("#### 📋 Variable Einnahmen im Zeitraum")
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        st.markdown('<p class="kpi-section-label">Variable Einnahmen im Zeitraum</p>', unsafe_allow_html=True)
disp = filtered_einnahmen.copy()
if "Datum" in disp.columns:
disp["Datum"] = disp["Datum"].dt.strftime("%d.%m.%Y")
@@ -671,7 +1118,7 @@ def _rule_color(actual, target):
# TAB 3 – 🏠 FIXKOSTEN
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("🏠 Fixkosten")]:
    fix_monat_summe_disp  = df_fixkosten["Betrag"].sum() if not df_fixkosten.empty else 0.0
    fix_monat_summe_disp    = df_fixkosten["Betrag"].sum() if not df_fixkosten.empty else 0.0
fix_zeitraum_summe_disp = fix_monat_summe_disp * num_months

hdr = (
@@ -694,9 +1141,10 @@ def _rule_color(actual, target):
color_discrete_sequence=COMPLEMENTARY_COLORS,
)
fig_fix.update_traces(textinfo="label+percent entry")
            apply_chart_theme(fig_fix, height=600)
st.plotly_chart(fig_fix, use_container_width=True)
with col2:
        st.write("**Fixkosten Tabelle (monatlich)**")
        st.markdown('<p class="kpi-section-label">Fixkosten Tabelle (monatlich)</p>', unsafe_allow_html=True)
if not df_fixkosten.empty:
f_kat_fix = st.multiselect(
"Kategorie", sorted(df_fixkosten["Kategorie"].dropna().unique()), key="filter_fix_kat"
@@ -710,17 +1158,18 @@ def _rule_color(actual, target):
st.data_editor(df_ft, hide_index=True, use_container_width=True, key=f"fix_f_{mode}")
st.info(f"**Monatliche Fixkosten: {fmt_eur(df_ft['Betrag'].sum())}**")

    # Horizontales Balkendiagramm für Fixkosten-Kategorien
if not df_fixkosten.empty:
        st.divider()
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
df_fix_bar = df_fixkosten.groupby("Kategorie")["Betrag"].sum().reset_index().sort_values("Betrag")
fig_fix_bar = px.bar(
df_fix_bar, x="Betrag", y="Kategorie", orientation="h",
color="Kategorie", color_discrete_sequence=COMPLEMENTARY_COLORS,
title="Fixkosten nach Kategorie (monatlich)",
text_auto=".2f",
)
        fig_fix_bar.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
        fig_fix_bar.update_traces(textfont=dict(color="#D4C5A0"))
        fig_fix_bar.update_layout(showlegend=False)
        apply_chart_theme(fig_fix_bar)
st.plotly_chart(fig_fix_bar, use_container_width=True)


@@ -734,7 +1183,6 @@ def _rule_color(actual, target):
if not filtered_ausgaben.empty:
col1, col2 = st.columns([1.5, 1])
with col1:
            # Kategorie-Filter für Chart
f_kat_var_c = st.multiselect(
"Kategorien (Chart-Filter)",
sorted(filtered_ausgaben["Kategorie"].dropna().unique()),
@@ -753,10 +1201,11 @@ def _rule_color(actual, target):
color_discrete_sequence=COMPLEMENTARY_COLORS,
)
fig_var_sun.update_traces(textinfo="label+percent entry")
            apply_chart_theme(fig_var_sun, height=550)
st.plotly_chart(fig_var_sun, use_container_width=True)

with col2:
            st.write("**📋 Einzelbuchungen**")
            st.markdown('<p class="kpi-section-label">Einzelbuchungen</p>', unsafe_allow_html=True)
f_kat_var = st.multiselect(
"Kategorie",
sorted(filtered_ausgaben["Kategorie"].dropna().unique()),
@@ -786,7 +1235,7 @@ def _rule_color(actual, target):
# TAB 5 – ⚖️ SALDO-ZEITSTRAHL & SANKEY-CASHFLOW
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("⚖️ Saldo & Cashflow")]:
    st.subheader("📅 Monatlicher Saldo-Zeitstrahl")
    st.subheader("Monatlicher Saldo-Zeitstrahl")

if not df_ausgaben.empty or not df_einnahmen.empty:
df_v, df_e = df_ausgaben.copy(), df_einnahmen.copy()
@@ -820,16 +1269,18 @@ def _rule_color(actual, target):
if zeitstrahl:
df_zs = pd.DataFrame(zeitstrahl).sort_values("Sort")

            # Saldo-Bar
fig_zs = px.bar(
df_zs, x="Monat", y="Saldo", text_auto=".2f",
                color="Saldo", color_continuous_scale="RdYlGn",
                title="Monatliches Saldo (Einnahmen − Ausgaben)",
                color="Saldo", color_continuous_scale=[
                    [0.0, "#E05252"], [0.45, "#E87040"],
                    [0.55, "#C9A84C"], [1.0, "#50C878"]
                ],
                title="Monatliches Saldo — Einnahmen − Ausgaben",
)
            fig_zs.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            fig_zs.update_traces(textfont=dict(color="#D4C5A0"))
            apply_chart_theme(fig_zs)
st.plotly_chart(fig_zs, use_container_width=True)

            # Einnahmen vs. Ausgaben Linie
df_zs_long = df_zs.melt(
id_vars=["Monat", "Sort"],
value_vars=["Einnahmen", "Ausgaben"],
@@ -840,12 +1291,13 @@ def _rule_color(actual, target):
markers=True, title="Einnahmen vs. Ausgaben im Zeitverlauf",
color_discrete_map={"Einnahmen": COLOR_POSITIVE, "Ausgaben": COLOR_NEGATIVE},
)
            fig_ev.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            fig_ev.update_traces(line=dict(width=2.5), marker=dict(size=8))
            apply_chart_theme(fig_ev)
st.plotly_chart(fig_ev, use_container_width=True)

# ── SANKEY-DIAGRAMM ───────────────────────────────────────────────
    st.divider()
    st.write("### 🌊 Cashflow-Sankey-Diagramm")
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
    st.markdown('<p class="kpi-section-label">Cashflow-Sankey-Diagramm</p>', unsafe_allow_html=True)

total_einn_fix = (
(df_fix_einnahmen.groupby("Person")["Betrag"].sum() * num_months).reset_index()
@@ -864,38 +1316,34 @@ def _rule_color(actual, target):
])

if (not total_einn_fix.empty or not total_einn_var.empty) and not df_ausg_all.empty:
        # Einnahmenquellen (Personen)
einn_personen = sorted(
set(total_einn_fix["Person"].tolist()) | set(total_einn_var["Person"].tolist())
)
label_list = list(einn_personen) + ["🏦 Budget (Gesamt)"]
budget_idx = len(einn_personen)
source, target, value, color_link, link_labels = [], [], [], [], []

        # Einnahmen → Budget
for i, p in enumerate(einn_personen):
val = (
total_einn_fix[total_einn_fix["Person"] == p]["Betrag"].sum() +
total_einn_var[total_einn_var["Person"] == p]["Betrag"].sum()
)
if val > 0:
source.append(i); target.append(budget_idx)
                value.append(round(val, 2)); color_link.append("rgba(31,119,180,0.4)")
                value.append(round(val, 2)); color_link.append("rgba(201,168,76,0.35)")
link_labels.append(fmt_eur(val))

        # Budget → Kategorien
        unique_kats  = sorted(df_ausg_all["Kategorie"].dropna().unique())
        kat_start    = len(label_list)
        unique_kats = sorted(df_ausg_all["Kategorie"].dropna().unique())
        kat_start   = len(label_list)
label_list.extend(unique_kats)
for i, k in enumerate(unique_kats):
val = df_ausg_all[df_ausg_all["Kategorie"] == k]["Betrag"].sum()
if val > 0:
source.append(budget_idx); target.append(kat_start + i)
value.append(round(val, 2))
                color_link.append(hex_to_rgba(COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)], 0.45))
                color_link.append(hex_to_rgba(COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)], 0.4))
link_labels.append(fmt_eur(val))

        # Kategorien → Unterkategorien
unique_subs = (
df_ausg_all.groupby(["Kategorie", "Unterkategorie"])["Betrag"].sum().reset_index()
)
@@ -909,12 +1357,11 @@ def _rule_color(actual, target):
color_link.append(
hex_to_rgba(
COMPLEMENTARY_COLORS[unique_kats.index(row["Kategorie"]) % len(COMPLEMENTARY_COLORS)],
                        0.3,
                        0.25,
)
)
link_labels.append(fmt_eur(row["Betrag"]))

        # Saldo-Link (falls positiv)
gesamt_einn_s = sum(value[:len(einn_personen)])
gesamt_ausg_s = df_ausg_all["Betrag"].sum()
if gesamt_einn_s > gesamt_ausg_s:
@@ -923,15 +1370,14 @@ def _rule_color(actual, target):
saldo_val = gesamt_einn_s - gesamt_ausg_s
source.append(budget_idx); target.append(saldo_idx)
value.append(round(saldo_val, 2))
            color_link.append("rgba(40,167,69,0.5)")
            color_link.append("rgba(80,200,120,0.45)")
link_labels.append(fmt_eur(saldo_val))

        # Node-Farben
node_colors = (
[COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)] for i in range(len(einn_personen))] +
[COLOR_ACCENT] +
[COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)] for i in range(len(unique_kats))] +
            ["#adb5bd"] * len(unique_subs) +
            ["rgba(138,155,174,0.6)"] * len(unique_subs) +
([COLOR_POSITIVE] if gesamt_einn_s > gesamt_ausg_s else [])
)

@@ -947,12 +1393,14 @@ def _rule_color(actual, target):
source=source, target=target,
value=value, color=color_link,
customdata=link_labels,
                hovertemplate="Von: %{source.label}<br>Nach: %{target.label}<br>Betrag: %{customdata}<extra></extra>",
                hovertemplate="Von: %{source.label}<br>Nach: %{target.label}<br>%{customdata}<extra></extra>",
),
)])
fig_sankey.update_layout(
            title_text="💸 Cashflow: Einnahmen → Budget → Kategorien → Unterkategorien → Saldo",
            font_size=12, height=650,
            title_text="💸 Cashflow: Einnahmen → Budget → Kategorien → Saldo",
            font=dict(family="Georgia, serif", color="#D4C5A0", size=11),
            paper_bgcolor="rgba(0,0,0,0)",
            height=650,
)
st.plotly_chart(fig_sankey, use_container_width=True)
else:
@@ -963,7 +1411,7 @@ def _rule_color(actual, target):
# TAB 6 – 📈 TRENDS
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("📈 Trends")]:
    st.subheader("📈 Trend-Analyse")
    st.subheader("Trend-Analyse")

if not df_ausgaben.empty:
trend_tabs = st.tabs(["📁 Kategorien", "🔍 Unterkategorien"])
@@ -983,14 +1431,14 @@ def _rule_color(actual, target):
.groupby(["Sort", "Monat", "Kategorie"])["Betrag"]
.sum().reset_index().sort_values("Sort")
)
                    st.plotly_chart(
                        px.line(
                            res, x="Monat", y="Betrag", color="Kategorie",
                            markers=True, color_discrete_sequence=COMPLEMENTARY_COLORS,
                            title="Monatliche Ausgaben nach Kategorie",
                        ),
                        use_container_width=True,
                    fig_trend_kat = px.line(
                        res, x="Monat", y="Betrag", color="Kategorie",
                        markers=True, color_discrete_sequence=COMPLEMENTARY_COLORS,
                        title="Monatliche Ausgaben nach Kategorie",
)
                    fig_trend_kat.update_traces(line=dict(width=2.5), marker=dict(size=8))
                    apply_chart_theme(fig_trend_kat)
                    st.plotly_chart(fig_trend_kat, use_container_width=True)

with trend_tabs[1]:
sel_subs = []
@@ -1019,64 +1467,66 @@ def tg(k=kat, m=mk, s=subs):
.groupby(["Sort", "Monat", "Unterkategorie"])["Betrag"]
.sum().reset_index().sort_values("Sort")
)
                    st.plotly_chart(
                        px.line(
                            res, x="Monat", y="Betrag", color="Unterkategorie",
                            markers=True, color_discrete_sequence=COMPLEMENTARY_COLORS,
                            title="Monatliche Ausgaben nach Unterkategorie",
                        ),
                        use_container_width=True,
                    fig_trend_sub = px.line(
                        res, x="Monat", y="Betrag", color="Unterkategorie",
                        markers=True, color_discrete_sequence=COMPLEMENTARY_COLORS,
                        title="Monatliche Ausgaben nach Unterkategorie",
)
                    fig_trend_sub.update_traces(line=dict(width=2.5), marker=dict(size=8))
                    apply_chart_theme(fig_trend_sub)
                    st.plotly_chart(fig_trend_sub, use_container_width=True)
else:
st.info("Keine Ausgabendaten für Trend-Analyse verfügbar.")


# ──────────────────────────────────────────────────────────────────────
# TAB 7 – 📐 KENNZAHLEN (Simon & Alisia IDENTISCH)
# TAB 7 – 📐 KENNZAHLEN
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("📐 Kennzahlen")]:

    # Sub-Tabs: Kennzahlen + Spar-Modul (nur für Simon sinnvoll, aber für alle verfügbar)
kenn_subtabs = st.tabs(["📐 Kennzahlen & Sparquote", "💰 Spar-Planung", "💸 Zusatzbudget"])

    # ── SUB-TAB 1: KENNZAHLEN (unveränderter Original-Code) ─────────────
    # ── SUB-TAB 1: KENNZAHLEN ─────────────────────────────────────────
with kenn_subtabs[0]:
        st.subheader("📐 Kennzahlen & Sparquote")
        st.subheader("Kennzahlen & Sparquote")

akt_einn = gesamt_einnahmen

if akt_einn > 0:
            # KPI-Reihe
m1, m2, m3, m4 = st.columns(4)
m1.metric("Gesamteinnahmen", fmt_eur(akt_einn))
m2.metric("Gesamtausgaben",  fmt_eur(gesamt_ausgaben))
m3.metric("Sparbetrag",      fmt_eur(gesamt_spar))
m4.metric("Sparquote",       f"{sparquote:.1f} %")

            # Sparquoten-Gauge
fig_gauge = go.Figure(go.Indicator(
mode="gauge+number+delta",
value=sparquote,
delta={"reference": 20, "suffix": " pp zum 20%-Ziel"},
                title={"text": "Aktuelle Sparquote (%)"},
                title={"text": "Aktuelle Sparquote (%)", "font": {"color": "#C9A84C", "family": "Georgia, serif"}},
                number={"font": {"color": "#E8E0D0", "family": "Georgia, serif"}},
gauge={
                    "axis": {"range": [0, 60]},
                    "axis": {"range": [0, 60], "tickcolor": "#8A9BAE",
                             "tickfont": {"color": "#8A9BAE"}, "gridcolor": "rgba(255,255,255,0.1)"},
"bar": {"color": COLOR_ACCENT},
                    "bgcolor": "rgba(255,255,255,0.03)",
                    "bordercolor": "rgba(201,168,76,0.2)",
"steps": [
                        {"range": [0, 10],  "color": "#dc3545"},
                        {"range": [10, 20], "color": "#ffc107"},
                        {"range": [20, 60], "color": "#28a745"},
                        {"range": [0, 10],  "color": "rgba(224,82,82,0.2)"},
                        {"range": [10, 20], "color": "rgba(232,112,64,0.2)"},
                        {"range": [20, 60], "color": "rgba(80,200,120,0.12)"},
],
"threshold": {
                        "line": {"color": "#003f5c", "width": 4},
                        "line": {"color": COLOR_ACCENT, "width": 3},
"thickness": 0.75, "value": 20,
},
},
))
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=350,
                                     font=dict(family="Georgia, serif", color="#D4C5A0"))
st.plotly_chart(fig_gauge, use_container_width=True)

            # Burn-Rate Erklärung
            st.divider()
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
bc1, bc2 = st.columns(2)
with bc1:
st.metric(
@@ -1095,20 +1545,17 @@ def tg(k=kat, m=mk, s=subs):
st.metric("⚡ Monatl. Ausgaben (Ø)", fmt_eur(monatl_ausgaben_calc))
st.metric("🐖 Monatl. Sparbetrag (Ø)", fmt_eur(gesamt_spar / num_months if num_months > 0 else 0))

            # Sparquote Zeitverlauf
            st.divider()
            st.write("### 📈 Entwicklung der Sparquote")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Entwicklung der Sparquote</p>', unsafe_allow_html=True)
df_v_all = df_ausgaben.copy()
df_e_all = df_einnahmen.copy()

            # "Sort"-Spalte nur anlegen wenn Datum-Spalte vorhanden UND nicht leer
for d in [df_v_all, df_e_all]:
if "Datum" in d.columns and not d.empty and d["Datum"].notnull().any():
d["Sort"] = d["Datum"].dt.strftime("%Y-%m")
else:
d["Sort"] = pd.Series(dtype="object")

            # Monate sicher sammeln – "Sort" existiert jetzt immer
monate_kenn = sorted(
set(df_v_all["Sort"].dropna().unique()) |
set(df_e_all["Sort"].dropna().unique())
@@ -1137,20 +1584,25 @@ def tg(k=kat, m=mk, s=subs):
title="Sparquote im Zeitverlauf (%)",
color_discrete_sequence=[COLOR_ACCENT],
)
                fig_t.update_traces(
                    line=dict(color=COLOR_ACCENT, width=2.5),
                    fillcolor=hex_to_rgba(COLOR_ACCENT, 0.12),
                    marker=dict(size=8, color=COLOR_ACCENT),
                )
fig_t.add_hline(
                    y=20, line_dash="dash", line_color=COLOR_WARN,
                    y=20, line_dash="dash", line_color=COLOR_WARN, line_width=1.5,
annotation_text="Ziel: 20 %", annotation_position="top right",
                    annotation_font=dict(color=COLOR_WARN),
)
                fig_t.update_layout(plot_bgcolor="rgba(0,0,0,0)")
                apply_chart_theme(fig_t)
st.plotly_chart(fig_t, use_container_width=True)
else:
st.warning("Keine Einnahmen gefunden.")

    # ── SUB-TAB 2: SPAR-PLANUNG ───────────────────────────────────────────
    # ── SUB-TAB 2: SPAR-PLANUNG ───────────────────────────────────────
with kenn_subtabs[1]:
        st.subheader("💰 Spar-Planung & Portfolio-Allokation")
        st.subheader("Spar-Planung & Portfolio-Allokation")

        # ── Basis: monatlicher Sparbetrag aus Fixkosten ───────────────────
spar_basis_monat = (
df_fixkosten[df_fixkosten["Unterkategorie"] == "Sparen"]["Betrag"].sum()
if not df_fixkosten.empty else 0.0
@@ -1164,17 +1616,15 @@ def tg(k=kat, m=mk, s=subs):
"Dieser Betrag ist die 100 %-Basis aller Berechnungen."
)

            # ── Konstanten ────────────────────────────────────────────────
PAV_FIX        = 150.0
PAV_ZUSCHUSS   = 45.0
MAX_TILGUNG    = 1083.0
MONATE_IM_JAHR = 12

budget_nach_pav = max(0.0, spar_basis_monat - PAV_FIX)

            # ── Slider ────────────────────────────────────────────────────
            st.markdown("---")
            st.write("### ⚙️ Interaktive Verteilung")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Interaktive Verteilung</p>', unsafe_allow_html=True)
sl1, sl2 = st.columns(2)

max_tilgung_slider = min(MAX_TILGUNG, budget_nach_pav)
@@ -1202,15 +1652,13 @@ def tg(k=kat, m=mk, s=subs):
help="Restbudget nach pAV und Sondertilgung",
)

            # ── Berechnungen ──────────────────────────────────────────────
investition = max(0.0, spar_basis_monat - PAV_FIX - tilgung - urlaub)
summe_check = PAV_FIX + tilgung + urlaub + investition

if summe_check > spar_basis_monat + 0.01:
st.error(f"⚠️ Rechenkonflikt: Summe ({fmt_eur(summe_check)}) > Basis ({fmt_eur(spar_basis_monat)}). Slider zurücksetzen.")
investition = 0.0

            # ── [NEU #2] Restbetrag-Anzeige unter den Slidern ────────────
inv_pct = (investition / spar_basis_monat * 100) if spar_basis_monat > 0 else 0
inv_col1, inv_col2, inv_col3, inv_col4 = st.columns(4)
inv_col1.metric("🛡️ pAV (fix)", fmt_eur(PAV_FIX), f"{PAV_FIX/spar_basis_monat*100:.1f} % der Basis")
@@ -1223,7 +1671,6 @@ def tg(k=kat, m=mk, s=subs):
delta_color="normal",
)

            # ── Portfolio-Aufteilung ──────────────────────────────────────
core_total    = investition * 0.85
sat_total     = investition * 0.15
msci_world    = core_total * (60 / 85)
@@ -1232,19 +1679,17 @@ def tg(k=kat, m=mk, s=subs):
semiconductor = sat_total * (10 / 15)
zockergeld    = sat_total * (5  / 15)

            # ── Session State ─────────────────────────────────────────────
if "zocker_akkum" not in st.session_state:
st.session_state.zocker_akkum = 0.0

            # ── [NEU #1] Gestapeltes Balkendiagramm ──────────────────────
            st.markdown("---")
            st.write("### 📊 Monatliche Verteilung auf einen Blick")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Monatliche Verteilung auf einen Blick</p>', unsafe_allow_html=True)
fig_bar_stacked = go.Figure()
bar_kategorien = ["Sparbetrag"]
bar_config = [
("🛡️ pAV",            PAV_FIX,           COLOR_NEGATIVE),
("🏦 Sondertilgung",   float(tilgung),    COLOR_WARN),
                ("🌴 Privat/Urlaub",   float(urlaub),     "#a05195"),
                ("🌴 Privat/Urlaub",   float(urlaub),     "#7B68EE"),
("📈 Investment",       investition,       COLOR_POSITIVE),
]
for label, wert, farbe in bar_config:
@@ -1256,22 +1701,21 @@ def tg(k=kat, m=mk, s=subs):
text=[fmt_eur(wert)],
textposition="inside",
insidetextanchor="middle",
                    textfont=dict(color="#0D0F14", size=11),
))
fig_bar_stacked.update_layout(
barmode="stack",
title="Aufteilung des monatlichen Sparbetrags",
yaxis_title="€",
yaxis_range=[0, spar_basis_monat * 1.1],
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
height=350,
)
            apply_chart_theme(fig_bar_stacked, height=350)
st.plotly_chart(fig_bar_stacked, use_container_width=True)

            # ── Wasserfall + pAV-Kachel ───────────────────────────────────
            st.markdown("---")
            st.write("### 🔽 Wasserfall & Private Altersvorsorge")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Wasserfall & Private Altersvorsorge</p>', unsafe_allow_html=True)
col_wf, col_pav = st.columns([2, 1])

with col_wf:
@@ -1285,22 +1729,25 @@ def tg(k=kat, m=mk, s=subs):
y=wf_y,
text=wf_text,
textposition="outside",
                    connector={"line": {"color": COLOR_NEUTRAL}},
                    increasing={"marker": {"color": COLOR_POSITIVE}},
                    decreasing={"marker": {"color": COLOR_NEGATIVE}},
                    totals={"marker": {"color": COLOR_ACCENT}},
                    textfont=dict(color="#D4C5A0"),
                    connector={"line": {"color": "rgba(138,155,174,0.3)", "width": 1}},
                    increasing={"marker": {"color": COLOR_POSITIVE,
                                           "line": {"color": "rgba(255,255,255,0.1)", "width": 1}}},
                    decreasing={"marker": {"color": COLOR_NEGATIVE,
                                           "line": {"color": "rgba(255,255,255,0.1)", "width": 1}}},
                    totals={"marker": {"color": COLOR_ACCENT,
                                       "line": {"color": "rgba(255,255,255,0.1)", "width": 1}}},
))
fig_wf.update_layout(
title="Spar-Wasserfall: Monatliche Verteilung",
yaxis_title="€",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
showlegend=False,
)
                apply_chart_theme(fig_wf)
st.plotly_chart(fig_wf, use_container_width=True)

with col_pav:
                st.write("#### 🛡️ Private Altersvorsorge")
                st.markdown('<p class="kpi-section-label">Private Altersvorsorge</p>', unsafe_allow_html=True)
anzahl_monate_daten = max(1, len(
set(df_ausgaben["Monat_Jahr"].dropna().unique())
if not df_ausgaben.empty and "Monat_Jahr" in df_ausgaben.columns
@@ -1316,18 +1763,15 @@ def tg(k=kat, m=mk, s=subs):
st.metric("💰 Gesamtkapital (inkl. Zuschuss)", fmt_eur(pav_kapital_gesamt + pav_zuschuss_gesamt))
st.info(f"📅 Monatlich: **{fmt_eur(PAV_FIX)}** eigen + **{fmt_eur(PAV_ZUSCHUSS)}** Zuschuss = **{fmt_eur(PAV_FIX + PAV_ZUSCHUSS)}** gesamt")

            # ── [NEU #3] pAV-Zeitstrahl ────────────────────────────────────
            st.markdown("---")
            st.write("#### 📈 pAV-Kapitalentwicklung im Zeitverlauf")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">pAV-Kapitalentwicklung im Zeitverlauf</p>', unsafe_allow_html=True)
if anzahl_monate_daten >= 1:
                # Alle Datenmonate sortiert aufbauen
alle_pav_monate = sorted(
set(df_ausgaben["Monat_Jahr"].dropna().unique())
if not df_ausgaben.empty and "Monat_Jahr" in df_ausgaben.columns
else []
)
if not alle_pav_monate:
                    # Fallback: synthetische Monate ab heute rückwärts
import calendar
heute = datetime.now()
alle_pav_monate = []
@@ -1340,9 +1784,9 @@ def tg(k=kat, m=mk, s=subs):

pav_timeline = []
for idx_m, monat_str in enumerate(alle_pav_monate, start=1):
                    eigen_kum   = PAV_FIX      * idx_m
                    eigen_kum    = PAV_FIX      * idx_m
zuschuss_kum = PAV_ZUSCHUSS * idx_m
                    gesamt_kum  = eigen_kum + zuschuss_kum
                    gesamt_kum   = eigen_kum + zuschuss_kum
try:
mn, yr = monat_str.split("-")
label = f"{MONATE_DE[mn]} {yr}"
@@ -1364,86 +1808,92 @@ def tg(k=kat, m=mk, s=subs):
marker_color=COLOR_ACCENT,
text=df_pav_tl["Eigene Einzahlungen"].map(fmt_eur),
textposition="inside",
                    textfont=dict(color="#0D0F14"),
))
fig_pav_tl.add_trace(go.Bar(
x=df_pav_tl["Monat"], y=df_pav_tl["Staatl. Zuschuss"],
name="Staatl. Zuschuss",
marker_color=COLOR_POSITIVE,
text=df_pav_tl["Staatl. Zuschuss"].map(fmt_eur),
textposition="inside",
                    textfont=dict(color="#0D0F14"),
))
fig_pav_tl.add_trace(go.Scatter(
x=df_pav_tl["Monat"], y=df_pav_tl["Gesamtkapital"],
name="Gesamtkapital",
mode="lines+markers+text",
line=dict(color=COLOR_WARN, width=2, dash="dot"),
                    marker=dict(size=8),
                    marker=dict(size=8, color=COLOR_WARN),
text=df_pav_tl["Gesamtkapital"].map(fmt_eur),
textposition="top center",
                    textfont=dict(color=COLOR_WARN),
))
fig_pav_tl.update_layout(
barmode="stack",
title="Kumulative pAV-Entwicklung (eigene Einzahlungen + Zuschuss)",
yaxis_title="€ (kumuliert)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
legend=dict(orientation="h"),
height=400,
)
                apply_chart_theme(fig_pav_tl, height=400)
st.plotly_chart(fig_pav_tl, use_container_width=True)
else:
st.info("Keine Monatsdaten für den Zeitstrahl verfügbar.")

            # ── [ANGEPASST #4] Tilgungs-Gauge + Portfolio-Chart ──────────
            st.markdown("---")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
col_gauge, col_port = st.columns(2)

with col_gauge:
                st.write("#### 🏦 Sondertilgung – Jahresfortschritt")
                st.markdown('<p class="kpi-section-label">Sondertilgung — Jahresfortschritt</p>', unsafe_allow_html=True)
tilgung_jahresbetrag = tilgung * MONATE_IM_JAHR
monat_aktuell        = datetime.now().month
monate_verbleibend   = max(1, MONATE_IM_JAHR - monat_aktuell + 1)
tilgung_hochrechnung = tilgung * monate_verbleibend
tilgung_prozent      = min(100.0, tilgung_hochrechnung / 13000.0 * 100)

                # Balkenfarbe: rot < 5k, gelb 5k–7k, grün > 7k
if tilgung_hochrechnung < 5000:
tg_bar_color = COLOR_NEGATIVE
elif tilgung_hochrechnung < 7000:
                    tg_bar_color = "#ffc107"
                    tg_bar_color = COLOR_WARN
else:
tg_bar_color = COLOR_POSITIVE

fig_tg = go.Figure(go.Indicator(
mode="gauge+number+delta",
value=tilgung_hochrechnung,
                    number={"suffix": " €", "valueformat": ",.0f"},
                    number={"suffix": " €", "valueformat": ",.0f",
                            "font": {"color": "#E8E0D0", "family": "Georgia, serif"}},
delta={"reference": 13000, "valueformat": ",.0f", "suffix": " € zum Limit"},
                    title={"text": f"Hochrechnung bis Jahresende<br><sup>{monate_verbleibend} Monate × {fmt_eur(tilgung)}</sup>"},
                    title={"text": f"Hochrechnung bis Jahresende<br><sup>{monate_verbleibend} Monate × {fmt_eur(tilgung)}</sup>",
                           "font": {"color": "#C9A84C", "family": "Georgia, serif"}},
gauge={
                        "axis": {"range": [0, 13000]},
                        "axis": {"range": [0, 13000], "tickcolor": "#8A9BAE",
                                 "tickfont": {"color": "#8A9BAE"}},
"bar": {"color": tg_bar_color},
                        "bgcolor": "rgba(255,255,255,0.03)",
                        "bordercolor": "rgba(201,168,76,0.2)",
"steps": [
                            {"range": [0, 5000],   "color": "#fde8e8"},
                            {"range": [5000, 7000], "color": "#fff3cd"},
                            {"range": [7000, 13000],"color": "#d4edda"},
                            {"range": [0, 5000],    "color": "rgba(224,82,82,0.15)"},
                            {"range": [5000, 7000],  "color": "rgba(232,112,64,0.15)"},
                            {"range": [7000, 13000], "color": "rgba(80,200,120,0.1)"},
],
"threshold": {
                            "line": {"color": COLOR_NEGATIVE, "width": 4},
                            "line": {"color": COLOR_NEGATIVE, "width": 3},
"thickness": 0.75,
"value": 13000,
},
},
))
                fig_tg.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)")
                fig_tg.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)",
                                      font=dict(family="Georgia, serif", color="#D4C5A0"))
st.plotly_chart(fig_tg, use_container_width=True)
st.caption(
f"Jahresbetrag bei gleichbleibender Rate: **{fmt_eur(tilgung_jahresbetrag)}** "
f"| Limit: **13.000,00 €** | Ausnutzung: **{tilgung_prozent:.1f} %**"
)

with col_port:
                st.write("#### 📈 Portfolio-Allokation")
                st.markdown('<p class="kpi-section-label">Portfolio-Allokation</p>', unsafe_allow_html=True)
if investition > 0:
port_labels  = ["Investment", "Core (85%)", "Satellite (15%)",
"MSCI World", "Europa", "EM",
@@ -1472,14 +1922,14 @@ def tg(k=kat, m=mk, s=subs):
fig_sun.update_layout(
height=350, paper_bgcolor="rgba(0,0,0,0)",
margin=dict(t=10, b=10, l=10, r=10),
                        font=dict(family="Georgia, serif", color="#D4C5A0"),
)
st.plotly_chart(fig_sun, use_container_width=True)
else:
st.info("💡 Kein Restbetrag für Investment — Slider anpassen.")

            # ── Portfolio-Detailtabelle ───────────────────────────────────
            st.markdown("---")
            st.write("### 📋 Portfolio-Detailübersicht")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Portfolio-Detailübersicht</p>', unsafe_allow_html=True)
port_detail_cols = st.columns(5)
port_items = [
("🌍 MSCI World",    msci_world,    "Core · 60 %"),
@@ -1491,9 +1941,8 @@ def tg(k=kat, m=mk, s=subs):
for col, (label, betrag, info) in zip(port_detail_cols, port_items):
col.metric(label, fmt_eur(betrag), info)

            # ── Zockergeld-Akkumulator ────────────────────────────────────
            st.markdown("---")
            st.write("### 🎲 Zockergeld-Kasse")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Zockergeld-Kasse</p>', unsafe_allow_html=True)
zk1, zk2, zk3 = st.columns([1, 1, 1])
with zk1:
st.metric("💶 Aktueller Monatsbetrag", fmt_eur(zockergeld))
@@ -1509,9 +1958,8 @@ def tg(k=kat, m=mk, s=subs):
st.session_state.zocker_akkum += zockergeld
st.success(f"+ {fmt_eur(zockergeld)} zur Zockerkasse hinzugefügt.")

            # ── Zusammenfassungs-Tabelle ──────────────────────────────────
            st.markdown("---")
            st.write("### 🧾 Monatsübersicht")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Monatsübersicht</p>', unsafe_allow_html=True)
summary_data = {
"Posten": [
"🐖 Sparbetrag (Basis)",
@@ -1548,9 +1996,9 @@ def tg(k=kat, m=mk, s=subs):
}
st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

    # ── SUB-TAB 3: ZUSATZBUDGET-RECHNER [NEU #5] ─────────────────────────
    # ── SUB-TAB 3: ZUSATZBUDGET-RECHNER ──────────────────────────────
with kenn_subtabs[2]:
        st.subheader("💸 Zusatzbudget-Rechner")
        st.subheader("Zusatzbudget-Rechner")
st.info(
"Hier kannst du ein einmalig verfügbares Zusatzbudget eingeben (z. B. Bonus, Rückerstattung, "
"Monatsüberschuss) und siehst sofort, wie es gemäß deiner Core-Satellite-Strategie aufgeteilt wird."
@@ -1568,7 +2016,6 @@ def tg(k=kat, m=mk, s=subs):
)

if zusatz_betrag > 0:
            # Gleiche Portfolio-Aufteilung: Core 85% / Satellite 15%
z_core_total    = zusatz_betrag * 0.85
z_sat_total     = zusatz_betrag * 0.15
z_msci_world    = z_core_total * (60 / 85)
@@ -1577,29 +2024,27 @@ def tg(k=kat, m=mk, s=subs):
z_semiconductor = z_sat_total  * (10 / 15)
z_zockergeld    = z_sat_total  * (5  / 15)

            st.markdown("---")
            st.write(f"### 📊 Aufteilung für {fmt_eur(zusatz_betrag)}")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown(f'<p class="kpi-section-label">Aufteilung für {fmt_eur(zusatz_betrag)}</p>', unsafe_allow_html=True)

            # Metric-Kacheln
zb_c1, zb_c2 = st.columns(2)
with zb_c1:
st.metric("🔵 Core-Anteil (85 %)", fmt_eur(z_core_total))
with zb_c2:
st.metric("🟠 Satellite-Anteil (15 %)", fmt_eur(z_sat_total))

            st.markdown("##### Core-Positionen")
            st.markdown('<p class="kpi-section-label">Core-Positionen</p>', unsafe_allow_html=True)
zc1, zc2, zc3 = st.columns(3)
zc1.metric("🌍 MSCI World (60 %)", fmt_eur(z_msci_world))
zc2.metric("🇪🇺 Europa (15 %)",     fmt_eur(z_europa))
zc3.metric("🌏 EM (10 %)",           fmt_eur(z_em))

            st.markdown("##### Satellite-Positionen")
            st.markdown('<p class="kpi-section-label">Satellite-Positionen</p>', unsafe_allow_html=True)
zs1, zs2 = st.columns(2)
zs1.metric("💻 Semiconductor (10 %)", fmt_eur(z_semiconductor))
zs2.metric("🎲 Zockergeld (5 %)",     fmt_eur(z_zockergeld))

            # Sunburst-Visualisierung
            st.markdown("---")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
z_port_labels  = ["Zusatzbudget", "Core (85%)", "Satellite (15%)",
"MSCI World", "Europa", "EM",
"Semiconductor", "Zockergeld"]
@@ -1629,37 +2074,26 @@ def tg(k=kat, m=mk, s=subs):
height=450,
paper_bgcolor="rgba(0,0,0,0)",
margin=dict(t=40, b=10, l=10, r=10),
                font=dict(family="Georgia, serif", color="#D4C5A0"),
)
st.plotly_chart(fig_z_sun, use_container_width=True)

            # Detailtabelle
            st.markdown("---")
            st.write("### 🧾 Detailübersicht Zusatzbudget")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Detailübersicht Zusatzbudget</p>', unsafe_allow_html=True)
z_summary = {
"Position": [
                    "💶 Zusatzbudget (gesamt)",
                    "─────────────────────",
                    "🔵 Core (85 %)",
                    "   🌍 MSCI World (60 %)",
                    "   🇪🇺 Europa (15 %)",
                    "   🌏 EM (10 %)",
                    "🟠 Satellite (15 %)",
                    "   💻 Semiconductor (10 %)",
                    "   🎲 Zockergeld (5 %)",
                    "💶 Zusatzbudget (gesamt)", "─────────────────────",
                    "🔵 Core (85 %)", "   🌍 MSCI World (60 %)", "   🇪🇺 Europa (15 %)",
                    "   🌏 EM (10 %)", "🟠 Satellite (15 %)",
                    "   💻 Semiconductor (10 %)", "   🎲 Zockergeld (5 %)",
],
"Betrag": [
fmt_eur(zusatz_betrag), "────────",
                    fmt_eur(z_core_total),
                    fmt_eur(z_msci_world),
                    fmt_eur(z_europa),
                    fmt_eur(z_em),
                    fmt_eur(z_sat_total),
                    fmt_eur(z_semiconductor),
                    fmt_eur(z_zockergeld),
                    fmt_eur(z_core_total), fmt_eur(z_msci_world), fmt_eur(z_europa),
                    fmt_eur(z_em), fmt_eur(z_sat_total), fmt_eur(z_semiconductor), fmt_eur(z_zockergeld),
],
"Anteil": [
                    "100,0 %", "────",
                    "85,0 %",
                    "100,0 %", "────", "85,0 %",
f"{z_msci_world / zusatz_betrag * 100:.1f} %",
f"{z_europa / zusatz_betrag * 100:.1f} %",
f"{z_em / zusatz_betrag * 100:.1f} %",
@@ -1670,7 +2104,7 @@ def tg(k=kat, m=mk, s=subs):
}
st.dataframe(pd.DataFrame(z_summary), hide_index=True, use_container_width=True)
else:
            st.markdown("---")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
st.write("👆 Gib oben einen Betrag ein, um die Portfolio-Aufteilung zu berechnen.")


@@ -1679,17 +2113,15 @@ def tg(k=kat, m=mk, s=subs):
# ──────────────────────────────────────────────────────────────────────
if mode == "unser":
with tabs[tab_idx("🤝 Lastenverteilung")]:
        st.subheader("🤝 Lastenverteilung & Fairness-Modell")
        st.subheader("Lastenverteilung & Fairness-Modell")

if not df_fix_einnahmen.empty:
            # ── Einnahmen pro Person ──────────────────────────────────
einn_pro_person = (
df_fix_einnahmen.groupby("Person")["Betrag"].sum() * num_months
).reset_index()
einn_pro_person.columns = ["Person", "Einnahmen"]
total_einn_all = einn_pro_person["Einnahmen"].sum()

            # Variable Einnahmen per Person hinzufügen (falls vorhanden)
if not filtered_einnahmen.empty and "Person" in filtered_einnahmen.columns:
var_per = filtered_einnahmen.groupby("Person")["Betrag"].sum().reset_index()
var_per.columns = ["Person", "Einnahmen_var"]
@@ -1702,14 +2134,13 @@ def tg(k=kat, m=mk, s=subs):
einn_pro_person["Einnahmen"] / total_einn_all * 100
).round(1)

            # ── Ausgaben pro Person (falls Spalte vorhanden) ──────────
hat_person_spalte = (
not df_fixkosten.empty and "Person" in df_fixkosten.columns
) or (
not filtered_ausgaben.empty and "Person" in filtered_ausgaben.columns
)

            st.write("#### 💰 Einnahmen-Beitragsverteilung")
            st.markdown('<p class="kpi-section-label">Einnahmen-Beitragsverteilung</p>', unsafe_allow_html=True)
col_e1, col_e2 = st.columns([1, 1])
with col_e1:
fig_einn_p = px.pie(
@@ -1718,31 +2149,31 @@ def tg(k=kat, m=mk, s=subs):
color_discrete_sequence=COMPLEMENTARY_COLORS,
hole=0.4,
)
                fig_einn_p.update_traces(textinfo="label+percent+value")
                fig_einn_p.update_traces(textinfo="label+percent+value",
                                          textfont=dict(color="#D4C5A0"))
                apply_chart_theme(fig_einn_p)
st.plotly_chart(fig_einn_p, use_container_width=True)
with col_e2:
df_einn_disp = einn_pro_person.copy()
df_einn_disp["Einnahmen"] = df_einn_disp["Einnahmen"].map(fmt_eur)
st.dataframe(df_einn_disp, hide_index=True, use_container_width=True)

                # Fairness-Metrik: Abweichung von 50/50
n_persons = len(einn_pro_person)
if n_persons == 2:
anteil_a = einn_pro_person["Anteil_Einn_%"].iloc[0]
anteil_b = einn_pro_person["Anteil_Einn_%"].iloc[1]
abw = abs(anteil_a - 50)
                    st.divider()
                    st.write("**⚖️ Fairness-Index (50/50-Basis)**")
                    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
                    st.markdown('<p class="kpi-section-label">Fairness-Index (50/50-Basis)</p>', unsafe_allow_html=True)
if abw <= 5:
st.success(f"✅ Sehr ausgewogen — Abweichung: {abw:.1f} pp")
elif abw <= 15:
st.warning(f"⚠️ Leicht ungleich — Abweichung: {abw:.1f} pp")
else:
st.error(f"❌ Deutliche Ungleichverteilung — Abweichung: {abw:.1f} pp")

            # ── Fairness-Modell: Ausgaben relativ zum Einkommen ──────
            st.divider()
            st.write("#### 🎯 Proportionales Fairness-Modell")
            st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
            st.markdown('<p class="kpi-section-label">Proportionales Fairness-Modell</p>', unsafe_allow_html=True)
st.info(
"**Idee:** Jede Person sollte Ausgaben proportional zu ihrem Einkommensanteil tragen. "
"Das Modell berechnet, wie viel jede Person bei fairer Aufteilung zahlen würde."
@@ -1762,24 +2193,27 @@ def tg(k=kat, m=mk, s=subs):
df_fair = pd.DataFrame(fairness_rows)
st.dataframe(df_fair, hide_index=True, use_container_width=True)

                # Gauge-Chart für Fairness
if len(einn_pro_person) == 2:
anteil_fair = einn_pro_person["Anteil_Einn_%"].tolist()
fig_fair = go.Figure(go.Bar(
x=einn_pro_person["Person"].tolist(),
y=anteil_fair,
marker_color=COMPLEMENTARY_COLORS[:2],
                        marker_line=dict(color="rgba(255,255,255,0.1)", width=1),
text=[f"{v:.1f} %" for v in anteil_fair],
textposition="outside",
                        textfont=dict(color="#D4C5A0"),
))
fig_fair.add_hline(y=50, line_dash="dash", line_color=COLOR_NEUTRAL,
                                       annotation_text="50/50-Linie")
                                       line_width=1.5,
                                       annotation_text="50/50-Linie",
                                       annotation_font=dict(color=COLOR_NEUTRAL))
fig_fair.update_layout(
title="Einkommensanteile im Vergleich",
yaxis_range=[0, 100],
yaxis_title="Anteil (%)",
                        plot_bgcolor="rgba(0,0,0,0)",
)
                    apply_chart_theme(fig_fair)
st.plotly_chart(fig_fair, use_container_width=True)
else:
st.info("Keine Einnahmen-Daten mit Personenzuordnung verfügbar.")
@@ -1789,10 +2223,9 @@ def tg(k=kat, m=mk, s=subs):
# TAB 9 – 💡 OPTIMIERUNGSPOTENZIAL
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("💡 Optimierungspotenzial")]:
    st.subheader("💡 Optimierungspotenzial & Automatische Insights")
    st.subheader("Optimierungspotenzial & Automatische Insights")

    # ── Handlungsempfehlungen basierend auf KPIs ─────────────────────
    st.write("### 🎯 Automatische Handlungsempfehlungen")
    st.markdown('<p class="kpi-section-label">Automatische Handlungsempfehlungen</p>', unsafe_allow_html=True)
empfehlungen = []

if fix_quote > 60:
@@ -1862,9 +2295,8 @@ def tg(k=kat, m=mk, s=subs):
else:
st.success("✅ Alle Kennzahlen im grünen Bereich. Hervorragende Finanzführung!")

    # ── Kategorien mit >15 % Anstieg zum Vormonat ────────────────────
    st.divider()
    st.write("### 📊 Ausgaben-Alarm: Kategorien mit ≥ 15 % Anstieg zum Vormonat")
    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
    st.markdown('<p class="kpi-section-label">Ausgaben-Alarm: Kategorien mit ≥ 15 % Anstieg zum Vormonat</p>', unsafe_allow_html=True)

if not df_ausgaben.empty and "Datum" in df_ausgaben.columns:
df_alarm = df_ausgaben.copy()
@@ -1898,7 +2330,6 @@ def tg(k=kat, m=mk, s=subs):
df_a = pd.DataFrame(alarm_rows).sort_values("Veränderung", ascending=False)
st.dataframe(df_a, hide_index=True, use_container_width=True)

                # Visualisierung: Alarmkategorien
cur_m_label  = datum_zu_monat(datetime.strptime(f"01-{cur_m}", "%d-%Y-%m")) or cur_m
prev_m_label = datum_zu_monat(datetime.strptime(f"01-{prev_m}", "%d-%Y-%m")) or prev_m

@@ -1918,7 +2349,8 @@ def tg(k=kat, m=mk, s=subs):
title="Vergleich: Aktuell vs. Vormonat (Alarmkategorien)",
text_auto=".2f",
)
                fig_alarm.update_layout(plot_bgcolor="rgba(0,0,0,0)")
                fig_alarm.update_traces(textfont=dict(color="#D4C5A0"))
                apply_chart_theme(fig_alarm)
st.plotly_chart(fig_alarm, use_container_width=True)
else:
st.success(f"✅ Keine Kategorie mit ≥ 15 % Anstieg gegenüber dem Vormonat ({prev_m}).")
@@ -1927,10 +2359,9 @@ def tg(k=kat, m=mk, s=subs):
else:
st.info("Keine Ausgabendaten für Alarm-Analyse verfügbar.")

    # ── Unterkategorien-Detailvergleich ──────────────────────────────
if not df_ausgaben.empty and "Datum" in df_ausgaben.columns:
        st.divider()
        st.write("### 🔍 Detailvergleich auf Unterkategorie-Ebene")
        st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)
        st.markdown('<p class="kpi-section-label">Detailvergleich auf Unterkategorie-Ebene</p>', unsafe_allow_html=True)
df_sub_alarm = df_ausgaben.copy()
df_sub_alarm["Sort"] = df_sub_alarm["Datum"].dt.strftime("%Y-%m")
df_sub_alarm = df_sub_alarm.dropna(subset=["Sort"])
