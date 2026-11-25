#!/usr/bin/env python3
# Stage A: design candidate references with VoiceDesign, one batched call per seed.
#   python3 design.py cast.json OUTDIR "c12,c13,..." 41,1163,2026,7,99,512
# Writes OUTDIR/<id>_s<seed>.wav and OUTDIR/design.json (batch order per seed, so a re-run reproduces).
import json, sys, os, time, torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
cast = {c["id"]: c for c in json.load(open(sys.argv[1]))}
out = sys.argv[2]; ids = sys.argv[3].split(","); seeds = [int(s) for s in sys.argv[4].split(",")]
os.makedirs(out, exist_ok=True)
d = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cuda:0", dtype=torch.bfloat16)
rec = {"model": "Qwen3-TTS-12Hz-1.7B-VoiceDesign", "batches": []}
CH = int(os.environ.get("CHUNK", "11"))
for s in seeds:
    for k in range(0, len(ids), CH):
        part = ids[k:k + CH]
        torch.manual_seed(s); torch.cuda.manual_seed_all(s); t = time.time()
        w, sr = d.generate_voice_design(text=[cast[i]["ref_text"] for i in part], instruct=[cast[i]["instruct"] for i in part], language=["English"] * len(part))
        for i, x in zip(part, w): sf.write(f"{out}/{i}_s{s}.wav", x, sr)
        rec["batches"].append({"seed": s, "order": part, "wall_s": round(time.time() - t, 1)})
        print("seed", s, k, round(time.time() - t, 1), flush=True)
        json.dump(rec, open(f"{out}/design.json", "w"), indent=1)
