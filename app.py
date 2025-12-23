import streamlit as st
import pandas as pd
import smtplib
import io
import os
from email.message import EmailMessage
import google.generativeai as genai

# --- 1. AI Image Generation Fix ---
def generate_ai_image_bytes(api_key, prompt):
    try:
        genai.configure(api_key=api_key)
        # 2025 Standard: Using imagen-2.5 for dedicated image generation
        model = genai.GenerativeModel('gemini-2.5-flash-image') 
        result = model.generate_content(prompt)
        
        # FIX: Explicitly extracting bytes from the Gemini response candidates
        if result.candidates and result.candidates[0].content.parts:
            image_bytes = result.candidates[0].content.parts[0].inline_data.data
            return image_bytes
        return None
    except Exception as e:
        st.error(f"AI Generation Error: {e}")
        return None

# --- 2. Office 365 Email Fix ---
def send_o365_email(sender, password, receiver, subject, body, manual_file=None, image_data=None, image_name="visual.png"):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(body)

    # Attach the primary file (PDF/Document)
    if manual_file is not None:
        msg.add_attachment(
            manual_file.getvalue(),
            maintype='application',
            subtype='octet-stream',
            filename=manual_file.name
        )

    # Attach the Image (Manual OR AI)
    if image_data is not None:
        # If it's a file uploader object, get value. If it's bytes (AI), use directly.
        final_img_bytes = image_data.getvalue() if hasattr(image_data, 'getvalue') else image_data
        msg.add_attachment(
            final_img_bytes,
            maintype='image',
            subtype='png',
            filename=image_name
        )

    try:
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send to {receiver}: {e}")
        return False

# --- 3. Streamlit UI ---
st.set_page_config(page_title="Outreach Master", layout="wide")
st.title("📧 Business Outreach (O365 + AI/Manual)")

with st.sidebar:
    st.header("🔑 Credentials")
    sender_email = st.text_input("Office 365 Email")
    app_password = st.text_input("App Password", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")

# --- Step 1: Uploads ---
col1, col2 = st.columns(2)
with col1:
    uploaded_csv = st.file_uploader("1. Upload Business List (CSV)", type=["csv"])
with col2:
    manual_doc = st.file_uploader("2. Attach Brochure/PDF (Optional)", type=["pdf", "docx"])

# --- Step 2: Image Selection Strategy ---
st.header("3. Visual Strategy")
image_mode = st.radio("How would you like to handle the image?", 
                      ["Generate Unique AI Image for each", "Upload ONE Static Image for all", "No Image"])

static_image = None
if image_mode == "Upload ONE Static Image for all":
    static_image = st.file_uploader("Upload the image to send", type=["png", "jpg", "jpeg"])

if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
    st.dataframe(df.head(3))

    subject_temp = st.text_input("Subject line", "A gift for {Business Name}")
    body_temp = st.text_area("Message body", "Hi {Business Name}, please see the attached visual!")

    # --- PREVIEW ---
    st.divider()
    if st.button("👁️ Preview First Email"):
        row = df.iloc[0]
        biz = row.get('Business Name', 'Client')
        
        # Determine preview image
        preview_img = None
        if image_mode == "Generate Unique AI Image for each":
            prompt = row.get('Prompt', f"Professional marketing image for {biz}")
            with st.spinner("AI is painting..."):
                preview_img = generate_ai_image_bytes(gemini_key, prompt)
        elif image_mode == "Upload ONE Static Image for all":
            preview_img = static_image

        # Show Preview
        if preview_img:
            st.image(preview_img, caption=f"Visual for {biz}", width=400)
            st.success("Preview Loaded!")
        else:
            st.warning("No image to display in preview.")

    # --- BULK RUN ---
    if st.button("🚀 START CAMPAIGN", type="primary"):
        if not (sender_email and app_password):
            st.error("Enter email credentials!")
        else:
            bar = st.progress(0)
            for i, row in df.iterrows():
                biz = str(row.get('Business Name', 'Client'))
                target = str(row.get('Email', ''))
                
                # Get Image for this specific row
                current_img = None
                if image_mode == "Generate Unique AI Image for each":
                    current_img = generate_ai_image_bytes(gemini_key, row.get('Prompt', f"Photo for {biz}"))
                elif image_mode == "Upload ONE Static Image for all":
                    current_img = static_image

                # Send
                success = send_o365_email(
                    sender_email, app_password, target,
                    subject_temp.replace("{Business Name}", biz),
                    body_temp.replace("{Business Name}", biz),
                    manual_file=manual_doc,
                    image_data=current_img
                )
                
                if success: st.toast(f"Sent: {biz}")
                bar.progress((i + 1) / len(df))
            st.balloons()
