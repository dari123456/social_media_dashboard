# frontend/pages/4_🔎_Check-In_Scanner.py

import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import os # Just for this example, you'll import your real backend

# --- ⚠️ TODO: REPLACE THIS FAKE FUNCTION ---
#
# This is where you connect to your *real* backend logic.
# You might import a function from your `backend` folder,
# or make an API call to your `backend/main.py` if it's a server.
#
def check_ticket_in_database(ticket_id):
    """
    Checks the ticket ID against the database.
    
    Returns: A dictionary, e.g.:
    {"status": "success", "name": "Jane Doe"}
    or
    {"status": "error", "message": "Ticket not found"}
    """
    st.info(f"Checking ticket: {ticket_id}") # Displayed to user
    
    # --- FAKE DATABASE LOGIC ---
    # Replace this with your actual database query
    fake_database = {
        "TKT-A1B2C3D4": {"name": "Alice Smith", "status": "valid"},
        "TKT-E5F6G7H8": {"name": "Bob Johnson", "status": "used"},
    }
    
    if ticket_id in fake_database:
        registration = fake_database[ticket_id]
        if registration["status"] == "valid":
            # In a real app, you'd update status to "used" here
            return {"status": "success", "name": registration["name"]}
        else:
            return {"status": "error", "message": "Ticket already checked in."}
    else:
        return {"status": "error", "message": "Ticket not found."}
# --- END OF FAKE FUNCTION ---


# --- STREAMLIT PAGE CODE ---

st.set_page_config(page_title="Check-in Scanner", layout="centered")
st.title("🎫 Event Check-in Scanner")

# 1. Create the camera input widget
img_file_buffer = st.camera_input(
    "Point camera at the QR code and take photo:",
    key="camera",
    help="Allow camera access. Position the QR code in the frame and take a photo."
)

if img_file_buffer is not None:
    # 2. Open the image buffer
    try:
        image = Image.open(img_file_buffer)
        
        # 3. Decode the QR code
        decoded_objects = decode(image)
        
        if not decoded_objects:
            st.error("No QR code found. Please try again.", icon="❌")
        else:
            # Get the data from the first QR code found
            ticket_id = decoded_objects[0].data.decode("utf-8")
            
            # 4. Check the database
            with st.spinner("Verifying ticket..."):
                response = check_ticket_in_database(ticket_id)
                
                if response["status"] == "success":
                    st.success(f"Welcome, {response['name']}!", icon="✅")
                else:
                    st.error(response["message"], icon="❌")
            
            # Clear the camera input so you can scan another
            st.session_state["camera"] = None

    except Exception as e:
        st.error(f"An error occurred: {e}")