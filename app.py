import streamlit as st
from supabase import create_client
import pandas as pd

# Page Configuration
st.set_page_config(page_title="YouTube Shorts Tracker", page_icon="📊", layout="wide")

st.title("📊 YouTube Shorts View History Dashboard")
st.markdown("Tracking hourly view growth automatically.")

# Retrieve secrets safely from Streamlit Cloud settings
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch Data
@st.cache_data(ttl=60)
def load_data():
    response = supabase.table("short_views").select("*").execute()
    return pd.DataFrame(response.data)

df = load_data()

if df.empty:
    st.info("No view entries found in database yet.")
else:
    # Ensure proper data formats
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    df["videocount"] = pd.to_numeric(df["videocount"])

    # Line Chart for View Growth Over Time
    st.subheader("📈 View Growth Timeline")
    chart_data = df.pivot(index="updated_at", columns="videoid", values="videocount")
    st.line_chart(chart_data)

    # Raw Data Table Toggle
    with st.expander("View Raw Database Entries"):
        st.dataframe(df)
