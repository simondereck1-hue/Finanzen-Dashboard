import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. KONFIGURATION & DESIGN ---
st.set_page_config(page_title="Finanzzentrale", layout="wide")

# --- DASHBOARD-AUSWAHL IN DER SIDEBAR ---
with st.sidebar:
    st.header("👤 Dashboard wählen")
    if 'mode' not in st.session_state:
        st.session_state.mode = 'unser'

    if st.button("Unsere Finanzen", use_container_width=True):
        st.session_state.mode = 'unser'
    if st.button("Simons Finanzen", use_container_width=True):
        st.session_state.mode = 'simon'
    if st.button("Alisias Finanzen", use_container_width=True):
        st.session_state.mode = 'alisia'

    if st.session_state.mode == 'unser':
        st.success("Aktive Ansicht: Unsere Finanzen")
        SHEET_ID = "1y3lfS_jumaUDM-ms8NQWA_-MpVMWyfc0vGeWUIzX_Rc"
        dashboard_title = "🚀 Unsere Finanzzentrale"
    elif st.session_state.mode == 'simon':
        st.info("Aktive Ansicht: Simons Finanzen")
        SHEET_ID = "1VUPcu7bMKC1ws4KYomeiCHuOfKlDdMwp7NiaOlv-AWI"
        dashboard_title = "👤 Simons Finanzzentrale"
    else:
        st.info("Aktive Ansicht: Alisias Finanzen")
        SHEET_ID = "1eCvGkPpavtdgrj1_FgnMqyeMJS6ye6NmhGIf1O_E--4"
        dashboard_title = "👤 Alisias Finanzzentrale"

st.title(dashboard_title)

COMPLEMENTARY_COLORS = ["#003f5c", "#ff7c43", "#2f4b7c", "#ffa600", "#665191", "#f95d6a", "#a05195", "#d45087"]

MONATE_DE = {
    "01": "Januar", "02": "Februar", "03": "März", "04": "April",
    "05": "Mai", "06": "Juni", "07": "Juli", "08": "August",
    "09": "September", "10": "Oktober", "11": "November", "12": "Dezember"
}

# --- Hilfsfunktion: Robuste Betragsbereinigung ---
def clean_betrag(series):
    """
    Wandelt Beträge aus Google Sheets zuverlässig in Float um.
    Unterstützt: '1.234,56', '1234,56', '1234.56', '1.234,56 €', etc.
    """
    s = series.astype(str).str.strip()
    s = s.str.replace('€', '', regex=False).str.replace(' ', '', regex=False)
    
    has_both = s.str.contains(r'\.') & s.str.contains(r',')
    
    result = s.copy()
    result[has_both] = s[has_both].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    result[~has_both & s.str.contains(r',')] = s[~has_both & s.str.contains(r',')].str.replace(',', '.', regex=False)
    
    return pd.to_numeric(result, errors='coerce').fillna(0.0)

# --- Hilfsfunktion: Datum sicher zu Monatsstring ---
def datum_zu_monat(x):
    """Wandelt ein Datum sicher in 'Monat Jahr' um, ignoriert NaT."""
    try:
        # Sicherstellen, dass nur Monat und Jahr verwendet werden, um "Februar 1" Fehler zu vermeiden
        return f"{MONATE_DE[x.strftime('%m')]} {x.year}"
    except Exception:
        return None

# --- 2. GOOGLE SHEETS VERBINDUNG via gspread ---
@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def sheet_to_df(worksheet):
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- 3. DATENFUNKTIONEN ---
@st.cache_data(ttl=600)
def load_data(sheet_id):
    client = get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)

    ausgaben = sheet_to_df(spreadsheet.worksheet("Ausgaben"))
    fixkosten = sheet_to_df(spreadsheet.worksheet("Fixkosten"))
    fix_einnahmen = sheet_to_df(spreadsheet.worksheet("Fix_Einnahmen"))
    einnahmen = sheet_to_df(spreadsheet.worksheet("Einnahmen"))

    for df in [ausgaben, fixkosten, fix_einnahmen, einnahmen]:
        if 'Betrag' in df.columns:
            df['Betrag'] = clean_betrag(df['Betrag'])
        else:
            df['Betrag'] = 0.0

    for df in [ausgaben, einnahmen]:
        if 'Datum' in df.columns:
            # Explizite Angabe des Formats für Google Sheets TT.MM.JJJJ
            df['Datum'] = pd.to_datetime(df['Datum'], dayfirst=True, errors='coerce')

    return ausgaben, fixkosten, fix_einnahmen, einnahmen

