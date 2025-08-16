# frontend/pages/3_🗓️_Scheduling_and_Publishing.py
import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
BACKEND_API_URL = "http://localhost:8000"
PLATFORM_EMOJIS = {"facebook": "👍", "instagram": "📸", "twitter": "🐦"}

# --- API Functions ---
def trigger_action(action: str):
    try:
        response = requests.post(f"{BACKEND_API_URL}/api/v1/workflow/{action}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to trigger {action}. Details: {e}")
        return None

def get_posts_from_api(endpoint: str):
    try:
        response = requests.get(f"{BACKEND_API_URL}/api/v1/posts/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch {endpoint} posts. Details: {e}")
        return []

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
            result = trigger_action("schedule")
            if result: st.success("✅ Scheduling started!")
with col2:
    st.warning("**Publish one due post per platform.**")
    if st.button("📡 Publish Next Due Posts (Step 5)", use_container_width=True):
        with st.spinner("Publishing..."):
            result = trigger_action("publish")
            if result: st.success("✅ Publishing started!")

# --- Display Area with Tabs ---
st.markdown("---")
st.header("Content Queues")

# Create tabs for a cleaner layout
tab1, tab2 = st.tabs(["Scheduled", "Published History"])

with tab1:
    st.subheader("Upcoming Scheduled Posts")
    if st.button("🔄 Refresh Schedule"):
        st.rerun()

    scheduled_posts = get_posts_from_api("scheduled")
    if not scheduled_posts:
        st.info("The schedule is empty. Approve posts and run the scheduler.")
    else:
        df_scheduled = pd.DataFrame(scheduled_posts)
        df_scheduled['Platform'] = df_scheduled['platform'].apply(lambda x: f"{PLATFORM_EMOJIS.get(x, '❓')} {x.capitalize()}")
        columns_to_show = ['Platform', 'Scheduled_Time', 'Name', 'Conclusion', 'Posted_Status']
        st.dataframe(df_scheduled[[col for col in columns_to_show if col in df_scheduled.columns]], use_container_width=True)

with tab2:
    st.subheader("Published History")
    if st.button("🔄 Refresh History"):
        st.rerun()

    posted_posts = get_posts_from_api("posted")
    if not posted_posts:
        st.info("No posts have been published yet.")
    else:
        df_posted = pd.DataFrame(posted_posts)
        df_posted['Platform'] = df_posted['platform'].apply(lambda x: f"{PLATFORM_EMOJIS.get(x, '❓')} {x.capitalize()}")
        # Make the post link clickable
        df_posted['Post_Link'] = df_posted['Post_Link'].apply(lambda x: f'<a href="{x}" target="_blank">View Post</a>' if x else "No Link")
        columns_to_show = ['Platform', 'Scheduled_Time', 'Name', 'Post_Link']
        st.markdown(df_posted[[col for col in columns_to_show if col in df_posted.columns]].to_html(escape=False, index=False), unsafe_allow_html=True)