\
import numpy as np
import torchaudio
import torch
from speechbrain.pretrained import EncoderClassifier

_cls = None

def _load_classifier():
    global _cls
    if _cls is None:
        _cls = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts={"device": "cpu"}
        )
    return _cls

def wav_to_xvector(wav_path: str) -> np.ndarray:
    cls = _load_classifier()
    waveform, sr = torchaudio.load(wav_path)
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    emb = cls.encode_batch(waveform).squeeze(0).squeeze(0)
    return emb.detach().cpu().numpy()
