import os
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Shorts Analytics Dashboard", page_icon="🎬", layout="wide"
)

# --- SLEEK CSS STYLING ---
st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
        
        div[data-testid="stMetricValue"] {
            font-size: 22px;
            font-weight: 700;
            color: #7c3aed;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SUPABASE CONNECTION (USING STREAMLIT SECRETS) ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- DATA FETCHING ---
@st.cache_data(ttl=60)
def load_data():
    tracked_res = supabase.table("tracked_videos").select("*").execute()
    df_tracked = pd.DataFrame(tracked_res.data)

    views_res = (
        supabase.table("short_views")
        .select("*")
        .order("updated_at", desc=False)
        .execute()
    )
    df_views = pd.DataFrame(views_res.data)

    if not df_views.empty:
        df_views["updated_at"] = pd.to_datetime(df_views["updated_at"])
        df_views["videocount"] = pd.to_numeric(df_views["videocount"])

    return df_tracked, df_views


df_tracked, df_views = load_data()

# --- HEADER SECTION ---
st.title("🎬 Shorts Analytics Dashboard")
st.caption(
    "⚡ Automated 30-min view tracking for 30 active days | 📦 Historical data preserved for 6 months"
)

if df_tracked.empty or df_views.empty:
    st.info(
        "No data available yet. Make sure videos are in `tracked_videos` and `track.py` has run!"
    )
    st.stop()

# Merge title into views dataframe for easy access if available
if "title" not in df_tracked.columns:
    df_tracked["title"] = df_tracked["videoid"]  # fallback if column missing

df_views = df_views.merge(
    df_tracked[["videoid", "title"]], on="videoid", how="left"
)
df_views["title"] = df_views["title"].fillna(df_views["videoid"])

# --- HELPER LOGIC FOR KPIS & VELOCITY ---
latest_per_video = (
    df_views.sort_values("updated_at")
    .groupby("videoid")
    .last()
    .reset_index()
)
total_views_overall = latest_per_video["videocount"].sum()
top_performing_row = latest_per_video.sort_values(
    "videocount", ascending=False
).iloc[0]


def get_velocity_metrics(df_sub):
    if df_sub.empty:
        return 0, 0, 0, 0

    latest_time = df_sub["updated_at"].max()
    latest_val = df_sub.iloc[-1]["videocount"]

    def calc_delta(hours):
        cutoff = latest_time - pd.Timedelta(hours=hours)
        past_rows = df_sub[df_sub["updated_at"] <= cutoff]
        if not past_rows.empty:
            return latest_val - past_rows.iloc[-1]["videocount"]
        return latest_val - df_sub.iloc[0]["videocount"]

    return (
        calc_delta(24),
        calc_delta(24 * 7),
        calc_delta(24 * 15),
        calc_delta(24 * 30),
    )


# --- TOP-LEVEL OVERALL KPIS ---
kpi_col1, kpi_col2 = st.columns(2)

with kpi_col1:
    with st.container(border=True):
        st.caption("🌐 TOTAL VIEWS OVERALL")
        st.header(f"{total_views_overall:,}")

with kpi_col2:
    with st.container(border=True):
        st.caption("🏆 TOP PERFORMING REEL")
        top_vid_id = top_performing_row["videoid"]
        top_title = top_performing_row["title"]
        top_url = f"https://youtube.com/shorts/{top_vid_id}"
        top_thumb = f"https://img.youtube.com/vi/{top_vid_id}/hqdefault.jpg"

        top_left, top_right = st.columns([1, 2])
        with top_left:
            st.image(top_thumb, use_column_width=True)
        with top_right:
            st.header(f"{top_performing_row['videocount']:,} views")
            st.markdown(f"**{top_title}**")
            st.markdown(f"🔗 [Watch on YouTube]({top_url})")

st.write("---")

# --- INTERACTIVE SELECTION STATE ---
if "selected_video_id" not in st.session_state:
    st.session_state.selected_video_id = df_tracked["videoid"].iloc[0]

selected_id = st.session_state.selected_video_id
selected_row = df_tracked[df_tracked["videoid"] == selected_id]
selected_title = (
    selected_row["title"].values[0]
    if not selected_row.empty and pd.notna(selected_row["title"].values[0])
    else selected_id
)
selected_url = f"https://youtube.com/shorts/{selected_id}"

# --- SINGLE TARGETED GRAPH & METRICS ---
df_selected = df_views[df_views["videoid"] == selected_id].sort_values(
    "updated_at"
)

with st.container(border=True):
    st.subheader(f"📊 Detailed Analytics — {selected_title}")
    st.markdown(f"🔗 **Direct URL:** [{selected_url}]({selected_url})")

    col_thumb, col_chart = st.columns([1, 2.5])

    with col_thumb:
        thumb_url = f"https://img.youtube.com/vi/{selected_id}/hqdefault.jpg"
        st.image(thumb_url, use_column_width=True, caption=selected_title)

    with col_chart:
        v_24h, v_7d, v_15d, v_30d = get_velocity_metrics(df_selected)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("24h Gain", f"+{v_24h:,}")
        m2.metric("7d Gain", f"+{v_7d:,}")
        m3.metric("15d Gain", f"+{v_7d:,}")
        m4.metric("30d Gain", f"+{v_30d:,}")

        fig = px.line(
            df_selected,
            x="updated_at",
            y="videocount",
            markers=True,
            labels={"updated_at": "Timestamp", "videocount": "Total Views"},
        )

        fig.update_traces(
            line_color="#7c3aed",
            line_width=3,
            marker=dict(size=6, color="#a855f7"),
        )
        fig.update_layout(
            template="plotly_dark",
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

# --- SHORTS DIRECTORY GRID ---
st.subheader("📱 Tracked Shorts Directory")
st.caption("Click any card below to focus its individual graph above")

directory_cols = st.columns(3)
for idx, row in df_tracked.iterrows():
    vid = row["videoid"]
    v_title = row.get("title") if pd.notna(row.get("title")) else vid
    short_url = f"https://youtube.com/shorts/{vid}"

    vid_views_df = df_views[df_views["videoid"] == vid]
    latest_val = (
        vid_views_df.iloc[-1]["videocount"] if not vid_views_df.empty else 0
    )
    thumb_url = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"

    col_target = directory_cols[idx % 3]
    with col_target:
        with st.container(border=True):
            st.image(thumb_url, use_column_width=True)
            st.markdown(f"**{v_title}**")
            st.markdown(f"🔗 [Watch Short]({short_url})")
            st.write(f"👁️ **{latest_val:,}** views")
            st.caption("🟢 Active (30-day window)")

            if st.button(
                f"📈 Select Video", key=f"btn_{vid}", use_container_width=True
            ):
                st.session_state.selected_video_id = vid
                st.rerun()

# --- RAW DATA EXPANDER ---
with st.expander("View Raw Database Entries"):
    st.dataframe(df_views)
