# streamlit_gemini_voice.py

import streamlit as st
from st_mic_recorder import mic_recorder
import google.generativeai as genai
from PIL import Image
import io, base64, os

# --- API Key setup ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("Environment variable GOOGLE_API_KEY not set.")
else:
    genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

# --- Streamlit page settings ---
st.set_page_config(page_title="🎤📷 AI Image & Voice Assistant", layout="wide")
st.title("🎤📷 AI Image & Voice Assistant")

# --- Session state for history ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Mode selection ---
mode = st.radio("Choose Response Mode:", ["Expert", "ELI5"], horizontal=True)

# --- Clear history button ---
if st.button("🗑️ Clear History"):
    st.session_state.history = []
    st.success("History cleared!")

# --- Image upload ---
uploaded_files = st.file_uploader(
    "📂 Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True
)

# --- Voice input ---
st.subheader("🎙️ Speak your prompt")
voice_text = mic_recorder(
    start_prompt="🎤 Record", stop_prompt="⏹️ Stop",
    just_once=True, use_container_width=True
)

# --- Text input ---
user_input = st.text_area("Or type your question:")

if voice_text:
    user_input = voice_text
    st.success(f"🗣️ Recognized: {user_input}")

# --- Gemini Response Function ---
def get_gemini_response(prompt, images, mode):
    contents = [prompt]
    for img in images:
        contents.append(img)

    if mode == "Expert":
        sys_instruction = "Act as a domain expert. Give detailed, structured explanations."
    else:
        sys_instruction = "Explain like I’m 5 (simple, fun, easy to understand)."

    response = model.generate_content(
        [
            {"role": "system", "parts": [sys_instruction]},
            {"role": "user", "parts": contents},
        ]
    )
    return response.text

# --- Submit button ---
if st.button("🚀 Generate Response"):
    if not user_input and not uploaded_files:
        st.warning("Please provide a prompt or upload an image.")
    else:
        images = []
        for file in uploaded_files:
            try:
                image = Image.open(file)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()
                images.append({"mime_type": "image/png", "data": img_b64})
            except Exception as e:
                st.error(f"Failed to process {file.name}: {e}")

        response = get_gemini_response(user_input, images, mode)
        st.session_state.history.append({"user": user_input, "bot": response})

# --- Show history ---
st.subheader("💬 Conversation History")
for chat in st.session_state.history:
    st.markdown(f"**🧑 You:** {chat['user']}")
    st.markdown(f"**🤖 AI:** {chat['bot']}")
    st.divider()
