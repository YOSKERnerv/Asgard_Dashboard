import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re
from typing import Optional

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="ASGARD Alliance Dashboard", page_icon="⚔️", layout="wide")

# =========================
# CUSTOM CSS
# =========================
st.markdown(
    """
    <style>
    .main { background-color: #0f1117; color: white; }
    .stApp { background: linear-gradient(to right, #0f1117, #151a28); }
    h1, h2, h3 { color: #00ffd5; }
    .metric-card { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0px 0px 15px rgba(0,255,213,0.15); text-align: center; }
    section[data-testid="stSidebar"] { background: #111827; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# TITLE
# =========================
st.title("⚔️ ASGARD ALLIANCE PERFORMANCE DASHBOARD")
st.markdown("### Advanced Interactive Analytics & Ranking System")

# =========================
# DATA LOADER
# =========================
# (Local upload only) combine all sheets into a commonSheet


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _collapse_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Remove merge suffixes (_x, _y) and merge columns that normalize to the same base name.
    # First, strip _x, _y suffixes from column names
    rename_map = {}
    for c in df.columns:
        if c.endswith('_x') or c.endswith('_y'):
            base = c[:-2]
            rename_map[c] = base
    if rename_map:
        df = df.rename(columns=rename_map)
    
    groups = {}
    for c in df.columns:
        key = _normalize(c)
        groups.setdefault(key, []).append(c)

    out = pd.DataFrame(index=df.index)
    for key, members in groups.items():
        if len(members) == 1:
            out[members[0]] = df[members[0]]
            continue
        # multiple columns with same normalized name: try numeric sum first
        try:
            numeric = df[members].apply(lambda col: pd.to_numeric(col.astype(str).str.replace(r",", "", regex=True), errors='coerce'))
            if numeric.notna().sum().sum() > 0:
                out[members[0]] = numeric.sum(axis=1, skipna=True)
                continue
        except Exception:
            pass
        # fallback: take first non-null value across columns
        out[members[0]] = df[members].bfill(axis=1).iloc[:, 0]

    # ensure canonical Member column name
    for c in list(out.columns):
        if _normalize(c) == 'member' and c != 'Member':
            out.rename(columns={c: 'Member'}, inplace=True)

    return out


def _parse_numeric_series(s: pd.Series) -> pd.Series:
    # Accept either a Series or a DataFrame (duplicate column labels may produce a DataFrame)
    if isinstance(s, pd.DataFrame):
        # coalesce duplicate columns by taking first non-null value across columns
        try:
            s = s.bfill(axis=1).iloc[:, 0]
        except Exception:
            s = s.iloc[:, 0]

    # Convert messy numeric-like text into floats: remove commas, handle dashes and percent signs
    s = s.astype(str).fillna("")
    s = s.str.replace(r"\xa0", "", regex=False)
    s = s.str.replace(r"[,]", "", regex=True)
    s = s.str.strip()
    s = s.replace({'-': None, '—': None, '': None, 'nan': None, 'N/A': None, 'n/a': None})
    # handle percent
    pct = s.str.endswith('%')
    if pct.any():
        try:
            s = s.str.rstrip('%')
            out = pd.to_numeric(s, errors='coerce')
            out[pct] = out[pct] / 100.0
            return out
        except Exception:
            pass
    return pd.to_numeric(s, errors='coerce')


def _detect_columns(df: pd.DataFrame) -> dict:
    cols = {c: c for c in df.columns}
    col_map = {}
    # best candidate for member column: any col with 'member' in name, prefer non-numeric values
    member_cands = [c for c in df.columns if re.search(r'member', c, re.I)]
    if member_cands:
        best = None
        best_score = -1
        for c in member_cands:
            ser = df[c].astype(str)
            score = ser.dropna().map(lambda x: 1 if re.search(r'[A-Za-z]', str(x)) else 0).sum()
            if score > best_score:
                best_score = score
                best = c
        if best:
            col_map['Member'] = best

    # detect duel week columns (look for 'duel' and a week number)
    for c in df.columns:
        m = re.search(r'duel.*?([1-9])', c, re.I)
        if m:
            n = int(m.group(1))
            col_map[f'Duel_W{n}'] = c
        else:
            # fallback: 'week 1' and 'duel' presence
            if re.search(r'week\s*[1-9]', c, re.I) and re.search(r'duel', c, re.I):
                m2 = re.search(r'week\s*([1-9])', c, re.I)
                if m2:
                    col_map[f'Duel_W{int(m2.group(1))}'] = c

    # detect tech week columns
    for c in df.columns:
        m = re.search(r'tech.*?([1-9])', c, re.I)
        if m:
            n = int(m.group(1))
            col_map[f'Tech_W{n}'] = c
        else:
            # sometimes tech sheets have dates only; try to pick month/day patterns with 'May' presence
            if re.search(r'may|apr|jun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec', c, re.I):
                # avoid daily average or 'daily' columns
                if re.search(r'daily|average', c, re.I):
                    continue
                # assign sequentially if not already assigned
                for i in range(1, 5):
                    if f'Tech_W{i}' not in col_map:
                        col_map[f'Tech_W{i}'] = c
                        break

    # If tech columns still not found, fall back to any largely-numeric columns (excluding duel columns)
    tech_needed = [i for i in range(1, 4) if f'Tech_W{i}' not in col_map]
    if tech_needed:
        numeric_scores = []
        for c in df.columns:
            if c in col_map.values():
                continue
            ser = df[c]
            # score by parsable numeric count
            try:
                parsed = pd.to_numeric(ser.astype(str).str.replace(r",", "", regex=True), errors='coerce')
                score = parsed.notna().sum()
            except Exception:
                score = 0
            numeric_scores.append((score, c))
        numeric_scores.sort(reverse=True)
        for idx, (score, c) in enumerate(numeric_scores):
            if idx >= len(tech_needed):
                break
            if score > 20:  # require at least some numeric data
                col_map[f'Tech_W{tech_needed[idx]}'] = c

    # detect CP growth column
    for c in df.columns:
        if re.search(r'23.*day.*growth|23 days growth|23 days|growth|cp', c, re.I):
            col_map['CP_23d_Growth'] = c
            break

    return col_map


@st.cache_data
def load_data(uploaded: Optional[io.BytesIO]) -> pd.DataFrame:
    # Local upload only. If Excel, combine all sheets into a single DataFrame (commonSheet).
    if uploaded is None:
        return pd.DataFrame()

    try:
        uploaded.seek(0)
        name = uploaded.name.lower()
        if name.endswith((".xls", ".xlsx")):
            all_sheets = pd.read_excel(uploaded, sheet_name=None)
            # Build a clean merged dataframe by Member: extract Member + numeric columns from each sheet
            merged = None
            for sheet_name, df in all_sheets.items():
                if not isinstance(df, pd.DataFrame) or df.empty:
                    continue
                # detect columns in this sheet
                det = _detect_columns(df)
                # find a member column for this sheet
                member_col = det.get('Member') or next((c for c in df.columns if re.search(r'member', c, re.I)), None)
                if not member_col:
                    continue
                tmp = pd.DataFrame()
                tmp['Member'] = df[member_col].astype(str).str.strip()
                # bring in any detected duel/tech/cp columns
                for k in ['Duel_W1','Duel_W2','Duel_W3','Duel_W4','Tech_W1','Tech_W2','Tech_W3','CP_23d_Growth']:
                    if k in det and det[k] in df.columns:
                        tmp[k] = _parse_numeric_series(df[det[k]])
                if merged is None:
                    merged = tmp
                else:
                    merged = pd.merge(merged, tmp, on='Member', how='outer')
            if merged is None:
                return pd.DataFrame()
            # After merging, sum duplicate numeric columns (from multiple sheets) into canonical columns
            # Identify numeric-like columns
            numeric_cols = [c for c in merged.columns if re.match(r'Duel_W\d+|Tech_W\d+|CP_23d_Growth', c)]
            # collapse any duplicate columns created by merge (e.g., Duel_W1_x, Duel_W1_y) by grouping Member and summing numerics
            cleaned = merged.copy()
            cleaned[numeric_cols] = cleaned[numeric_cols].apply(pd.to_numeric, errors='coerce')
            cleaned = cleaned.groupby('Member', as_index=False)[numeric_cols].sum()
            cleaned.attrs['commonSheet_created_from'] = list(all_sheets.keys())
            return cleaned
        else:
            return pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Failed to read uploaded file: {e}")
        return pd.DataFrame()

# =========================
# SIDEBAR - Controls
# =========================
st.sidebar.title("⚙️ Dashboard Filters")
uploaded = st.sidebar.file_uploader("Upload Excel/CSV (required)", type=["xlsx", "xls", "csv"])
metric_option = st.sidebar.selectbox("Select Ranking Metric", ['Overall_Score', 'Total_Duel', 'Total_Tech', 'CP_23d_Growth'])
view_option = st.sidebar.radio("Choose View", ['Top 10', 'Bottom 10', 'All Members'])
search_member = st.sidebar.text_input("🔍 Search Member")

st.sidebar.markdown("---")
st.sidebar.subheader("Scoring Weights")
weight_duel = st.sidebar.slider("Duel weight (x1000)", 0.0, 5.0, 1.0)
weight_tech = st.sidebar.slider("Tech weight (x1)", 0.0, 5.0, 1.0)
weight_cp = st.sidebar.slider("CP Growth weight (x100)", 0.0, 5.0, 1.0)

st.sidebar.markdown("---")
st.sidebar.markdown("Upload your local copy if the Google Sheet is private or inaccessible.")


# =========================
# LOAD & VALIDATE DATA
# =========================
consolidated = load_data(uploaded)

# Collapse any duplicate columns that may have been introduced during merging
if not consolidated.empty:
    consolidated = _collapse_duplicate_columns(consolidated)

if consolidated.empty:
    st.error("No data loaded — please upload an Excel/CSV file in the sidebar.")
    if uploaded is not None:
        st.markdown("**Uploaded file preview (first 10 rows):**")
        try:
            uploaded.seek(0)
            if uploaded.name.lower().endswith(('.xls', '.xlsx')):
                preview = pd.read_excel(uploaded, sheet_name=0)
            else:
                preview = pd.read_csv(uploaded)
            st.write(preview.head(10))
            st.markdown("**Detected columns:**")
            st.write(list(preview.columns))
        except Exception as e:
            st.error(f"Failed to parse uploaded file: {e}")
    st.stop()

# If an Excel was uploaded and combined, offer the combined commonSheet for download
if uploaded is not None and uploaded.name.lower().endswith(('.xls', '.xlsx')):
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            consolidated.to_excel(writer, sheet_name='commonSheet', index=False)
        buffer.seek(0)
        st.download_button('Download combined commonSheet.xlsx', data=buffer, file_name='commonSheet.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception:
        pass

# --- Aggregate duplicated member rows into a single row per Member ---
if not consolidated.empty:
    # coalesce any columns that look like member name columns into a single 'Member' column
    member_candidates = [c for c in consolidated.columns if re.search(r'member', c, re.I)]
    if member_candidates:
        consolidated['Member'] = consolidated[member_candidates].bfill(axis=1).iloc[:, 0].astype(str)
        # drop the original member columns except the canonical 'Member' if they existed
        for c in member_candidates:
            if c != 'Member' and c in consolidated.columns:
                try:
                    consolidated.drop(columns=[c], inplace=True)
                except Exception:
                    pass

# -------------------------
# Column mapping UI
# -------------------------
columns = consolidated.columns.tolist()
st.sidebar.markdown("---")
st.sidebar.subheader("Column Mapping (optional)")
auto_map = st.sidebar.checkbox("Auto-detect columns", value=True)
if not auto_map:
    member_col = st.sidebar.selectbox("Member column", options=columns)
    duel_cols = st.sidebar.multiselect("Duel columns (weeks)", options=columns)
    tech_cols = st.sidebar.multiselect("Tech columns (weeks)", options=columns)
    cp_col = st.sidebar.selectbox("CP growth column (optional)", options=[''] + columns)
else:
    member_col = None
    duel_cols = []
    tech_cols = []
    cp_col = ''


# =========================
# FLEXIBLE COLUMN MAPPING
# =========================
expected_cols = [
    'Member', 'Duel_W1', 'Duel_W2', 'Duel_W3', 'Duel_W4',
    'Tech_W1', 'Tech_W2', 'Tech_W3', 'CP_23d_Growth',
    'Is_On_Kicking_List', 'Kick_Tech_Status', 'Kick_Duel_Status', 'Kick_Tier', 'Kick_Notes'
]

col_map = {}
for exp in expected_cols:
    for col in consolidated.columns:
        if _normalize(exp) == _normalize(col) or _normalize(exp) in _normalize(col) or _normalize(col) in _normalize(exp):
            col_map[exp] = col
            break

# If expected-based mapping didn't find everything, try smarter detection
detected = _detect_columns(consolidated)
for k, v in detected.items():
    # do not overwrite explicit mappings found from expected_cols
    if k not in col_map:
        col_map[k] = v

# Ensure no duplicate columns before renaming
consolidated = _collapse_duplicate_columns(consolidated)

# Standardize column names to user's format
standard_rename = {
    'Duel_W1': 'duelWeek_1',
    'Duel_W2': 'duelWeek_2',
    'Duel_W3': 'duelWeek_3',
    'Duel_W4': 'duelWeek_4',
    'Tech_W1': 'techWeek_1',
    'Tech_W2': 'techWeek_2',
    'Tech_W3': 'techWeek_3',
    'Tech_W4': 'techWeek_4',
    'CP_23d_Growth': 'member_CP',
}

if col_map:
    consolidated = consolidated.rename(columns={v: k for k, v in col_map.items()})

# Apply standard naming
consolidated = consolidated.rename(columns=standard_rename)


# =========================
# CLEAN & PREPARE
# =========================
# If user provided manual mapping, use it. Otherwise rely on auto-detected columns.
if member_col:
    # map member column
    consolidated['Member'] = consolidated[member_col].astype(str)

# Normalize numeric columns or mapped columns (use new standard names)
if auto_map:
    numeric_cols = ['duelWeek_1', 'duelWeek_2', 'duelWeek_3', 'duelWeek_4', 'techWeek_1', 'techWeek_2', 'techWeek_3', 'member_CP']
    for c in numeric_cols:
        if c in consolidated.columns:
            consolidated[c] = _parse_numeric_series(consolidated[c])

    consolidated['Total_Duel'] = consolidated[[c for c in ['duelWeek_1','duelWeek_2','duelWeek_3','duelWeek_4'] if c in consolidated.columns]].sum(axis=1)
    consolidated['Total_Tech'] = consolidated[[c for c in ['techWeek_1','techWeek_2','techWeek_3'] if c in consolidated.columns]].sum(axis=1)
    cp_series = consolidated['member_CP'] if 'member_CP' in consolidated.columns else pd.Series(0, index=consolidated.index)
else:
    # manual mapping
    # coerce selected duel/tech cols
    if duel_cols:
        for c in duel_cols:
            consolidated[c] = _parse_numeric_series(consolidated[c])
        consolidated['Total_Duel'] = consolidated[duel_cols].sum(axis=1)
    else:
        consolidated['Total_Duel'] = 0

    if tech_cols:
        for c in tech_cols:
            consolidated[c] = _parse_numeric_series(consolidated[c])
        consolidated['Total_Tech'] = consolidated[tech_cols].sum(axis=1)
    else:
        consolidated['Total_Tech'] = 0

    if cp_col and cp_col in consolidated.columns:
        cp_series = _parse_numeric_series(consolidated[cp_col])
    else:
        cp_series = pd.Series(0, index=consolidated.index)

# Ensure Member exists and drop NA
if 'Member' in consolidated.columns:
    consolidated = consolidated.dropna(subset=['Member'])
else:
    st.error("No `Member` column found. Use column mapping to select the member column.")
    st.stop()

# Show detected mapping and sample parsed numeric columns for verification
with st.expander("Detected column mapping and sample values", expanded=True):
    st.write({k: v for k, v in col_map.items()})
    sample_cols = [c for c in ['Member', 'duelWeek_1','duelWeek_2','duelWeek_3','duelWeek_4','techWeek_1','techWeek_2','techWeek_3','member_CP','Total_Duel','Total_Tech'] if c in consolidated.columns]
    if sample_cols:
        # Ensure no duplicate columns before display
        display_df = consolidated[sample_cols].copy()
        # Check for and remove any remaining duplicates
        if len(display_df.columns) != len(set(display_df.columns)):
            display_df = display_df.loc[:, ~display_df.columns.duplicated(keep='first')]
        st.write(display_df.head(10))

# Aggregate per-member so each member appears once (sum numeric weeks)
agg_numeric = [c for c in consolidated.columns if re.match(r'duelWeek_\d+|techWeek_\d+|member_CP|Total_Duel|Total_Tech', c)]
other_cols = [c for c in consolidated.columns if c not in agg_numeric and c != 'Member']

# Add kickingList column if not present (default 0 for all members)
if 'kickingList' not in consolidated.columns:
    consolidated['kickingList'] = 0
if len(consolidated) > 0:
    consolidated = consolidated.groupby('Member', as_index=False).agg({**{c: 'sum' for c in agg_numeric}, **{c: 'first' for c in other_cols}})

    # offer aggregated commonSheet for download (one row per Member)
    try:
        agg_buffer = io.BytesIO()
        with pd.ExcelWriter(agg_buffer, engine='openpyxl') as writer:
            consolidated.to_excel(writer, sheet_name='commonSheet', index=False)
        agg_buffer.seek(0)
        st.download_button('Download aggregated commonSheet.xlsx', data=agg_buffer, file_name='commonSheet_aggregated.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception:
        pass

    # Ensure `Member` column exists after aggregation; try to recover from index or infer a member-like column
    if 'Member' not in consolidated.columns:
        if consolidated.index.name:
            consolidated = consolidated.reset_index()
        else:
            # infer a member column by looking for a column with many alphabetic values
            for c in consolidated.columns:
                try:
                    ser = consolidated[c].astype(str)
                    if ser.str.contains(r'[A-Za-z]').sum() > (len(ser) * 0.5):
                        consolidated.rename(columns={c: 'Member'}, inplace=True)
                        break
                except Exception:
                    continue
        if 'Member' not in consolidated.columns:
            consolidated['Member'] = consolidated.index.astype(str)

    # Ensure Member is string
    consolidated['Member'] = consolidated['Member'].astype(str)

# Interactive overall score using sidebar weights
consolidated['Overall_Score'] = (
    consolidated['Total_Duel'].fillna(0) * (1000 * weight_duel) +
    consolidated['Total_Tech'].fillna(0) * weight_tech +
    cp_series.fillna(0) * (100 * weight_cp)
)


# =========================
# FILTER & SORT
# =========================
filtered_df = consolidated.copy()
if search_member:
    filtered_df = filtered_df[filtered_df['Member'].astype(str).str.contains(search_member, case=False)]

if view_option == 'Top 10':
    filtered_df = filtered_df.sort_values(by=metric_option, ascending=False).head(10)
elif view_option == 'Bottom 10':
    filtered_df = filtered_df.sort_values(by=metric_option, ascending=True).head(10)
else:
    filtered_df = filtered_df.sort_values(by=metric_option, ascending=False)


# =========================
# KPI CARDS
# =========================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class='metric-card'><h3>👥 Members</h3><h1>{len(consolidated)}</h1></div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class='metric-card'><h3>⚔️ Total Duel</h3><h1>{round(consolidated.get('Total_Duel', pd.Series()).sum(), 2)}</h1></div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class='metric-card'><h3>🧪 Total Tech</h3><h1>{round(consolidated.get('Total_Tech', pd.Series()).sum(), 2)}</h1></div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class='metric-card'><h3>🚀 Total CP Growth</h3><h1>{round(consolidated.get('CP_23d_Growth', pd.Series()).sum(), 2)}</h1></div>
    """, unsafe_allow_html=True)

