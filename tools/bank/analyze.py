# Objective read of audition wavs: whisper transcript, F0 (pyin) median/range, spectral centroid, duration.
import sys, glob, json, numpy as np, librosa, torch
from transformers import pipeline
asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", device=0, torch_dtype=torch.float16)
res = {}
import os
SH = os.environ.get("SHARD")
ps_all = sorted(glob.glob(sys.argv[1] + "/*.wav"))
if SH:
    k, n = map(int, SH.split("/")); ps_all = ps_all[k::n]
for p in ps_all:
    y, sr = librosa.load(p, sr=24000)
    f0, vf, _ = librosa.pyin(y, fmin=50, fmax=400, sr=sr)
    f = f0[~np.isnan(f0)]
    cen = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    t = asr(librosa.resample(y, orig_sr=sr, target_sr=16000))["text"].strip()
    res[p] = dict(dur=round(len(y)/sr,2), f0_med=round(float(np.median(f)),1) if len(f) else None,
                  f0_p10=round(float(np.percentile(f,10)),1) if len(f) else None, f0_p90=round(float(np.percentile(f,90)),1) if len(f) else None,
                  voiced=round(float(np.mean(vf)),2), centroid=round(cen), rms_db=round(float(20*np.log10(np.sqrt(np.mean(y**2))+1e-9)),1), text=t)
    print(p, json.dumps(res[p]), flush=True)
json.dump(res, open(sys.argv[1] + (f"/analysis-{SH.replace('/', 'of')}.json" if SH else "/analysis.json"), "w"), indent=1)