df_ausgaben, df_fixkosten, df_fix_einnahmen, df_einnahmen = load_data(SHEET_ID)

# --- 4. SIDEBAR (ZEITRAUM-FILTER) ---
if os.path.exists("Bild Dashboard.PNG"):
    st.sidebar.image("Bild Dashboard.PNG", use_container_width=True)

st.sidebar.header("🔍 Globaler Filter")

# Monat_Jahr Spalten für den Filter erstellen
for df in [df_ausgaben, df_einnahmen]:
    if not df.empty and 'Datum' in df.columns:
        df['Filter_Label'] = df['Datum'].apply(datum_zu_monat)
        df['Monat_Jahr'] = df['Datum'].dt.strftime('%m-%Y')
    else:
        df['Filter_Label'] = None
        df['Monat_Jahr'] = None

# Verfügbare Monate sammeln (Mapping von Label zu technischem Wert)
filter_mapping = {}
if not df_ausgaben.empty:
    valid_ausgaben = df_ausgaben.dropna(subset=['Filter_Label', 'Monat_Jahr'])
    filter_mapping.update(dict(zip(valid_ausgaben['Filter_Label'], valid_ausgaben['Monat_Jahr'])))
if not df_einnahmen.empty:
    valid_einnahmen = df_einnahmen.dropna(subset=['Filter_Label', 'Monat_Jahr'])
    filter_mapping.update(dict(zip(valid_einnahmen['Filter_Label'], valid_einnahmen['Monat_Jahr'])))

# Sortierung der Monate (Neueste zuerst)
sorted_labels = sorted(filter_mapping.keys(), 
                      key=lambda x: datetime.strptime(filter_mapping[x], "%m-%Y"), 
                      reverse=True)

month_options = ["Gesamter Zeitraum", "Benutzerdefinierter Zeitraum"] + sorted_labels
selected_label = st.sidebar.selectbox("Zeitraum wählen", month_options)

if selected_label == "Gesamter Zeitraum":
    num_months = len(sorted_labels) if sorted_labels else 1
    filtered_ausgaben = df_ausgaben.copy()
    filtered_einnahmen = df_einnahmen.copy()
elif selected_label == "Benutzerdefinierter Zeitraum":
    col_start, col_end = st.sidebar.columns(2)
    min_datum = df_ausgaben['Datum'].min().date() if not df_ausgaben.empty and pd.notnull(df_ausgaben['Datum'].min()) else datetime.today().date()
    start_date = col_start.date_input("Startdatum", value=min_datum)
    end_date = col_end.date_input("Enddatum", value=datetime.today().date())
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    filtered_ausgaben = df_ausgaben[(df_ausgaben['Datum'] >= start_dt) & (df_ausgaben['Datum'] <= end_dt)].copy()
    filtered_einnahmen = df_einnahmen[(df_einnahmen['Datum'] >= start_dt) & (df_einnahmen['Datum'] <= end_dt)].copy()
    
    diff = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    num_months = max(1, diff)
else:
    num_months = 1
    tech_val = filter_mapping[selected_label]
    filtered_ausgaben = df_ausgaben[df_ausgaben['Monat_Jahr'] == tech_val].copy()
    filtered_einnahmen = df_einnahmen[df_einnahmen['Monat_Jahr'] == tech_val].copy()

st.sidebar.divider()

# --- 5. TABS ---
tab_titles = ["📊 Gesamtkostenübersicht", "💰 Einnahmen", "🏠 Fixkosten", "🛒 Variabel", "⚖️ Saldo-Zeitstrahl", "📈 Trends"]
if st.session_state.mode in ['simon', 'alisia']:
    tab_titles.append("📈 Kennzahlen")

