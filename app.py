"""
╔══════════════════════════════════════════════════════════════════════╗
║                  FINANZZENTRALE — WORLD-CLASS EDITION               ║
║      Senior Full-Stack · Streamlit · Plotly · Private Finance       ║
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
# 1. IMPORTS & GLOBALE KONFIGURATION
# ──────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Finanzzentrale",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design-System ─────────────────────────────────────────────────────
COMPLEMENTARY_COLORS = [
    "#003f5c", "#ff7c43", "#2f4b7c", "#ffa600",
    "#665191", "#f95d6a", "#a05195", "#d45087",
]
COLOR_POSITIVE  = "#28a745"
COLOR_NEGATIVE  = "#dc3545"
COLOR_NEUTRAL   = "#6c757d"
COLOR_ACCENT    = "#003f5c"
COLOR_WARN      = "#ff7c43"

# ── Deutsches Monats-Mapping ──────────────────────────────────────────
MONATE_DE = {
    "01": "Januar",  "02": "Februar", "03": "März",    "04": "April",
    "05": "Mai",     "06": "Juni",    "07": "Juli",    "08": "August",
    "09": "September","10": "Oktober","11": "November","12": "Dezember",
}

# ── Google-Sheets IDs ─────────────────────────────────────────────────
SHEET_IDS = {
    "unser":  "1y3lfS_jumaUDM-ms8NQWA_-MpVMWyfc0vGeWUIzX_Rc",
    "simon":  "1VUPcu7bMKC1ws4KYomeiCHuOfKlDdMwp7NiaOlv-AWI",
    "alisia": "1eCvGkPpavtdgrj1_FgnMqyeMJS6ye6NmhGIf1O_E--4",
}


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
        result[mask_nat] = pd.to_datetime(
            series[mask_nat], dayfirst=True, errors="coerce"
        )
    return result


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


# ──────────────────────────────────────────────────────────────────────
# 3. GOOGLE SHEETS — VERBINDUNG & DATENLADEN
# ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_gspread_client():
    """Erstellt einen gspread-Client aus den Streamlit-Secrets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


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
    fix_einnahmen = sheet_to_df(spreadsheet.worksheet("Fix_Einnahmen"))
    einnahmen    = sheet_to_df(spreadsheet.worksheet("Einnahmen"))

    # Beträge bereinigen
    for df in [ausgaben, fixkosten, fix_einnahmen, einnahmen]:
        df["Betrag"] = clean_betrag(df["Betrag"]) if "Betrag" in df.columns else 0.0

    # Datum parsen
    for df in [ausgaben, einnahmen]:
        if "Datum" in df.columns:
            df["Datum"] = clean_datum(df["Datum"])

    return ausgaben, fixkosten, fix_einnahmen, einnahmen


# ──────────────────────────────────────────────────────────────────────
# 4. SIDEBAR — NAVIGATION & ZEITRAUM-FILTER
# ──────────────────────────────────────────────────────────────────────

with st.sidebar:
    # ── Dashboard-Bild ─────────────────────────────────────────────
    if os.path.exists("Bild Dashboard.PNG"):
        st.image("Bild Dashboard.PNG", use_container_width=True)

    st.header("👤 Dashboard wählen")

    if "mode" not in st.session_state:
        st.session_state.mode = "unser"

    btn_cfg = [
        ("🚀 Unsere Finanzen",  "unser"),
        ("👤 Simons Finanzen",  "simon"),
        ("👤 Alisias Finanzen", "alisia"),
    ]
    for label, key in btn_cfg:
        if st.button(label, use_container_width=True):
            st.session_state.mode = key

    mode = st.session_state.mode
    SHEET_ID = SHEET_IDS[mode]

    if mode == "unser":
        st.success("✅ Unsere Finanzen")
        dashboard_title = "🚀 Unsere Finanzzentrale"
    elif mode == "simon":
        st.info("✅ Simons Finanzen")
        dashboard_title = "👤 Simons Finanzzentrale"
    else:
        st.info("✅ Alisias Finanzen")
        dashboard_title = "👤 Alisias Finanzzentrale"

    st.divider()

# ── Daten laden ───────────────────────────────────────────────────────
st.title(dashboard_title)

df_ausgaben, df_fixkosten, df_fix_einnahmen, df_einnahmen = load_data(SHEET_ID)

# ── Monat_Jahr Spalten anlegen ────────────────────────────────────────
for df in [df_ausgaben, df_einnahmen]:
    if not df.empty and "Datum" in df.columns:
        df["Filter_Label"] = df["Datum"].apply(datum_zu_monat)
        df["Monat_Jahr"]   = df["Datum"].dt.strftime("%m-%Y")
    else:
        df["Filter_Label"] = None
        df["Monat_Jahr"]   = None

# ── Verfügbare Monate für Filter ──────────────────────────────────────
filter_mapping = {}
for df in [df_ausgaben, df_einnahmen]:
    if not df.empty and "Filter_Label" in df.columns:
        valid = df.dropna(subset=["Filter_Label", "Monat_Jahr"])
        filter_mapping.update(dict(zip(valid["Filter_Label"], valid["Monat_Jahr"])))

def _sort_key(label):
    tech = filter_mapping.get(label, "01-1970")
    try:
        return datetime.strptime(tech, "%m-%Y")
    except Exception:
        return datetime.min

sorted_labels = sorted(filter_mapping.keys(), key=_sort_key)
month_options = ["Gesamter Zeitraum", "Benutzerdefinierter Zeitraum"] + sorted_labels

# ── Zeitraum-Selektor in der Sidebar ─────────────────────────────────
with st.sidebar:
    st.header("🔍 Globaler Zeitfilter")
    selected_label = st.selectbox("Zeitraum wählen", month_options)

# ── Filter anwenden ───────────────────────────────────────────────────
if selected_label == "Gesamter Zeitraum":
    alle_monate = set()
    for df in [df_ausgaben, df_einnahmen]:
        if not df.empty and "Monat_Jahr" in df.columns:
            alle_monate.update(df["Monat_Jahr"].dropna().unique())
    num_months         = len(alle_monate) if alle_monate else 1
    filtered_ausgaben  = df_ausgaben.copy()
    filtered_einnahmen = df_einnahmen.copy()

