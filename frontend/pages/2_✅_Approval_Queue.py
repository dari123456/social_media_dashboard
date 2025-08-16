# frontend/pages/2_✅_Approval_Queue.py
import streamlit as st
import pandas as pd
import sys, os
from pathlib import Path

# add the REPO ROOT (…/social_media_dashboard) to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from backend.bots import orchestrator, config, clients

PLATFORM_EMOJIS = {"facebook": "👍", "instagram": "📸", "twitter": "🐦"}

# --- Helpers that read/write directly to Google Sheets ---
def fetch_awaiting_approval_df() -> pd.DataFrame:
    gc = clients.get_gspread_client()
    rows = []
    for platform_name, platform_cfg in config.PLATFORMS.items():
        try:
            ws = gc.open(platform_cfg.sheet_name).worksheet(platform_cfg.steps['step3'])
            recs = ws.get_all_records()
            if not recs:
                continue
            df = pd.DataFrame(recs)
            if 'Approved_by_human' in df.columns:
                df = df[df['Approved_by_human'].astype(str).str.strip() == ""]
            else:
                df = pd.DataFrame()
            if not df.empty:
                df['platform'] = platform_name
                rows.extend(df.to_dict('records'))
        except Exception as e:
            st.warning(f"[{platform_name}] cannot read approval queue: {e}")
    return pd.DataFrame(rows)

def update_approval_status(platform: str, post_id: str, status: str) -> bool:
    gc = clients.get_gspread_client()
    platform_cfg = config.PLATFORMS.get(platform)
    if not platform_cfg:
        st.error("Platform not found")
        return False
    try:
        spreadsheet = gc.open(platform_cfg.sheet_name)
        ws = spreadsheet.worksheet(platform_cfg.steps['step3'])
        cell = ws.find(post_id)
        if not cell:
            st.error(f"Post ID {post_id} not found.")
            return False
        headers = ws.row_values(1)
        approval_col_index = -1
        for i, header in enumerate(headers):
            if header.strip().lower() == 'approved_by_human':
                approval_col_index = i + 1  # 1-indexed
                break
        if approval_col_index == -1:
            st.error("Could not find 'Approved_by_human' column.")
            return False
        ws.update_cell(cell.row, approval_col_index, status)
        return True
    except Exception as e:
        st.error(f"Update failed: {e}")
        return False

# --- Page Setup and State ---
st.set_page_config(page_title="Approval Queue", page_icon="✅", layout="wide")
st.title("✅ Approval Queue")
st.markdown("Review the generated posts below. Approve them to send to scheduling, or Reject them to remove from the queue.")

if 'posts' not in st.session_state:
    # CHANGED: store list-of-dicts, not a DataFrame
    st.session_state.posts = fetch_awaiting_approval_df().to_dict('records')

if st.button("🔄 Refresh Queue"):
    # CHANGED: same conversion on refresh
    st.session_state.posts = fetch_awaiting_approval_df().to_dict('records')
    st.rerun()

if not st.session_state.posts:
    st.success("🎉 The approval queue is empty! All posts have been reviewed.")
else:
    st.info(f"You have **{len(st.session_state.posts)}** posts awaiting your approval.")
    for i, post in enumerate(st.session_state.posts):
        platform = post.get('platform', 'N/A')
        emoji = PLATFORM_EMOJIS.get(platform, "❓")
        with st.container(border=True):
            col1, col2 = st.columns([1, 3])
            with col1:
                image_url = post.get('Matched_Image_Path')
                if image_url and str(image_url).startswith('http'):
                    st.image(image_url, use_container_width=True)
                else:
                    st.text("No Image")

            with col2:
                st.subheader(f"{emoji} {platform.capitalize()} Post")
                text = post.get('Facebook_Post_Text') or post.get('Instagram_Caption') or post.get('Tweet', '[No text generated]')
                hashtags = post.get('Facebook_Hashtags') or post.get('Instagram_Hashtags', '')
                st.markdown(f"**Post Text:**\n\n{text}")
                if hashtags:
                    st.markdown(f"**Hashtags:**\n\n`{hashtags}`")
                st.markdown(f"**Conclusion:** *{post.get('Conclusion', 'N/A')}*")

                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    approve_key = f"approve-{i}-{post.get('post_id', '')}"
                    if st.button("👍 Approve", key=approve_key, use_container_width=True):
                        with st.spinner("Approving..."):
                            if update_approval_status(platform, post.get('post_id'), "yes"):
                                st.session_state.posts = fetch_awaiting_approval_df().to_dict('records')
                                st.rerun()
                with action_col2:
                    reject_key = f"reject-{i}-{post.get('post_id', '')}"
                    if st.button("👎 Reject", key=reject_key, use_container_width=True):
                        with st.spinner("Rejecting..."):
                            if update_approval_status(platform, post.get('post_id'), "no"):
                                st.session_state.posts = fetch_awaiting_approval_df().to_dict('records')
                                st.rerun()