tabs = st.tabs(tab_titles)

# Sicherstellung, dass Betrag-Spalten existieren für die Berechnung
fix_summe_scaled = df_fixkosten['Betrag'].sum() * num_months if 'Betrag' in df_fixkosten.columns else 0
einn_fix_summe_scaled = df_fix_einnahmen['Betrag'].sum() * num_months if 'Betrag' in df_fix_einnahmen.columns else 0

# TAB 1: GESAMTKOSTENÜBERSICHT
with tabs[0]:
    df_fix_scaled = df_fixkosten.assign(Typ='Fix', Betrag=df_fixkosten['Betrag'] * num_months) if not df_fixkosten.empty else pd.DataFrame()
    df_all = pd.concat([df_fix_scaled, filtered_ausgaben.assign(Typ='Variabel')]) if not filtered_ausgaben.empty or not df_fix_scaled.empty else pd.DataFrame()
    
    gesamt_ausgaben = df_all['Betrag'].sum() if not df_all.empty else 0
    st.subheader(f"Übersicht & Tabellenfilter — Gesamt: {gesamt_ausgaben:,.2f} €")

    col_l, col_r = st.columns([1.5, 1])
    with col_r:
        st.write("**Tabellenfilter**")
        if not df_all.empty:
            f_kat = st.multiselect("Kategorie auswählen", options=sorted(df_all["Kategorie"].dropna().unique()), key="filter_all_kat")
            f_sub = st.multiselect("Unterkategorie auswählen", options=sorted(df_all["Unterkategorie"].dropna().unique()), key="filter_all_sub")
            df_filtered_table = df_all.copy()
            if f_kat: df_filtered_table = df_filtered_table[df_filtered_table["Kategorie"].isin(f_kat)]
            if f_sub: df_filtered_table = df_filtered_table[df_filtered_table["Unterkategorie"].isin(f_sub)]
            df_grouped = df_filtered_table.groupby(['Kategorie', 'Unterkategorie'])['Betrag'].sum().reset_index()
            st.dataframe(df_grouped, hide_index=True, use_container_width=True)
            st.info(f"**Summe ausgewählte Positionen: {df_filtered_table['Betrag'].sum():,.2f} €**")
        else:
            st.info("Keine Daten vorhanden.")
    
    with col_l:
        if not df_all.empty:
            fig = px.sunburst(df_all, path=['Typ', 'Kategorie', 'Unterkategorie'], values='Betrag', height=600, color_discrete_sequence=COMPLEMENTARY_COLORS)
            fig.update_traces(textinfo="label+percent entry")
            st.plotly_chart(fig, use_container_width=True)

# TAB 2: EINNAHMEN
with tabs[1]:
    aktuelle_einnahmen = (filtered_einnahmen['Betrag'].sum() if not filtered_einnahmen.empty else 0) + einn_fix_summe_scaled
    st.subheader(f"Einnahmen Details — Gesamt: {aktuelle_einnahmen:,.2f} €")
    col1, col2 = st.columns([1.5, 1])
    with col2:
        st.write("**Einnahmen Übersicht**")
        if not df_fix_einnahmen.empty:
            f_pers = st.multiselect("Person auswählen", options=sorted(df_fix_einnahmen["Person"].dropna().unique()), key="filter_einn_pers")
            df_einn_table = df_fix_einnahmen.copy()
            df_einn_table['Betrag'] = df_einn_table['Betrag'] * num_months
            if f_pers: df_einn_table = df_einn_table[df_einn_table["Person"].isin(f_pers)]
            st.data_editor(df_einn_table, hide_index=True, use_container_width=True, key=f"einn_f_{st.session_state.mode}")
            st.info(f"**Summe ausgewählte Einnahmen: {df_einn_table['Betrag'].sum():,.2f} €**")
    with col1:
        if not df_fix_einnahmen.empty:
            df_einn_fig = df_fix_einnahmen.copy().assign(Betrag=df_fix_einnahmen['Betrag'] * num_months)
            fig_einn = px.pie(df_einn_fig, values='Betrag', names='Person', title="Verteilung Fix-Einnahmen", height=600, color_discrete_sequence=COMPLEMENTARY_COLORS)
            fig_einn.update_traces(textinfo="label+percent")
            st.plotly_chart(fig_einn, use_container_width=True)