elif selected_label == "Benutzerdefinierter Zeitraum":
    with st.sidebar:
        col_s, col_e = st.columns(2)
        min_d = (
            df_ausgaben["Datum"].min().date()
            if not df_ausgaben.empty and pd.notnull(df_ausgaben["Datum"].min())
            else datetime.today().date()
        )
        start_date = col_s.date_input("Von", value=min_d)
        end_date   = col_e.date_input("Bis", value=datetime.today().date())
    start_dt = pd.to_datetime(start_date)
    end_dt   = pd.to_datetime(end_date)
    filtered_ausgaben  = df_ausgaben[(df_ausgaben["Datum"] >= start_dt) & (df_ausgaben["Datum"] <= end_dt)].copy()
    filtered_einnahmen = df_einnahmen[(df_einnahmen["Datum"] >= start_dt) & (df_einnahmen["Datum"] <= end_dt)].copy()
    diff = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    num_months = max(1, diff)

else:
    num_months = 1
    tech_val           = filter_mapping[selected_label]
    filtered_ausgaben  = df_ausgaben[df_ausgaben["Monat_Jahr"] == tech_val].copy()
    filtered_einnahmen = df_einnahmen[df_einnahmen["Monat_Jahr"] == tech_val].copy()

with st.sidebar:
    st.divider()
    if selected_label == "Gesamter Zeitraum":
        st.info(f"📅 Gesamter Zeitraum ({num_months} Monat/e)")
    elif selected_label != "Benutzerdefinierter Zeitraum":
        st.info(f"📅 Aktiver Monat: {selected_label}")
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
var_einnahmen_summe = filtered_einnahmen["Betrag"].sum() if not filtered_einnahmen.empty else 0.0

gesamt_einnahmen = var_einnahmen_summe + einn_fix_summe_scaled
gesamt_ausgaben  = var_ausgaben_summe  + fix_summe_scaled
saldo            = gesamt_einnahmen - gesamt_ausgaben

# ── Sparbetrag (Fix + Variabel) ───────────────────────────────────────
spar_fix = (
    df_fixkosten[df_fixkosten["Unterkategorie"] == "Sparen"]["Betrag"].sum() * num_months
    if not df_fixkosten.empty else 0.0
)
spar_var = (
    filtered_ausgaben[filtered_ausgaben["Unterkategorie"] == "Sparen"]["Betrag"].sum()
    if not filtered_ausgaben.empty else 0.0
)
gesamt_spar = spar_fix + spar_var
sparquote   = (gesamt_spar / gesamt_einnahmen * 100) if gesamt_einnahmen > 0 else 0.0

# ── 50/30/20-Regel ────────────────────────────────────────────────────
# Fixkosten (ohne Sparen) → "50"-Bucket
# Variable Ausgaben (ohne Sparen) → "30"-Bucket (Wünsche/variabel)
# Sparen → "20"-Bucket
fix_ohne_spar = (
    df_fixkosten[df_fixkosten["Unterkategorie"] != "Sparen"]["Betrag"].sum() * num_months
    if not df_fixkosten.empty else 0.0
)
var_ohne_spar = (
    filtered_ausgaben[filtered_ausgaben["Unterkategorie"] != "Sparen"]["Betrag"].sum()
    if not filtered_ausgaben.empty else 0.0
)
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
        return 0.0
    try:
        dt = datetime.strptime(target_monat, "%m-%Y")
        prev_month = dt.replace(day=1) - pd.DateOffset(months=1)
        prev_str   = prev_month.strftime("%m-%Y")
        return df[df["Monat_Jahr"] == prev_str]["Betrag"].sum()
    except Exception:
        return 0.0

# Aktueller und Vormonats-Wert für Ausgaben (skaliert auf 1 Monat für Vergleich)
cur_monat_ausgaben  = var_ausgaben_summe / num_months if num_months > 1 else var_ausgaben_summe
prev_monat_ausgaben = _get_vormonat_daten(
    df_ausgaben,
    filter_mapping.get(selected_label) if selected_label not in ["Gesamter Zeitraum", "Benutzerdefinierter Zeitraum"] else None,
)
delta_ausgaben = cur_monat_ausgaben - prev_monat_ausgaben

cur_monat_einnahmen  = var_einnahmen_summe / num_months if num_months > 1 else var_einnahmen_summe
prev_monat_einnahmen = _get_vormonat_daten(
    df_einnahmen,
    filter_mapping.get(selected_label) if selected_label not in ["Gesamter Zeitraum", "Benutzerdefinierter Zeitraum"] else None,
)
delta_einnahmen = cur_monat_einnahmen - prev_monat_einnahmen


# ──────────────────────────────────────────────────────────────────────
# 6. KPI-HEADER (immer sichtbar, über den Tabs)
# ──────────────────────────────────────────────────────────────────────

st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
    "💰 Gesamteinnahmen",
    fmt_eur(gesamt_einnahmen),
    delta_str(delta_einnahmen),
    delta_color="normal",
)
c2.metric(
    "💸 Gesamtausgaben",
    fmt_eur(gesamt_ausgaben),
    delta_str(delta_ausgaben),
    delta_color="inverse",   # Anstieg = rot (schlechter)
)
c3.metric(
    "📈 Saldo",
    fmt_eur(saldo),
    delta_color="off",
)
c4.metric(
    "🐖 Sparquote",
    f"{sparquote:.1f} %",
    delta_color="off",
)
c5.metric(
    "🔥 Burn-Rate",
    f"{burn_rate_monate:.1f} Mon.",
    help="Wie viele Monate reichen die Ersparnisse im gewählten Zeitraum, falls alle Einnahmen wegfallen?",
    delta_color="off",
)
st.divider()


# ──────────────────────────────────────────────────────────────────────
# 7. TAB-DEFINITION
# ──────────────────────────────────────────────────────────────────────

tab_titles = [
    "📊 Gesamtübersicht",
    "💰 Einnahmen",
    "🏠 Fixkosten",
    "🛒 Variabel",
    "⚖️ Saldo & Cashflow",
    "📈 Trends",
    "📐 Kennzahlen",
]
if mode == "unser":
    tab_titles.append("🤝 Lastenverteilung")

tab_titles.append("💡 Optimierungspotenzial")

tabs = st.tabs(tab_titles)

# Hilfsfunktion: Tab-Index sicher bestimmen
def tab_idx(name: str) -> int:
    return tab_titles.index(name)


