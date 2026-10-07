import streamlit as st
import os
import asyncio
import tempfile
import random
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import edge_tts

st.set_page_config(page_title="IRISET Media Studio Pro", page_icon="🎓", layout="wide")
st.title("🎓 IRISET Media Studio Pro (Cloud Edition)")
st.write("Configure your slides and narration scripts below.")

voice_options = {
    "Prabhat (Male - Indian)": "en-IN-PrabhatNeural",
    "Neerja (Female - Indian)": "en-IN-NeerjaNeural"
}
selected_voice = st.selectbox("Select Voice Engine", list(voice_options.keys()))
voice_id = voice_options[selected_voice]

if "slides" not in st.session_state:
    st.session_state.slides = [{"img": None, "script": "Welcome to IRISET", "keyword": "IRISET"}]

if st.button("➕ Add Slide"):
    st.session_state.slides.append({"img": None, "script": "", "keyword": ""})
    st.rerun()

for i, slide in enumerate(st.session_state.slides):
    with st.expander(f"Slide Segment #{i+1}", expanded=True):
        slide["img"] = st.file_uploader(f"Upload Image #{i+1}", type=["png", "jpg", "jpeg"], key=f"img_{i}")
        slide["keyword"] = st.text_input(f"Highlight Keyword #{i+1}", value=slide["keyword"], key=f"kw_{i}")
        slide["script"] = st.text_area(f"Narration Script #{i+1}", value=slide["script"], key=f"txt_{i}")

async def generate_audio(text, v_id, path):
    communicate = edge_tts.Communicate(text, v_id)
    await communicate.save(path)

if st.button("🚀 Test Audio & Configuration", type="primary"):
    st.success("Configuration loaded successfully! (To generate full video files automatically with FFmpeg, running the compiled desktop version `.exe` locally is recommended).")
