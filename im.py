# streamlit_gemini_app_v6_fixed.py
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
            txt_data += f"Idea {i}:\nRaw: {item['raw']}\nScript:\n{item['script']}\n"
            txt_data += "Scenes:\n"
            for scene in item.get("scenes", []):
                txt_data += f"  {scene.get('title','Scene')}:\n"
                txt_data += f"    Script: {scene.get('script','')}\n"
                txt_data += f"    Image Prompt: {scene.get('image','')}\n"
                txt_data += f"    Narration: {scene.get('narration','')}\n"
            txt_data += f"Category: {item['category']}\nTone: {item['tone']}\n\n{'-'*40}\n\n"
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
# 🔹 Tab 2: Enhanced Video Idea Organizer
# ===============================
with tab2:
    st.header("🎬 Video Idea Organizer (Enhanced)")

    # User input
    raw_idea = st.text_area("📝 Enter your raw video idea:", placeholder="Type your video idea here...")

    # Category & Tone presets
    category_options = ["Content Creation", "Business", "Academic", "Project Idea"]
    tone_options = ["Creative", "Funny", "Motivational", "Tutorial", "Educational"]

    category = st.selectbox("📂 Select Category:", category_options, index=0)
    tone = st.selectbox("🎨 Select Tone:", tone_options, index=0)

    refine_btn = st.button("Refine Idea into Video Script & Scenes")

    # Helper: Estimate video duration
    def estimate_duration(text):
        words = len(text.split())
        duration_minutes = max(1, round(words / 150))  # 150 words ~ 1 min
        return duration_minutes

    # Helper: Refine idea via AI
    def refine_video_idea(raw_text, category, tone):
        if not raw_text.strip():
            return {"script": "Please enter a raw video idea.", "scenes": []}

        prompt = f"""
        You are a professional video content creator.
        Refine the following idea into a **video script** for a **minimum 1-minute video**.
        Include 4-6 scenes with: Script, AI image prompt, and narration-ready text.
        Maintain category: {category} and tone: {tone}.
        Raw idea: {raw_text}
        Provide output in {selected_language}.
        Format:
        Scene 1:
        Script: ...
        Image Prompt: ...
        Narration: ...
        Scene 2:
        Script: ...
        Image Prompt: ...
        Narration: ...
        """
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            response = model.generate_content(prompt)
            text = response.text

            # Split by scenes
            scenes = []
            for part in text.split("Scene ")[1:]:
                lines = part.strip().split("\n")
                scene_dict = {"title": "Scene " + lines[0].split(":")[0]}
                for line in lines[1:]:
                    if line.startswith("Script:"):
                        scene_dict["script"] = line.replace("Script:", "").strip()
                    elif line.startswith("Image Prompt:"):
                        scene_dict["image"] = line.replace("Image Prompt:", "").strip()
                    elif line.startswith("Narration:"):
                        scene_dict["narration"] = line.replace("Narration:", "").strip()
                scenes.append(scene_dict)

            return {"script": text, "scenes": scenes}

        except Exception as e:
            return {"script": f"Error refining idea: {e}", "scenes": []}

    # Refine and display
    if refine_btn:
        result = refine_video_idea(raw_idea, category, tone)
        scenes = result["scenes"]
        st.subheader("✨ Video Script & Scenes")

        # Display each scene as a card
        for i, scene in enumerate(scenes):
            st.markdown(f"### {scene['title']}")
            st.markdown(f"**Script:** {scene.get('script','')}")
            st.markdown(f"**Image Prompt:** {scene.get('image','')}")
            st.markdown(f"**Narration:** {scene.get('narration','')}")
            st.button("📋 Copy Script", key=f"copy_script_{i}")
            st.button("📋 Copy Image Prompt", key=f"copy_image_{i}")

        # Duration estimation
        total_duration = sum(estimate_duration(s.get("script","")) for s in scenes)
        st.info(f"🕒 Estimated Video Duration: ~{total_duration} minutes")

        # Save to session history
        st.session_state["video_idea_history"].append({
            "raw": raw_idea,
            "script": result["script"],
            "scenes": scenes,
            "category": category,
            "tone": tone
        })

        # Export buttons
        st.download_button("💾 Export as JSON", data=str(result), file_name="video_idea.json", mime="application/json")
        st.download_button("💾 Export as Markdown", data=result["script"], file_name="video_idea.md", mime="text/markdown")

# ===============================
# 🔹 Tab 3: Analyzer History
# ===============================
with tab3:
    st.header("📜 Analyzer History")
    if st.session_state["analyzer_history"]:
        to_delete = []
        for i, (q, r) in enumerate(st.session_state["analyzer_history"]):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                exp = st.expander(f"Query {i+1}")
            with col2:
                if st.button("🗑️", key=f"del_analyzer_{i}"):
                    to_delete.append(i)
            with exp:
                st.markdown(f"**Q:** {q}")
                st.markdown(f"**A:** {r}")
        for idx in sorted(to_delete, reverse=True):
            st.session_state["analyzer_history"].pop(idx)
    else:
        st.info("No analyzer history available.")

# ===============================
# 🔹 Tab 4: Video Idea History
# ===============================
with tab4:
    st.header("📜 Video Idea History")
    if st.session_state["video_idea_history"]:
        to_delete = []
        for i, item in enumerate(st.session_state["video_idea_history"]):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                exp = st.expander(f"Idea {i+1}")
            with col2:
                if st.button("🗑️", key=f"del_video_{i}"):
                    to_delete.append(i)
            with exp:
                st.markdown(f"**Raw Idea:** {item['raw']}")
                st.markdown(f"**Category:** {item['category']}")
                st.markdown(f"**Tone:** {item['tone']}")
                st.markdown(f"**Script & Scenes:**")
                for scene in item.get("scenes", []):
                    st.markdown(f"### {scene.get('title','Scene')}")
                    st.markdown(f"**Script:** {scene.get('script','')}")
                    st.markdown(f"**Image Prompt:** {scene.get('image','')}")
                    st.markdown(f"**Narration:** {scene.get('narration','')}")
        for idx in sorted(to_delete, reverse=True):
            st.session_state["video_idea_history"].pop(idx)
    else:
        st.info("No video idea history yet.")