# TAB 3: FIXKOSTEN
with tabs[2]:
    fix_monat_summe = df_fixkosten['Betrag'].sum() if not df_fixkosten.empty else 0
    fix_zeitraum_summe = fix_monat_summe * num_months
    
    st.subheader(f"Fixkosten Analyse — Zeitraum ({num_months} Mon.): {fix_zeitraum_summe:,.2f} €")
    col1, col2 = st.columns([1.5, 1])
    with col1:
        if not df_fixkosten.empty:
            df_fix_fig = df_fixkosten.copy()
            df_fix_fig['Betrag'] = df_fix_fig['Betrag'] * num_months
            fig_fix_pie = px.sunburst(df_fix_fig, path=['Kategorie', 'Unterkategorie'], values='Betrag', title=f"Fixkosten Verteilung ({num_months} Mon.)", height=600, color_discrete_sequence=COMPLEMENTARY_COLORS)
            fig_fix_pie.update_traces(textinfo="label+percent entry")
            st.plotly_chart(fig_fix_pie, use_container_width=True)
    with col2:
        st.write("**Fixkosten Tabelle**")
        if not df_fixkosten.empty:
            f_kat_fix = st.multiselect("Kategorie auswählen", options=sorted(df_fixkosten["Kategorie"].dropna().unique()), key="filter_fix_kat")
            f_sub_fix = st.multiselect("Unterkategorie auswählen", options=sorted(df_fixkosten["Unterkategorie"].dropna().unique()), key="filter_fix_sub")
            df_fix_table = df_fixkosten.copy()
            df_fix_table['Betrag'] = df_fix_table['Betrag'] * num_months
            if f_kat_fix: df_fix_table = df_fix_table[df_fix_table["Kategorie"].isin(f_kat_fix)]
            if f_sub_fix: 
                df_fix_table = df_fix_table[df_fix_table["Unterkategorie"].isin(f_sub_fix)]
            st.data_editor(df_fix_table, hide_index=True, use_container_width=True, key=f"fix_f_{st.session_state.mode}")
            st.info(f"**Summe ausgewählte Fixkosten: {df_fix_table['Betrag'].sum():,.2f} €**")

# TAB 4: VARIABEL
with tabs[3]:
    var_summe = filtered_ausgaben['Betrag'].sum() if not filtered_ausgaben.empty else 0
    st.subheader(f"Variable Ausgaben — Zeitraum: {var_summe:,.2f} €")
    if not filtered_ausgaben.empty:
        col1, col2 = st.columns([1.5, 1])
        with col1:
            fig_var_pie = px.sunburst(filtered_ausgaben, path=['Kategorie', 'Unterkategorie'], values='Betrag', title="Struktur Variable Ausgaben", height=600, color_discrete_sequence=COMPLEMENTARY_COLORS)
            fig_var_pie.update_traces(textinfo="label+percent entry")
            st.plotly_chart(fig_var_pie, use_container_width=True)
        with col2:
            st.write("**Einzelbuchungen**")
            f_kat_var = st.multiselect("Kategorie auswählen", options=sorted(filtered_ausgaben["Kategorie"].dropna().unique()), key="filter_var_kat")
            f_sub_var = st.multiselect("Unterkategorie auswählen", options=sorted(filtered_ausgaben["Unterkategorie"].dropna().unique()), key="filter_var_sub")
            df_var_table = filtered_ausgaben.copy()
            if f_kat_var: df_var_table = df_var_table[df_var_table["Kategorie"].isin(f_kat_var)]
            if f_sub_var: df_var_table = df_var_table[df_var_table["Unterkategorie"].isin(f_sub_var)]
            
            disp_df = df_var_table.copy()
            if not disp_df.empty and 'Datum' in disp_df.columns:
                disp_df['Datum'] = disp_df['Datum'].dt.strftime('%d.%m.%Y')
            st.dataframe(disp_df[['Datum', 'Kategorie', 'Unterkategorie', 'Betrag']], hide_index=True, use_container_width=True)
            st.info(f"**Summe ausgewählte Buchungen: {df_var_table['Betrag'].sum():,.2f} €**")
    else:
        st.info("Keine Daten für diesen Zeitraum.")

