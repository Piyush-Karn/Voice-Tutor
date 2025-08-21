import os
import tempfile
import streamlit as st

def save_and_play_audio(wav_bytes: bytes, label: str = "Reply"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(wav_bytes)
        tmp.flush()
        path = tmp.name
    with open(path, "rb") as f:
        st.audio(f.read(), format="audio/wav")
    try:
        os.unlink(path)
    except Exception:
        pass