# ──────────────────────────────────────────────────────────────────────
# TAB 1 – 📊 GESAMTKOSTENÜBERSICHT
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("📊 Gesamtübersicht")]:

    df_fix_scaled = (
        df_fixkosten.assign(Typ="Fix", Betrag=df_fixkosten["Betrag"] * num_months)
        if not df_fixkosten.empty else pd.DataFrame()
    )
    df_all = pd.concat([
        df_fix_scaled,
        filtered_ausgaben.assign(Typ="Variabel") if not filtered_ausgaben.empty else pd.DataFrame(),
    ])

    gesamt_gesamt = df_all["Betrag"].sum() if not df_all.empty else 0

    st.subheader(f"Gesamtausgaben im Zeitraum: {fmt_eur(gesamt_gesamt)}")

    # ── 50/30/20-Analyse ─────────────────────────────────────────────
    st.write("#### 🎯 50/30/20-Regelanalyse")
    r1, r2, r3 = st.columns(3)

    def _rule_color(actual, target):
        return COLOR_POSITIVE if actual <= target else COLOR_NEGATIVE

    with r1:
        st.metric(
            "🏠 Fixkosten (Soll ≤ 50 %)",
            f"{fix_quote:.1f} %",
            delta=f"{fix_quote - 50:.1f} pp zum Ziel",
            delta_color="inverse",
        )
    with r2:
        st.metric(
            "🛒 Variabel (Soll ≤ 30 %)",
            f"{var_quote:.1f} %",
            delta=f"{var_quote - 30:.1f} pp zum Ziel",
            delta_color="inverse",
        )
    with r3:
        st.metric(
            "🐖 Sparen (Soll ≥ 20 %)",
            f"{sparquote:.1f} %",
            delta=f"{sparquote - 20:.1f} pp zum Ziel",
            delta_color="normal",
        )

    # Gauge-Chart für 50/30/20
    fig_rule = go.Figure()
    categories  = ["Fixkosten", "Variabel", "Sparen"]
    actual_vals = [fix_quote, var_quote, sparquote]
    target_vals = [50, 30, 20]
    bar_colors  = [
        COLOR_POSITIVE if a <= t else COLOR_NEGATIVE
        for a, t in zip(actual_vals, target_vals)
    ]

    fig_rule.add_trace(go.Bar(
        x=categories, y=actual_vals,
        marker_color=bar_colors,
        name="Ist",
        text=[f"{v:.1f} %" for v in actual_vals],
        textposition="outside",
    ))
    fig_rule.add_trace(go.Scatter(
        x=categories, y=target_vals,
        mode="markers+text",
        marker=dict(size=14, color=COLOR_ACCENT, symbol="diamond"),
        text=[f"Ziel: {v} %" for v in target_vals],
        textposition="top center",
        name="Zielwert",
    ))
    fig_rule.update_layout(
        title="50/30/20-Regelanalyse (Ist vs. Ziel)",
        yaxis_title="Anteil am Einkommen (%)",
        yaxis_range=[0, max(max(actual_vals), 55)],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_rule, use_container_width=True)

    st.divider()

    # ── Sunburst + Tabelle ────────────────────────────────────────────
    col_l, col_r = st.columns([1.5, 1])
    with col_r:
        st.write("**🔎 Tabellenfilter**")
        if not df_all.empty:
            f_kat = st.multiselect(
                "Kategorie",
                sorted(df_all["Kategorie"].dropna().unique()),
                key="filter_all_kat",
            )
            f_sub = st.multiselect(
                "Unterkategorie",
                sorted(df_all["Unterkategorie"].dropna().unique()),
                key="filter_all_sub",
            )
            df_ft = df_all.copy()
            if f_kat: df_ft = df_ft[df_ft["Kategorie"].isin(f_kat)]
            if f_sub: df_ft = df_ft[df_ft["Unterkategorie"].isin(f_sub)]
            df_grouped = df_ft.groupby(["Kategorie", "Unterkategorie"])["Betrag"].sum().reset_index()
            df_grouped["Betrag"] = df_grouped["Betrag"].map(lambda x: f"{x:,.2f} €")
            st.dataframe(df_grouped, hide_index=True, use_container_width=True)
            summe_sel = df_ft["Betrag"].sum()
            st.info(f"**Summe: {fmt_eur(summe_sel)}**")
        else:
            st.info("Keine Daten vorhanden.")

    with col_l:
        if not df_all.empty:
            fig_sun = px.sunburst(
                df_all,
                path=["Typ", "Kategorie", "Unterkategorie"],
                values="Betrag",
                height=600,
                color_discrete_sequence=COMPLEMENTARY_COLORS,
                title="Ausgabenstruktur (Fix + Variabel)",
            )
            fig_sun.update_traces(textinfo="label+percent entry")
            st.plotly_chart(fig_sun, use_container_width=True)

    # ── Fix vs. Variabel Donut ────────────────────────────────────────
    st.divider()
    st.write("#### 📐 Fixe vs. Variable Kostenstruktur")
    ratio_col1, ratio_col2 = st.columns(2)
    with ratio_col1:
        fig_ratio = go.Figure(go.Pie(
            labels=["Fixkosten", "Variable Kosten", "Sparbetrag"],
            values=[fix_ohne_spar, var_ohne_spar, gesamt_spar],
            hole=0.55,
            marker_colors=[COMPLEMENTARY_COLORS[0], COMPLEMENTARY_COLORS[1], COLOR_POSITIVE],
            textinfo="label+percent",
        ))
        fig_ratio.update_layout(
            title="Ausgabenstruktur Donut",
            annotations=[dict(text=fmt_eur(gesamt_ausgaben), x=0.5, y=0.5, showarrow=False, font_size=14)],
        )
        st.plotly_chart(fig_ratio, use_container_width=True)
    with ratio_col2:
        st.write("**Interpretation**")
        st.markdown(f"""
| Kennzahl | Wert | Bewertung |
|----------|------|-----------|
| Fixkostenquote | **{fix_quote:.1f} %** | {"✅ Im Ziel" if fix_quote <= 50 else "⚠️ Zu hoch"} |
| Variable Quote | **{var_quote:.1f} %** | {"✅ Im Ziel" if var_quote <= 30 else "⚠️ Zu hoch"} |
| Sparquote | **{sparquote:.1f} %** | {"✅ Im Ziel" if sparquote >= 20 else "⚠️ Zu niedrig"} |
| Burn-Rate | **{burn_rate_monate:.1f} Monate** | {"✅ Solide" if burn_rate_monate >= 3 else "⚠️ Zu gering"} |
        """)


