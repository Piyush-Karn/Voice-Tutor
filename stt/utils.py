import io
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

def load_audio_to_mono_16k(file_bytes: bytes):
    data, sr = sf.read(io.BytesIO(file_bytes), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr != 16000:
        mono = resample_poly(mono, 16000, sr)
    return mono, 16000

def to_int16_pcm(mono_float: np.ndarray):
    mono_clipped = np.clip(mono_float, -1.0, 1.0)
    return (mono_clipped * 32767).astype(np.int16)
