# streamlit_gemini_app.py
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import traceback

# ===============================
# 🔹 App Config
# ===============================
st.set_page_config(page_title="AI Image & Text Analyzer", layout="wide")

# Sidebar instructions
st.sidebar.title("📌 How to Use")
st.sidebar.markdown("""
1. Upload one or more images.  
2. (Optional) Enter a question/prompt.  
3. Click **Analyze** to get results.  

✨ Features:
- Multi-image upload  
- Chat history (with clear option)  
- Educational toggle (Explain Like I’m 5 vs Expert)  
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
def get_gemini_response(prompt_text, pil_imgs, user_input_text, style_mode):
    style = "Explain like I’m 5." if style_mode == "Explain Like I'm 5" else "Give a detailed expert analysis."
    final_prompt = f"{prompt_text}\n\n{style}\n\nUser question: {user_input_text}".strip()

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-002')
        parts = [final_prompt] + pil_imgs   # combine text + images
        response = model.generate_content(parts)
        return response.text
    except Exception as e:
        raise RuntimeError("Gemini call failed: " + str(e)) from e

# ===============================
# 🔹 Main Logic
# ===============================
input_prompt = """
You are an expert in analyzing images (e.g., leaves, food, objects).
Give insights based on the uploaded images and user’s question.
"""

resp_text = ""

if submit:
    if not API_KEY:
        st.error("Missing API key — set GOOGLE_API_KEY in your environment.")
    elif not uploaded_files:
        st.error("Please upload at least one image.")
    else:
        try:
            pil_images = []
            for f in uploaded_files:
                img = Image.open(f).convert("RGB")
                st.image(img, caption=f"Uploaded: {f.name}", use_container_width=True)
                pil_images.append(img)

            with st.spinner("🤖 Analyzing with Gemini..."):
                user_q = user_text or "Identify and explain the uploaded image(s)."
                resp_text = get_gemini_response(input_prompt, pil_images, user_q, mode)

                st.subheader("✨ Response")
                st.write(resp_text)

                # Copy-to-clipboard box
                st.code(resp_text, language="markdown")

                # Save to history
                st.session_state["history"].append((user_q, resp_text))

        except Exception as exc:
            st.error("Error while calling the Gemini API.")
            st.text(traceback.format_exc())

# ===============================
# 🔹 History Section with Clear
# ===============================
if st.session_state["history"]:
    st.sidebar.subheader("📜 Chat History")

    # Button to clear history
    if st.sidebar.button("🗑️ Clear History"):
        st.session_state["history"] = []
        st.sidebar.success("History cleared!")

    for i, (q, r) in enumerate(st.session_state["history"], 1):
        with st.sidebar.expander(f"Query {i}"):
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {r}")