# ──────────────────────────────────────────────────────────────────────
# TAB 2 – 💰 EINNAHMEN
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("💰 Einnahmen")]:
    einn_monat_fix = einn_fix_monat
    aktuelle_einnahmen = var_einnahmen_summe + einn_fix_summe_scaled

    if num_months > 1:
        hdr = (
            f"Gesamtzeitraum ({num_months} Mon.): {fmt_eur(aktuelle_einnahmen)} "
            f"| Monatliche Fixeinnahmen: {fmt_eur(einn_monat_fix)}"
        )
    else:
        hdr = f"Monatliche Einnahmen: {fmt_eur(aktuelle_einnahmen)}"
    st.subheader(hdr)

    col1, col2 = st.columns([1.5, 1])
    with col2:
        st.write("**Einnahmenübersicht (monatlich)**")
        if not df_fix_einnahmen.empty:
            f_pers = st.multiselect(
                "Person auswählen",
                sorted(df_fix_einnahmen["Person"].dropna().unique()),
                key="filter_einn_pers",
            )
            df_et = df_fix_einnahmen.copy()
            if f_pers:
                df_et = df_et[df_et["Person"].isin(f_pers)]
            st.data_editor(df_et, hide_index=True, use_container_width=True, key=f"einn_f_{mode}")
            st.info(f"**Monatl. Fixeinnahmen: {fmt_eur(df_et['Betrag'].sum())}**")
    with col1:
        if not df_fix_einnahmen.empty:
            fig_einn = px.pie(
                df_fix_einnahmen,
                values="Betrag",
                names="Person",
                title="Verteilung Fix-Einnahmen (monatlich)",
                height=500,
                color_discrete_sequence=COMPLEMENTARY_COLORS,
            )
            fig_einn.update_traces(textinfo="label+percent+value")
            st.plotly_chart(fig_einn, use_container_width=True)

    # Variable Einnahmen (falls vorhanden)
    if not filtered_einnahmen.empty:
        st.divider()
        st.write("#### 📋 Variable Einnahmen im Zeitraum")
        disp = filtered_einnahmen.copy()
        if "Datum" in disp.columns:
            disp["Datum"] = disp["Datum"].dt.strftime("%d.%m.%Y")
        st.dataframe(disp, hide_index=True, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────
# TAB 3 – 🏠 FIXKOSTEN
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("🏠 Fixkosten")]:
    fix_monat_summe_disp  = df_fixkosten["Betrag"].sum() if not df_fixkosten.empty else 0.0
    fix_zeitraum_summe_disp = fix_monat_summe_disp * num_months

    hdr = (
        f"Monatlich: {fmt_eur(fix_monat_summe_disp)} | "
        f"Zeitraum ({num_months} Mon.): {fmt_eur(fix_zeitraum_summe_disp)}"
        if num_months > 1
        else f"Monatliche Fixkosten: {fmt_eur(fix_monat_summe_disp)}"
    )
    st.subheader(hdr)

    col1, col2 = st.columns([1.5, 1])
    with col1:
        if not df_fixkosten.empty:
            fig_fix = px.sunburst(
                df_fixkosten,
                path=["Kategorie", "Unterkategorie"],
                values="Betrag",
                title="Fixkosten Verteilung (monatlich)",
                height=600,
                color_discrete_sequence=COMPLEMENTARY_COLORS,
            )
            fig_fix.update_traces(textinfo="label+percent entry")
            st.plotly_chart(fig_fix, use_container_width=True)
    with col2:
        st.write("**Fixkosten Tabelle (monatlich)**")
        if not df_fixkosten.empty:
            f_kat_fix = st.multiselect(
                "Kategorie", sorted(df_fixkosten["Kategorie"].dropna().unique()), key="filter_fix_kat"
            )
            f_sub_fix = st.multiselect(
                "Unterkategorie", sorted(df_fixkosten["Unterkategorie"].dropna().unique()), key="filter_fix_sub"
            )
            df_ft = df_fixkosten.copy()
            if f_kat_fix: df_ft = df_ft[df_ft["Kategorie"].isin(f_kat_fix)]
            if f_sub_fix: df_ft = df_ft[df_ft["Unterkategorie"].isin(f_sub_fix)]
            st.data_editor(df_ft, hide_index=True, use_container_width=True, key=f"fix_f_{mode}")
            st.info(f"**Monatliche Fixkosten: {fmt_eur(df_ft['Betrag'].sum())}**")

    # Horizontales Balkendiagramm für Fixkosten-Kategorien
    if not df_fixkosten.empty:
        st.divider()
        df_fix_bar = df_fixkosten.groupby("Kategorie")["Betrag"].sum().reset_index().sort_values("Betrag")
        fig_fix_bar = px.bar(
            df_fix_bar, x="Betrag", y="Kategorie", orientation="h",
            color="Kategorie", color_discrete_sequence=COMPLEMENTARY_COLORS,
            title="Fixkosten nach Kategorie (monatlich)",
            text_auto=".2f",
        )
        fig_fix_bar.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_fix_bar, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────
# TAB 4 – 🛒 VARIABLE AUSGABEN
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("🛒 Variabel")]:
    var_summe_disp = filtered_ausgaben["Betrag"].sum() if not filtered_ausgaben.empty else 0
    st.subheader(f"Variable Ausgaben im Zeitraum: {fmt_eur(var_summe_disp)}")

    if not filtered_ausgaben.empty:
        col1, col2 = st.columns([1.5, 1])
        with col1:
            # Kategorie-Filter für Chart
            f_kat_var_c = st.multiselect(
                "Kategorien (Chart-Filter)",
                sorted(filtered_ausgaben["Kategorie"].dropna().unique()),
                key="filter_var_kat_chart",
            )
            df_var_chart = (
                filtered_ausgaben[filtered_ausgaben["Kategorie"].isin(f_kat_var_c)]
                if f_kat_var_c else filtered_ausgaben
            )
            fig_var_sun = px.sunburst(
                df_var_chart,
                path=["Kategorie", "Unterkategorie"],
                values="Betrag",
                title="Struktur Variable Ausgaben",
                height=550,
                color_discrete_sequence=COMPLEMENTARY_COLORS,
            )
            fig_var_sun.update_traces(textinfo="label+percent entry")
            st.plotly_chart(fig_var_sun, use_container_width=True)

        with col2:
            st.write("**📋 Einzelbuchungen**")
            f_kat_var = st.multiselect(
                "Kategorie",
                sorted(filtered_ausgaben["Kategorie"].dropna().unique()),
                key="filter_var_kat",
            )
            f_sub_var = st.multiselect(
                "Unterkategorie",
                sorted(filtered_ausgaben["Unterkategorie"].dropna().unique()),
                key="filter_var_sub",
            )
            df_vt = filtered_ausgaben.copy()
            if f_kat_var: df_vt = df_vt[df_vt["Kategorie"].isin(f_kat_var)]
            if f_sub_var: df_vt = df_vt[df_vt["Unterkategorie"].isin(f_sub_var)]

            disp = df_vt.copy()
            if "Datum" in disp.columns:
                disp["Datum"] = disp["Datum"].dt.strftime("%d.%m.%Y")
            if "Betrag" in disp.columns:
                cols_show = [c for c in ["Datum", "Kategorie", "Unterkategorie", "Betrag"] if c in disp.columns]
                st.dataframe(disp[cols_show], hide_index=True, use_container_width=True)
            st.info(f"**Summe: {fmt_eur(df_vt['Betrag'].sum())}**")
    else:
        st.info("Keine Daten für diesen Zeitraum.")