# TAB 5: SALDO-ZEITSTRAHL
with tabs[4]:
    st.subheader("📅 Monatlicher Saldo-Zeitstrahl & Cashflow")
    def hex_to_rgba(hex_val, opacity):
        hex_val = hex_val.lstrip('#')
        lv = len(hex_val)
        rgb = tuple(int(hex_val[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"

    if not df_ausgaben.empty or not df_einnahmen.empty:
        df_v, df_e = df_ausgaben.copy(), df_einnahmen.copy()
        for d in [df_v, df_e]:
            if 'Datum' in d.columns and d['Datum'].notnull().any():
                d['Monat_Sort'] = d['Datum'].dt.strftime('%Y-%m')
            else:
                d['Monat_Sort'] = pd.Series(dtype='object')

        alle_monate_sort = sorted(list(set(df_v['Monat_Sort'].dropna().unique()) | set(df_e['Monat_Sort'].dropna().unique())))

        zeitstrahl_daten = []
        for m in alle_monate_sort:
            v_m = df_v[df_v['Monat_Sort'] == m]['Betrag'].sum()
            e_m = df_e[df_e['Monat_Sort'] == m]['Betrag'].sum()
            fix_e = df_fix_einnahmen['Betrag'].sum() if not df_fix_einnahmen.empty else 0
            fix_v = df_fixkosten['Betrag'].sum() if not df_fixkosten.empty else 0
            saldo = (e_m + fix_e) - (v_m + fix_v)
            y, mn = m.split('-')
            zeitstrahl_daten.append({"Monat": f"{MONATE_DE[mn]} {y}", "Saldo": saldo, "Sort": m})

        if zeitstrahl_daten:
            df_zs = pd.DataFrame(zeitstrahl_daten).sort_values("Sort")
            fig_zs = px.bar(df_zs, x='Monat', y='Saldo', text_auto='.2f', color='Saldo', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_zs, use_container_width=True)

        st.divider()
        st.write("### 🌊 Cashflow-Flussdiagramm")
        
        total_einn_fix = (df_fix_einnahmen.groupby('Person')['Betrag'].sum() * num_months).reset_index() if not df_fix_einnahmen.empty else pd.DataFrame(columns=['Person', 'Betrag'])
        total_einn_var = filtered_einnahmen.groupby('Person')['Betrag'].sum().reset_index() if not filtered_einnahmen.empty else pd.DataFrame(columns=['Person', 'Betrag'])
        
        df_ausg_all = pd.concat([
            (df_fixkosten.copy().assign(Betrag=df_fixkosten['Betrag'] * num_months)).assign(Quelle='Fixkosten') if not df_fixkosten.empty else pd.DataFrame(),
            filtered_ausgaben.assign(Quelle='Variable Ausgaben') if not filtered_ausgaben.empty else pd.DataFrame()
        ])

        if not df_ausg_all.empty or not total_einn_fix.empty:
            einn_labels = sorted(list(set(total_einn_fix['Person']) | set(total_einn_var['Person'])))
            label_list = einn_labels + ["Budget (Gesamt)"]
            budget_idx = len(einn_labels)
            source, target, value, color_link = [], [], [], []
            for i, p in enumerate(einn_labels):
                val = total_einn_fix[total_einn_fix['Person']==p]['Betrag'].sum() + total_einn_var[total_einn_var['Person']==p]['Betrag'].sum()
                if val > 0:
                    source.append(i); target.append(budget_idx); value.append(val); color_link.append("rgba(31, 119, 180, 0.4)")

            unique_kats = sorted(df_ausg_all['Kategorie'].unique())
            kat_start_idx = len(label_list)
            label_list.extend(unique_kats)
            for i, k in enumerate(unique_kats):
                val = df_ausg_all[df_ausg_all['Kategorie'] == k]['Betrag'].sum()
                if val > 0:
                    source.append(budget_idx); target.append(kat_start_idx+i); value.append(val)
                    color_link.append(hex_to_rgba(COMPLEMENTARY_COLORS[i % len(COMPLEMENTARY_COLORS)], 0.4))

            unique_subs = df_ausg_all.groupby(['Kategorie', 'Unterkategorie'])['Betrag'].sum().reset_index()
            sub_start_idx = len(label_list)
            label_list.extend(unique_subs['Unterkategorie'].tolist())
            for idx, row in unique_subs.iterrows():
                if row['Betrag'] > 0:
                    k_i = kat_start_idx + unique_kats.index(row['Kategorie'])
                    source.append(k_i); target.append(sub_start_idx+idx); value.append(row['Betrag'])
                    color_link.append(hex_to_rgba(COMPLEMENTARY_COLORS[unique_kats.index(row['Kategorie']) % len(COMPLEMENTARY_COLORS)], 0.4))

            gesamt_einn = sum(value[:len(einn_labels)])
            gesamt_ausg = df_ausg_all['Betrag'].sum()
            if gesamt_einn > gesamt_ausg:
                label_list.append("Saldo / Ersparnis")
                saldo_idx = len(label_list)-1
                source.append(budget_idx); target.append(saldo_idx); value.append(gesamt_einn - gesamt_ausg)
                color_link.append("rgba(40, 167, 69, 0.4)")

            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, label=label_list, color="lightgray"),
                link=dict(source=source, target=target, value=value, color=color_link)
            )])
            st.plotly_chart(fig_sankey, use_container_width=True)

