# frontend/pages/2_✅_Approval_Queue.py
import streamlit as st
import requests

# --- Configuration ---
BACKEND_API_URL = "http://localhost:8000"
PLATFORM_EMOJIS = {
    "facebook": "👍",
    "instagram": "📸",
    "twitter": "🐦"
}

# --- API Functions ---
def get_posts_to_approve():
    """Fetches all posts awaiting approval from the backend API."""
    try:
        response = requests.get(f"{BACKEND_API_URL}/api/v1/posts/awaiting-approval")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to connect to the backend API. Is it running? Details: {e}")
        return []

def send_post_action(action: str, platform: str, post_id: str):
    """Sends an 'approve' or 'reject' request to the backend."""
    try:
        payload = {"platform": platform, "post_id": post_id}
        response = requests.post(f"{BACKEND_API_URL}/api/v1/posts/{action}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to {action} post. Details: {e}")
        return None

# --- Page Setup and State Management ---
st.set_page_config(page_title="Approval Queue", page_icon="✅", layout="wide")

if 'posts' not in st.session_state:
    st.session_state.posts = get_posts_to_approve()

# --- Page Display ---
st.title("✅ Approval Queue")
st.markdown("Review the generated posts below. Approve them to send to scheduling, or Reject them to remove from the queue.")

if st.button("🔄 Refresh Queue"):
    st.session_state.posts = get_posts_to_approve()
    st.rerun()

if not st.session_state.posts:
    st.success("🎉 The approval queue is empty! All posts have been reviewed.")
else:
    st.info(f"You have **{len(st.session_state.posts)}** posts awaiting your approval.")
    
    # Use enumerate to get a unique index for each post
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
                
                # --- Action Buttons ---
                action_col1, action_col_2 = st.columns(2)
                
                with action_col1:
                    # THE FIX: The key now uses the index 'i' to guarantee uniqueness
                    approve_key = f"approve-{i}-{post.get('post_id', '')}"
                    if st.button("👍 Approve", key=approve_key, use_container_width=True):
                        with st.spinner("Approving..."):
                            send_post_action("approve", platform, post.get('post_id'))
                            st.session_state.posts = get_posts_to_approve() # Refresh data
                            st.rerun()

                with action_col_2:
                    reject_key = f"reject-{i}-{post.get('post_id', '')}"
                    if st.button("👎 Reject", key=reject_key, use_container_width=True):
                        with st.spinner("Rejecting..."):
                            send_post_action("reject", platform, post.get('post_id'))
                            st.session_state.posts = get_posts_to_approve() # Refresh data
                            st.rerun()