# ──────────────────────────────────────────────────────────────────────
# TAB 5 – ⚖️ SALDO-ZEITSTRAHL & SANKEY-CASHFLOW
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("⚖️ Saldo & Cashflow")]:
    st.subheader("📅 Monatlicher Saldo-Zeitstrahl")

    if not df_ausgaben.empty or not df_einnahmen.empty:
        df_v, df_e = df_ausgaben.copy(), df_einnahmen.copy()
        for d in [df_v, df_e]:
            if "Datum" in d.columns and d["Datum"].notnull().any():
                d["Monat_Sort"] = d["Datum"].dt.strftime("%Y-%m")
            else:
                d["Monat_Sort"] = pd.Series(dtype="object")

        alle_monate_sort = sorted(
            set(df_v["Monat_Sort"].dropna().unique()) |
            set(df_e["Monat_Sort"].dropna().unique())
        )

        zeitstrahl = []
        for m in alle_monate_sort:
            v_m   = df_v[df_v["Monat_Sort"] == m]["Betrag"].sum()
            e_m   = df_e[df_e["Monat_Sort"] == m]["Betrag"].sum()
            fix_e = einn_fix_monat
            fix_v = fix_monat_summe
            saldo_m = (e_m + fix_e) - (v_m + fix_v)
            y, mn = m.split("-")
            zeitstrahl.append({
                "Monat": f"{MONATE_DE[mn]} {y}",
                "Saldo": saldo_m,
                "Einnahmen": e_m + fix_e,
                "Ausgaben":  v_m + fix_v,
                "Sort": m,
            })

        if zeitstrahl:
            df_zs = pd.DataFrame(zeitstrahl).sort_values("Sort")

            # Saldo-Bar
            fig_zs = px.bar(
                df_zs, x="Monat", y="Saldo", text_auto=".2f",
                color="Saldo", color_continuous_scale="RdYlGn",
                title="Monatliches Saldo (Einnahmen − Ausgaben)",
            )
            fig_zs.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_zs, use_container_width=True)

            # Einnahmen vs. Ausgaben Linie
            df_zs_long = df_zs.melt(
                id_vars=["Monat", "Sort"],
                value_vars=["Einnahmen", "Ausgaben"],
                var_name="Typ", value_name="Betrag",
            )
            fig_ev = px.line(
                df_zs_long, x="Monat", y="Betrag", color="Typ",
                markers=True, title="Einnahmen vs. Ausgaben im Zeitverlauf",
                color_discrete_map={"Einnahmen": COLOR_POSITIVE, "Ausgaben": COLOR_NEGATIVE},
            )
            fig_ev.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_ev, use_container_width=True)

    # ── SANKEY-DIAGRAMM ───────────────────────────────────────────────
    st.divider()
    st.write("### 🌊 Cashflow-Sankey-Diagramm")

    total_einn_fix = (
        (df_fix_einnahmen.groupby("Person")["Betrag"].sum() * num_months).reset_index()
        if not df_fix_einnahmen.empty
        else pd.DataFrame(columns=["Person", "Betrag"])
    )
    total_einn_var = (
        filtered_einnahmen.groupby("Person")["Betrag"].sum().reset_index()
        if not filtered_einnahmen.empty
        else pd.DataFrame(columns=["Person", "Betrag"])
    )
    df_ausg_all = pd.concat([
        df_fixkosten.copy().assign(Betrag=df_fixkosten["Betrag"] * num_months)
        if not df_fixkosten.empty else pd.DataFrame(),
        filtered_ausgaben if not filtered_ausgaben.empty else pd.DataFrame(),
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
                link_labels.append(fmt_eur(val))

        # Budget → Kategorien
        unique_kats  = sorted(df_ausg_all["Kategorie"].dropna().unique())
        kat_start    = len(label_list)
        label_list.extend(unique_kats)
        for i, k in enumerate(unique_kats):
            val = df_ausg_all[df_ausg_all["Kategorie"] == k]["Betrag"].sum()
            if val > 0:
                source.append(budget_idx); target.append(kat_start + i)
                value.append(round(val, 2))
                color_link.append(hex_to_rgba(COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)], 0.45))
                link_labels.append(fmt_eur(val))

        # Kategorien → Unterkategorien
        unique_subs = (
            df_ausg_all.groupby(["Kategorie", "Unterkategorie"])["Betrag"].sum().reset_index()
        )
        sub_start = len(label_list)
        label_list.extend(unique_subs["Unterkategorie"].tolist())
        for idx, row in unique_subs.iterrows():
            if row["Betrag"] > 0:
                k_i = kat_start + unique_kats.index(row["Kategorie"])
                source.append(k_i); target.append(sub_start + idx)
                value.append(round(row["Betrag"], 2))
                color_link.append(
                    hex_to_rgba(
                        COMPLEMENTARY_COLORS[unique_kats.index(row["Kategorie"]) % len(COMPLEMENTARY_COLORS)],
                        0.3,
                    )
                )
                link_labels.append(fmt_eur(row["Betrag"]))

        # Saldo-Link (falls positiv)
        gesamt_einn_s = sum(value[:len(einn_personen)])
        gesamt_ausg_s = df_ausg_all["Betrag"].sum()
        if gesamt_einn_s > gesamt_ausg_s:
            label_list.append("✅ Saldo / Ersparnis")
            saldo_idx = len(label_list) - 1
            saldo_val = gesamt_einn_s - gesamt_ausg_s
            source.append(budget_idx); target.append(saldo_idx)
            value.append(round(saldo_val, 2))
            color_link.append("rgba(40,167,69,0.5)")
            link_labels.append(fmt_eur(saldo_val))

        # Node-Farben
        node_colors = (
            [COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)] for i in range(len(einn_personen))] +
            [COLOR_ACCENT] +
            [COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)] for i in range(len(unique_kats))] +
            ["#adb5bd"] * len(unique_subs) +
            ([COLOR_POSITIVE] if gesamt_einn_s > gesamt_ausg_s else [])
        )

        fig_sankey = go.Figure(data=[go.Sankey(
            arrangement="snap",
            node=dict(
                pad=18, thickness=22,
                label=label_list,
                color=node_colors,
                hovertemplate="%{label}<br>Betrag: %{value:,.2f} €<extra></extra>",
            ),
            link=dict(
                source=source, target=target,
                value=value, color=color_link,
                customdata=link_labels,
                hovertemplate="Von: %{source.label}<br>Nach: %{target.label}<br>Betrag: %{customdata}<extra></extra>",
            ),
        )])
        fig_sankey.update_layout(
            title_text="💸 Cashflow: Einnahmen → Budget → Kategorien → Unterkategorien → Saldo",
            font_size=12, height=650,
        )
        st.plotly_chart(fig_sankey, use_container_width=True)
    else:
        st.info("Nicht genügend Daten für das Sankey-Diagramm.")


