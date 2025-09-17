# streamlit_gemini_app_v6.py
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
st.set_page_config(page_title="AI Analyzer + Video Idea Organizer", layout="wide")

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
if "analyzer_history" not in st.session_state:
    st.session_state["analyzer_history"] = []

if "video_idea_history" not in st.session_state:
    st.session_state["video_idea_history"] = []

# ===============================
# 🔹 Sidebar
# ===============================
st.sidebar.title("📌 Settings / History")

st.sidebar.subheader("📝 How It Works")
st.sidebar.markdown("""
**Image & Text Analyzer:**  
1. Upload images (jpg, jpeg, png).  
2. Optionally add a question.  
3. Select language and click Analyze.  

**Video Idea Organizer:**  
1. Enter raw video idea.  
2. Select category & tone.  
3. Click Refine to generate script + image prompts for a 1+ minute video.  

**History Tabs:**  
- Tab 3: Analyzer History  
- Tab 4: Video Idea History  
""")

# Language selection
language_options = ["English", "Hindi", "Telugu", "Spanish", "French"]
selected_language = st.sidebar.selectbox("🌐 Select Output Language:", language_options)

# Sidebar controls
st.sidebar.subheader("🗑️ / 💾 Manage History")

# Analyzer history
if st.sidebar.button("🗑️ Clear Analyzer History"):
    st.session_state["analyzer_history"] = []
    st.sidebar.success("Analyzer history cleared!")

if st.sidebar.button("💾 Download Analyzer History"):
    if st.session_state["analyzer_history"]:
        txt_data = ""
        for i, (q, r) in enumerate(st.session_state["analyzer_history"], 1):
            txt_data += f"Query {i}:\n{q}\nResponse:\n{r}\n\n{'-'*40}\n\n"
        st.sidebar.download_button(
            label="Download Analyzer History as TXT",
            data=txt_data,
            file_name="analyzer_history.txt",
            mime="text/plain"
        )
    else:
        st.sidebar.warning("No analyzer history to download!")

# Video idea history
if st.sidebar.button("🗑️ Clear Video Idea History"):
    st.session_state["video_idea_history"] = []
    st.sidebar.success("Video idea history cleared!")

if st.sidebar.button("💾 Download Video Idea History"):
    if st.session_state["video_idea_history"]:
        txt_data = ""
        for i, item in enumerate(st.session_state["video_idea_history"], 1):
            txt_data += f"Idea {i}:\nRaw: {item['raw']}\nScript:\n{item['script']}\nImage Prompts:\n{item['images']}\nCategory: {item['category']}\nTone: {item['tone']}\n\n{'-'*40}\n\n"
        st.sidebar.download_button(
            label="Download Video Idea History as TXT",
            data=txt_data,
            file_name="video_idea_history.txt",
            mime="text/plain"
        )
    else:
        st.sidebar.warning("No video idea history to download!")

# ===============================
# 🔹 Tabs UI
# ===============================
tab1, tab2, tab3, tab4 = st.tabs([
    "📷 Image & Text Analyzer", 
    "🎬 Video Idea Organizer", 
    "📜 Analyzer History", 
    "📜 Video Idea History"
])

