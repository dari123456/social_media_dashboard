# backend/bots/email_sender.py
import os
import smtplib
import ssl
from email.mime.text import MIMEText

def send_approval_notification(article_title: str, recipient_emails: list):
    """Sends an email notifying users that content is ready for approval."""
    
    # Load credentials from the environment
    sender_email = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    
    if not all([sender_email, password, recipient_emails]):
        print("EMAIL_SENDER: Missing sender, password, or recipients. Skipping email.")
        return

    subject = f"Action Required: Content for '{article_title}' is Ready for Approval"
    
    # We will need the URL to our Streamlit app. For now, it's a placeholder.
    # In a real deployment, this would be your public URL.
    STREAMLIT_URL = "http://localhost:8501/Approval_Queue"
    
    body = f"""
Dear Communication Manager,

The automated content generation for the article "{article_title}" is complete.

The new posts are now waiting for your review in the approval dashboard.

Please click the link below to access the queue:
{STREAMLIT_URL}

Thank you,
Your Friendly Automation Bot
"""
    message = MIMEText(body, "plain")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = ", ".join(recipient_emails)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_emails, message.as_string())
        print(f"EMAIL_SENDER: Successfully sent approval notification to: {', '.join(recipient_emails)}")
    except Exception as e:
        print(f"EMAIL_SENDER: FAILED to send email. Error: {e}")