st.markdown("---")


# =========================
# LEADERBOARD
# =========================
st.subheader("🏆 Alliance Leaderboard")
# Ensure filtered_df has a Member column (may be in the index after grouping)
if 'Member' not in filtered_df.columns:
    try:
        filtered_df = filtered_df.reset_index()
    except Exception:
        pass
    if 'Member' not in filtered_df.columns:
        # try to find a likely member-like column
        for c in filtered_df.columns:
            try:
                ser = filtered_df[c].astype(str)
                if ser.str.contains(r'[A-Za-z]').sum() > (len(ser) * 0.5):
                    filtered_df.rename(columns={c: 'Member'}, inplace=True)
                    break
            except Exception:
                continue
    if 'Member' not in filtered_df.columns:
        filtered_df['Member'] = filtered_df.index.astype(str)

display_cols = [c for c in ['Member','Total_Duel','Total_Tech','member_CP','Overall_Score'] if c in filtered_df.columns]
if display_cols:
    # Remove any duplicate column names
    display_cols = list(dict.fromkeys(display_cols))
    try:
        st.dataframe(filtered_df[display_cols], use_container_width=True, height=450)
    except Exception as e:
        st.error(f"Error displaying leaderboard: {e}")


# =========================
# BAR CHART
# =========================
st.subheader("📊 Performance Comparison")
if metric_option in filtered_df.columns:
    fig_bar = px.bar(filtered_df, x='Member', y=metric_option, color=metric_option, text_auto=True, template='plotly_dark', title=f'{metric_option} Ranking')
    fig_bar.update_layout(height=550, xaxis_title='Members', yaxis_title=metric_option, title_x=0.5)
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info(f"Metric '{metric_option}' not found in data.")


