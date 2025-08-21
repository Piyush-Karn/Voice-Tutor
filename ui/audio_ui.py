import streamlit as st
from stt.stt_service import STTService
from nlp.mistral_service import LLMService
from tts.tts_service import TTSService
from tts.voice_utils import save_and_play_audio
from config.settings import Settings

def render_audio_ui(settings: Settings):
    st.subheader("Voice")
    st.write("Upload a short audio clip (WAV/MP3/M4A/OGG/WEBM). Keep it under 30s for quick results.")
    audio_file = st.file_uploader("Choose audio", type=["wav", "mp3", "m4a", "ogg", "webm", "opus"])
    go = st.button("Transcribe and Reply")

    if go and audio_file is not None:
        audio_bytes = audio_file.read()
        st.info("Transcribing...")
        stt = STTService(settings)
        text = stt.transcribe(audio_bytes, language=settings.LANGUAGE) or ""
        if not text:
            st.warning("Could not transcribe the audio. Try a clearer recording.")
            return
        st.success(f"Transcript: {text}")

        st.info("Thinking...")
        llm = LLMService(settings)
        reply = llm.generate(text)
        st.success(f"Tutor: {reply}")

        st.info("Speaking...")
        tts = TTSService(settings)
        wav_bytes = tts.synthesize(reply)
        save_and_play_audio(wav_bytes, "Tutor Reply")
