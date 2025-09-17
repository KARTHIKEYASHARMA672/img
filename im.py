import streamlit as st
import google.generativeai as genai
import os
import io
import base64
import speech_recognition as sr
from PIL import Image

# ----------------- CONFIG -----------------
genai.configure(api_key="YOUR_API_KEY")  # 🔑 Replace with your Gemini API key
model = genai.GenerativeModel("gemini-1.5-flash")

# ----------------- SESSION STATE -----------------
if "history" not in st.session_state:
    st.session_state.history = []

# ----------------- FUNCTIONS -----------------
def recognize_speech():
    """Capture voice and convert to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... please speak clearly")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

    try:
        text = recognizer.recognize_google(audio)
        st.success(f"✅ Recognized Speech: {text}")
        return text
    except sr.UnknownValueError:
        st.error("❌ Could not understand audio")
    except sr.RequestError:
        st.error("⚠️ Speech Recognition service unavailable")
    return None

def get_gemini_response(prompt, images, mode):
    """Send text + images to Gemini model"""
    contents = [prompt]
    for img in images:
        contents.append(img)

    # Choose system instruction
    if mode == "Expert":
        sys_instruction = "Act as a domain expert. Give detailed, structured explanations."
    else:
        sys_instruction = "Explain like I’m 5 (simple, fun, easy to understand)."

    response = model.generate_content(
        [{"role": "system", "parts": [sys_instruction]},
         {"role": "user", "parts": contents}]
    )
    return response.text

def add_to_history(user_text, response):
    st.session_state.history.append({"user": user_text, "bot": response})

# ----------------- UI -----------------
st.title("🎤📷 AI Image & Voice Assistant")

col1, col2 = st.columns([2,1])
with col1:
    mode = st.radio("Choose Response Mode:", ["Expert", "ELI5"], horizontal=True)
with col2:
    if st.button("🗑️ Clear History"):
        st.session_state.history = []

uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Text input OR speech input
tab1, tab2 = st.tabs(["⌨️ Type Prompt", "🎙️ Speak Prompt"])

with tab1:
    user_input = st.text_area("Enter your question:", key="typed_prompt")

with tab2:
    if st.button("🎤 Record Voice"):
        voice_text = recognize_speech()
        if voice_text:
            st.session_state["typed_prompt"] = voice_text
            user_input = voice_text

# ----------------- RUN AI -----------------
if st.button("🚀 Generate Response"):
    if not user_input and not uploaded_files:
        st.warning("Please provide a prompt or upload an image.")
    else:
        images = []
        for file in uploaded_files:
            image = Image.open(file)
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            images.append({"mime_type": "image/png", "data": img_b64})

        response = get_gemini_response(user_input, images, mode)
        add_to_history(user_input, response)

# ----------------- DISPLAY HISTORY -----------------
st.subheader("💬 Conversation History")
for chat in st.session_state.history:
    st.markdown(f"**🧑 You:** {chat['user']}")
    st.markdown(f"**🤖 AI:** {chat['bot']}")
    st.divider()
