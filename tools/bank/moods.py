#!/usr/bin/env python3
# Stage B: delivery-reference candidates. Clone each voice's locked ref with one sentence per delivery group, N seeds.
#   python3 moods.py refs.json OUTDIR seeds      refs.json = {voice: {"wav":..., "text":..., "groups":[...]}}
import json, sys, os, time, torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
S = {"neutral": "Yes, this is the right number. I'm home most evenings, so you can call back then.",
     "up": "Oh, that's wonderful news! Really, I'm so glad you called, this made my whole day!",
     "hot": "No! Absolutely not! I've told you people a hundred times, stop calling this number!",
     "low": "Oh... I'm just so tired. It's been a long, long day, and I really don't have it in me.",
     "hush": "Shh, keep your voice down, please. I can't talk right now, someone might hear me."}
refs = json.load(open(sys.argv[1])); out = sys.argv[2]; seeds = [int(s) for s in sys.argv[3].split(",")]
os.makedirs(out, exist_ok=True)
b = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cuda:0", dtype=torch.bfloat16)
P = {v: b.create_voice_clone_prompt(ref_audio=r["wav"], ref_text=r["text"])[0] for v, r in refs.items()}
jobs = [(v, g) for v, r in refs.items() for g in ["neutral"] + [g for g in r["groups"] if g != "neutral"]]
BS = int(os.environ.get("BS", "32")); rec = []
for s in seeds:
    for k in range(0, len(jobs), BS):
        part = [j for j in jobs[k:k + BS] if not os.path.exists(f"{out}/{j[0]}_{j[1]}_s{s}.wav")]
        if not part: continue
        torch.manual_seed(s); torch.cuda.manual_seed_all(s); t = time.time()
        w, sr = b.generate_voice_clone(text=[S[g] for _, g in part], language=["English"] * len(part), voice_clone_prompt=[P[v] for v, _ in part])
        for (v, g), x in zip(part, w): sf.write(f"{out}/{v}_{g}_s{s}.wav", x, sr)
        rec.append({"seed": s, "order": part}); print("seed", s, k, len(part), round(time.time() - t, 1), flush=True)
json.dump({"sentences": S, "batches": rec}, open(f"{out}/moods.json", "w"), indent=1)
