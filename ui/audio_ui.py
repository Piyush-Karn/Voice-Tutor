import streamlit as st
import av
import io
import time
import wave
import os
os.environ["AIORTC_ICE_TCP"] = "1" # enable TCP ICE candidates
os.environ["AIORTC_SDP_DSCP"] = "0" # avoid DSCP marking issues on Windows
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase, RTCConfiguration

from stt.stt_service import STTService
from nlp.mistral_service import LLMService
from tts.tts_service import TTSService
from tts.voice_utils import save_and_play_audio
from config.settings import Settings



RTC_CONFIG = RTCConfiguration({"iceServers": []})
PARTIAL_WINDOW_SEC = 4.0
PARTIAL_COOLDOWN_SEC = 1.5

class StreamingState:
    def __init__(self):
        self.frames = []
        self.sample_rate = 48000
        self.partial_buf = []
        self.last_partial_time = 0.0
        self.partial_text = ""
        self.has_audio = False

class AudioProcessor(AudioProcessorBase):
    def __init__(self, state: StreamingState) -> None:
        self.state = state

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        try:
            pcm = frame.to_ndarray()
            if pcm.ndim == 2:
                pcm = pcm.mean(axis=0).astype(np.int16)
            else:
                pcm = pcm.astype(np.int16)
            b = pcm.tobytes()
            self.state.frames.append(b)
            self.state.partial_buf.append(b)
            self.state.sample_rate = frame.sample_rate or self.state.sample_rate
            self.state.has_audio = True
        except Exception as e:
            # lightweight debug
            print("recv_audio error:", e)
        return frame

def _pcm_bytes_to_wav(pcm_bytes: bytes, sr: int, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()

def _trim_to_window(state: StreamingState) -> bytes:
    if not state.partial_buf:
        return b""
    blob = b"".join(state.partial_buf)
    bytes_per_sec = state.sample_rate * 2
    needed = int(PARTIAL_WINDOW_SEC * bytes_per_sec)
    if len(blob) > needed:
        blob = blob[-needed:]
        acc = 0
        new_chunks = []
        for ch in reversed(state.partial_buf):
            if acc >= needed:
                break
            new_chunks.insert(0, ch)
            acc += len(ch)
        state.partial_buf = new_chunks
    return blob

def _init_state():
    if "webrtc_connected" not in st.session_state:
        st.session_state["webrtc_connected"] = False
    if "processor_attached" not in st.session_state:
        st.session_state["processor_attached"] = False
    if "is_recording" not in st.session_state:
        st.session_state["is_recording"] = False
    if "stream_state" not in st.session_state:
        st.session_state["stream_state"] = StreamingState()
    if "selected_device_id" not in st.session_state:
        st.session_state["selected_device_id"] = None
    if "last_debug" not in st.session_state:
        st.session_state["last_debug"] = "init"

def render_audio_ui(settings: Settings):
    _init_state()
    state: StreamingState = st.session_state["stream_state"]

    st.subheader("Voice (Live Transcription)")
    st.write("Select your microphone, then click Start Recording. Speak, then click Stop Recording. Finally, press Transcribe and Reply.")

    # Device selection UI (text field for exact deviceId to maximize reliability)
    with st.expander("Select device", expanded=False):
        st.caption("If unsure, leave blank. To ensure a specific mic is used, paste its deviceId here.")
        device_id = st.text_input("Input deviceId (optional)", value=st.session_state["selected_device_id"] or "")
        if st.button("Apply Device", key="btn_apply_device"):
            st.session_state["selected_device_id"] = device_id or None

    # Build constraints: when deviceId provided, set exact device
    constraints = {"audio": True, "video": False}
    if st.session_state["selected_device_id"]:
        constraints = {
            "audio": {"deviceId": {"exact": st.session_state["selected_device_id"]}},
            "video": False
        }

    ctx = webrtc_streamer(
        key="voice-persist",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints=constraints,
        async_processing=True,
    )

    # Attach once when pipeline is active
    if ctx and ctx.state.playing:
        st.session_state["webrtc_connected"] = True
        if not st.session_state["processor_attached"]:
            ctx.audio_receiver._processor = AudioProcessor(state)
            st.session_state["processor_attached"] = True
            st.session_state["last_debug"] = "processor_attached"
    else:
        st.session_state["webrtc_connected"] = False

    # One toggle button
    toggle_label = "Stop Recording" if st.session_state["is_recording"] else "Start Recording"
    if st.button(toggle_label, key="btn_toggle"):
        if not st.session_state["webrtc_connected"]:
            st.warning("Mic pipeline not connected yet. Allow permission and wait for connection, then try again.")
        else:
            st.session_state["is_recording"] = not st.session_state["is_recording"]
            if st.session_state["is_recording"]:
                # Start: do NOT clear processor or pipeline; only reset buffers
                state.frames.clear()
                state.partial_buf.clear()
                state.partial_text = ""
                state.last_partial_time = 0.0
                state.has_audio = False
                st.session_state["last_debug"] = "recording_started"
                st.info("Recording... speak your question.")
            else:
                st.session_state["last_debug"] = "recording_stopped"
                if state.has_audio:
                    st.success("Recording stopped. Click Transcribe and Reply.")
                else:
                    st.warning("No audio detected. Check mic, device selection, and try again.")

    # Live captions
    partial_box = st.empty()
    if st.session_state["is_recording"] and st.session_state["processor_attached"]:
        now = time.time()
        if now - state.last_partial_time > PARTIAL_COOLDOWN_SEC:
            part_pcm = _trim_to_window(state)
            if part_pcm:
                wav_bytes = _pcm_bytes_to_wav(part_pcm, state.sample_rate, channels=1)
                stt_quick = STTService(settings)
                try:
                    partial_text = stt_quick.transcribe(wav_bytes, language=settings.LANGUAGE) or ""
                    if partial_text:
                        state.partial_text = partial_text
                        state.last_partial_time = now
                        st.session_state["last_debug"] = "partial_ok"
                except Exception as e:
                    st.session_state["last_debug"] = f"partial_err:{e}"
        partial_box.info(f"Live captions: {state.partial_text or 'Listening...'}")
    else:
        partial_box.empty()

    # Visible debug line to see state transitions
    st.caption(f"Debug: connected={st.session_state['webrtc_connected']}, processor={st.session_state['processor_attached']}, recording={st.session_state['is_recording']}, has_audio={state.has_audio}, last={st.session_state['last_debug']}")

    st.divider()
    if st.button("Transcribe and Reply", key="btn_process"):
        if not state.has_audio or len(state.frames) == 0:
            st.warning("No audio captured. Click Start Recording, speak, then Stop Recording.")
            return

        full_pcm = b"".join(state.frames)
        wav_bytes = _pcm_bytes_to_wav(full_pcm, state.sample_rate, channels=1)

        st.info("Transcribing final audio...")
        stt = STTService(settings)
        final_text = stt.transcribe(wav_bytes, language=settings.LANGUAGE) or ""
        if not final_text:
            st.warning("Could not transcribe. Please try again closer to the mic.")
            return
        st.success(f"Transcript: {final_text}")

        st.info("Thinking (Mistral API)...")
        llm = LLMService(settings, strict_api=True)
        reply = llm.generate(final_text)
        st.success(f"Tutor: {reply}")

        st.info("Speaking...")
        tts = TTSService(settings)
        out_wav = tts.synthesize(reply)
        save_and_play_audio(out_wav, "Tutor Reply")