# =========================
# RADAR CHART
# =========================
st.subheader("🛡️ Multi-Metric Radar Analysis")
radar_metrics = [m for m in ['Total_Duel','Total_Tech','member_CP'] if m in filtered_df.columns]
radar_df = filtered_df.head(5)
fig_radar = go.Figure()
for _, r in radar_df.iterrows():
    fig_radar.add_trace(go.Scatterpolar(r=[r.get(m, 0) or 0 for m in radar_metrics], theta=[m.replace('_',' ') for m in radar_metrics], fill='toself', name=r.get('Member')))
fig_radar.update_layout(template='plotly_dark', polar=dict(radialaxis=dict(visible=True)), height=600)
st.plotly_chart(fig_radar, use_container_width=True)


# =========================
# PIE CHART
# =========================
st.subheader("🎯 Contribution Distribution")
pie_metric = st.selectbox("Choose Distribution Metric", radar_metrics)
if pie_metric:
    pie_df = filtered_df[['Member', pie_metric]].dropna()
    fig_pie = px.pie(pie_df, names='Member', values=pie_metric, template='plotly_dark', hole=0.45)
    fig_pie.update_layout(height=600)
    st.plotly_chart(fig_pie, use_container_width=True)


# =========================
# MEMBER ANALYSIS
# =========================
st.subheader("🔎 Individual Member Analysis")
# Ensure members are strings and sort case-insensitively to avoid mixed-type comparison errors
try:
    members = consolidated['Member'].dropna().astype(str).unique().tolist()
