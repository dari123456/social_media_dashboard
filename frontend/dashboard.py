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

1.  **🚀 Start Workflow**: Enter an article URL, approver emails, and platforms to generate posts.
2.  **✅ Approval Queue**: Review all generated posts and approve/reject them.
3.  **🗓️ Scheduling & Publishing**: Build the schedule and publish due posts.

**Select a page from the sidebar on the left to begin.**
""")
