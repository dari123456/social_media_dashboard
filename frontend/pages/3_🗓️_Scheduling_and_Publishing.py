# frontend/pages/3_🗓️_Scheduling_and_Publishing.py
import streamlit as st
import pandas as pd
import sys, os
from pathlib import Path

# add the REPO ROOT (…/social_media_dashboard) to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# now these imports will work
# use the ones needed per page:
from backend.bots import orchestrator, config, clients


PLATFORM_EMOJIS = {"facebook": "👍", "instagram": "📸", "twitter": "🐦"}

# --- Helpers for Sheets ---
def fetch_scheduled_posts_df() -> pd.DataFrame:
    gc = clients.get_gspread_client()
    rows = []
    for platform_name, platform_cfg in config.PLATFORMS.items():
        try:
            ws = gc.open(platform_cfg.sheet_name).worksheet(platform_cfg.steps['step4'])
            records = ws.get_all_records()
            for r in records:
                r['platform'] = platform_name
                rows.append(r)
        except Exception as e:
            st.warning(f"[{platform_name}] cannot read schedule: {e}")
    df = pd.DataFrame(rows)
    if not df.empty and 'Scheduled_Time' in df.columns:
        df = df.sort_values('Scheduled_Time', na_position='last')
    return df

def fetch_posted_history_df() -> pd.DataFrame:
    gc = clients.get_gspread_client()
    rows = []
    for platform_name, platform_cfg in config.PLATFORMS.items():
        try:
            ws = gc.open(platform_cfg.sheet_name).worksheet(platform_cfg.steps['step4'])
            records = ws.get_all_records()
            for r in records:
                if str(r.get('Posted_Status', '')).strip() == 'Posted':
                    r['platform'] = platform_name
                    rows.append(r)
        except Exception as e:
            st.warning(f"[{platform_name}] cannot read posted history: {e}")
    df = pd.DataFrame(rows)
    if not df.empty and 'Scheduled_Time' in df.columns:
        df = df.sort_values('Scheduled_Time', ascending=False, na_position='last')
    return df

# --- Page Setup ---
st.set_page_config(page_title="Scheduling & Publishing", page_icon="🗓️", layout="wide")
st.title("🗓️ Scheduling & Publishing Command Center")
st.markdown("---")

# --- Workflow Controls ---
st.header("Workflow Controls")
col1, col2 = st.columns(2)
with col1:
    st.info("**Update the schedule from all approved posts.**")
    if st.button("🚀 Run Scheduler (Step 4)", use_container_width=True):
        with st.spinner("Building the schedule..."):
            orchestrator.run_scheduling_for_all_platforms()
            st.success("✅ Scheduling started (direct call).")
with col2:
    st.warning("**Publish one due post per platform.**")
    if st.button("📡 Publish Next Due Posts (Step 5)", use_container_width=True):
        with st.spinner("Publishing..."):
            orchestrator.run_publishing_for_all_platforms()
            st.success("✅ Publishing run started (direct call).")

# --- Display Area with Tabs ---
st.markdown("---")
st.header("Content Queues")

tab1, tab2 = st.tabs(["Scheduled", "Published History"])

with tab1:
    st.subheader("Upcoming Scheduled Posts")
    if st.button("🔄 Refresh Schedule"):
        st.rerun()

    df_scheduled = fetch_scheduled_posts_df()
    if df_scheduled.empty:
        st.info("The schedule is empty. Approve posts and run the scheduler.")
    else:
        df_scheduled['Platform'] = df_scheduled['platform'].apply(lambda x: f"{PLATFORM_EMOJIS.get(x, '❓')} {x.capitalize()}")
        columns_to_show = ['Platform', 'Scheduled_Time', 'Name', 'Conclusion', 'Posted_Status']
        st.dataframe(df_scheduled[[c for c in columns_to_show if c in df_scheduled.columns]], use_container_width=True)

with tab2:
    st.subheader("Published History")
    if st.button("🔄 Refresh History"):
        st.rerun()

    df_posted = fetch_posted_history_df()
    if df_posted.empty:
        st.info("No posts have been published yet.")
    else:
        df_posted['Platform'] = df_posted['platform'].apply(lambda x: f"{PLATFORM_EMOJIS.get(x, '❓')} {x.capitalize()}")
        if 'Post_Link' in df_posted.columns:
            df_posted['Post_Link'] = df_posted['Post_Link'].apply(lambda x: f'<a href="{x}" target="_blank">View Post</a>' if x else "No Link")
            cols = ['Platform', 'Scheduled_Time', 'Name', 'Post_Link']
            st.markdown(df_posted[[c for c in cols if c in df_posted.columns]].to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.dataframe(df_posted, use_container_width=True)
