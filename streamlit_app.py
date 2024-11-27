import os
import cv2
import numpy as np
from gtts import gTTS  # Google Text-to-Speech
from PIL import Image  # Pillow for image handling
from moviepy.editor import *  # MoviePy for video editing
import tempfile
import streamlit as st
import google.generativeai as genai

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("AI-Generated Sales Demo Video")
st.write("Create a sales demo video using text-to-speech, AI-generated content, and images.")

# Prompt input field
prompt = st.text_input("Enter your product description:", "Innovative AI software solution for businesses.")

# Button to generate response and video
if st.button("Generate Sales Demo Video"):
    try:
        # Generate AI content (sales demo)
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_content = model.generate_content(prompt).text

        # Generate text-to-speech from AI content
        tts = gTTS(text=ai_content, lang='en')
        audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(audio_file.name)

        # Image slideshow creation
        image_files = ["image1.jpg", "image2.jpg", "image3.jpg"]  # Add your image paths
        image_clips = []
        duration_per_image = 3  # Duration to display each image (in seconds)

        for image_file in image_files:
            img = Image.open(image_file)
            img = img.resize((1280, 720))  # Resize to fit video dimensions
            img_array = np.array(img)
            height, width, _ = img_array.shape

            # Create a video clip for each image
            image_clip = ImageClip(img_array)
            image_clip = image_clip.set_duration(duration_per_image).set_fps(24)
            image_clips.append(image_clip)

        # Combine image clips into a video slideshow
        video = concatenate_videoclips(image_clips, method="compose")

        # Load audio file (text-to-speech) and set its duration to match the video
        audio_clip = AudioFileClip(audio_file.name)
        video = video.set_audio(audio_clip)

        # Output the final video
        output_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        video.write_videofile(output_video_file.name, codec="libx264", audio_codec="aac")

        # Provide download link
        st.video(output_video_file.name)

    except Exception as e:
        st.error(f"Error: {e}")
