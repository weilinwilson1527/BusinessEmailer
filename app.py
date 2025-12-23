import streamlit as st
import pandas as pd
import smtplib
import os
import google.generativeai as genai
from email.message import EmailMessage

# --- Updated Office 365 Email Function ---
def send_automated_email_o365(sender, password, receiver, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(body)

    # Attach local file if provided
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as f:
            file_data = f.read()
            # Office 365 is picky about mime types; 'application/octet-stream' is a safe bet
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=os.path.basename(attachment_path))

    # --- OFFICE 365 SMTP SETTINGS ---
    # Server: smtp.office365.com | Port: 587
    try:
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.ehlo()         # Identify ourselves to the server
            smtp.starttls()     # Secure the connection
            smtp.ehlo()         # Re-identify ourselves over the encrypted connection
            smtp.login(sender, password)
            smtp.send_message(msg)
    except Exception as e:
        raise Exception(f"Mail Error: {str(e)}")

# --- Streamlit Interface Updates ---
st.title("🚀 AI Business Outreach (Office 365 Edition)")

with st.sidebar:
    st.header("🔑 Microsoft Credentials")
    sender_email = st.text_input("Your O365 Email (e.g., name@company.com)")
    app_password = st.text_input("App Password", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")
    st.info("💡 Note: Office 365 requires SMTP Auth to be enabled in your Admin Center.")

# ... (rest of your CSV upload and AI generation logic stays the same) ...
# When calling the function in your loop, use:
# send_automated_email_o365(sender_email, app_password, target_email, formatted_subject, formatted_body)
