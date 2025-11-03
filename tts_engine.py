\
import os
import tempfile
import numpy as np
from typing import Optional
from scipy.io.wavfile import write as write_wav
from pydub import AudioSegment
import subprocess

import torch
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset

# Globals
_processor = None
_model = None
_vocoder = None

VOICES_DIR = "voices"
os.makedirs(VOICES_DIR, exist_ok=True)

# Predefined human-friendly voice names mapped to indices in cmu-arctic-xvectors
_PRESET_VOICES = {
    "abraham": 0,
    "amanuel": 5,
    "mikael": 9,
    "hana": 12,
    "sara": 18
}

def _load_models():
    global _processor, _model, _vocoder
    if _processor is None:
        _processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
    if _model is None:
        _model = SpeechT5ForTextToSpeech.from_pretrained("AddisuSeteye/speecht5_tts_amharic")
    if _vocoder is None:
        _vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

def _ensure_voice_file(name: str) -> str:
    """
    Ensure a speaker embedding npy exists for `name`. If missing,
    create from cmu-arctic-xvectors dataset using a stable index.
    """
    path = os.path.join(VOICES_DIR, f"{name}.npy")
    if os.path.exists(path):
        return path

    idx = _PRESET_VOICES.get(name.lower(), 0)
    ds = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
    xvec = ds[idx]["xvector"]
    np.save(path, np.array(xvec, dtype=np.float32))
    return path

def _get_user_voice_path(user_id: Optional[int]) -> Optional[str]:
    if user_id is None:
        return None
    p = os.path.join(VOICES_DIR, f"{user_id}.npy")
    return p if os.path.exists(p) else None

def _load_speaker_tensor(voice_name: Optional[str], user_id: Optional[int]) -> torch.Tensor:
    # Priority: user voice -> chosen named voice -> abraham
    p = _get_user_voice_path(user_id)
    if p is None:
        if voice_name is None:
            voice_name = "abraham"
        p = _ensure_voice_file(voice_name)
    arr = np.load(p)
    return torch.tensor(arr).unsqueeze(0)

def _apply_pitch_on_wav(src_wav: str, dst_wav: str, semitones: int = 0):
    """Use ffmpeg to shift pitch by N semitones while keeping duration."""
    if semitones == 0:
        # No processing, just copy
        AudioSegment.from_file(src_wav, format="wav").export(dst_wav, format="wav")
        return
    factor = 2 ** (semitones / 12.0)
    # asetrate changes pitch&speed, then atempo fixes speed
    cmd = [
        "ffmpeg", "-y", "-i", src_wav,
        "-af", f"asetrate=16000*{factor},aresample=16000,atempo={1/factor}",
        dst_wav
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def amharic_tts_to_ogg(text: str, user_id: Optional[int] = None,
                       voice_name: Optional[str] = None, pitch_semitones: int = 0) -> str:
    """
    Generate Amharic speech and return an .ogg opus file path.
    voice_name: one of ["abraham","amanuel","mikael","hana","sara"] or None.
    pitch_semitones: integer from -6..+6 typically.
    """
    _load_models()
    inputs = _processor(text=text, return_tensors="pt")
    spk = _load_speaker_tensor(voice_name, user_id)

    with torch.no_grad():
        speech = _model.generate_speech(
            inputs["input_ids"],
            speaker_embeddings=spk,
            vocoder=_vocoder
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wf:
        wav_path = wf.name
    audio_np = speech.numpy()
    write_wav(wav_path, rate=16000, data=(audio_np * 32767).astype(np.int16))

    # Optional pitch
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wf2:
        wav2 = wf2.name
    _apply_pitch_on_wav(wav_path, wav2, pitch_semitones)
    try:
        os.remove(wav_path)
    except Exception:
        pass

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as ogg:
        ogg_path = ogg.name
    AudioSegment.from_file(wav2, format="wav").export(
        ogg_path, format="ogg", codec="libopus", bitrate="48k"
    )
    try:
        os.remove(wav2)
    except Exception:
        pass
    return ogg_path