# ===============================
# 🔹 Tab 1: Image & Text Analyzer
# ===============================
with tab1:
    st.header("🔍 Image & Text Analyzer")

    user_text = st.text_input("💬 Ask a Question (optional):", key="input_text")
    uploaded_files = st.file_uploader(
        "📂 Upload image(s)...", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

    submit = st.button("Analyze")

    input_prompt_base = f"""
    You are an expert analyzing images. Provide detailed insights in {selected_language}.
    """

    def get_gemini_response(prompt_text, pil_imgs, user_input_text):
        final_prompt = f"{prompt_text}\nUser question: {user_input_text}".strip()
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            parts = [final_prompt] + pil_imgs
            response = model.generate_content(parts)
            return response.text
        except Exception as e:
            raise RuntimeError("Gemini call failed: " + str(e)) from e

    if submit:
        if not API_KEY:
            st.error("Missing API key.")
        elif not uploaded_files:
            st.error("Please upload at least one image.")
        else:
            try:
                pil_images = []
                st.subheader("📷 Uploaded Images")
                cols = st.columns(len(uploaded_files))
                for idx, f in enumerate(uploaded_files):
                    img = Image.open(f).convert("RGB")
                    pil_images.append(img)
                    cols[idx].image(img, caption=f.name, use_container_width=True)

                with st.spinner("🤖 Analyzing with Gemini..."):
                    user_q = user_text or "Analyze the uploaded images."
                    resp_text = get_gemini_response(input_prompt_base, pil_images, user_q)
                    st.subheader("✨ Response")
                    st.write(resp_text)

                    st.session_state["analyzer_history"].append((user_q, resp_text))

            except Exception as exc:
                st.error("Error while calling Gemini API.")
                st.text(traceback.format_exc())

# ===============================
# 🔹 Tab 2: Video Idea Organizer
# ===============================
with tab2:
    st.header("🎬 Video Idea Organizer")

    raw_idea = st.text_area("📝 Enter your raw video idea:", placeholder="Type your video idea here...")

    # Fixed category and tone
    category = "Content Creation"
    tone = "Creative"
    st.markdown(f"**Category:** {category}")
    st.markdown(f"**Tone:** {tone}")

    refine_btn = st.button("Refine Idea into Video Script & Images")

    def refine_video_idea(raw_text, category, tone):
        if not raw_text.strip():
            return {"script": "Please enter a raw video idea.", "images": ""}

        prompt = f"""
        You are a professional video content creator and AI prompt expert.
        Refine the following idea into a **video script** for a **minimum 1-minute video**.
        Include 4-6 scenes or segments.
        For each scene, provide a short **image prompt** describing visuals for AI image generation.
        Maintain category: {category} and tone: {tone}.
        Raw idea: {raw_text}
        Provide output in {selected_language}.
        Format:
        Scene 1:
        Script: ...
        Image Prompt: ...
        Scene 2:
        Script: ...
        Image Prompt: ...
        ...
        """
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            response = model.generate_content(prompt)
            return {"script": response.text, "images": response.text}  # same output for simplicity
        except Exception as e:
            return {"script": f"Error refining idea: {e}", "images": ""}

    if refine_btn:
        result = refine_video_idea(raw_idea, category, tone)
        st.subheader("✨ Refined Video Script & Scenes")
        st.info(result["script"])

        st.session_state["video_idea_history"].append({
            "raw": raw_idea,
            "script": result["script"],
            "images": result["images"],
            "category": category,
            "tone": tone
        })


# ===============================
# 🔹 Tab 3: Analyzer History
# ===============================
with tab3:
    st.header("📜 Analyzer History")
    if st.session_state["analyzer_history"]:
        for i, (q, r) in enumerate(st.session_state["analyzer_history"], 1):
            with st.expander(f"Query {i}"):
                st.markdown(f"**Q:** {q}")
                st.markdown(f"**A:** {r}")
    else:
        st.info("No analyzer history available.")

# ===============================
# 🔹 Tab 4: Video Idea History
# ===============================
with tab4:
    st.header("📜 Video Idea History")
    if st.session_state["video_idea_history"]:
        for i, item in enumerate(st.session_state["video_idea_history"], 1):
            with st.expander(f"Idea {i}"):
                st.markdown(f"**Raw:** {item['raw']}")
                st.markdown(f"**Script & Scenes:**\n{item['script']}")
                st.markdown(f"**Image Prompts:**\n{item['images']}")
                st.markdown(f"**Category:** {item['category']}")
                st.markdown(f"**Tone:** {item['tone']}")
    else:
        st.info("No video idea history yet.")