# TAB 6: TRENDS
with tabs[5]:
    st.subheader("📈 Trend-Analyse")
    if not df_ausgaben.empty:
        trend_tabs = st.tabs(["📁 Kategorien", "🔍 Unterkategorien"])
        with trend_tabs[0]:
            all_kats = sorted(df_ausgaben['Kategorie'].dropna().unique())
            col_select, col_plot = st.columns([1, 3])
            with col_select:
                selected_kats = [k for k in all_kats if st.checkbox(k, value=True, key=f"t_kat_{k}_{st.session_state.mode}")]
            with col_plot:
                df_tk = df_ausgaben[df_ausgaben['Kategorie'].isin(selected_kats)].copy()
                df_tk = df_tk.dropna(subset=['Datum'])
                if not df_tk.empty:
                    df_tk['Monat_Sort'] = df_tk['Datum'].dt.strftime('%Y-%m')
                    df_tk['Monat'] = df_tk['Datum'].apply(datum_zu_monat)
                    df_tk = df_tk.dropna(subset=['Monat'])
                    res = df_tk.groupby(['Monat_Sort', 'Monat', 'Kategorie'])['Betrag'].sum().reset_index().sort_values('Monat_Sort')
                    st.plotly_chart(px.line(res, x='Monat', y='Betrag', color='Kategorie', markers=True, color_discrete_sequence=COMPLEMENTARY_COLORS), use_container_width=True)
        with trend_tabs[1]:
            selected_subcats = []
            col_select, col_plot = st.columns([1, 3])
            with col_select:
                for kat in sorted(df_ausgaben['Kategorie'].dropna().unique()):
                    subs = sorted(df_ausgaben[df_ausgaben['Kategorie'] == kat]['Unterkategorie'].dropna().unique())
                    mk = f"mstr_{kat}_{st.session_state.mode}"
                    if mk not in st.session_state: st.session_state[mk] = True
                    def tg(k=kat, m=mk, s=subs):
                        for x in s: st.session_state[f"sb_{k}_{x}_{st.session_state.mode}"] = st.session_state[m]
                    c_on = st.checkbox(f"📁 **{kat}**", key=mk, on_change=tg)
                    for s in subs:
                        sk = f"sb_{kat}_{s}_{st.session_state.mode}"
                        if sk not in st.session_state: st.session_state[sk] = c_on
                        if st.checkbox(f"   └ {s}", key=sk): selected_subcats.append(s)
            with col_plot:
                df_ts = df_ausgaben[df_ausgaben['Unterkategorie'].isin(selected_subcats)].copy()
                df_ts = df_ts.dropna(subset=['Datum'])
                if not df_ts.empty:
                    df_ts['Monat_Sort'] = df_ts['Datum'].dt.strftime('%Y-%m')
                    df_ts['Monat'] = df_ts['Datum'].apply(datum_zu_monat)
                    df_ts = df_ts.dropna(subset=['Monat'])
                    res = df_ts.groupby(['Monat_Sort', 'Monat', 'Unterkategorie'])['Betrag'].sum().reset_index().sort_values('Monat_Sort')
                    st.plotly_chart(px.line(res, x='Monat', y='Betrag', color='Unterkategorie', markers=True, color_discrete_sequence=COMPLEMENTARY_COLORS), use_container_width=True)

