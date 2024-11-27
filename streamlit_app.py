import streamlit as st
import google.generativeai as genai
from gtts import gTTS  # Google Text-to-Speech
from PIL import Image
import numpy as np
import cv2
import tempfile
import os

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit App UI
st.title("AI-Powered Sales Demo Video Generator")
st.write("Create a professional video with TTS and your product image.")

# Section for Sales Demo
st.header("Create a Sales Demo Script")
product_name = st.text_input("Enter the product or service name:")
product_features = st.text_area("List the key features of the product or service:")
product_benefits = st.text_area("List the main benefits of the product or service:")
target_audience = st.text_input("Who is the target audience?")
use_case = st.text_area("Describe a common use case for the product or service:")
product_image = st.file_uploader("Upload the product image", type=["jpg", "jpeg", "png"])

# Button to generate sales demo
if st.button("Generate Sales Demo and Video"):
    try:
        # Generate Sales Demo Prompt
        demo_prompt = (
            f"Create a sales demo script for {product_name}. "
            f"The product features are: {product_features}. "
            f"The benefits are: {product_benefits}. "
            f"The target audience is: {target_audience}. "
            f"A common use case is: {use_case}. "
            f"Provide a clear, engaging demo that highlights the features and benefits."
        )
        
        # Load and configure the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(demo_prompt)
        sales_demo_script = response.text
        
        st.write("Sales Demo Script Generated:")
        st.write(sales_demo_script)
        
        # Convert text to speech (TTS) using gTTS
        tts = gTTS(text=sales_demo_script, lang='en')
        
        # Save the generated speech to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_file:
            audio_file_path = audio_file.name
            tts.save(audio_file_path)
        
        # Ensure the uploaded image is available
        if product_image is not None:
            # Open the image using Pillow
            image = Image.open(product_image)
            
            # Convert the image to a numpy array (OpenCV format)
            image_np = np.array(image)
            
            # Convert RGB to BGR (OpenCV uses BGR format)
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            # Set video parameters
            height, width, _ = image_np.shape
            fps = 1  # One frame per second, adjust for your needs
            duration = len(sales_demo_script.split()) / 2  # Estimate duration based on word count

            # Create a VideoWriter object
            video_output_path = "/tmp/sales_demo_video.avi"
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(video_output_path, fourcc, fps, (width, height))
            
            # Write the image frames (one frame for each second of video)
            for _ in range(int(fps * duration)):
                video_writer.write(image_np)  # Add the same image as every frame

            video_writer.release()

            # Provide a download link for the video
            st.download_button("Download Video", video_output_path, file_name="sales_demo_video.avi", mime="video/avi")

    except Exception as e:
        st.error(f"Error: {e}")