# ──────────────────────────────────────────────────────────────────────
# TAB 6 – 📈 TRENDS
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("📈 Trends")]:
    st.subheader("📈 Trend-Analyse")

    if not df_ausgaben.empty:
        trend_tabs = st.tabs(["📁 Kategorien", "🔍 Unterkategorien"])

        with trend_tabs[0]:
            all_kats = sorted(df_ausgaben["Kategorie"].dropna().unique())
            col_sel, col_plt = st.columns([1, 3])
            with col_sel:
                sel_kats = [k for k in all_kats if st.checkbox(k, value=True, key=f"t_kat_{k}_{mode}")]
            with col_plt:
                df_tk = df_ausgaben[df_ausgaben["Kategorie"].isin(sel_kats)].dropna(subset=["Datum"]).copy()
                if not df_tk.empty:
                    df_tk["Sort"]  = df_tk["Datum"].dt.strftime("%Y-%m")
                    df_tk["Monat"] = df_tk["Datum"].apply(datum_zu_monat)
                    res = (
                        df_tk.dropna(subset=["Monat"])
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
                    )

        with trend_tabs[1]:
            sel_subs = []
            col_sel, col_plt = st.columns([1, 3])
            with col_sel:
                for kat in sorted(df_ausgaben["Kategorie"].dropna().unique()):
                    subs = sorted(df_ausgaben[df_ausgaben["Kategorie"] == kat]["Unterkategorie"].dropna().unique())
                    mk = f"mstr_{kat}_{mode}"
                    if mk not in st.session_state: st.session_state[mk] = True
                    def tg(k=kat, m=mk, s=subs):
                        for x in s:
                            st.session_state[f"sb_{k}_{x}_{mode}"] = st.session_state[m]
                    c_on = st.checkbox(f"📁 **{kat}**", key=mk, on_change=tg)
                    for s in subs:
                        sk = f"sb_{kat}_{s}_{mode}"
                        if sk not in st.session_state: st.session_state[sk] = c_on
                        if st.checkbox(f"   └ {s}", key=sk):
                            sel_subs.append(s)
            with col_plt:
                df_ts = df_ausgaben[df_ausgaben["Unterkategorie"].isin(sel_subs)].dropna(subset=["Datum"]).copy()
                if not df_ts.empty:
                    df_ts["Sort"]  = df_ts["Datum"].dt.strftime("%Y-%m")
                    df_ts["Monat"] = df_ts["Datum"].apply(datum_zu_monat)
                    res = (
                        df_ts.dropna(subset=["Monat"])
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
                    )
    else:
        st.info("Keine Ausgabendaten für Trend-Analyse verfügbar.")


# ──────────────────────────────────────────────────────────────────────
# TAB 7 – 📐 KENNZAHLEN (Simon & Alisia IDENTISCH)
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("📐 Kennzahlen")]:
    st.subheader("📐 Kennzahlen & Sparquote")

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
            gauge={
                "axis": {"range": [0, 60]},
                "bar": {"color": COLOR_ACCENT},
                "steps": [
                    {"range": [0, 10],  "color": "#dc3545"},
                    {"range": [10, 20], "color": "#ffc107"},
                    {"range": [20, 60], "color": "#28a745"},
                ],
                "threshold": {
                    "line": {"color": "#003f5c", "width": 4},
                    "thickness": 0.75, "value": 20,
                },
            },
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Burn-Rate Erklärung
        st.divider()
        bc1, bc2 = st.columns(2)
        with bc1:
            st.metric(
                "🔥 Burn-Rate (Monate)",
                f"{burn_rate_monate:.1f}",
                help="Wie viele Monate reichen die Ersparnisse im Zeitraum, falls Einnahmen wegfallen?",
            )
            if burn_rate_monate < 3:
                st.error("⚠️ Notgroschen zu gering – Ziel: ≥ 3 Monate Ausgaben als Reserve.")
            elif burn_rate_monate < 6:
                st.warning("📊 Solide – Empfehlung: 6 Monate anstreben.")
            else:
                st.success("✅ Exzellent – Notgroschen über 6 Monate.")
        with bc2:
            monatl_ausgaben_calc = gesamt_ausgaben / num_months if num_months > 0 else 0
            st.metric("⚡ Monatl. Ausgaben (Ø)", fmt_eur(monatl_ausgaben_calc))
            st.metric("🐖 Monatl. Sparbetrag (Ø)", fmt_eur(gesamt_spar / num_months if num_months > 0 else 0))

        # Sparquote Zeitverlauf
        st.divider()
        st.write("### 📈 Entwicklung der Sparquote")
        df_v_all = df_ausgaben.copy()
        df_e_all = df_einnahmen.copy()
        for d in [df_v_all, df_e_all]:
            if "Datum" in d.columns:
                d["Sort"] = d["Datum"].dt.strftime("%Y-%m")

        monate_kenn = sorted(
            set(df_v_all["Sort"].dropna().unique()) |
            set(df_e_all["Sort"].dropna().unique())
        )
        trend_data = []
        for m in monate_kenn:
            e_m = df_e_all[df_e_all["Sort"] == m]["Betrag"].sum() + einn_fix_monat
            spar_fix_m = (
                df_fixkosten[df_fixkosten["Unterkategorie"] == "Sparen"]["Betrag"].sum()
                if not df_fixkosten.empty else 0
            )
            spar_var_m = (
                df_v_all[
                    (df_v_all["Sort"] == m) & (df_v_all["Unterkategorie"] == "Sparen")
                ]["Betrag"].sum()
            )
            s_m = spar_fix_m + spar_var_m
            q   = (s_m / e_m * 100) if e_m > 0 else 0
            y, mn = m.split("-")
            trend_data.append({"Monat": f"{MONATE_DE[mn]} {y}", "Sparquote": q, "Sort": m})

        if trend_data:
            df_trend = pd.DataFrame(trend_data).sort_values("Sort")
            fig_t = px.area(
                df_trend, x="Monat", y="Sparquote", markers=True,
                title="Sparquote im Zeitverlauf (%)",
                color_discrete_sequence=[COLOR_ACCENT],
            )
            fig_t.add_hline(
                y=20, line_dash="dash", line_color=COLOR_WARN,
                annotation_text="Ziel: 20 %", annotation_position="top right",
            )
            fig_t.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_t, use_container_width=True)
    else:
        st.warning("Keine Einnahmen gefunden.")


