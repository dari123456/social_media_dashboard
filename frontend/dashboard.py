# frontend/dashboard.py
import streamlit as st

st.set_page_config(
    page_title="Social Media Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Welcome to the Social Media Automation Dashboard")
st.markdown("---")
st.header("How to Use This Dashboard")
st.markdown("""
Navigate through the pages in the sidebar to control the content automation workflow.

1.  **🚀 Start Workflow**: Begin by entering an article URL to fetch its content, generate summaries, and create posts.
2.  **✅ Approval Queue**: (Coming soon) Review all generated posts and approve them for scheduling.
3.  **🗓️ Scheduling & Publishing**: (Coming soon) View the content calendar and manage the publishing schedule.

**Select a page from the sidebar on the left to begin.**
""")