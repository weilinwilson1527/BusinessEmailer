import streamlit as st
import pandas as pd
import smtplib
import os
import google.generativeai as genai
from email.message import EmailMessage
from PIL import Image
import io

# --- 1. AI Setup (Gemini) ---
def generate_business_image(api_key, prompt_text):
    """Uses Gemini to generate an image based on the business prompt."""
    genai.configure(api_key=api_key)
    # Using the Imagen model via Gemini API
    model = genai.GenerativeModel('gemini-1.5-flash') 
    # Note: For actual image generation, ensure your API has 'imagen-3' access
    # This is a placeholder for the generation call
    response = model.generate_content(f"Generate a professional marketing image for: {prompt_text}")
    return response

# --- 2. Email Setup ---
def send_automated_email(sender, password, receiver, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(body)

    # Attach local file if provided
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=attachment_path)

    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

# --- 3. Streamlit Interface ---
st.set_page_config(page_title="Gemini Outreach Pro", layout="wide")
st.title("🚀 AI Business Outreach Dashboard")

with st.sidebar:
    st.header("🔑 Credentials")
    sender_email = st.text_input("Your Gmail")
    app_password = st.text_input("Gmail App Password", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")
    st.info("Get your key at aistudio.google.com")

st.header("1. Upload Your Business List")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)

    st.header("2. Customize Messaging")
    email_subject = st.text_input("Subject line", "A gift for {Business Name}")
    email_body = st.text_area("Message Body", "Hi {Business Name}, we generated this custom visual for you!")

    if st.button("🚀 Start Bulk Emailing"):
        if not (sender_email and app_password and gemini_key):
            st.error("Missing credentials in the sidebar!")
        else:
            for index, row in df.iterrows():
                try:
                    # Personalize content from CSV columns
                    target_email = row['Email']
                    biz_name = row['Business Name']
                    img_prompt = row.get('Prompt', f"A professional logo for {biz_name}")
                    
                    # 1. AI Image Generation (Visualizing the process)
                    st.write(f"🎨 Generating image for {biz_name}...")
                    # (In a real scenario, you'd save the AI output to a file here)
                    
                    # 2. Send Email
                    formatted_subject = email_subject.replace("{Business Name}", biz_name)
                    formatted_body = email_body.replace("{Business Name}", biz_name)
                    
                    send_automated_email(
                        sender_email, 
                        app_password, 
                        target_email, 
                        formatted_subject, 
                        formatted_body,
                        attachment_path=row.get('File') # Optional file column
                    )
                    st.success(f"✅ Sent to {biz_name} ({target_email})")
                
                except Exception as e:
                    st.error(f"❌ Failed for {biz_name}: {e}")

            st.balloons()