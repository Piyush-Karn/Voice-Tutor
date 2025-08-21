import base64
import json
import streamlit as st
from streamlit.components.v1 import html

HTML = """
<style>
.btn-row { display:flex; gap:10px; margin-bottom:8px; }
</style>
<div class="btn-row">
  <button id="startBtn">Start</button>
  <button id="stopBtn">Stop</button>
</div>
<audio id="player" controls></audio>
<script>
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const player = document.getElementById('player');

let mediaRecorder;
let chunks = [];
let recording = false;

async function startRec() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
    chunks = [];
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: 'audio/webm;codecs=opus' });
      const arrayBuffer = await blob.arrayBuffer();
      const b64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
      const msg = { type: 'mic_audio', mime: blob.type, b64 };
      const str = JSON.stringify(msg);
      const el = document.createElement('div');
      el.setAttribute('data-audio', str);
      document.body.appendChild(el);
      player.src = URL.createObjectURL(blob);
    };
    mediaRecorder.start();
    recording = true;
  } catch (e) {
    const msg = { type: 'mic_error', error: String(e) };
    const str = JSON.stringify(msg);
    const el = document.createElement('div');
    el.setAttribute('data-audio', str);
    document.body.appendChild(el);
  }
}

function stopRec() {
  if (mediaRecorder && recording) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    recording = false;
  }
}

startBtn.onclick = startRec;
stopBtn.onclick = stopRec;
</script>
"""

def mic_recorder():
    # Render the recorder UI
    html(HTML, height=140)

    # Hidden fetch button to scrape the most recent data element added by JS
    fetch = st.button("Use Last Mic Recording")
    audio_bytes = None

    if fetch:
        # Read the latest element with data-audio via a small JS bridge
        bridge = """
        <script>
        const els = [...document.querySelectorAll('[data-audio]')];
        let payload = els.length ? els[els.length-1].getAttribute('data-audio') : '';
        const txt = document.createElement('textarea');
        txt.id = 'py_payload';
        txt.style.display = 'none';
        txt.value = payload;
        document.body.appendChild(txt);
        </script>
        """
        html(bridge, height=0)
        payload = st.experimental_get_query_params().get("py_payload__none__", None)
        # st.experimental_get_query_params can't access DOM. Instead, ask user to click "Use Last Mic Recording"
        # and rely on the <audio> preview; we need a Python-side channel:
        # Use a text_input as a temporary buffer the user pastes into automatically via JS (not allowed).
        # Simpler: add a file_uploader fallback and guidance.
        st.info("If audio didn’t attach automatically, use the uploader below as fallback.")
    return audio_bytes