# TAB: KENNZAHLEN (Für Simon und Alisia)
if st.session_state.mode in ['simon', 'alisia']:
    with tabs[6]:
        st.subheader("📉 Kennzahlen & Sparquote")
        akt_einn = (filtered_einnahmen['Betrag'].sum() if not filtered_einnahmen.empty else 0) + einn_fix_summe_scaled
        
        spar_fix = df_fixkosten[df_fixkosten['Unterkategorie'] == 'Sparen']['Betrag'].sum() * num_months if not df_fixkosten.empty else 0
        spar_var = filtered_ausgaben[filtered_ausgaben['Unterkategorie'] == 'Sparen']['Betrag'].sum() if not filtered_ausgaben.empty else 0
        akt_spar = spar_fix + spar_var

        if akt_einn > 0:
            sparquote = (akt_spar / akt_einn) * 100
            m1, m2, m3 = st.columns(3)
            m1.metric("Gesamteinnahmen", f"{akt_einn:,.2f} €")
            m2.metric("Sparbetrag Gesamt", f"{akt_spar:,.2f} €")
            m3.metric("Sparquote", f"{sparquote:.2f} %")

            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = sparquote, title = {'text': "Aktuelle Sparquote (%)"},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#2f4b7c"},
                    'steps': [{'range': [0, 10], 'color': "#8B0000"}, {'range': [10, 20], 'color': "#FFFF00"}, {'range': [20, 100], 'color': "#28a745"}]}
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.divider()
            st.write("### 📈 Entwicklung der Sparquote")
            df_v_all, df_e_all = df_ausgaben.copy(), df_einnahmen.copy()
            for d in [df_v_all, df_e_all]:
                if 'Datum' in d.columns:
                    d['Monat_Sort'] = d['Datum'].dt.strftime('%Y-%m')
            
            monate = sorted(list(set(df_v_all['Monat_Sort'].dropna().unique()) | set(df_e_all['Monat_Sort'].dropna().unique())))

            trend_data = []
            fix_e_m = df_fix_einnahmen['Betrag'].sum() if not df_fix_einnahmen.empty else 0
            fix_s_m = df_fixkosten[df_fixkosten['Unterkategorie'] == 'Sparen']['Betrag'].sum() if not df_fixkosten.empty else 0
            
            for m in monate:
                e_m = df_e_all[df_e_all['Monat_Sort'] == m]['Betrag'].sum() + fix_e_m
                s_m = df_v_all[(df_v_all['Monat_Sort'] == m) & (df_v_all['Unterkategorie'] == 'Sparen')]['Betrag'].sum() + fix_s_m
                quote = (s_m / e_m * 100) if e_m > 0 else 0
                y, mn = m.split('-')
                trend_data.append({"Monat": f"{MONATE_DE[mn]} {y}", "Sparquote": quote, "Sort": m})
            
            if trend_data:
                df_trend = pd.DataFrame(trend_data).sort_values("Sort")
                fig_trend = px.line(df_trend, x='Monat', y='Sparquote', markers=True, title="Sparquote im Zeitverlauf (%)")
                fig_trend.update_traces(line_color='#2f4b7c', fill='tozeroy', text=df_trend['Sparquote'].round(1).astype(str) + '%', textposition="top center")
                st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("Keine Einnahmen gefunden.")