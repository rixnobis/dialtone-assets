#!/usr/bin/env python3
# Batched whisper over a directory of takes: {path: {text, dur, rms_db, lead_s, tail_s}} -> DIR/asr.json
import sys, glob, json, numpy as np, soundfile as sf, torch, librosa
from transformers import pipeline
asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", device=0, torch_dtype=torch.float16)
d = sys.argv[1]; outp = f"{d}/asr.json"
try: res = json.load(open(outp))
except Exception: res = {}
ps = [p for p in sorted(glob.glob(d + "/*.wav")) if p not in res]
def meta(y, sr):
    a = np.abs(y); thr = max(a.max() * 0.03, 1e-4); nz = np.where(a > thr)[0]
    lead = nz[0] / sr if len(nz) else 0; tail = (len(y) - nz[-1]) / sr if len(nz) else 0
    return dict(dur=round(len(y) / sr, 2), rms_db=round(float(20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)), 1), lead_s=round(lead, 2), tail_s=round(tail, 2))
B = 64
for k in range(0, len(ps), B):
    part = ps[k:k + B]; ys = []
    for p in part:
        y, sr = sf.read(p); ys.append((y.astype(np.float32), sr))
    inp = [librosa.resample(y, orig_sr=sr, target_sr=16000) for y, sr in ys]
    outs = asr(inp, batch_size=32, generate_kwargs={"language": "english"})
    for p, (y, sr), o in zip(part, ys, outs): res[p.split("/")[-1]] = dict(text=o["text"].strip(), **meta(y, sr))
    json.dump(res, open(outp, "w"), indent=0); print("asr", k + len(part), "/", len(ps), flush=True)
