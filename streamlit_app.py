import os
import tempfile
import numpy as np
from PIL import Image  # Pillow for image handling
from gtts import gTTS  # Google Text-to-Speech
import streamlit as st
import google.generativeai as genai
from moviepy.editor import *  # MoviePy for video editing
from PyPDF2 import PdfReader  # To read PDFs

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("AI-Generated Sales Demo Video")
st.write("Upload your images and PDF description to generate a sales demo video.")

# File uploader for product description PDF
pdf_file = st.file_uploader("Upload a Product Description PDF", type=["pdf"])

# File uploader for images (multiple files allowed)
image_files = st.file_uploader("Upload Product Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Button to generate response and video
if st.button("Generate Sales Demo Video"):
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

        # Step 2: Generate AI content (sales demo) using Google Generative AI
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_content = model.generate_content(text).text

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

    except Exception as e:
        st.error(f"Error: {e}")
