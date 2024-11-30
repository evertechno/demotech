import os
import tempfile
import numpy as np
from PIL import Image
from gtts import gTTS  # Google Text-to-Speech
import streamlit as st
import google.generativeai as genai
from moviepy.editor import *  # MoviePy for video editing
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas  # Built-in for PDF generation
import time
import re

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("AI-Generated Sales Proposal/Demo Video")
st.write("Provide some basic information about your product to generate a sales proposal and demo video.")

# Step 1: Get inputs from the user for the Sales Proposal
user_name = st.text_input("Your Name")
company_name = st.text_input("Your Company Name")
target_company = st.text_input("Target Company Name (To whom the presentation is being created)")
product_name = st.text_input("Product Name", "AI-based Business Software")
product_description = st.text_area("Product Description", "This product helps businesses automate their operations using AI.")
target_audience = st.text_input("Target Audience", "Small and Medium Businesses (SMBs)")
unique_features = st.text_area("Unique Features", "Automated reporting, AI-driven insights, Cloud-based platform.")

# New Inputs for Enhanced Customization
customer_testimonials = st.text_area("Customer Testimonials (Optional)", "This product has helped us increase efficiency by 30%.")
call_to_action = st.text_area("Call to Action", "Contact us today for a free demo!")
video_duration_per_image = st.slider("Set Video Duration Per Image (seconds)", min_value=2, max_value=10, value=3)

# File uploader for product images (multiple files allowed)
image_files = st.file_uploader("Upload Product Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Function to sanitize content by removing unwanted symbols
def sanitize_text_for_tts(text):
    # Remove unwanted characters (e.g., asterisks, brackets, etc.)
    sanitized_text = re.sub(r'[*#\[\]\*\n]', ' ', text)
    # Optionally, remove extra spaces between words
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
    return sanitized_text

# Button to generate response and video
if st.button("Generate Sales Proposal and Video"):
    try:
        # Start timer to measure performance
        start_time = time.time()

        # Step 2: Generate AI content (sales proposal) based on user inputs
        ai_content = genai.GenerativeModel('gemini-1.5-flash').generate_content(
            f"Create a clean and professional sales proposal for a product called '{product_name}' from {company_name}. "
            f"The product helps '{target_audience}' with the following features: {unique_features}. "
            f"The product description is: {product_description}. This proposal is being made for the target company {target_company}. "
            f"Please avoid any special symbols, and ensure the text is suitable for a corporate presentation."
        ).text

        # Add customer testimonials and call-to-action if provided
        if customer_testimonials:
            ai_content += f"\n\nCustomer Testimonials:\n{customer_testimonials}"

        if call_to_action:
            ai_content += f"\n\nCall to Action:\n{call_to_action}"

        # Sanitize the content to remove unwanted symbols
        ai_content_sanitized = sanitize_text_for_tts(ai_content)

        # Allow user to modify the AI-generated content
        editable_content = st.text_area("Edit Generated Proposal", ai_content, height=200)

        # Use the editable content if modified
        ai_content = editable_content.strip() if editable_content.strip() else ai_content

        # Step 3: Generate text-to-speech from the sanitized AI content
        tts = gTTS(text=ai_content_sanitized, lang='en')
        audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(audio_file.name)

        # Step 4: Create a video from uploaded images
        if image_files:
            image_clips = []
            for image_file in image_files:
                img = Image.open(image_file)
                img = img.resize((640, 360))  # Resize to smaller size for faster processing
                img_array = np.array(img)

                # Check if the image is grayscale (2D) or color (3D)
                if len(img_array.shape) == 2:  # Grayscale image (height, width)
                    height, width = img_array.shape
                    img_array = np.expand_dims(img_array, axis=-1)  # Add a color dimension (1 channel)
                else:  # Color image (height, width, channels)
                    height, width, _ = img_array.shape

                # Create a video clip for each image
                image_clip = ImageClip(img_array)
                image_clip = image_clip.set_duration(video_duration_per_image).set_fps(24)
                image_clips.append(image_clip)

            # Combine image clips into a single video slideshow
            video = concatenate_videoclips(image_clips, method="compose")
        else:
            st.error("Please upload at least one image for the slideshow.")
            video = None

        # Step 5: Combine the video with the generated audio (text-to-speech)
        if video is not None:
            # Load audio file (text-to-speech) and set its duration to match the video
            audio_clip = AudioFileClip(audio_file.name)
            video = video.set_audio(audio_clip)

            # Output the final video
            output_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            video.write_videofile(output_video_file.name, codec="libx264", audio_codec="aac")

            # Provide a download link for the generated video
            st.download_button(
                label="Download Sales Demo Video",
                data=open(output_video_file.name, "rb").read(),
                file_name="sales_demo_video.mp4",
                mime="video/mp4",
            )

        # Step 6: Generate PDF from the AI-generated content (for Sales Proposal)
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(pdf_file.name, pagesize=letter)
        c.setFont("Helvetica", 12)

        # Add content (AI-generated text) to the PDF
        text_object = c.beginText(40, 750)  # Starting point of text
        text_object.textLines(ai_content)

        c.drawText(text_object)
        c.showPage()
        c.save()

        # Provide a download link for the generated PDF
        st.download_button(
            label="Download Proposal as PDF",
            data=open(pdf_file.name, "rb").read(),
            file_name="sales_proposal.pdf",
            mime="application/pdf",
        )

        # Step 7: Email Option (using mailto)
        email_recipient = st.text_input("Enter recipient email address:")
        if email_recipient:
            email_body = f"Please find attached the generated sales proposal. You can download it here: [Download PDF](sandbox:/files/{pdf_file.name})"
            email_link = f"mailto:{email_recipient}?subject=Your Sales Proposal is ready&body={email_body}"

            st.markdown(f"Click to send the proposal by email: [Send Email]({email_link})")

        # Display total processing time for performance tracking
        end_time = time.time()
        st.write(f"Processing completed in {end_time - start_time:.2f} seconds.")

    except Exception as e:
        st.error(f"Error: {e}")
