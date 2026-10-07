import streamlit as st
import os
import asyncio
import tempfile
import random
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw, ImageFont
from mutagen.mp3 import MP3
import edge_tts

st.set_page_config(page_title="IRISET Media Studio Pro", page_icon="🎓", layout="wide")
st.title("🎓 IRISET Media Studio Pro (Cloud Web Edition)")
st.write("Generate synchronized voice narration and slide graphics directly from your browser.")

voice_options = {
    "Prabhat (Male - Indian)": "en-IN-PrabhatNeural",
    "Neerja (Female - Indian)": "en-IN-NeerjaNeural",
    "Neerja Expressive (Female - Indian)": "en-IN-NeerjaExpressiveNeural"
}
selected_voice = st.selectbox("Select Voice Engine", list(voice_options.keys()))
voice_id = voice_options[selected_voice]

burn_subs = st.checkbox("✨ Burn Subtitles & Keywords", value=True)
custom_filename = st.text_input("Output Audio Package Name", value="IRISET_Training_Package")

if "slides" not in st.session_state:
    st.session_state.slides = [
        {"img": None, "script": "Welcome to Indian Railways Institute of Signal Engineering and Telecommunications", "keyword": "IRISET Academy"},
        {"img": None, "script": "Welcome to Optical Digital Telecommunication Laboratory", "keyword": "ODT Lab"}
    ]

if st.button("➕ Add Slide"):
    st.session_state.slides.append({"img": None, "script": "", "keyword": ""})
    st.rerun()

for i, slide in enumerate(st.session_state.slides):
    with st.expander(f"Slide Segment #{i+1}", expanded=True):
        col1, col2 = st.columns([2, 3])
        with col1:
            slide["img"] = st.file_uploader(f"Upload Image #{i+1}", type=["png", "jpg", "jpeg"], key=f"img_{i}")
        with col2:
            slide["keyword"] = st.text_input(f"Highlight Keyword #{i+1}", value=slide["keyword"], key=f"kw_{i}")
            slide["script"] = st.text_area(f"Narration Script #{i+1}", value=slide["script"], key=f"txt_{i}", height=75)
            
        if len(st.session_state.slides) > 1 and st.button(f"🗑️ Remove Segment #{i+1}", key=f"del_{i}"):
            st.session_state.slides.pop(i)
            st.rerun()

async def generate_audio(text, v_id, path):
    communicate = edge_tts.Communicate(text, v_id)
    await communicate.save(path)

if st.button("🚀 Synthesize Voice & Generate Package", type="primary", use_container_width=True):
    valid = True
    for idx, s in enumerate(st.session_state.slides):
        if not s["img"] or not s["script"].strip():
            st.error(f"Please ensure Slide #{idx+1} has both an image and a script!")
            valid = False
            
    if valid:
        temp_dir = tempfile.gettempdir()
        safe_name = "".join(c for c in custom_filename if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        
        try:
            for idx, s in enumerate(st.session_state.slides):
                audio_path = os.path.join(temp_dir, f"{safe_name}_segment_{idx+1}.mp3")
                asyncio.run(generate_audio(s["script"], voice_id, audio_path))
                
                with open(audio_path, "rb") as f:
                    st.download_button(f"📥 Download Audio Segment #{idx+1} ({s['keyword'] or 'Slide'})", f, file_name=f"{safe_name}_seg_{idx+1}.mp3", mime="audio/mpeg")
                    
            st.success("🎉 Voice narration segments successfully generated and ready for download!")
        except Exception as e:
            st.error(f"Synthesis failed: {e}")
