import os
import tempfile
import numpy as np
from PIL import Image  # Pillow for image handling
from gtts import gTTS  # Google Text-to-Speech
import streamlit as st
import google.generativeai as genai
from moviepy.editor import *  # MoviePy for video editing
from PyPDF2 import PdfReader  # To read PDFs
from fpdf import FPDF  # To generate PDF proposals

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("AI-Generated Sales Proposal/Demo Video")
st.write("Upload your images and PDF description to generate a sales demo or proposal video.")

# Option for selecting between sales demo or proposal
option = st.selectbox("Select the type of content you want to generate:", ("Sales Demo", "Sales Proposal"))

# File uploader for product description PDF
pdf_file = st.file_uploader("Upload a Product Description PDF", type=["pdf"])

# File uploader for images (multiple files allowed)
image_files = st.file_uploader("Upload Product Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Editable text area for modifying proposal/demo content
editable_content = st.text_area("Edit Generated Proposal/Demo Content", height=200)

# Button to generate response and video
if st.button("Generate Sales Video"):
    try:
        # Step 1: Process the PDF file to extract the product description text
        if pdf_file is not None:
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            # Fallback to a default description if no PDF is uploaded
            text = "Innovative AI software solution for businesses."

        # Step 2: Generate AI content (sales proposal or demo) based on user selection
        if option == "Sales Demo":
            ai_content = genai.GenerativeModel('gemini-1.5-flash').generate_content(f"Create a sales demo for the following product: {text}").text
        else:  # Sales Proposal
            ai_content = genai.GenerativeModel('gemini-1.5-flash').generate_content(f"Create a sales proposal for the following product: {text}").text

        # Allow user to modify the AI-generated content
        if editable_content.strip() != "":
            ai_content = editable_content

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

        # Step 6: Generate PDF from the AI-generated content (for Sales Proposal)
        if option == "Sales Proposal":
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Title
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Sales Proposal", ln=True, align="C")

            # Content
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)
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

        # Step 7: Email Option (using mailto)
        email_recipient = st.text_input("Enter recipient email address:")
        if email_recipient:
            email_body = f"Please find attached the generated {option}. You can download it here: [Download PDF](sandbox:/files/{output_pdf_file.name})"
            email_link = f"mailto:{email_recipient}?subject=Your {option} is ready&body={email_body}"

            st.markdown(f"Click to send the proposal/demo by email: [Send Email]({email_link})")

    except Exception as e:
        st.error(f"Error: {e}")
