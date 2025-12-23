import streamlit as st
import pandas as pd
import smtplib
import os
import google.generativeai as genai
from email.message import EmailMessage
from PIL import Image
import io

# --- 1. AI Image Generation (Gemini/Imagen) ---
def generate_ai_image_bytes(api_key, prompt):
    try:
        genai.configure(api_key=api_key)
        # Using the standard Imagen model name for Gemini 2025
        model = genai.GenerativeModel('gemini-2.5-flash-image') 
        result = model.generate_content(prompt)
        
        # Get the image bytes from the response
        image_bytes = result.candidates[0].content.parts[0].inline_data.data
        return image_bytes
    except Exception as e:
        st.error(f"AI Image Error: {e}")
        return None

# --- 2. Email Setup (FIXED VERSION) ---
def send_automated_email_o365(sender, password, receiver, subject, body, manual_file=None, ai_img_bytes=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(body)

    # Attach the Manual File
    if manual_file is not None:
        msg.add_attachment(
            manual_file.getvalue(),
            maintype='application',
            subtype='octet-stream',
            filename=manual_file.name
        )

    # Attach the AI Generated Image (Now correctly receiving ai_img_bytes)
    if ai_img_bytes is not None:
        msg.add_attachment(
            ai_img_bytes,
            maintype='image',
            subtype='png',
            filename='personalized_image.png'
        )

    try:
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email Failed for {receiver}: {e}")
        return False

# --- 3. Streamlit Interface ---
st.set_page_config(page_title="Pro Outreach Automator", layout="centered")
st.title("🚀 AI Business Outreach Dashboard")

with st.sidebar:
    st.header("🔑 Settings")
    sender_email = st.text_input("Office 365 Email")
    app_password = st.text_input("Email Password", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")
    st.info("Get your key at aistudio.google.com")

st.header("1. Upload Your Business List")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
manual_attachment = st.file_uploader("Attach a file (PDF, Brochure, etc.)", type=["pdf", "png", "jpg", "docx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Business List", df.head(3))

    st.header("2. Customize Messaging")
    email_subject = st.text_input("Subject line", "A gift for {Business Name}")
    email_body = st.text_area("Message Body", "Hi {Business Name}, we generated this custom visual for you!")

    st.divider()
    st.subheader("👁️ Preview & Double Check")

    if st.button("👀 Preview Email Content"):
        if not gemini_key:
            st.error("Please enter your Gemini API Key in the sidebar first!")
        else:
            first_row = df.iloc[0]
            # Handle potential missing columns gracefully
            biz_name = first_row.get('Business Name', 'Valued Customer')
            preview_prompt = first_row.get('Prompt', f"A professional photo for {biz_name}")
            
            with st.spinner("Generating AI image for preview..."):
                img_bytes = generate_ai_image_bytes(gemini_key, preview_prompt)
                if img_bytes:
                    st.image(img_bytes, caption=f"AI Image for {biz_name}", width=400)
                    st.info(f"Email will be sent to: {first_row.get('Email', 'No Email Found')}")
                    st.success("Preview generated! If this looks good, click 'Start Bulk Sending' below.")

    st.divider()
    if st.button("🚀 Start Bulk Sending", type="primary"):
        if not (sender_email and app_password and gemini_key):
            st.error("Missing credentials in the sidebar.")
        else:
            progress = st.progress(0)
            status_text = st.empty()
            
            for i, row in df.iterrows():
                biz_name = str(row.get('Business Name', 'Client'))
                target = str(row.get('Email', ''))
                
                if not target or "@" not in target:
                    st.warning(f"Skipping {biz_name}: Invalid Email")
                    continue

                prompt = row.get('Prompt', f"Professional marketing visual for {biz_name}")
                status_text.text(f"Sending to {biz_name}...")
                
                # 1. Generate Image
                img_data = generate_ai_image_bytes(gemini_key, prompt)
                
                # 2. Personalize Text
                formatted_subject = email_subject.replace("{Business Name}", biz_name)
                formatted_body = email_body.replace("{Business Name}", biz_name)
                
                # 3. Send (All 7 arguments now match the function definition)
                success = send_automated_email_o365(
                        sender_email,
                        app_password,
                        target,
                        formatted_subject,
                        formatted_body,
                        manual_file=manual_attachment,
                        ai_img_bytes=img_data
                    )
                
                if success:
                    st.toast(f"✅ Sent to {biz_name}")
                
                progress.progress((i + 1) / len(df))

            status_text.text("Bulk sending complete!")
            st.balloons()
