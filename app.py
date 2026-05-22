
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="ASGARD Alliance Dashboard",
    page_icon="⚔️",
    layout="wide"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown(
    """
    <style>
    .main {
        background-color: #0f1117;
        color: white;
    }

    .stApp {
        background: linear-gradient(to right, #0f1117, #151a28);
    }

    h1, h2, h3 {
        color: #00ffd5;
    }

    .metric-card {
        background: rgba(255,255,255,0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0px 0px 15px rgba(0,255,213,0.15);
        text-align: center;
    }

    .dataframe {
        color: white;
    }

    section[data-testid="stSidebar"] {
        background: #111827;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# TITLE
# =========================
st.title("⚔️ ASGARD ALLIANCE PERFORMANCE DASHBOARD")
st.markdown("### Advanced Interactive Analytics & Ranking System")

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=60)
def load_data():

    sheet_id = "1pJUuzkhPdbC7KVqrS1mxKxtY2CsACyyTwAnxF6VEYYo"

    sheet_name = "Consolidated_Data"

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    df = pd.read_csv(url)

    return df

consolidated = load_data()

# =========================
# CLEAN DATA
# =========================
consolidated = consolidated.dropna(subset=['Member'])

numeric_cols = [
    'Duel_W1', 'Duel_W2', 'Duel_W3', 'Duel_W4',
    'Tech_W1', 'Tech_W2', 'Tech_W3',
    'CP_23d_Growth'
]

for col in numeric_cols:
    if col in consolidated.columns:
        consolidated[col] = pd.to_numeric(consolidated[col], errors='coerce')

# =========================
# CREATE TOTALS
# =========================
consolidated['Total_Duel'] = consolidated[['Duel_W1','Duel_W2','Duel_W3','Duel_W4']].sum(axis=1)

consolidated['Total_Tech'] = consolidated[['Tech_W1','Tech_W2','Tech_W3']].sum(axis=1)

consolidated['Overall_Score'] = (
    consolidated['Total_Duel'].fillna(0) * 1000 +
    consolidated['Total_Tech'].fillna(0) +
    consolidated['CP_23d_Growth'].fillna(0) * 100
)

# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.title("⚙️ Dashboard Filters")

metric_option = st.sidebar.selectbox(
    "Select Ranking Metric",
    [
        'Overall_Score',
        'Total_Duel',
        'Total_Tech',
        'CP_23d_Growth'
    ]
)

view_option = st.sidebar.radio(
    "Choose View",
    ['Top 10', 'Bottom 10', 'All Members']
)

search_member = st.sidebar.text_input("🔍 Search Member")

# =========================
# FILTER DATA
# =========================
filtered_df = consolidated.copy()

if search_member:
    filtered_df = filtered_df[
        filtered_df['Member'].astype(str).str.contains(search_member, case=False)
    ]

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
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3>👥 Members</h3>
            <h1>{len(consolidated)}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3>⚔️ Total Duel</h3>
            <h1>{round(consolidated['Total_Duel'].sum(), 2)}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3>🧪 Total Tech</h3>
            <h1>{round(consolidated['Total_Tech'].sum(), 2)}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div class='metric-card'>
            <h3>🚀 Total CP Growth</h3>
            <h1>{round(consolidated['CP_23d_Growth'].sum(), 2)}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# =========================
# LEADERBOARD
# =========================
st.subheader("🏆 Alliance Leaderboard")

leaderboard = filtered_df[[
    'Member',
    'Total_Duel',
    'Total_Tech',
    'CP_23d_Growth',
    'Overall_Score'
]]

st.dataframe(
    leaderboard,
    use_container_width=True,
    height=450
)

# =========================
# BAR CHART
# =========================
st.subheader("📊 Performance Comparison")

fig_bar = px.bar(
    filtered_df,
    x='Member',
    y=metric_option,
    color=metric_option,
    text_auto=True,
    template='plotly_dark',
    title=f'{metric_option} Ranking'
)

fig_bar.update_layout(
    height=550,
    xaxis_title='Members',
    yaxis_title=metric_option,
    title_x=0.5
)

st.plotly_chart(fig_bar, use_container_width=True)

# =========================
# RADAR CHART
# =========================
st.subheader("🛡️ Multi-Metric Radar Analysis")

radar_df = filtered_df.head(5)

fig_radar = go.Figure()

for _, row in radar_df.iterrows():
    fig_radar.add_trace(go.Scatterpolar(
        r=[
            row['Total_Duel'] if pd.notna(row['Total_Duel']) else 0,
            row['Total_Tech'] if pd.notna(row['Total_Tech']) else 0,
            row['CP_23d_Growth'] if pd.notna(row['CP_23d_Growth']) else 0
        ],
        theta=['Duel', 'Tech', 'CP Growth'],
        fill='toself',
        name=row['Member']
    ))

fig_radar.update_layout(
    template='plotly_dark',
    polar=dict(radialaxis=dict(visible=True)),
    height=600
)

st.plotly_chart(fig_radar, use_container_width=True)

# =========================
# PIE CHART
# =========================
st.subheader("🎯 Contribution Distribution")

pie_metric = st.selectbox(
    "Choose Distribution Metric",
    ['Total_Duel', 'Total_Tech', 'CP_23d_Growth']
)

pie_df = filtered_df[['Member', pie_metric]].dropna()

fig_pie = px.pie(
    pie_df,
    names='Member',
    values=pie_metric,
    template='plotly_dark',
    hole=0.45
)

fig_pie.update_layout(height=600)

st.plotly_chart(fig_pie, use_container_width=True)

# =========================
# MEMBER ANALYSIS
# =========================
st.subheader("🔎 Individual Member Analysis")

member_choice = st.selectbox(
    "Select Member",
    consolidated['Member'].dropna().unique()
)

member_df = consolidated[consolidated['Member'] == member_choice]

if not member_df.empty:

    member_data = pd.DataFrame({
        'Metric': [
            'Duel W1',
            'Duel W2',
            'Duel W3',
            'Duel W4',
            'Tech W1',
            'Tech W2',
            'Tech W3'
        ],
        'Value': [
            member_df['Duel_W1'].values[0],
            member_df['Duel_W2'].values[0],
            member_df['Duel_W3'].values[0],
            member_df['Duel_W4'].values[0],
            member_df['Tech_W1'].values[0],
            member_df['Tech_W2'].values[0],
            member_df['Tech_W3'].values[0]
        ]
    })

    fig_member = px.line(
        member_data,
        x='Metric',
        y='Value',
        markers=True,
        template='plotly_dark',
        title=f'{member_choice} Performance Trend'
    )

    fig_member.update_layout(height=500)

    st.plotly_chart(fig_member, use_container_width=True)

# =========================
# KICKING LIST ANALYSIS
# =========================
st.subheader("⚠️ Kicking Queue Review")

kick_df = consolidated[
    consolidated['Is_On_Kicking_List'] == True
]

if not kick_df.empty:
    st.dataframe(
        kick_df[[
            'Member',
            'Kick_Tech_Status',
            'Kick_Duel_Status',
            'Kick_Tier',
            'Kick_Notes'
        ]],
        use_container_width=True
    )

else:
    st.success("No members currently in kicking review list.")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    """
    <center>
    <h4 style='color:#00ffd5;'>⚔️ ASGARD ALLIANCE ANALYTICS SYSTEM ⚔️</h4>
    <p style='color:gray;'>Modern Interactive Performance Intelligence Dashboard</p>
    </center>
    """,
    unsafe_allow_html=True
)
