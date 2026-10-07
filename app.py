import streamlit as st
import os
import asyncio
import tempfile
import random
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw, ImageFont
from mutagen.mp3 import MP3
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import edge_tts

st.set_page_config(page_title="IRISET Media Studio Pro", page_icon="🎓", layout="wide")
st.title("🎓 IRISET Media Studio Pro (Cloud Widescreen Edition)")
st.write("Generate full HD 16:9 widescreen training videos with neural voiceover and subtitles directly from your browser.")

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

burn_subs = st.sidebar.checkbox("✨ Burn Lower-Third Subtitles", value=True)
ken_burns = st.sidebar.checkbox("🎞️ Cinematic Zoom Animation", value=True)
custom_filename = st.sidebar.text_input("Output Video Filename", value="IRISET_Training_Video")

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

def create_frame(img_bytes, text_chunk, keyword=""):
    raw_img = Image.open(img_bytes).convert("RGB")
    bg_fill = ImageOps.fit(raw_img, (1920, 1080), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    bg_fill = bg_fill.filter(ImageFilter.GaussianBlur(radius=30))
    bg_fill = ImageEnhance.Brightness(bg_fill).enhance(0.3)
    
    orig_w, orig_h = raw_img.size
    scale = min(1750 / orig_w, 920 / orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    resized_img = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    canvas = bg_fill.copy()
    paste_x = (1920 - new_w) // 2
    paste_y = (1080 - new_h) // 2 - 35
    canvas.paste(resized_img, (paste_x, paste_y))
    
    draw = ImageDraw.Draw(canvas, "RGBA")
    try:
        font = ImageFont.truetype("arial.ttf", 40)
        kw_font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
        kw_font = ImageFont.load_default()
        
    if keyword:
        kw_w = int(kw_font.getlength(keyword)) + 40
        draw.rounded_rectangle([1920 - kw_w - 60, 40, 1920 - 60, 100], radius=12, fill=(13, 148, 136, 230))
        draw.text((1920 - kw_w - 40, 50), f"★ {keyword}", fill=(255, 255, 255), font=kw_font)
        
    if text_chunk:
        draw.rectangle([60, 1080 - 110, 1920 - 60, 1080 - 30], fill=(0, 0, 0, 200))
        draw.text((1920 // 2, 1080 - 70), text_chunk, fill=(255, 255, 255), font=font, anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    return canvas

async def generate_audio(text, v_id, r_str, path):
    communicate = edge_tts.Communicate(text, v_id, rate=r_str)
    await communicate.save(path)

if st.button("🚀 Compile Full HD Widescreen Video", type="primary", use_container_width=True):
    valid = True
    for idx, s in enumerate(st.session_state.slides):
        if not s["img"] or not s["script"].strip():
            st.error(f"Please ensure Slide #{idx+1} has both an image and a script!")
            valid = False
            
    if valid:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        temp_dir = tempfile.gettempdir()
        safe_name = "".join(c for c in custom_filename if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        output_path = os.path.join(temp_dir, f"{safe_name}.mp4")
        
        try:
            clips = []
            total_slides = len(st.session_state.slides)
            
            for idx, s in enumerate(st.session_state.slides):
                status_text.text(f"Processing Segment {idx+1} of {total_slides}...")
                progress_bar.progress(idx / total_slides)
                
                audio_path = os.path.join(temp_dir, f"audio_{random.randint(1000,9999)}.mp3")
                asyncio.run(generate_audio(s["script"], voice_id, rate_str, audio_path))
                
                duration = MP3(audio_path).info.length
                audio_clip = AudioFileClip(audio_path)
                
                if burn_subs and s["script"].strip():
                    words = s["script"].split()
                    chunks = [" ".join(words[i:i+6]) for i in range(0, len(words), 6)]
                    sub_clips = []
                    for chunk in chunks:
                        chunk_dur = max(0.5, duration * (len(chunk.split()) / len(words)))
                        frame_img = create_frame(s["img"], chunk, s["keyword"])
                        img_path = os.path.join(temp_dir, f"frame_{random.randint(1000,9999)}.png")
                        frame_img.save(img_path)
                        
                        clip = ImageClip(img_path).set_duration(chunk_dur)
                        if ken_burns:
                            clip = clip.resize(lambda t: 1.0 + 0.06 * (t / chunk_dur))
                        sub_clips.append(clip)
                    slide_stream = concatenate_videoclips(sub_clips, method="compose")
                else:
                    frame_img = create_frame(s["img"], "", s["keyword"])
                    img_path = os.path.join(temp_dir, f"frame_{random.randint(1000,9999)}.png")
                    frame_img.save(img_path)
                    slide_stream = ImageClip(img_path).set_duration(duration)
                    if ken_burns:
                        slide_stream = slide_stream.resize(lambda t: 1.0 + 0.06 * (t / duration))
                        
                clips.append(slide_stream.set_audio(audio_clip))
                
            status_text.text("Stitching final broadcast video stream...")
            final_video = concatenate_videoclips(clips, method="compose")
            final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', bitrate="5000k", logger=None)
            
            progress_bar.progress(1.0)
            status_text.text("Compilation successful!")
            st.success("🎉 Full HD Widescreen Video compiled successfully!")
            
            with open(output_path, "rb") as f:
                st.download_button("📥 Download Compiled Video (.mp4)", f, file_name=f"{safe_name}.mp4", mime="video/mp4", use_container_width=True)
                
        except Exception as e:
            st.error(f"An error occurred during video compilation: {e}")
