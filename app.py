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

# ── Design-System (High-End Private Banking) ──────────────────────────
COMPLEMENTARY_COLORS = [
    "#1a3a5c", "#c9a84c", "#2e5984", "#e8c56a",
    "#4a7ba7", "#8b6914", "#6b9ec4", "#a07820",
]
COLOR_POSITIVE  = "#2d7a4f"
COLOR_NEGATIVE  = "#8b2635"
COLOR_NEUTRAL   = "#5a6475"
COLOR_ACCENT    = "#1a3a5c"
COLOR_WARN      = "#c9a84c"

# ── High-End Private Banking CSS Injection ────────────────────────────
_PRIVATE_BANK_CSS = """
<style>
/* ═══════════════════════════════════════════════════
   TYPOGRAPHY — Cormorant Garamond + DM Mono
═══════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:ital,wght@0,200;0,300;0,400;0,500;1,300&family=DM+Mono:wght@300;400&display=swap');

/* ═══════════════════════════════════════════════════
   CSS VARIABLES — Privatbank Colour Palette
═══════════════════════════════════════════════════ */
:root {
  --pb-navy:        #0d1f35;
  --pb-navy-mid:    #132944;
  --pb-navy-light:  #1a3a5c;
  --pb-navy-muted:  #243e5a;
  --pb-gold:        #c9a84c;
  --pb-gold-light:  #e8c56a;
  --pb-gold-dim:    #8b6914;
  --pb-cream:       #f5f0e8;
  --pb-cream-dark:  #ede6d6;
  --pb-slate:       #4a5568;
  --pb-slate-light: #718096;
  --pb-green:       #2d7a4f;
  --pb-red:         #8b2635;
  --pb-white:       #fafaf8;
  --pb-border:      rgba(201, 168, 76, 0.25);
  --pb-border-soft: rgba(201, 168, 76, 0.12);
  --pb-shadow:      0 4px 24px rgba(13, 31, 53, 0.18), 0 1px 4px rgba(13, 31, 53, 0.10);
  --pb-shadow-sm:   0 2px 12px rgba(13, 31, 53, 0.12);
  --pb-radius:      6px;
  --pb-radius-lg:   10px;
}

/* ═══════════════════════════════════════════════════
   GLOBAL — Base Reset & Typography
═══════════════════════════════════════════════════ */
html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 300;
  letter-spacing: 0.01em;
}

.stApp {
  background: linear-gradient(160deg, #0d1822 0%, #0f1f33 40%, #0d1a2e 100%) !important;
  min-height: 100vh;
}

/* Main content area */
.main .block-container {
  padding: 2rem 2.5rem 3rem 2.5rem !important;
  max-width: 1400px !important;
}

/* ═══════════════════════════════════════════════════
   SIDEBAR — Matrix-Helix with SVG Background
═══════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: linear-gradient(175deg, #07121e 0%, #0d1f35 35%, #0a1a2e 70%, #081320 100%) !important;
  border-right: 1px solid var(--pb-border) !important;
  position: relative;
  overflow: hidden;
}

/* Matrix-Helix SVG Pattern via pseudo-element simulation via background-image */
[data-testid="stSidebar"]::before {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  pointer-events: none;
  z-index: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='280' height='900' viewBox='0 0 280 900'%3E%3Cdefs%3E%3Cstyle%3E.helix%7Bfill:none;stroke-width:0.8%7D%3C/style%3E%3C/defs%3E%3Cg opacity='0.07'%3E%3Cpath class='helix' stroke='%23c9a84c' d='M40,0 Q140,45 240,90 Q140,135 40,180 Q140,225 240,270 Q140,315 40,360 Q140,405 240,450 Q140,495 40,540 Q140,585 240,630 Q140,675 40,720 Q140,765 240,810 Q140,855 40,900'/%3E%3Cpath class='helix' stroke='%234a7ba7' d='M240,0 Q140,45 40,90 Q140,135 240,180 Q140,225 40,270 Q140,315 240,360 Q140,405 40,450 Q140,495 240,540 Q140,585 40,630 Q140,675 240,720 Q140,765 40,810 Q140,855 240,900'/%3E%3C/g%3E%3Cg opacity='0.05'%3E%3Cpath class='helix' stroke='%23c9a84c' stroke-width='0.4' d='M70,0 Q140,30 210,60 Q140,90 70,120 Q140,150 210,180 Q140,210 70,240 Q140,270 210,300 Q140,330 70,360 Q140,390 210,420 Q140,450 70,480 Q140,510 210,540 Q140,570 70,600 Q140,630 210,660 Q140,690 70,720 Q140,750 210,780 Q140,810 70,840 Q140,870 210,900'/%3E%3Cpath class='helix' stroke='%234a7ba7' stroke-width='0.4' d='M210,0 Q140,30 70,60 Q140,90 210,120 Q140,150 70,180 Q140,210 210,240 Q140,270 70,300 Q140,330 210,360 Q140,390 70,420 Q140,450 210,480 Q140,510 70,540 Q140,570 210,600 Q140,630 70,660 Q140,690 210,720 Q140,750 70,780 Q140,810 210,840 Q140,870 70,900'/%3E%3C/g%3E%3Cg opacity='0.04'%3E%3Ccircle cx='140' cy='90' r='2' fill='%23c9a84c'/%3E%3Ccircle cx='140' cy='180' r='1.5' fill='%23c9a84c'/%3E%3Ccircle cx='140' cy='270' r='2' fill='%234a7ba7'/%3E%3Ccircle cx='140' cy='360' r='1.5' fill='%23c9a84c'/%3E%3Ccircle cx='140' cy='450' r='2' fill='%234a7ba7'/%3E%3Ccircle cx='140' cy='540' r='1.5' fill='%23c9a84c'/%3E%3Ccircle cx='140' cy='630' r='2' fill='%23c9a84c'/%3E%3Ccircle cx='140' cy='720' r='1.5' fill='%234a7ba7'/%3E%3Ccircle cx='140' cy='810' r='2' fill='%23c9a84c'/%3E%3Ccircle cx='40' cy='90' r='1.2' fill='%23c9a84c' opacity='0.6'/%3E%3Ccircle cx='240' cy='90' r='1.2' fill='%234a7ba7' opacity='0.6'/%3E%3Ccircle cx='40' cy='270' r='1.2' fill='%234a7ba7' opacity='0.6'/%3E%3Ccircle cx='240' cy='270' r='1.2' fill='%23c9a84c' opacity='0.6'/%3E%3Ccircle cx='40' cy='450' r='1.2' fill='%23c9a84c' opacity='0.6'/%3E%3Ccircle cx='240' cy='450' r='1.2' fill='%234a7ba7' opacity='0.6'/%3E%3Ccircle cx='40' cy='630' r='1.2' fill='%234a7ba7' opacity='0.6'/%3E%3Ccircle cx='240' cy='630' r='1.2' fill='%23c9a84c' opacity='0.6'/%3E%3Ccircle cx='40' cy='810' r='1.2' fill='%23c9a84c' opacity='0.6'/%3E%3C/g%3E%3Cg opacity='0.03' stroke='%23c9a84c' stroke-width='0.3' fill='none'%3E%3Cline x1='40' y1='90' x2='240' y2='90'/%3E%3Cline x1='40' y1='180' x2='240' y2='180'/%3E%3Cline x1='40' y1='270' x2='240' y2='270'/%3E%3Cline x1='40' y1='360' x2='240' y2='360'/%3E%3Cline x1='40' y1='450' x2='240' y2='450'/%3E%3Cline x1='40' y1='540' x2='240' y2='540'/%3E%3Cline x1='40' y1='630' x2='240' y2='630'/%3E%3Cline x1='40' y1='720' x2='240' y2='720'/%3E%3Cline x1='40' y1='810' x2='240' y2='810'/%3E%3C/g%3E%3C/svg%3E");
  background-repeat: repeat-y;
  background-size: 280px auto;
  opacity: 1;
}

[data-testid="stSidebar"] > div {
  position: relative;
  z-index: 1;
}

[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: var(--pb-cream) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 300 !important;
  letter-spacing: 0.04em !important;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  font-family: 'Cormorant Garamond', serif !important;
  font-weight: 400 !important;
  font-size: 1.1rem !important;
  color: var(--pb-gold-light) !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase;
  border-bottom: 1px solid var(--pb-border) !important;
  padding-bottom: 0.5rem !important;
  margin-bottom: 0.8rem !important;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
  border-color: var(--pb-border) !important;
  margin: 1rem 0 !important;
}

/* Sidebar info/success boxes */
[data-testid="stSidebar"] .stAlert {
  background: rgba(201, 168, 76, 0.08) !important;
  border: 1px solid var(--pb-border) !important;
  border-radius: var(--pb-radius) !important;
  color: var(--pb-cream) !important;
}

/* Sidebar caption */
[data-testid="stSidebar"] .stCaption {
  color: var(--pb-slate-light) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
}

/* Sidebar selectbox */
[data-testid="stSidebar"] .stSelectbox > div > div {
  background: rgba(26, 58, 92, 0.6) !important;
  border: 1px solid var(--pb-border) !important;
  border-radius: var(--pb-radius) !important;
  color: var(--pb-cream) !important;
  font-weight: 300 !important;
}

/* ═══════════════════════════════════════════════════
   SIDEBAR BUTTONS — Dashboard Navigation
═══════════════════════════════════════════════════ */
[data-testid="stSidebar"] .stButton > button {
  background: linear-gradient(135deg, rgba(26, 58, 92, 0.7) 0%, rgba(13, 31, 53, 0.8) 100%) !important;
  border: 1px solid var(--pb-border) !important;
  border-radius: var(--pb-radius) !important;
  color: var(--pb-cream) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 300 !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  padding: 0.55rem 1rem !important;
  transition: all 0.25s ease !important;
  width: 100% !important;
  text-align: left !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
  background: linear-gradient(135deg, rgba(201, 168, 76, 0.2) 0%, rgba(26, 58, 92, 0.9) 100%) !important;
  border-color: var(--pb-gold) !important;
  color: var(--pb-gold-light) !important;
  box-shadow: 0 0 16px rgba(201, 168, 76, 0.15) !important;
  transform: translateX(2px) !important;
}

/* ═══════════════════════════════════════════════════
   MAIN TITLE
═══════════════════════════════════════════════════ */
h1 {
  font-family: 'Cormorant Garamond', serif !important;
  font-weight: 400 !important;
  font-size: 2.4rem !important;
  color: var(--pb-cream) !important;
  letter-spacing: 0.05em !important;
  line-height: 1.2 !important;
}

h1::after {
  content: "";
  display: block;
  width: 80px;
  height: 1px;
  background: linear-gradient(90deg, var(--pb-gold), transparent);
  margin-top: 0.5rem;
}

h2, h3 {
  font-family: 'Cormorant Garamond', serif !important;
  font-weight: 400 !important;
  color: var(--pb-cream) !important;
  letter-spacing: 0.03em !important;
}

h4, h5, h6 {
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 400 !important;
  color: var(--pb-cream-dark) !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  font-size: 0.78rem !important;
}

p, li, label {
  color: rgba(245, 240, 232, 0.82) !important;
  font-weight: 300 !important;
  line-height: 1.7 !important;
}

/* ═══════════════════════════════════════════════════
   KPI METRIC CARDS
═══════════════════════════════════════════════════ */
[data-testid="stMetric"] {
  background: linear-gradient(145deg, rgba(26, 58, 92, 0.55) 0%, rgba(13, 31, 53, 0.70) 100%) !important;
  border: 1px solid var(--pb-border) !important;
  border-radius: var(--pb-radius-lg) !important;
  padding: 1.2rem 1.4rem !important;
  box-shadow: var(--pb-shadow-sm) !important;
  backdrop-filter: blur(12px) !important;
  transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
  position: relative !important;
  overflow: hidden !important;
}

[data-testid="stMetric"]::before {
  content: "";
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: linear-gradient(180deg, var(--pb-gold), transparent);
  border-radius: 3px 0 0 3px;
}

[data-testid="stMetric"]:hover {
  border-color: rgba(201, 168, 76, 0.4) !important;
  box-shadow: var(--pb-shadow) !important;
}

[data-testid="stMetricLabel"] {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.68rem !important;
  font-weight: 400 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  color: var(--pb-gold) !important;
  opacity: 0.85 !important;
}

[data-testid="stMetricValue"] {
  font-family: 'DM Mono', monospace !important;
  font-size: 1.55rem !important;
  font-weight: 300 !important;
  color: var(--pb-cream) !important;
  letter-spacing: -0.01em !important;
  line-height: 1.3 !important;
}

[data-testid="stMetricDelta"] {
  font-family: 'DM Mono', monospace !important;
  font-size: 0.75rem !important;
  font-weight: 300 !important;
  letter-spacing: 0.02em !important;
}

/* ═══════════════════════════════════════════════════
   TABS — Navigation
═══════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(13, 31, 53, 0.6) !important;
  border-bottom: 1px solid var(--pb-border) !important;
  gap: 0 !important;
  padding: 0 0.5rem !important;
  border-radius: var(--pb-radius) var(--pb-radius) 0 0 !important;
}

.stTabs [data-baseweb="tab"] {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 0.73rem !important;
  font-weight: 400 !important;
  letter-spacing: 0.07em !important;
  text-transform: uppercase !important;
  color: var(--pb-slate-light) !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  padding: 0.75rem 1rem !important;
  transition: all 0.2s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
  color: var(--pb-gold-light) !important;
  background: rgba(201, 168, 76, 0.05) !important;
}

.stTabs [aria-selected="true"] {
  color: var(--pb-gold-light) !important;
  border-bottom: 2px solid var(--pb-gold) !important;
  background: rgba(201, 168, 76, 0.08) !important;
}

.stTabs [data-baseweb="tab-panel"] {
  background: rgba(13, 31, 53, 0.35) !important;
  border: 1px solid var(--pb-border-soft) !important;
  border-top: none !important;
  border-radius: 0 0 var(--pb-radius) var(--pb-radius) !important;
  padding: 1.5rem !important;
  backdrop-filter: blur(8px) !important;
}

/* ═══════════════════════════════════════════════════
   DATAFRAMES & TABLES
═══════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  border-radius: var(--pb-radius-lg) !important;
  overflow: hidden !important;
  border: 1px solid var(--pb-border) !important;
  box-shadow: var(--pb-shadow-sm) !important;
}

[data-testid="stDataFrame"] table {
  background: rgba(13, 31, 53, 0.6) !important;
}

[data-testid="stDataFrame"] thead th {
  background: rgba(26, 58, 92, 0.8) !important;
  color: var(--pb-gold) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 400 !important;
  font-size: 0.68rem !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  border-bottom: 1px solid var(--pb-border) !important;
  padding: 0.7rem 1rem !important;
}

[data-testid="stDataFrame"] tbody td {
  color: var(--pb-cream) !important;
  font-family: 'DM Mono', monospace !important;
  font-weight: 300 !important;
  font-size: 0.82rem !important;
  border-bottom: 1px solid rgba(201, 168, 76, 0.06) !important;
  padding: 0.55rem 1rem !important;
}

[data-testid="stDataFrame"] tbody tr:hover td {
  background: rgba(201, 168, 76, 0.06) !important;
}

/* ═══════════════════════════════════════════════════
   ALERT / INFO BOXES
═══════════════════════════════════════════════════ */
.stAlert {
  border-radius: var(--pb-radius) !important;
  border-left: 3px solid var(--pb-gold) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 300 !important;
  font-size: 0.85rem !important;
}

.stAlert[data-baseweb="notification"] {
  background: rgba(26, 58, 92, 0.5) !important;
  border: 1px solid var(--pb-border) !important;
  color: var(--pb-cream) !important;
}

/* Success */
.element-container .stSuccess {
  background: rgba(45, 122, 79, 0.15) !important;
  border-left-color: var(--pb-green) !important;
  color: rgba(200, 235, 215, 0.9) !important;
}

/* Warning */
.element-container .stWarning {
  background: rgba(201, 168, 76, 0.12) !important;
  border-left-color: var(--pb-gold) !important;
  color: rgba(245, 235, 200, 0.9) !important;
}

/* Error */
.element-container .stError {
  background: rgba(139, 38, 53, 0.15) !important;
  border-left-color: var(--pb-red) !important;
  color: rgba(240, 200, 205, 0.9) !important;
}

/* Info */
.element-container .stInfo {
  background: rgba(26, 58, 92, 0.45) !important;
  border-left-color: rgba(74, 123, 167, 0.8) !important;
  color: rgba(200, 220, 245, 0.9) !important;
}

/* ═══════════════════════════════════════════════════
   SLIDERS
═══════════════════════════════════════════════════ */
.stSlider [data-baseweb="slider"] {
  padding: 0.5rem 0 !important;
}

.stSlider [data-testid="stTickBar"] {
  color: var(--pb-slate-light) !important;
  font-size: 0.68rem !important;
}

/* ═══════════════════════════════════════════════════
   MULTISELECT & SELECTBOX
═══════════════════════════════════════════════════ */
.stMultiSelect [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] > div {
  background: rgba(26, 58, 92, 0.5) !important;
  border: 1px solid var(--pb-border) !important;
  border-radius: var(--pb-radius) !important;
  color: var(--pb-cream) !important;
  font-weight: 300 !important;
}

.stMultiSelect [data-baseweb="tag"] {
  background: rgba(201, 168, 76, 0.2) !important;
  border: 1px solid var(--pb-gold-dim) !important;
  color: var(--pb-gold-light) !important;
  border-radius: 4px !important;
  font-size: 0.75rem !important;
  font-weight: 400 !important;
}

/* ═══════════════════════════════════════════════════
   CHECKBOXES
═══════════════════════════════════════════════════ */
.stCheckbox label {
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 300 !important;
  font-size: 0.82rem !important;
  color: var(--pb-cream) !important;
  letter-spacing: 0.02em !important;
}

/* ═══════════════════════════════════════════════════
   DATE INPUT
═══════════════════════════════════════════════════ */
.stDateInput input {
  background: rgba(26, 58, 92, 0.5) !important;
  border: 1px solid var(--pb-border) !important;
  border-radius: var(--pb-radius) !important;
  color: var(--pb-cream) !important;
  font-weight: 300 !important;
}

/* ═══════════════════════════════════════════════════
   DIVIDERS
═══════════════════════════════════════════════════ */
hr {
  border: none !important;
  border-top: 1px solid var(--pb-border-soft) !important;
  margin: 1.5rem 0 !important;
}

/* ═══════════════════════════════════════════════════
   SUBHEADER STYLING
═══════════════════════════════════════════════════ */
.stApp h2[data-testid="stHeading"],
.stSubheader {
  font-family: 'Cormorant Garamond', serif !important;
  font-weight: 400 !important;
  font-size: 1.6rem !important;
  color: var(--pb-cream) !important;
  letter-spacing: 0.02em !important;
  position: relative !important;
}

/* ═══════════════════════════════════════════════════
   PLOTLY CHART CONTAINERS
═══════════════════════════════════════════════════ */
[data-testid="stPlotlyChart"] {
  border-radius: var(--pb-radius-lg) !important;
  overflow: hidden !important;
  border: 1px solid var(--pb-border-soft) !important;
  box-shadow: var(--pb-shadow-sm) !important;
  background: rgba(13, 31, 53, 0.4) !important;
}

/* ═══════════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(13, 31, 53, 0.4); }
::-webkit-scrollbar-thumb {
  background: rgba(201, 168, 76, 0.3);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(201, 168, 76, 0.55); }

/* ═══════════════════════════════════════════════════
   MARKDOWN BOLD / STRONG
═══════════════════════════════════════════════════ */
strong, b {
  color: var(--pb-gold-light) !important;
  font-weight: 500 !important;
}

/* ═══════════════════════════════════════════════════
   COLUMN GAP REFINEMENT
═══════════════════════════════════════════════════ */
[data-testid="column"] {
  gap: 1rem !important;
}

/* ═══════════════════════════════════════════════════
   DATA EDITOR
═══════════════════════════════════════════════════ */
[data-testid="stDataEditor"] {
  border: 1px solid var(--pb-border) !important;
  border-radius: var(--pb-radius-lg) !important;
  overflow: hidden !important;
}

/* ═══════════════════════════════════════════════════
   MARKDOWN TABLES
═══════════════════════════════════════════════════ */
.stMarkdown table {
  border-collapse: collapse !important;
  width: 100% !important;
  font-family: 'DM Mono', monospace !important;
  font-size: 0.82rem !important;
  border-radius: var(--pb-radius) !important;
  overflow: hidden !important;
}

.stMarkdown table th {
  background: rgba(26, 58, 92, 0.8) !important;
  color: var(--pb-gold) !important;
  font-weight: 400 !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  font-size: 0.68rem !important;
  padding: 0.6rem 0.9rem !important;
  border-bottom: 1px solid var(--pb-border) !important;
}

.stMarkdown table td {
  color: var(--pb-cream) !important;
  font-weight: 300 !important;
  padding: 0.5rem 0.9rem !important;
  border-bottom: 1px solid rgba(201, 168, 76, 0.06) !important;
  background: rgba(13, 31, 53, 0.4) !important;
}

.stMarkdown table tr:hover td {
  background: rgba(201, 168, 76, 0.05) !important;
}

/* ═══════════════════════════════════════════════════
   IMAGE IN SIDEBAR
═══════════════════════════════════════════════════ */
[data-testid="stSidebar"] img {
  border-radius: var(--pb-radius) !important;
  border: 1px solid var(--pb-border) !important;
  opacity: 0.92 !important;
}

/* ═══════════════════════════════════════════════════
   HELP TOOLTIP ICON
═══════════════════════════════════════════════════ */
[data-testid="stTooltipIcon"] svg {
  fill: var(--pb-gold-dim) !important;
}
</style>
"""
st.markdown(_PRIVATE_BANK_CSS, unsafe_allow_html=True)

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


