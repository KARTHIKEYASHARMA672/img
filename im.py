# streamlit_gemini_fix.py
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import io
import traceback

# Configure — keep API key out of prints
API_KEY = os.getenv("GOOGLE_API_KEY")  # ensure this env var name matches what you set
if not API_KEY:
    st.error("Environment variable GOOGLE_API_KEY not set.")
else:
    genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Image Recognizer")
st.header("Image Recognizer")

# User prompts / file upload
user_text = st.text_input("Input Prompt:", key="input")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        pil_image = Image.open(uploaded_file).convert("RGB")   # SDK examples accept PIL.Image
        st.image(pil_image, caption="Uploaded Image.", use_container_width=True)
    except Exception as e:
        st.error(f"Failed to open image: {e}")
        pil_image = None
else:
    pil_image = None

submit = st.button("Tell me the details")

# Example multimodal prompt you already prepared (shortened for clarity)
input_prompt = """
You are an expert in analyzing leaves. ...
(put your full prompt text here)
"""

def get_gemini_response(prompt_text, pil_img, user_input_text):
    # Build the final text prompt (you may merge user_input_text & prompt_text)
    final_prompt = (prompt_text + "\n\nUser question: " + user_input_text).strip()
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-002')  # same style used in docs/examples
        # Pass a list where strings and PIL.Image objects are accepted
        # Order: text prompt first, then the image (matches examples)
        response = model.generate_content([final_prompt, pil_img])
        return response.text
    except Exception as e:
        # Re-raise or return a detailed error message for debugging
        raise RuntimeError("Gemini call failed: " + str(e)) from e

if submit:
    if not API_KEY:
        st.error("Missing API key — set GOOGLE_API_KEY in your environment.")
    elif pil_image is None:
        st.error("Please upload an image first.")
    else:
        try:
            with st.spinner("Contacting Gemini API..."):
                # Use the user_provided text if present, else a default prompt
                user_q = user_text or "Identify and explain the uploaded image."
                resp_text = get_gemini_response(input_prompt, pil_image, user_q)
                st.subheader("The Response is")
                st.write(resp_text)
        except Exception as exc:
            st.error("Error while calling the Gemini API. See details below.")
            st.text(traceback.format_exc())
