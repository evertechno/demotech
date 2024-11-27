import os
import tempfile
import numpy as np
from PIL import Image
from gtts import gTTS  # Google Text-to-Speech
import streamlit as st
import google.generativeai as genai
from moviepy.editor import *  # MoviePy for video editing
from fpdf import FPDF  # To generate PDF proposals

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("AI-Generated Sales Proposal/Demo Video")
st.write("Provide some basic information about your product to generate a sales proposal and demo video.")

# Step 1: Get inputs from the user for the Sales Proposal
product_name = st.text_input("Product Name", "AI-based Business Software")
product_description = st.text_area("Product Description", "This product helps businesses automate their operations using AI.")
target_audience = st.text_input("Target Audience", "Small and Medium Businesses (SMBs)")
unique_features = st.text_area("Unique Features", "Automated reporting, AI-driven insights, Cloud-based platform.")

# File uploader for product images (multiple files allowed)
image_files = st.file_uploader("Upload Product Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Button to generate response and video
if st.button("Generate Sales Proposal and Video"):
    try:
        # Step 2: Generate AI content (sales proposal) based on user inputs
        ai_content = genai.GenerativeModel('gemini-1.5-flash').generate_content(
            f"Create a sales proposal for a product called '{product_name}' that helps '{target_audience}' with the following features: {unique_features}. The product description is: {product_description}").text

        # Allow user to modify the AI-generated content
        editable_content = st.text_area("Edit Generated Proposal", ai_content, height=200)

        # Use the editable content if modified
        ai_content = editable_content.strip() if editable_content.strip() else ai_content

        # Step 3: Generate text-to-speech from AI content
        tts = gTTS(text=ai_content, lang='en')
        audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(audio_file.name)

        # Step 4: Create a video from uploaded images
        if image_files:
            image_clips = []
            duration_per_image = 3  # Duration each image is shown in the video (seconds)

            for image_file in image_files:
                img = Image.open(image_file)
                img = img.resize((1280, 720))  # Resize to fit video dimensions
                img_array = np.array(img)
                height, width, _ = img_array.shape

                # Create a video clip for each image
                image_clip = ImageClip(img_array)
                image_clip = image_clip.set_duration(duration_per_image).set_fps(24)
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
            st.video(output_video_file.name)

        # Step 6: Preprocess the text to replace unsupported characters (for PDF generation)
        ai_content = ai_content.replace("\u2013", "-")  # Replace en dash with hyphen
        ai_content = ai_content.replace("\u2014", "-")  # Replace em dash with hyphen
        ai_content = ai_content.replace("\u2018", "'")  # Replace left single quotation mark
        ai_content = ai_content.replace("\u2019", "'")  # Replace right single quotation mark
        ai_content = ai_content.replace("\u201C", '"')  # Replace left double quotation mark
        ai_content = ai_content.replace("\u201D", '"')  # Replace right double quotation mark
        ai_content = ai_content.replace("\u2022", "*")  # Replace bullet point

        # Step 7: Generate PDF from the AI-generated content (for Sales Proposal)
        pdf = FPDF()

        # Add a page
        pdf.add_page()

        # Set font (TrueType font for UTF-8 support)
        pdf.add_font('Arial', '', 'path_to_arial.ttf', uni=True)  # Use Arial TTF font
        pdf.set_font('Arial', '', 12)

        # Add title
        pdf.cell(200, 10, "Sales Proposal", ln=True, align="C")

        # Add content (AI-generated text)
        pdf.ln(10)
        pdf.multi_cell(0, 10, ai_content)

        # Save the PDF to a file
        output_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(output_pdf_file.name)

        # Provide a download link for the generated PDF
        st.download_button(
            label="Download Proposal as PDF",
            data=open(output_pdf_file.name, "rb").read(),
            file_name="sales_proposal.pdf",
            mime="application/pdf",
        )

        # Step 8: Email Option (using mailto)
        email_recipient = st.text_input("Enter recipient email address:")
        if email_recipient:
            email_body = f"Please find attached the generated sales proposal. You can download it here: [Download PDF](sandbox:/files/{output_pdf_file.name})"
            email_link = f"mailto:{email_recipient}?subject=Your Sales Proposal is ready&body={email_body}"

            st.markdown(f"Click to send the proposal by email: [Send Email]({email_link})")

    except Exception as e:
        st.error(f"Error: {e}")