def apply_pb_layout(fig, title: str = "", height: int = None) -> None:
    """Wendet das Private-Banking-Designsystem auf alle Plotly-Figures an."""
    base = dict(
        paper_bgcolor="rgba(13,31,53,0.0)",
        plot_bgcolor="rgba(13,31,53,0.0)",
        font=dict(
            family="DM Sans, DM Mono, sans-serif",
            color="rgba(245,240,232,0.82)",
            size=11,
        ),
        title=dict(
            text=title or (fig.layout.title.text or ""),
            font=dict(
                family="Cormorant Garamond, serif",
                size=16,
                color="rgba(245,240,232,0.9)",
            ),
            x=0.02,
            xanchor="left",
        ),
        legend=dict(
            bgcolor="rgba(13,31,53,0.55)",
            bordercolor="rgba(201,168,76,0.25)",
            borderwidth=1,
            font=dict(size=10, color="rgba(245,240,232,0.8)"),
        ),
        margin=dict(l=16, r=16, t=48, b=16),
    )
    if height:
        base["height"] = height
    fig.update_layout(**base)
    fig.update_xaxes(
        gridcolor="rgba(201,168,76,0.07)",
        linecolor="rgba(201,168,76,0.18)",
        tickfont=dict(size=10, color="rgba(245,240,232,0.65)"),
        title_font=dict(size=11, color="rgba(245,240,232,0.7)"),
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="rgba(201,168,76,0.07)",
        linecolor="rgba(201,168,76,0.18)",
        tickfont=dict(size=10, color="rgba(245,240,232,0.65)"),
        title_font=dict(size=11, color="rgba(245,240,232,0.7)"),
        zeroline=False,
    )


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

    if "mode" not in st.session_state:
        st.session_state.mode = "unser"

    # ── Aktives Dashboard anzeigen ─────────────────────────────────
    _mode_labels = {
        "unser":  ("Gemeinsam", "avatar_unser.jpg",  "🚀"),
        "simon":  ("Simon",     "avatar_simon.jpg",  "👤"),
        "alisia": ("Alisia",    "avatar_alisia.jpg", "👤"),
    }
    _cur_name, _cur_avatar, _cur_icon = _mode_labels[st.session_state.mode]

    st.markdown("""
    <div style="
        text-align: center;
        padding: 1.2rem 0.5rem 0.8rem 0.5rem;
    ">
        <div style="
            font-family: 'DM Sans', sans-serif;
            font-size: 0.6rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(201,168,76,0.75);
            margin-bottom: 0.5rem;
        ">Aktives Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # Profilbild oder Fallback-Avatar anzeigen
    _sb_col1, _sb_col2, _sb_col3 = st.columns([1, 2, 1])
    with _sb_col2:
        if os.path.exists(_cur_avatar):
            st.image(_cur_avatar, use_container_width=True)
        else:
            st.markdown(f"""
            <div style="
                width: 72px; height: 72px;
                border-radius: 50%;
                background: linear-gradient(135deg, rgba(26,58,92,0.9), rgba(13,31,53,0.95));
                border: 2px solid rgba(201,168,76,0.5);
                display: flex; align-items: center; justify-content: center;
                margin: 0 auto;
                font-size: 2rem;
                box-shadow: 0 0 20px rgba(201,168,76,0.15);
            ">{_cur_icon}</div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        text-align: center;
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.1rem;
        font-weight: 400;
        color: rgba(245,240,232,0.92);
        letter-spacing: 0.06em;
        margin-top: 0.5rem;
        margin-bottom: 1.2rem;
    ">{_cur_name}</div>
    """, unsafe_allow_html=True)

    # ── Dashboard-Wählen Button ────────────────────────────────────
    if st.button("⊞  Dashboard Wählen", use_container_width=True, key="btn_open_modal"):
        st.session_state["_show_dashboard_modal"] = True
        st.rerun()

    st.divider()

# ── Dashboard-Auswahl Modal ───────────────────────────────────────────
if st.session_state.get("_show_dashboard_modal", False):

    # ── Vollbild-Overlay CSS: Sidebar + Header komplett ausblenden ────
    st.markdown("""
    <style>
    /* Sidebar vollständig ausblenden wenn Modal aktiv */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    /* Hauptinhalt auf volle Breite ausweiten */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    /* Header/Toolbar ausblenden */
    [data-testid="stHeader"] {
        display: none !important;
    }
    /* Vollbild-Overlay */
    .pb-fullscreen-overlay {
        position: fixed;
        inset: 0;
        background: linear-gradient(160deg, #07121e 0%, #0d1f35 40%, #0a1726 100%);
        z-index: 99999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        animation: pb-overlay-fadein 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
    }
    @keyframes pb-overlay-fadein {
        from { opacity: 0; transform: scale(1.03); }
        to   { opacity: 1; transform: scale(1); }
    }
    /* Dekorativer Hintergrund-Kreis */
    .pb-fullscreen-overlay::before {
        content: "";
        position: absolute;
        width: 700px;
        height: 700px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(201,168,76,0.04) 0%, transparent 70%);
        pointer-events: none;
    }
    /* Innerer Content-Wrapper */
    .pb-overlay-inner {
        position: relative;
        z-index: 1;
        width: 100%;
        max-width: 860px;
        padding: 0 2rem;
        animation: pb-inner-slidein 0.55s cubic-bezier(0.22, 1, 0.36, 1) 0.05s both;
    }
    @keyframes pb-inner-slidein {
        from { opacity: 0; transform: translateY(28px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .pb-overlay-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2rem;
        font-weight: 400;
        color: rgba(245,240,232,0.97);
        letter-spacing: 0.06em;
        text-align: center;
        margin-bottom: 0.4rem;
    }
    .pb-overlay-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.65rem;
        font-weight: 300;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: rgba(201,168,76,0.7);
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .pb-overlay-divider {
        width: 80px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(201,168,76,0.55), transparent);
        margin: 0 auto 2.5rem auto;
    }
    /* Avatar-Card */
    .pb-avatar-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.75rem;
        padding: 1.6rem 1rem 1.2rem 1rem;
        border-radius: 12px;
        border: 1px solid rgba(201,168,76,0.14);
        background: rgba(26,58,92,0.28);
        cursor: pointer;
        transition: all 0.28s cubic-bezier(0.22, 1, 0.36, 1);
        text-align: center;
        animation: pb-card-popin 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
    }
    .pb-avatar-card:nth-child(1) { animation-delay: 0.12s; }
    .pb-avatar-card:nth-child(2) { animation-delay: 0.20s; }
    .pb-avatar-card:nth-child(3) { animation-delay: 0.28s; }
    @keyframes pb-card-popin {
        from { opacity: 0; transform: translateY(20px) scale(0.96); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }
    .pb-avatar-card:hover {
        border-color: rgba(201,168,76,0.5);
        background: rgba(201,168,76,0.09);
        transform: translateY(-5px);
        box-shadow: 0 12px 36px rgba(201,168,76,0.14), 0 0 0 1px rgba(201,168,76,0.18);
    }
    .pb-avatar-card.active {
        border-color: rgba(201,168,76,0.65);
        background: rgba(201,168,76,0.12);
        box-shadow: 0 0 0 1px rgba(201,168,76,0.30), 0 10px 28px rgba(201,168,76,0.12);
    }
    .pb-avatar-circle {
        width: 88px;
        height: 88px;
        border-radius: 50%;
        border: 2px solid rgba(201,168,76,0.45);
        box-shadow: 0 0 22px rgba(201,168,76,0.13);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #1a3a5c, #0d1f35);
        flex-shrink: 0;
    }
    .pb-avatar-circle img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 50%;
    }
    .pb-avatar-fallback-inner {
        font-size: 2.2rem;
        line-height: 1;
    }
    .pb-avatar-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.15rem;
        font-weight: 400;
        color: rgba(245,240,232,0.92);
        letter-spacing: 0.06em;
    }
    .pb-avatar-sub {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.6rem;
        font-weight: 300;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        color: rgba(201,168,76,0.65);
    }
    /* Wechsel-Animation beim Auswählen */
    @keyframes pb-select-flash {
        0%   { background: rgba(201,168,76,0.08); }
        40%  { background: rgba(201,168,76,0.28); box-shadow: 0 0 40px rgba(201,168,76,0.25); }
        100% { background: rgba(201,168,76,0.12); }
    }
    .pb-avatar-card.selecting {
        animation: pb-select-flash 0.5s ease forwards;
    }
    </style>

    <div class="pb-fullscreen-overlay">
      <div class="pb-overlay-inner">
        <div class="pb-overlay-title">Dashboard wählen</div>
        <div class="pb-overlay-subtitle">Persönliche Finanzansicht auswählen</div>
        <div class="pb-overlay-divider"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Avatar-Bilder als Base64 einbetten (Streamlit-kompatibel) ────
    import base64

    def _img_to_b64(path: str) -> str | None:
        try:
            with open(path, "rb") as f:
                data = f.read()
            ext = path.rsplit(".", 1)[-1].lower()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "image/jpeg")
            return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        except Exception:
            return None

    _modal_cfg = [
        ("unser",  "Gemeinsam", "avatar_unser.jpg",  "🚀", "Unsere Finanzen"),
        ("simon",  "Simon",     "avatar_simon.jpg",  "👤", "Simons Finanzen"),
        ("alisia", "Alisia",    "avatar_alisia.jpg", "👤", "Alisias Finanzen"),
    ]

    _modal_cols = st.columns(3, gap="large")
    for _col, (_key, _name, _avatar_file, _icon, _sub) in zip(_modal_cols, _modal_cfg):
        with _col:
            _is_active = (st.session_state.mode == _key)
            _active_class = "active" if _is_active else ""
            # Avatar: Base64-eingebettetes Bild oder Emoji-Fallback
            _b64 = _img_to_b64(_avatar_file)
            if _b64:
                _avatar_inner = f'<img src="{_b64}" alt="{_name}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'
            else:
                _avatar_inner = f'<span class="pb-avatar-fallback-inner">{_icon}</span>'
            st.markdown(f"""
            <div class="pb-avatar-card {_active_class}">
                <div class="pb-avatar-circle">{_avatar_inner}</div>
                <div class="pb-avatar-name">{_name}</div>
                <div class="pb-avatar-sub">{_sub}</div>
            </div>
            """, unsafe_allow_html=True)
            # Button zum Wählen (mit Wechsel-Animation via JS-Klasse)
            if st.button(
                "✓ Aktiv" if _is_active else "Wählen",
                key=f"modal_select_{_key}",
                use_container_width=True,
            ):
                st.session_state.mode = _key
                st.session_state["_show_dashboard_modal"] = False
                # Kurze Übergangs-Animation beim Verlassen des Modals
                st.markdown("""
                <style>
                .pb-fullscreen-overlay {
                    animation: pb-overlay-fadeout 0.35s cubic-bezier(0.55, 0, 1, 0.45) forwards !important;
                }
                @keyframes pb-overlay-fadeout {
                    from { opacity: 1; transform: scale(1); }
                    to   { opacity: 0; transform: scale(0.97); }
                }
                </style>
                """, unsafe_allow_html=True)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    _close_col1, _close_col2, _close_col3 = st.columns([1, 2, 1])
    with _close_col2:
        if st.button("✕  Schließen", key="btn_close_modal", use_container_width=True):
            st.session_state["_show_dashboard_modal"] = False
            st.rerun()

    st.divider()

