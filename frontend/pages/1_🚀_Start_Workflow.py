# frontend/pages/1_🚀_Start_Workflow.py
import streamlit as st
import requests

# --- Configuration ---
BACKEND_API_URL = "http://localhost:8000"

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
    
    # --- NEW EMAIL INPUT ---
    approver_emails = st.text_input(
        "Approver Email(s)",
        placeholder="email1@example.com, email2@example.com",
        help="Enter one or more email addresses, separated by commas or semicolons."
    )
    
    st.write("Select Platforms:")
    col1, col2, col3, col4 = st.columns(4)
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
            if use_twitter: platforms_to_run.append("twitter")
                
            if not platforms_to_run:
                st.warning("Please select at least one platform.")
            else:
                with st.spinner("Sending request to the backend..."):
                    try:
                        api_endpoint = f"{BACKEND_API_URL}/api/v1/workflow/start"
                        payload = {
                            "article_url": article_url,
                            "platforms": platforms_to_run,
                            "approver_emails": approver_emails # Add emails to the payload
                        }
                        response = requests.post(api_endpoint, json=payload)
                        
                        if response.status_code == 200:
                            st.success(f"✅ Success! {response.json().get('message')}")
                            st.info("Content is being generated. An email will be sent to approvers when it's ready.")
                        else:
                            st.error(f"Error from API: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to connect to the backend API. Details: {e}")