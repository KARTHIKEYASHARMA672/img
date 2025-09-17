# streamlit_gemini_app_v4.py
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
st.set_page_config(page_title="AI Image & Knowledge Assistant + Idea Organizer", layout="wide")

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

if "idea_history" not in st.session_state:
    st.session_state["idea_history"] = []

# ===============================
# 🔹 Sidebar
# ===============================
st.sidebar.title("📌 Settings / History")

# How it works section
st.sidebar.subheader("📝 How It Works")
st.sidebar.markdown("""
**Image & Text Analysis:**  
1. Upload images (jpg, jpeg, png).  
2. Optionally add a question.  
3. Select language and click Analyze.  
4. View response in main tab.  

**Daily Idea Organizer:**  
1. Enter any raw idea.  
2. Select category & tone.  
3. Click Refine to polish the prompt.  
4. Save or share refined ideas.  
""")

# Language selection
language_options = ["English", "Hindi", "Telugu", "Spanish", "French"]
selected_language = st.sidebar.selectbox("🌐 Select Output Language:", language_options)

# History controls
st.sidebar.subheader("📜 History")
if st.sidebar.button("🗑️ Clear AI History"):
    st.session_state["history"] = []
    st.sidebar.success("AI history cleared!")

if st.sidebar.button("💾 Download AI History"):
    if st.session_state["history"]:
        txt_data = ""
        for i, (q, r) in enumerate(st.session_state["history"], 1):
            txt_data += f"Query {i}:\n{q}\nResponse:\n{r}\n\n{'-'*40}\n\n"
        st.sidebar.download_button(
            label="Download AI History as TXT",
            data=txt_data,
            file_name="ai_history.txt",
            mime="text/plain"
        )
    else:
        st.sidebar.warning("No AI history to download!")

# Idea Organizer history
if st.sidebar.button("🗑️ Clear Idea History"):
    st.session_state["idea_history"] = []
    st.sidebar.success("Idea history cleared!")

if st.sidebar.button("💾 Download Idea History"):
    if st.session_state["idea_history"]:
        txt_data = ""
        for i, item in enumerate(st.session_state["idea_history"], 1):
            txt_data += f"Idea {i}:\nRaw: {item['raw']}\nRefined: {item['refined']}\nCategory: {item['category']}\nTone: {item['tone']}\n\n{'-'*40}\n\n"
        st.sidebar.download_button(
            label="Download Idea History as TXT",
            data=txt_data,
            file_name="idea_history.txt",
            mime="text/plain"
        )
    else:
        st.sidebar.warning("No idea history to download!")

# ===============================
# 🔹 Tabs UI
# ===============================
tab1, tab2, tab3 = st.tabs(["Image & Text Analysis", "History", "Daily Idea Organizer"])

# ===============================
# 🔹 Tab 1: Image & Text Analysis
# ===============================
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
    You are an expert analyzing images. Provide detailed insights in {selected_language}.
    """

    resp_text = ""
    summary_text = ""

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
                
                # Side-by-side display using columns
                num_files = len(uploaded_files)
                cols = st.columns(num_files)
                for idx, f in enumerate(uploaded_files):
                    img = Image.open(f).convert("RGB")
                    pil_images.append(img)
                    cols[idx].image(img, caption=f.name, use_container_width=True)

                with st.spinner("🤖 Analyzing with Gemini..."):
                    user_q = user_text or "Analyze the uploaded images."
                    resp_text = get_gemini_response(input_prompt_base, pil_images, user_q)
                    st.subheader("✨ Response")
                    st.write(resp_text)

                    # Save history
                    st.session_state["history"].append((user_q, resp_text))

                    # Generate summary (first 2–3 sentences)
                    summary_text = ". ".join(resp_text.split(".")[:3]) + "."
                    st.subheader("📝 Summary")
                    st.write(summary_text)

            except Exception as exc:
                st.error("Error while calling Gemini API.")
                st.text(traceback.format_exc())

# ===============================
# 🔹 Tab 2: History
# ===============================
with tab2:
    st.header("📜 Chat & Idea History")
    st.subheader("AI Image/Text Queries")
    if st.session_state["history"]:
        for i, (q, r) in enumerate(st.session_state["history"], 1):
            with st.expander(f"Query {i}"):
                st.markdown(f"**Q:** {q}")
                st.markdown(f"**A:** {r}")
    else:
        st.info("No AI history available.")

    st.subheader("Refined Ideas")
    if st.session_state["idea_history"]:
        for i, item in enumerate(st.session_state["idea_history"], 1):
            with st.expander(f"Idea {i}"):
                st.markdown(f"**Raw:** {item['raw']}")
                st.markdown(f"**Refined:** {item['refined']}")
                st.markdown(f"**Category:** {item['category']}")
                st.markdown(f"**Tone:** {item['tone']}")
    else:
        st.info("No refined ideas yet.")

# ===============================
# 🔹 Tab 3: Daily Idea Organizer
# ===============================
with tab3:
    st.header("💡 Daily Idea Organizer")

    raw_idea = st.text_area("📝 Enter your raw idea:", placeholder="Type anything...")
    category = st.selectbox("📂 Select Category:", ["Project Idea", "Content Creation", "Business", "Academic"])
    tone = st.selectbox("🎨 Select Tone:", ["Creative", "Professional", "Academic"])

    refine_btn = st.button("Refine Idea")

    def refine_idea(raw_text, category, tone):
        """
        Generate a polished idea prompt using Gemini AI.
        """
        if not raw_text.strip():
            return "Please enter a raw idea to refine."
        prompt = f"""
        You are an expert prompt writer. Refine the following raw idea into a clear, actionable prompt.
        Category: {category}
        Tone: {tone}
        Raw idea: {raw_text}
        Provide the refined prompt in {selected_language}.
        """
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error refining idea: {e}"

    if refine_btn:
        refined = refine_idea(raw_idea, category, tone)
        st.subheader("✨ Refined Prompt")
        st.info(refined)

        # Save to session history
        st.session_state["idea_history"].append({
            "raw": raw_idea,
            "refined": refined,
            "category": category,
            "tone": tone
        })

        # Optional: share or copy button
        st.button("📋 Copy to Clipboard", on_click=lambda: st.experimental_set_query_params(copy=refined))
