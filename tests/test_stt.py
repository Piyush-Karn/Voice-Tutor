import io
import numpy as np
import soundfile as sf
from stt.utils import load_audio_to_mono_16k

def test_audio_loader():
sr = 22050
t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
tone = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
buf = io.BytesIO()
sf.write(buf, tone, sr, format="WAV")
data = buf.getvalue()
mono, sr2 = load_audio_to_mono_16k(data)
assert sr2 == 16000
assert mono.ndim == 1
assert len(mono) > 1000