# ──────────────────────────────────────────────────────────────────────
# TAB 8 – 🤝 LASTENVERTEILUNG (nur "Unsere Finanzen")
# ──────────────────────────────────────────────────────────────────────
if mode == "unser":
    with tabs[tab_idx("🤝 Lastenverteilung")]:
        st.subheader("🤝 Lastenverteilung & Fairness-Modell")

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
                einn_pro_person = einn_pro_person.merge(var_per, on="Person", how="left").fillna(0)
                einn_pro_person["Einnahmen"] += einn_pro_person["Einnahmen_var"]
                einn_pro_person.drop(columns=["Einnahmen_var"], inplace=True)
                total_einn_all = einn_pro_person["Einnahmen"].sum()

            einn_pro_person["Anteil_Einn_%"] = (
                einn_pro_person["Einnahmen"] / total_einn_all * 100
            ).round(1)

            # ── Ausgaben pro Person (falls Spalte vorhanden) ──────────
            hat_person_spalte = (
                not df_fixkosten.empty and "Person" in df_fixkosten.columns
            ) or (
                not filtered_ausgaben.empty and "Person" in filtered_ausgaben.columns
            )

            st.write("#### 💰 Einnahmen-Beitragsverteilung")
            col_e1, col_e2 = st.columns([1, 1])
            with col_e1:
                fig_einn_p = px.pie(
                    einn_pro_person, values="Einnahmen", names="Person",
                    title="Einnahmenverteilung nach Person",
                    color_discrete_sequence=COMPLEMENTARY_COLORS,
                    hole=0.4,
                )
                fig_einn_p.update_traces(textinfo="label+percent+value")
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
                    if abw <= 5:
                        st.success(f"✅ Sehr ausgewogen — Abweichung: {abw:.1f} pp")
                    elif abw <= 15:
                        st.warning(f"⚠️ Leicht ungleich — Abweichung: {abw:.1f} pp")
                    else:
                        st.error(f"❌ Deutliche Ungleichverteilung — Abweichung: {abw:.1f} pp")

            # ── Fairness-Modell: Ausgaben relativ zum Einkommen ──────
            st.divider()
            st.write("#### 🎯 Proportionales Fairness-Modell")
            st.info(
                "**Idee:** Jede Person sollte Ausgaben proportional zu ihrem Einkommensanteil tragen. "
                "Das Modell berechnet, wie viel jede Person bei fairer Aufteilung zahlen würde."
            )

            if total_einn_all > 0 and gesamt_ausgaben > 0:
                fairness_rows = []
                for _, row in einn_pro_person.iterrows():
                    anteil = row["Einnahmen"] / total_einn_all
                    fair_beitrag = anteil * gesamt_ausgaben
                    fairness_rows.append({
                        "Person": row["Person"],
                        "Einkommensanteil": f"{anteil * 100:.1f} %",
                        "Fairer Ausgabenbeitrag": fmt_eur(fair_beitrag),
                        "Tatsächliche Einnahmen": fmt_eur(row["Einnahmen"]),
                    })
                df_fair = pd.DataFrame(fairness_rows)
                st.dataframe(df_fair, hide_index=True, use_container_width=True)

                # Gauge-Chart für Fairness
                if len(einn_pro_person) == 2:
                    anteil_fair = einn_pro_person["Anteil_Einn_%"].tolist()
                    fig_fair = go.Figure(go.Bar(
                        x=einn_pro_person["Person"].tolist(),
                        y=anteil_fair,
                        marker_color=COMPLEMENTARY_COLORS[:2],
                        text=[f"{v:.1f} %" for v in anteil_fair],
                        textposition="outside",
                    ))
                    fig_fair.add_hline(y=50, line_dash="dash", line_color=COLOR_NEUTRAL,
                                       annotation_text="50/50-Linie")
                    fig_fair.update_layout(
                        title="Einkommensanteile im Vergleich",
                        yaxis_range=[0, 100],
                        yaxis_title="Anteil (%)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig_fair, use_container_width=True)
        else:
            st.info("Keine Einnahmen-Daten mit Personenzuordnung verfügbar.")


# ──────────────────────────────────────────────────────────────────────
# TAB 9 – 💡 OPTIMIERUNGSPOTENZIAL
# ──────────────────────────────────────────────────────────────────────
with tabs[tab_idx("💡 Optimierungspotenzial")]:
    st.subheader("💡 Optimierungspotenzial & Automatische Insights")

    # ── Handlungsempfehlungen basierend auf KPIs ─────────────────────
    st.write("### 🎯 Automatische Handlungsempfehlungen")
    empfehlungen = []

    if fix_quote > 60:
        empfehlungen.append({
            "Priorität": "🔴 Hoch",
            "Kategorie": "Fixkosten",
            "Befund": f"Fixkostenquote bei {fix_quote:.1f} % (Ziel: ≤ 50 %)",
            "Empfehlung": "Verträge und Abonnements kritisch prüfen. Verhandeln oder kündigen Sie laufende Kosten.",
        })
    elif fix_quote > 50:
        empfehlungen.append({
            "Priorität": "🟡 Mittel",
            "Kategorie": "Fixkosten",
            "Befund": f"Fixkostenquote bei {fix_quote:.1f} % — leicht über dem Ziel",
            "Empfehlung": "Kleinere Einsparungen bei fixen Kosten anstreben.",
        })

    if sparquote < 10:
        empfehlungen.append({
            "Priorität": "🔴 Hoch",
            "Kategorie": "Sparen",
            "Befund": f"Sparquote bei {sparquote:.1f} % — kritisch niedrig",
            "Empfehlung": "Sofortiger Aufbau eines automatischen Sparplans empfohlen (Ziel: ≥ 20 %).",
        })
    elif sparquote < 20:
        empfehlungen.append({
            "Priorität": "🟡 Mittel",
            "Kategorie": "Sparen",
            "Befund": f"Sparquote bei {sparquote:.1f} % (Ziel: 20 %)",
            "Empfehlung": "Sparrate schrittweise erhöhen. 'Pay yourself first'-Prinzip anwenden.",
        })
    else:
        empfehlungen.append({
            "Priorität": "🟢 Gut",
            "Kategorie": "Sparen",
            "Befund": f"Sparquote bei {sparquote:.1f} % — Ziel erreicht",
            "Empfehlung": "Weiter so! Prüfen Sie Investitionsmöglichkeiten für den Überschuss.",
        })

    if burn_rate_monate < 3:
        empfehlungen.append({
            "Priorität": "🔴 Hoch",
            "Kategorie": "Notgroschen",
            "Befund": f"Burn-Rate nur {burn_rate_monate:.1f} Monate",
            "Empfehlung": "Aufbau eines Notgroschens von 3–6 Monatsnettolöhnen hat oberste Priorität.",
        })

    if var_quote > 35:
        empfehlungen.append({
            "Priorität": "🟡 Mittel",
            "Kategorie": "Variable Ausgaben",
            "Befund": f"Variable Ausgabenquote bei {var_quote:.1f} % (Ziel: ≤ 30 %)",
            "Empfehlung": "Konsumausgaben analysieren. Kategorien mit Einsparpotenzial gezielt reduzieren.",
        })

    if gesamt_einnahmen > 0 and saldo < 0:
        empfehlungen.append({
            "Priorität": "🔴 Kritisch",
            "Kategorie": "Saldo",
            "Befund": f"Negativer Saldo: {fmt_eur(saldo)}",
            "Empfehlung": "Ausgaben sofort auf den Prüfstand stellen. Einnahmen erhöhen oder Kosten stark senken.",
        })

    if empfehlungen:
        df_emp = pd.DataFrame(empfehlungen)
        st.dataframe(df_emp, hide_index=True, use_container_width=True)
    else:
        st.success("✅ Alle Kennzahlen im grünen Bereich. Hervorragende Finanzführung!")

    # ── Kategorien mit >15 % Anstieg zum Vormonat ────────────────────
    st.divider()
    st.write("### 📊 Ausgaben-Alarm: Kategorien mit ≥ 15 % Anstieg zum Vormonat")

    if not df_ausgaben.empty and "Datum" in df_ausgaben.columns:
        df_alarm = df_ausgaben.copy()
        df_alarm["Sort"] = df_alarm["Datum"].dt.strftime("%Y-%m")
        df_alarm = df_alarm.dropna(subset=["Sort"])

        monate_alarm = sorted(df_alarm["Sort"].dropna().unique())
        if len(monate_alarm) >= 2:
            cur_m  = monate_alarm[-1]
            prev_m = monate_alarm[-2]

            cur_kat  = df_alarm[df_alarm["Sort"] == cur_m].groupby("Kategorie")["Betrag"].sum()
            prev_kat = df_alarm[df_alarm["Sort"] == prev_m].groupby("Kategorie")["Betrag"].sum()

            alarm_rows = []
            for kat in cur_kat.index:
                cur_val  = cur_kat[kat]
                prev_val = prev_kat.get(kat, 0)
                if prev_val > 0:
                    pct_change = (cur_val - prev_val) / prev_val * 100
                    if pct_change >= 15:
                        alarm_rows.append({
                            "Kategorie": kat,
                            "Vormonat": fmt_eur(prev_val),
                            "Aktuell": fmt_eur(cur_val),
                            "Veränderung": f"+{pct_change:.1f} %",
                            "Status": "🔴 Alarm" if pct_change >= 30 else "🟡 Warnung",
                        })

            if alarm_rows:
                df_a = pd.DataFrame(alarm_rows).sort_values("Veränderung", ascending=False)
                st.dataframe(df_a, hide_index=True, use_container_width=True)

                # Visualisierung: Alarmkategorien
                cur_m_label  = datum_zu_monat(datetime.strptime(f"01-{cur_m}", "%d-%Y-%m")) or cur_m
                prev_m_label = datum_zu_monat(datetime.strptime(f"01-{prev_m}", "%d-%Y-%m")) or prev_m

                alarm_kats = [r["Kategorie"] for r in alarm_rows]
                df_comp = pd.DataFrame({
                    "Kategorie": alarm_kats * 2,
                    "Betrag": (
                        [cur_kat[k] for k in alarm_kats] +
                        [prev_kat.get(k, 0) for k in alarm_kats]
                    ),
                    "Monat": [cur_m_label] * len(alarm_kats) + [prev_m_label] * len(alarm_kats),
                })
                fig_alarm = px.bar(
                    df_comp, x="Kategorie", y="Betrag", color="Monat",
                    barmode="group",
                    color_discrete_sequence=[COLOR_NEGATIVE, COLOR_NEUTRAL],
                    title="Vergleich: Aktuell vs. Vormonat (Alarmkategorien)",
                    text_auto=".2f",
                )
                fig_alarm.update_layout(plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_alarm, use_container_width=True)
            else:
                st.success(f"✅ Keine Kategorie mit ≥ 15 % Anstieg gegenüber dem Vormonat ({prev_m}).")
        else:
            st.info("Mindestens 2 Monate Daten für Vormonatsvergleich erforderlich.")
    else:
        st.info("Keine Ausgabendaten für Alarm-Analyse verfügbar.")

    # ── Unterkategorien-Detailvergleich ──────────────────────────────
    if not df_ausgaben.empty and "Datum" in df_ausgaben.columns:
        st.divider()
        st.write("### 🔍 Detailvergleich auf Unterkategorie-Ebene")
        df_sub_alarm = df_ausgaben.copy()
        df_sub_alarm["Sort"] = df_sub_alarm["Datum"].dt.strftime("%Y-%m")
        df_sub_alarm = df_sub_alarm.dropna(subset=["Sort"])
        monate_sa = sorted(df_sub_alarm["Sort"].unique())

        if len(monate_sa) >= 2:
            cur_m2  = monate_sa[-1]
            prev_m2 = monate_sa[-2]
            cur_sub  = df_sub_alarm[df_sub_alarm["Sort"] == cur_m2].groupby(["Kategorie", "Unterkategorie"])["Betrag"].sum()
            prev_sub = df_sub_alarm[df_sub_alarm["Sort"] == prev_m2].groupby(["Kategorie", "Unterkategorie"])["Betrag"].sum()

            sub_rows = []
            for idx in cur_sub.index:
                c_val = cur_sub[idx]
                p_val = prev_sub.get(idx, 0)
                if p_val > 0:
                    pct = (c_val - p_val) / p_val * 100
                    sub_rows.append({
                        "Kategorie": idx[0],
                        "Unterkategorie": idx[1],
                        "Vormonat": fmt_eur(p_val),
                        "Aktuell": fmt_eur(c_val),
                        "Δ %": f"{pct:+.1f} %",
                        "Trend": "📈" if pct > 0 else "📉",
                    })

            if sub_rows:
                df_sub_cmp = pd.DataFrame(sub_rows).sort_values("Δ %", ascending=False)
                st.dataframe(df_sub_cmp, hide_index=True, use_container_width=True)