except Exception:
    try:
        consolidated = consolidated.reset_index()
        if 'Member' in consolidated.columns:
            members = consolidated['Member'].dropna().astype(str).unique().tolist()
        else:
            members = consolidated.index.astype(str).unique().tolist()
    except Exception:
        members = []
members.sort(key=lambda x: x.lower())
member_choice = st.selectbox("Select Member", members)
try:
    member_df = consolidated[consolidated['Member'] == member_choice]
except Exception:
    try:
        tmp = consolidated.reset_index()
        if 'Member' in tmp.columns:
            member_df = tmp[tmp['Member'] == member_choice]
            consolidated = tmp
        else:
            member_df = consolidated.loc[consolidated.index.astype(str) == member_choice]
            if isinstance(member_df, pd.Series):
                member_df = member_df.to_frame().T
    except Exception:
        member_df = pd.DataFrame()

if not member_df.empty:
    member_data = pd.DataFrame({
        'Metric': ['Duel W1','Duel W2','Duel W3','Duel W4','Tech W1','Tech W2','Tech W3'],
        'Value': [
            member_df.get('Duel_W1').values[0] if 'Duel_W1' in member_df else None,
            member_df.get('Duel_W2').values[0] if 'Duel_W2' in member_df else None,
            member_df.get('Duel_W3').values[0] if 'Duel_W3' in member_df else None,
            member_df.get('Duel_W4').values[0] if 'Duel_W4' in member_df else None,
            member_df.get('Tech_W1').values[0] if 'Tech_W1' in member_df else None,
            member_df.get('Tech_W2').values[0] if 'Tech_W2' in member_df else None,
            member_df.get('Tech_W3').values[0] if 'Tech_W3' in member_df else None,
        ]
    })
    fig_member = px.line(member_data, x='Metric', y='Value', markers=True, template='plotly_dark', title=f'{member_choice} Performance Trend')
    fig_member.update_layout(height=500)
    st.plotly_chart(fig_member, use_container_width=True)


# Download filtered data
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("Download filtered CSV", data=csv, file_name='filtered_members.csv', mime='text/csv')


# =========================
# KICKING LIST ANALYSIS
# =========================
st.subheader("⚠️ Kicking Queue Review")
kick_col = 'kickingList'
if kick_col in consolidated.columns:
    kick_df = consolidated[consolidated[kick_col] == 1]
else:
    kick_df = pd.DataFrame()

if not kick_df.empty:
    show_cols = [c for c in ['Member','Total_Duel','Total_Tech','member_CP','kickingList'] if c in kick_df.columns]
    st.dataframe(kick_df[show_cols], use_container_width=True)
else:
    st.success("No members currently in kicking review list.")


# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("""
<center>
<h4 style='color:#00ffd5;'>⚔️ ASGARD ALLIANCE ANALYTICS SYSTEM ⚔️</h4>
<p style='color:gray;'>Modern Interactive Performance Intelligence Dashboard</p>
</center>
""", unsafe_allow_html=True)
