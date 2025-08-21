import streamlit as st
from nlp.mistral_service import LLMService
from tts.tts_service import TTSService
from tts.voice_utils import save_and_play_audio
from config.settings import Settings

def _init_session():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

def render_chat_ui(settings: Settings):
    _init_session()
    st.subheader("Chat")
    user_input = st.text_input("Type a question (e.g., What is a noun?)", key="chat_input")
    col1, col2 = st.columns([1, 1])
    with col1:
        ask = st.button("Ask")
    with col2:
        clear = st.button("Clear")

    if clear:
        st.session_state["messages"] = []
        st.rerun()

    if ask and user_input.strip():
        st.session_state["messages"].append(("user", user_input.strip()))
        llm = LLMService(settings)
        reply = llm.generate(user_input.strip())
        st.session_state["messages"].append(("bot", reply))
        tts = TTSService(settings)
        wav_bytes = tts.synthesize(reply)
        save_and_play_audio(wav_bytes, "Tutor Reply")

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for role, text in st.session_state["messages"]:
        css_class = "user" if role == "user" else "bot"
        st.markdown(f'<div class="chat-bubble {css_class}">{text}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
