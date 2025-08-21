import streamlit as st
from config.settings import Settings
from ui.chat_ui import render_chat_ui
from ui.audio_ui import render_audio_ui

st.set_page_config(page_title="Voice Tutor AI", page_icon="🧒🎧", layout="centered")

def main():
    st.title("Genie — Voice Tutor AI")
    st.caption("Kid-friendly voice tutor using your Mistral API and local STT/TTS.")
    settings = Settings.load()

    with st.sidebar:
        st.header("Settings")
        st.text(f"STT: {settings.STT_ENGINE}")
        st.text(f"LLM: {settings.LLM_PROVIDER}")
        st.text(f"TTS: {settings.TTS_ENGINE}")
        st.text(f"Language: {settings.LANGUAGE}")
        rate = st.slider("Voice Rate", 100, 220, settings.VOICE_RATE, 5)
        volume = st.slider("Voice Volume", 0, 100, int(settings.VOICE_VOLUME * 100), 5)
        if rate != settings.VOICE_RATE or volume != int(settings.VOICE_VOLUME * 100):
            settings.VOICE_RATE = rate
            settings.VOICE_VOLUME = volume / 100.0

    st.divider()
    render_audio_ui(settings)
    st.divider()
    render_chat_ui(settings)

if __name__ == "__main__":
    main()
