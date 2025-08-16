# frontend/pages/1_🚀_Start_Workflow.py
import streamlit as st

import sys, os
from pathlib import Path

# add the REPO ROOT (…/social_media_dashboard) to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# now these imports will work
# use the ones needed per page:
from backend.bots import orchestrator, config, clients


# --- Page Setup ---
st.set_page_config(page_title="Start Workflow", page_icon="🚀", layout="wide")

# --- Main Application ---
st.title("🚀 Start a New Workflow")
st.markdown("Enter an article URL, provide approver emails, and select platforms to generate content for.")

with st.form("start_workflow_form"):
    article_url = st.text_input(
        "Article URL",
        placeholder="https://example.com/your-article-url"
    )

    approver_emails = st.text_input(
        "Approver Email(s)",
        placeholder="email1@example.com, email2@example.com",
        help="Enter one or more email addresses, separated by commas or semicolons."
    )

    st.write("Select Platforms:")
    col1, col2, col3 = st.columns(3)
    with col1:
        use_facebook = st.checkbox("Facebook", value=True)
    with col2:
        use_instagram = st.checkbox("Instagram", value=True)
    with col3:
        use_twitter = st.checkbox("Twitter", value=True)

    submitted = st.form_submit_button("Fetch Article & Generate Content")

    if submitted:
        if not article_url or not approver_emails:
            st.error("Please provide both an Article URL and at least one Approver Email.")
        else:
            platforms_to_run = []
            if use_facebook: platforms_to_run.append("facebook")
            if use_instagram: platforms_to_run.append("instagram")
            if use_twitter:   platforms_to_run.append("twitter")

            if not platforms_to_run:
                st.warning("Please select at least one platform.")
            else:
                with st.spinner("Starting ingestion → generation workflow..."):
                    emails = [e.strip() for e in approver_emails.replace(";", ",").split(",") if e.strip()]
                    orchestrator.run_ingestion_to_generation(
                        article_url=article_url,
                        platforms=platforms_to_run,
                        approver_emails=emails
                    )
