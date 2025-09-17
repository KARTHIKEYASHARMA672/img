# streamlit_gemini_fix.py
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import traceback
from gtts import gTTS
import base64

# ===============================
# 🔹 App Config
# ===============================
st.set_page_config(page_title="AI Image & Text Analyzer", layout="wide")

# Theme toggle
theme = st.sidebar.radio("Choose Theme:", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        "<style>body {background-color: #121212; color: white;}</style>",
        unsafe_allow_html=True
    )

# Sidebar instructions
st.sidebar.title("📌 How to Use")
st.sidebar.markdown("""
1. Upload one or more images.  
2. (Optional) Enter a question/prompt.  
3. Click **Analyze** to get results.  

✨ Features:
- Multi-image upload  
- Chat history  
- OCR mode (for text in images)  
- Educational mode (Explain Like I’m 5 vs Expert)  
- Listen to responses  
""")

# ===============================
# 🔹 Gemini Config
# ===============================
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("Environment variable GOOGLE_API_KEY not set.")
else:
    genai.configure(api_key=API_KEY)

# ===============================
# 🔹 Session State for History
# ===============================
if "history" not in st.session_state:
    st.session_state["history"] = []

# ===============================
# 🔹 User Inputs
# ===============================
user_text = st.text_input("💬 Ask a Question (optional):", key="input")

uploaded_files = st.file_uploader(
    "📂 Upload image(s)...", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

mode = st.radio("Response Style:", ["Expert", "Explain Like I'm 5"], horizontal=True)

submit = st.button("🔍 Analyze")

# ===============================
# 🔹 Gemini Call
# ===============================
def get_gemini_response(prompt_text, pil_imgs, user_input_text):
    style = "Explain like I'm 5." if mode == "Explain Like I'm 5" else "Give a detailed expert analysis."
    final_prompt = f"{prompt_text}\n\n{style}\n\nUser question: {user_input_text}".strip()

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-002')
        parts = [final_prompt] + pil_imgs   # combine text + images
        response = model.generate_content(parts)
        return response.text
    except Exception as e:
        raise RuntimeError("Gemini call failed: " + str(e)) from e

# ===============================
# 🔹 OCR Feature (optional)
# ===============================
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

use_ocr = st.checkbox("Enable OCR (extract text from image)", value=False)

# ===============================
# 🔹 Main Logic
# ===============================
input_prompt = """
You are an expert in analyzing images (e.g., leaves, food, objects).
If OCR is enabled, extract the text first before answering.
"""

if submit:
    if not API_KEY:
        st.error("Missing API key — set GOOGLE_API_KEY in your environment.")
    elif not uploaded_files:
        st.error("Please upload at least one image.")
    else:
        try:
            pil_images = []
            ocr_texts = []
            for f in uploaded_files:
                img = Image.open(f).convert("RGB")
                st.image(img, caption=f"Uploaded: {f.name}", use_container_width=True)
                pil_images.append(img)

                if use_ocr and OCR_AVAILABLE:
                    ocr_result = pytesseract.image_to_string(img)
                    ocr_texts.append(ocr_result)

            if use_ocr and ocr_texts:
                user_text += "\n\nExtracted Text:\n" + "\n".join(ocr_texts)

            with st.spinner("🤖 Analyzing with Gemini..."):
                user_q = user_text or "Identify and explain the uploaded image(s)."
                resp_text = get_gemini_response(input_prompt, pil_images, user_q)

                st.subheader("✨ Response")
                st.write(resp_text)

                # Copy-to-clipboard
                st.code(resp_text, language="markdown")

                # Save to history
                st.session_state["history"].append((user_q, resp_text))

                # 🔊 Speech Output
                if st.button("🔊 Listen to Response"):
                    tts = gTTS(resp_text, lang="en")
                    tts.save("output.mp3")
                    st.audio("output.mp3")

        except Exception as exc:
            st.error("Error while calling the Gemini API.")
            st.text(traceback.format_exc())

# ===============================
# 🔹 History Section
# ===============================
if st.session_state["history"]:
    st.sidebar.subheader("📜 Chat History")
    for i, (q, r) in enumerate(st.session_state["history"], 1):
        with st.sidebar.expander(f"Query {i}"):
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {r}")
