# streamlit_gemini_advanced.py
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import traceback
from io import BytesIO
from collections import Counter
import re

# ===============================
# 🔹 App Config
# ===============================
st.set_page_config(page_title="AI Image & Knowledge Assistant", layout="wide")

# ===============================
# 🔹 Gemini Config
# ===============================
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("Environment variable GOOGLE_API_KEY not set.")
else:
    genai.configure(api_key=API_KEY)

# ===============================
# 🔹 Session State
# ===============================
if "history" not in st.session_state:
    st.session_state["history"] = []

# ===============================
# 🔹 Sidebar
# ===============================
st.sidebar.title("📌 Settings / History")

# Multi-modal selection
mode_options = ["Plants", "Food", "Vehicles"]
selected_mode = st.sidebar.selectbox("Select Analysis Mode:", mode_options)

# History controls
st.sidebar.subheader("📜 History")
if st.sidebar.button("🗑️ Clear History"):
    st.session_state["history"] = []
    st.sidebar.success("History cleared!")

if st.sidebar.button("💾 Download History"):
    if st.session_state["history"]:
        txt_data = ""
        for i, (q, r) in enumerate(st.session_state["history"], 1):
            txt_data += f"Query {i}:\n{q}\nResponse:\n{r}\n\n{'-'*40}\n\n"
        st.sidebar.download_button(
            label="Download as TXT",
            data=txt_data,
            file_name="ai_history.txt",
            mime="text/plain"
        )
    else:
        st.sidebar.warning("No history to download!")

# ===============================
# 🔹 Tabs UI
# ===============================
tab1, tab2 = st.tabs(["Image & Text Analysis", "History"])

with tab1:
    st.header("🔍 Image & Text Analysis")

    # User inputs
    user_text = st.text_input("💬 Ask a Question (optional):", key="input_text")
    uploaded_files = st.file_uploader(
        "📂 Upload image(s)...", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

    submit = st.button("Analyze")

    input_prompt_base = f"""
    You are an expert analyzing images in the selected mode: {selected_mode}.
    """

    resp_text = ""
    summary_text = ""
    highlighted_keywords = ""

    def get_gemini_response(prompt_text, pil_imgs, user_input_text):
        final_prompt = f"{prompt_text}\nUser question: {user_input_text}".strip()
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            parts = [final_prompt] + pil_imgs
            response = model.generate_content(parts)
            return response.text
        except Exception as e:
            raise RuntimeError("Gemini call failed: " + str(e)) from e

    def extract_keywords(text, top_n=10):
        words = re.findall(r'\b\w+\b', text.lower())
        common = Counter(words)
        stopwords = set([
            "the", "and", "of", "in", "to", "a", "is", "with", "for", "on", "as",
            "an", "by", "its", "this", "are", "be", "at", "or", "from"
        ])
        keywords = [word for word, freq in common.most_common() if word not in stopwords]
        return ", ".join(keywords[:top_n])

    if submit:
        if not API_KEY:
            st.error("Missing API key.")
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
                    user_q = user_text or f"Analyze the uploaded {selected_mode.lower()} images."
                    resp_text = get_gemini_response(input_prompt_base, pil_images, user_q)
                    st.subheader("✨ Response")
                    st.write(resp_text)

                    # Save history
                    st.session_state["history"].append((user_q, resp_text))

                    # Generate summary (first 2–3 sentences)
                    summary_text = ". ".join(resp_text.split(".")[:3]) + "."
                    st.subheader("📝 Summary")
                    st.write(summary_text)

                    # Highlight keywords
                    highlighted_keywords = extract_keywords(resp_text)
                    st.subheader("🔑 Keywords")
                    st.write(highlighted_keywords)

            except Exception as exc:
                st.error("Error while calling Gemini API.")
                st.text(traceback.format_exc())

# ===============================
# 🔹 History Tab
# ===============================
with tab2:
    st.header("📜 Chat History")
    if st.session_state["history"]:
        for i, (q, r) in enumerate(st.session_state["history"], 1):
            with st.expander(f"Query {i}"):
                st.markdown(f"**Q:** {q}")
                st.markdown(f"**A:** {r}")
    else:
        st.info("No history available.")