# ── Modus & Titel auflösen ────────────────────────────────────────────
mode = st.session_state.mode
SHEET_ID = SHEET_IDS[mode]

if mode == "unser":
    dashboard_title = "🚀 Unsere Finanzzentrale"
elif mode == "simon":
    dashboard_title = "👤 Simons Finanzzentrale"
else:
    dashboard_title = "👤 Alisias Finanzzentrale"

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
    apply_pb_layout(fig_rule, "50/30/20-Regelanalyse — Ist vs. Ziel")
    fig_rule.update_layout(
        yaxis_range=[0, max(max(actual_vals), 55)],
        legend=dict(orientation="h"),
    )
    fig_rule.update_yaxes(title_text="Anteil am Einkommen (%)")
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
        apply_pb_layout(fig_ratio, "Ausgabenstruktur")
        fig_ratio.update_layout(
            annotations=[dict(text=fmt_eur(gesamt_ausgaben), x=0.5, y=0.5, showarrow=False, font_size=12, font_color="rgba(245,240,232,0.9)")],
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
        fig_fix_bar.update_layout(showlegend=False)
        apply_pb_layout(fig_fix_bar, "Fixkosten nach Kategorie (monatlich)")
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
            apply_pb_layout(fig_zs, "Monatliches Saldo — Einnahmen − Ausgaben")
            fig_zs.update_layout(coloraxis_showscale=False)
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
            apply_pb_layout(fig_ev, "Einnahmen vs. Ausgaben im Zeitverlauf")
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
        apply_pb_layout(fig_sankey, "💸 Cashflow — Einnahmen → Budget → Kategorien → Saldo")
        fig_sankey.update_layout(font_size=11, height=650)
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

    # Sub-Tabs: Kennzahlen + Spar-Modul (nur für Simon sinnvoll, aber für alle verfügbar)
    kenn_subtabs = st.tabs(["📐 Kennzahlen & Sparquote", "💰 Spar-Planung", "💸 Zusatzbudget"])

    # ── SUB-TAB 1: KENNZAHLEN (unveränderter Original-Code) ─────────────
    with kenn_subtabs[0]:
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
            apply_pb_layout(fig_gauge)
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
                    y=20, line_dash="dash", line_color="rgba(201,168,76,0.7)",
                    annotation_text="Ziel: 20 %", annotation_position="top right",
                )
                apply_pb_layout(fig_t, "Sparquote im Zeitverlauf (%)")
                st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.warning("Keine Einnahmen gefunden.")

    # ── SUB-TAB 2: SPAR-PLANUNG ───────────────────────────────────────────
    with kenn_subtabs[1]:
        st.subheader("💰 Spar-Planung & Portfolio-Allokation")

        # ── Basis: monatlicher Sparbetrag aus Fixkosten ───────────────────
        spar_basis_monat = (
            df_fixkosten[df_fixkosten["Unterkategorie"] == "Sparen"]["Betrag"].sum()
            if not df_fixkosten.empty else 0.0
        )

        if spar_basis_monat <= 0:
            st.warning("⚠️ Kein 'Sparen'-Eintrag in den Fixkosten gefunden. Bitte prüfe die Google-Tabelle.")
        else:
            st.info(
                f"📌 Basis: **{fmt_eur(spar_basis_monat)}/Monat** aus dem Fixkosten-Block (Kategorie 'Sparen'). "
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
            sl1, sl2 = st.columns(2)

            max_tilgung_slider = min(MAX_TILGUNG, budget_nach_pav)
            with sl1:
                tilgung = st.slider(
                    "🏦 Sondertilgung Kredit (€/Monat)",
                    min_value=0,
                    max_value=int(max_tilgung_slider),
                    value=min(500, int(max_tilgung_slider)),
                    step=50,
                    key="slider_tilgung",
                    help=f"Max. {fmt_eur(MAX_TILGUNG)}/Monat = 13.000 €/Jahr Limit",
                )

            budget_nach_tilgung = max(0.0, budget_nach_pav - tilgung)

            with sl2:
                urlaub = st.slider(
                    "🌴 Privat / Urlaub (€/Monat)",
                    min_value=0,
                    max_value=int(budget_nach_tilgung),
                    value=min(200, int(budget_nach_tilgung)),
                    step=25,
                    key="slider_urlaub",
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
            inv_col2.metric("🏦 Sondertilgung", fmt_eur(tilgung), f"{tilgung/spar_basis_monat*100:.1f} % der Basis" if spar_basis_monat > 0 else "–")
            inv_col3.metric("🌴 Privat/Urlaub", fmt_eur(urlaub), f"{urlaub/spar_basis_monat*100:.1f} % der Basis" if spar_basis_monat > 0 else "–")
            inv_col4.metric(
                "📈 → Portfolio-Investment",
                fmt_eur(investition),
                f"{inv_pct:.1f} % der Basis",
                delta_color="normal",
            )

            # ── Portfolio-Aufteilung ──────────────────────────────────────
            core_total    = investition * 0.85
            sat_total     = investition * 0.15
            msci_world    = core_total * (60 / 85)
            europa        = core_total * (15 / 85)
            em            = core_total * (10 / 85)
            semiconductor = sat_total * (10 / 15)
            zockergeld    = sat_total * (5  / 15)

            # ── Session State ─────────────────────────────────────────────
            if "zocker_akkum" not in st.session_state:
                st.session_state.zocker_akkum = 0.0

            # ── [NEU #1] Gestapeltes Balkendiagramm ──────────────────────
            st.markdown("---")
            st.write("### 📊 Monatliche Verteilung auf einen Blick")
            fig_bar_stacked = go.Figure()
            bar_kategorien = ["Sparbetrag"]
            bar_config = [
                ("🛡️ pAV",            PAV_FIX,           COLOR_NEGATIVE),
                ("🏦 Sondertilgung",   float(tilgung),    COLOR_WARN),
                ("🌴 Privat/Urlaub",   float(urlaub),     "#a05195"),
                ("📈 Investment",       investition,       COLOR_POSITIVE),
            ]
            for label, wert, farbe in bar_config:
                fig_bar_stacked.add_trace(go.Bar(
                    name=label,
                    x=bar_kategorien,
                    y=[wert],
                    marker_color=farbe,
                    text=[fmt_eur(wert)],
                    textposition="inside",
                    insidetextanchor="middle",
                ))
            apply_pb_layout(fig_bar_stacked, "Aufteilung des monatlichen Sparbetrags")
            fig_bar_stacked.update_layout(
                barmode="stack",
                yaxis_range=[0, spar_basis_monat * 1.1],
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            fig_bar_stacked.update_yaxes(title_text="€")
            st.plotly_chart(fig_bar_stacked, use_container_width=True)

            # ── Wasserfall + pAV-Kachel ───────────────────────────────────
            st.markdown("---")
            st.write("### 🔽 Wasserfall & Private Altersvorsorge")
            col_wf, col_pav = st.columns([2, 1])

            with col_wf:
                wf_measure = ["absolute", "relative", "relative", "relative", "total"]
                wf_x       = ["Sparbetrag", "− pAV", "− Sondertilgung", "− Privat/Urlaub", "→ Investment"]
                wf_y       = [spar_basis_monat, -PAV_FIX, -float(tilgung), -float(urlaub), investition]
                wf_text    = [fmt_eur(v) for v in wf_y]
                fig_wf = go.Figure(go.Waterfall(
                    measure=wf_measure,
                    x=wf_x,
                    y=wf_y,
                    text=wf_text,
                    textposition="outside",
                    connector={"line": {"color": COLOR_NEUTRAL}},
                    increasing={"marker": {"color": COLOR_POSITIVE}},
                    decreasing={"marker": {"color": COLOR_NEGATIVE}},
                    totals={"marker": {"color": COLOR_ACCENT}},
                ))
                apply_pb_layout(fig_wf, "Spar-Wasserfall — Monatliche Verteilung")
                fig_wf.update_layout(showlegend=False)
                fig_wf.update_yaxes(title_text="€")
                st.plotly_chart(fig_wf, use_container_width=True)

            with col_pav:
                st.write("#### 🛡️ Private Altersvorsorge")
                anzahl_monate_daten = max(1, len(
                    set(df_ausgaben["Monat_Jahr"].dropna().unique())
                    if not df_ausgaben.empty and "Monat_Jahr" in df_ausgaben.columns
                    else []
                ))
                pav_kapital_gesamt  = PAV_FIX * anzahl_monate_daten
                pav_zuschuss_gesamt = PAV_ZUSCHUSS * anzahl_monate_daten

                st.metric("💼 Eigenes Kapital (kumuliert)",    fmt_eur(pav_kapital_gesamt),
                          help=f"Basiert auf {anzahl_monate_daten} Datenmonaten × {fmt_eur(PAV_FIX)}/Monat")
                st.metric("🎁 Staatl. Zuschuss (kumuliert)",   fmt_eur(pav_zuschuss_gesamt),
                          help=f"{fmt_eur(PAV_ZUSCHUSS)}/Monat × {anzahl_monate_daten} Monate")
                st.metric("💰 Gesamtkapital (inkl. Zuschuss)", fmt_eur(pav_kapital_gesamt + pav_zuschuss_gesamt))
                st.info(f"📅 Monatlich: **{fmt_eur(PAV_FIX)}** eigen + **{fmt_eur(PAV_ZUSCHUSS)}** Zuschuss = **{fmt_eur(PAV_FIX + PAV_ZUSCHUSS)}** gesamt")

            # ── [NEU #3] pAV-Zeitstrahl ────────────────────────────────────
            st.markdown("---")
            st.write("#### 📈 pAV-Kapitalentwicklung im Zeitverlauf")
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
                    for i in range(anzahl_monate_daten - 1, -1, -1):
                        m = heute.month - i
                        y = heute.year
                        while m <= 0:
                            m += 12; y -= 1
                        alle_pav_monate.append(f"{m:02d}-{y}")

                pav_timeline = []
                for idx_m, monat_str in enumerate(alle_pav_monate, start=1):
                    eigen_kum   = PAV_FIX      * idx_m
                    zuschuss_kum = PAV_ZUSCHUSS * idx_m
                    gesamt_kum  = eigen_kum + zuschuss_kum
                    try:
                        mn, yr = monat_str.split("-")
                        label = f"{MONATE_DE[mn]} {yr}"
                    except Exception:
                        label = monat_str
                    pav_timeline.append({
                        "Monat": label, "Sort": monat_str,
                        "Eigene Einzahlungen": eigen_kum,
                        "Staatl. Zuschuss": zuschuss_kum,
                        "Gesamtkapital": gesamt_kum,
                    })

                df_pav_tl = pd.DataFrame(pav_timeline).sort_values("Sort")

                fig_pav_tl = go.Figure()
                fig_pav_tl.add_trace(go.Bar(
                    x=df_pav_tl["Monat"], y=df_pav_tl["Eigene Einzahlungen"],
                    name="Eigene Einzahlungen",
                    marker_color=COLOR_ACCENT,
                    text=df_pav_tl["Eigene Einzahlungen"].map(fmt_eur),
                    textposition="inside",
                ))
                fig_pav_tl.add_trace(go.Bar(
                    x=df_pav_tl["Monat"], y=df_pav_tl["Staatl. Zuschuss"],
                    name="Staatl. Zuschuss",
                    marker_color=COLOR_POSITIVE,
                    text=df_pav_tl["Staatl. Zuschuss"].map(fmt_eur),
                    textposition="inside",
                ))
                fig_pav_tl.add_trace(go.Scatter(
                    x=df_pav_tl["Monat"], y=df_pav_tl["Gesamtkapital"],
                    name="Gesamtkapital",
                    mode="lines+markers+text",
                    line=dict(color=COLOR_WARN, width=2, dash="dot"),
                    marker=dict(size=8),
                    text=df_pav_tl["Gesamtkapital"].map(fmt_eur),
                    textposition="top center",
                ))
                apply_pb_layout(fig_pav_tl, "Kumulative pAV-Entwicklung — Einzahlungen + Zuschuss")
                fig_pav_tl.update_layout(
                    barmode="stack",
                    legend=dict(orientation="h"),
                    height=400,
                )
                fig_pav_tl.update_yaxes(title_text="€ (kumuliert)")
                st.plotly_chart(fig_pav_tl, use_container_width=True)
            else:
                st.info("Keine Monatsdaten für den Zeitstrahl verfügbar.")

            # ── [ANGEPASST #4] Tilgungs-Gauge + Portfolio-Chart ──────────
            st.markdown("---")
            col_gauge, col_port = st.columns(2)

            with col_gauge:
                st.write("#### 🏦 Sondertilgung – Jahresfortschritt")
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
                else:
                    tg_bar_color = COLOR_POSITIVE

                fig_tg = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=tilgung_hochrechnung,
                    number={"suffix": " €", "valueformat": ",.0f"},
                    delta={"reference": 13000, "valueformat": ",.0f", "suffix": " € zum Limit"},
                    title={"text": f"Hochrechnung bis Jahresende<br><sup>{monate_verbleibend} Monate × {fmt_eur(tilgung)}</sup>"},
                    gauge={
                        "axis": {"range": [0, 13000]},
                        "bar": {"color": tg_bar_color},
                        "steps": [
                            {"range": [0, 5000],   "color": "#fde8e8"},
                            {"range": [5000, 7000], "color": "#fff3cd"},
                            {"range": [7000, 13000],"color": "#d4edda"},
                        ],
                        "threshold": {
                            "line": {"color": COLOR_NEGATIVE, "width": 4},
                            "thickness": 0.75,
                            "value": 13000,
                        },
                    },
                ))
                apply_pb_layout(fig_tg)
                fig_tg.update_layout(height=350)
                st.plotly_chart(fig_tg, use_container_width=True)
                st.caption(
                    f"Jahresbetrag bei gleichbleibender Rate: **{fmt_eur(tilgung_jahresbetrag)}** "
                    f"| Limit: **13.000,00 €** | Ausnutzung: **{tilgung_prozent:.1f} %**"
                )

            with col_port:
                st.write("#### 📈 Portfolio-Allokation")
                if investition > 0:
                    port_labels  = ["Investment", "Core (85%)", "Satellite (15%)",
                                    "MSCI World", "Europa", "EM",
                                    "Semiconductor", "Zockergeld"]
                    port_parents = ["", "Investment", "Investment",
                                    "Core (85%)", "Core (85%)", "Core (85%)",
                                    "Satellite (15%)", "Satellite (15%)"]
                    port_values  = [investition, core_total, sat_total,
                                    msci_world, europa, em, semiconductor, zockergeld]
                    port_text    = [fmt_eur(v) for v in port_values]

                    fig_sun = go.Figure(go.Sunburst(
                        labels=port_labels,
                        parents=port_parents,
                        values=port_values,
                        customdata=port_text,
                        hovertemplate="<b>%{label}</b><br>%{customdata}<extra></extra>",
                        texttemplate="%{label}<br>%{customdata}",
                        branchvalues="total",
                        marker=dict(colors=[
                            COLOR_ACCENT, COMPLEMENTARY_COLORS[1], COMPLEMENTARY_COLORS[4],
                            COMPLEMENTARY_COLORS[0], COMPLEMENTARY_COLORS[2], COMPLEMENTARY_COLORS[3],
                            COMPLEMENTARY_COLORS[5], COMPLEMENTARY_COLORS[6],
                        ]),
                    ))
                    apply_pb_layout(fig_sun, "Portfolio-Allokation")
                    fig_sun.update_layout(
                        height=350,
                        margin=dict(t=48, b=10, l=10, r=10),
                    )
                    st.plotly_chart(fig_sun, use_container_width=True)
                else:
                    st.info("💡 Kein Restbetrag für Investment — Slider anpassen.")

            # ── Portfolio-Detailtabelle ───────────────────────────────────
            st.markdown("---")
            st.write("### 📋 Portfolio-Detailübersicht")
            port_detail_cols = st.columns(5)
            port_items = [
                ("🌍 MSCI World",    msci_world,    "Core · 60 %"),
                ("🇪🇺 Europa",        europa,         "Core · 15 %"),
                ("🌏 EM",             em,             "Core · 10 %"),
                ("💻 Semiconductor",  semiconductor, "Satellite · 10 %"),
                ("🎲 Zockergeld",     zockergeld,    "Satellite · 5 %"),
            ]
            for col, (label, betrag, info) in zip(port_detail_cols, port_items):
                col.metric(label, fmt_eur(betrag), info)

            # ── Zockergeld-Akkumulator ────────────────────────────────────
            st.markdown("---")
            st.write("### 🎲 Zockergeld-Kasse")
            zk1, zk2, zk3 = st.columns([1, 1, 1])
            with zk1:
                st.metric("💶 Aktueller Monatsbetrag", fmt_eur(zockergeld))
            with zk2:
                st.metric("🏦 Akkumuliert (noch nicht investiert)",
                          fmt_eur(st.session_state.zocker_akkum + zockergeld))
            with zk3:
                st.write(""); st.write("")
                if st.button("✅ Investiert! Kasse zurücksetzen", key="btn_zocker_reset", use_container_width=True):
                    st.session_state.zocker_akkum = 0.0
                    st.success("Zockergeld-Kasse wurde zurückgesetzt.")
                if st.button("➕ Monat hinzufügen", key="btn_zocker_add", use_container_width=True):
                    st.session_state.zocker_akkum += zockergeld
                    st.success(f"+ {fmt_eur(zockergeld)} zur Zockerkasse hinzugefügt.")

            # ── Zusammenfassungs-Tabelle ──────────────────────────────────
            st.markdown("---")
            st.write("### 🧾 Monatsübersicht")
            summary_data = {
                "Posten": [
                    "🐖 Sparbetrag (Basis)",
                    "🛡️ Private Altersvorsorge (fix)",
                    "🏦 Sondertilgung Kredit",
                    "🌴 Privat / Urlaub",
                    "📈 Investment (Restbetrag)",
                    "─────────────────────",
                    "   🌍 MSCI World (Core 60%)",
                    "   🇪🇺 Europa (Core 15%)",
                    "   🌏 EM (Core 10%)",
                    "   💻 Semiconductor (Sat. 10%)",
                    "   🎲 Zockergeld (Sat. 5%)",
                ],
                "Betrag": [
                    fmt_eur(spar_basis_monat), fmt_eur(PAV_FIX), fmt_eur(tilgung),
                    fmt_eur(urlaub), fmt_eur(investition), "────────",
                    fmt_eur(msci_world), fmt_eur(europa), fmt_eur(em),
                    fmt_eur(semiconductor), fmt_eur(zockergeld),
                ],
                "Anteil": [
                    "100,0 %",
                    f"{PAV_FIX / spar_basis_monat * 100:.1f} %",
                    f"{tilgung / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                    f"{urlaub / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                    f"{investition / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                    "────",
                    f"{msci_world / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                    f"{europa / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                    f"{em / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                    f"{semiconductor / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                    f"{zockergeld / spar_basis_monat * 100:.1f} %" if spar_basis_monat > 0 else "–",
                ],
            }
            st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

    # ── SUB-TAB 3: ZUSATZBUDGET-RECHNER [NEU #5] ─────────────────────────
    with kenn_subtabs[2]:
        st.subheader("💸 Zusatzbudget-Rechner")
        st.info(
            "Hier kannst du ein einmalig verfügbares Zusatzbudget eingeben (z. B. Bonus, Rückerstattung, "
            "Monatsüberschuss) und siehst sofort, wie es gemäß deiner Core-Satellite-Strategie aufgeteilt wird."
        )

        zusatz_betrag = st.number_input(
            "💶 Verfügbares Zusatzbudget (€)",
            min_value=0.0,
            max_value=100000.0,
            value=0.0,
            step=50.0,
            format="%.2f",
            key="zusatz_budget_input",
            help="Gib den Betrag ein, der zusätzlich investiert werden soll.",
        )

        if zusatz_betrag > 0:
            # Gleiche Portfolio-Aufteilung: Core 85% / Satellite 15%
            z_core_total    = zusatz_betrag * 0.85
            z_sat_total     = zusatz_betrag * 0.15
            z_msci_world    = z_core_total * (60 / 85)
            z_europa        = z_core_total * (15 / 85)
            z_em            = z_core_total * (10 / 85)
            z_semiconductor = z_sat_total  * (10 / 15)
            z_zockergeld    = z_sat_total  * (5  / 15)

            st.markdown("---")
            st.write(f"### 📊 Aufteilung für {fmt_eur(zusatz_betrag)}")

            # Metric-Kacheln
            zb_c1, zb_c2 = st.columns(2)
            with zb_c1:
                st.metric("🔵 Core-Anteil (85 %)", fmt_eur(z_core_total))
            with zb_c2:
                st.metric("🟠 Satellite-Anteil (15 %)", fmt_eur(z_sat_total))

            st.markdown("##### Core-Positionen")
            zc1, zc2, zc3 = st.columns(3)
            zc1.metric("🌍 MSCI World (60 %)", fmt_eur(z_msci_world))
            zc2.metric("🇪🇺 Europa (15 %)",     fmt_eur(z_europa))
            zc3.metric("🌏 EM (10 %)",           fmt_eur(z_em))

            st.markdown("##### Satellite-Positionen")
            zs1, zs2 = st.columns(2)
            zs1.metric("💻 Semiconductor (10 %)", fmt_eur(z_semiconductor))
            zs2.metric("🎲 Zockergeld (5 %)",     fmt_eur(z_zockergeld))

            # Sunburst-Visualisierung
            st.markdown("---")
            z_port_labels  = ["Zusatzbudget", "Core (85%)", "Satellite (15%)",
                              "MSCI World", "Europa", "EM",
                              "Semiconductor", "Zockergeld"]
            z_port_parents = ["", "Zusatzbudget", "Zusatzbudget",
                              "Core (85%)", "Core (85%)", "Core (85%)",
                              "Satellite (15%)", "Satellite (15%)"]
            z_port_values  = [zusatz_betrag, z_core_total, z_sat_total,
                              z_msci_world, z_europa, z_em, z_semiconductor, z_zockergeld]
            z_port_text    = [fmt_eur(v) for v in z_port_values]

            fig_z_sun = go.Figure(go.Sunburst(
                labels=z_port_labels,
                parents=z_port_parents,
                values=z_port_values,
                customdata=z_port_text,
                hovertemplate="<b>%{label}</b><br>%{customdata}<extra></extra>",
                texttemplate="%{label}<br>%{customdata}",
                branchvalues="total",
                marker=dict(colors=[
                    COLOR_ACCENT, COMPLEMENTARY_COLORS[1], COMPLEMENTARY_COLORS[4],
                    COMPLEMENTARY_COLORS[0], COMPLEMENTARY_COLORS[2], COMPLEMENTARY_COLORS[3],
                    COMPLEMENTARY_COLORS[5], COMPLEMENTARY_COLORS[6],
                ]),
            ))
            apply_pb_layout(fig_z_sun, f"Portfolio-Aufteilung Zusatzbudget ({fmt_eur(zusatz_betrag)})")
            fig_z_sun.update_layout(
                height=450,
                margin=dict(t=48, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_z_sun, use_container_width=True)

            # Detailtabelle
            st.markdown("---")
            st.write("### 🧾 Detailübersicht Zusatzbudget")
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
                ],
                "Anteil": [
                    "100,0 %", "────",
                    "85,0 %",
                    f"{z_msci_world / zusatz_betrag * 100:.1f} %",
                    f"{z_europa / zusatz_betrag * 100:.1f} %",
                    f"{z_em / zusatz_betrag * 100:.1f} %",
                    "15,0 %",
                    f"{z_semiconductor / zusatz_betrag * 100:.1f} %",
                    f"{z_zockergeld / zusatz_betrag * 100:.1f} %",
                ],
            }
            st.dataframe(pd.DataFrame(z_summary), hide_index=True, use_container_width=True)
        else:
            st.markdown("---")
            st.write("👆 Gib oben einen Betrag ein, um die Portfolio-Aufteilung zu berechnen.")


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
                    apply_pb_layout(fig_fair, "Einkommensanteile im Vergleich")
                    fig_fair.update_layout(yaxis_range=[0, 100])
                    fig_fair.update_yaxes(title_text="Anteil (%)")
                    fig_fair.add_hline(y=50, line_dash="dash", line_color="rgba(201,168,76,0.5)",
                                       annotation_text="50/50-Linie")
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
                apply_pb_layout(fig_alarm, "Vergleich — Aktuell vs. Vormonat (Alarmkategorien)")
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
