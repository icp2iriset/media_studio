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
st.write("Generate professional widescreen training media and voice narration directly from your browser.")

voice_options = {
    "Prabhat (Male - Indian)": "en-IN-PrabhatNeural",
    "Neerja (Female - Indian)": "en-IN-NeerjaNeural",
    "Neerja Expressive (Female - Indian)": "en-IN-NeerjaExpressiveNeural"
}
selected_voice = st.sidebar.selectbox("Select Voice Engine", list(voice_options.keys()))
voice_id = voice_options[selected_voice]

speed_options = {
    "Relaxed (0.9x)": "-10%",
    "Normal (1.0x)": "+0%",
    "Fast (1.1x)": "+10%"
}
selected_speed = st.sidebar.selectbox("Narration Speed", list(speed_options.keys()))
rate_str = speed_options[selected_speed]

custom_filename = st.sidebar.text_input("Output Package Name", value="IRISET_Training_Package")

if "slides" not in st.session_state:
    st.session_state.slides = [
        {"img": None, "script": "Welcome to Indian Railways Institute of Signal Engineering and Telecommunications", "keyword": "IRISET Academy"},
        {"img": None, "script": "Welcome to Optical Digital Telecommunication Laboratory", "keyword": "ODT Lab"}
    ]

col1, col2 = st.columns([4, 1])
with col1:
    st.subheader("📋 Slide Segments & Narration Scripts")
with col2:
    if st.button("➕ Add Slide"):
        st.session_state.slides.append({"img": None, "script": "", "keyword": ""})
        st.rerun()

for i, slide in enumerate(st.session_state.slides):
    with st.expander(f"Slide Segment #{i+1}", expanded=True):
        c1, c2 = st.columns([2, 3])
        with c1:
            slide["img"] = st.file_uploader(f"Upload Image #{i+1}", type=["png", "jpg", "jpeg"], key=f"img_{i}")
        with c2:
            slide["keyword"] = st.text_input(f"Highlight Keyword #{i+1}", value=slide["keyword"], key=f"kw_{i}")
            slide["script"] = st.text_area(f"Narration Script #{i+1}", value=slide["script"], key=f"txt_{i}", height=75)
            
        if len(st.session_state.slides) > 1 and st.button(f"🗑️ Remove Segment #{i+1}", key=f"del_{i}"):
            st.session_state.slides.pop(i)
            st.rerun()

async def generate_audio(text, v_id, r_str, path):
    communicate = edge_tts.Communicate(text, v_id, rate=r_str)
    await communicate.save(path)

if st.button("🚀 Generate Voiceover & Presentation Assets", type="primary", use_container_width=True):
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
                asyncio.run(generate_audio(s["script"], voice_id, rate_str, audio_path))
                
                audio_obj = MP3(audio_path)
                duration = audio_obj.info.length
                
                with open(audio_path, "rb") as f:
                    st.download_button(
                        label=f"📥 Download Audio Segment #{idx+1} ({s['keyword'] or 'Slide'}) - {duration:.1f}s",
                        data=f,
                        file_name=f"{safe_name}_seg_{idx+1}.mp3",
                        mime="audio/mpeg",
                        key=f"dl_{idx}"
                    )
            st.success("🎉 Voice narration segments successfully synthesized!")
        except Exception as e:
            st.error(f"Generation error: {e}")
