#!/usr/bin/env python3
# Stage C: render takes. jobs.json = [{"id","voice","delivery","text"}], refs.json = {voice: {delivery: {"wav","text"}}}
#   python3 render.py jobs.json refs.json OUTDIR takes [shard k/n]
import json, sys, os, time, torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
jobs = json.load(open(sys.argv[1])); refs = json.load(open(sys.argv[2])); out = sys.argv[3]; T = int(sys.argv[4])
if len(sys.argv) > 5:
    k, n = map(int, sys.argv[5].split("/")); jobs = jobs[k::n]
if os.environ.get("MEMFRAC"): torch.cuda.set_per_process_memory_fraction(float(os.environ["MEMFRAC"]))
os.makedirs(out, exist_ok=True)
b = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cuda:0", dtype=torch.bfloat16)
P = {}
def prompt(v, d):
    r = refs[v].get(d) or refs[v]["neutral"]; key = r["wav"]
    if key not in P: P[key] = b.create_voice_clone_prompt(ref_audio=r["wav"], ref_text=r["text"])[0]
    return P[key]
items = sorted([(j, t) for j in jobs for t in range(T)], key=lambda x: len(x[0]["text"]))  # bucket by length
BS = int(os.environ.get("BS", "32")); n = 0; t0 = time.time()
for k in range(0, len(items), BS):
    part = [(j, t) for j, t in items[k:k + BS] if not os.path.exists(f"{out}/{j['id']}_{t}.wav")]
    if not part: continue
    s = 7000 + k; torch.manual_seed(s); torch.cuda.manual_seed_all(s)
    w, sr = b.generate_voice_clone(text=[j["text"] for j, _ in part], language=["English"] * len(part),
                                   voice_clone_prompt=[prompt(j["voice"], j["delivery"]) for j, _ in part])
    for (j, t), x in zip(part, w): sf.write(f"{out}/{j['id']}_{t}.wav", x, sr)
    n += len(part); print("batch", k, len(part), "done", n, round(time.time() - t0), "s", flush=True)
