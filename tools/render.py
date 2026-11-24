#!/usr/bin/env python3
# Renders every line in lines.json with Qwen3-TTS (Apache-2.0, needs the qwen-tts package and a CUDA GPU).
#
#   python3 tools/render.py OUTDIR [takes]
#
# Stage 1 designs each caller once with the VoiceDesign model (voices.json: description, seed, a
# reference sentence) and writes OUTDIR/ref/<voice>.wav. VoiceDesign invents a new speaker on every
# call, so it is only used for that one sentence. Stage 2 clones the reference with the Base model
# for every line, `takes` times with different seeds (default 3), into OUTDIR/takes/<line>_<n>.wav.
# Existing files are kept, so a re-run only fills gaps. tools/pick.py chooses one take per line.
import json, os, sys
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
takes = int(sys.argv[2]) if len(sys.argv) > 2 else 3
voices = json.load(open(os.path.join(root, "voices.json")))
lines = json.load(open(os.path.join(root, "lines.json")))
os.makedirs(f"{out}/ref", exist_ok=True)
os.makedirs(f"{out}/takes", exist_ok=True)


def seed(s):
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


need = [v for v in voices if not os.path.exists(f"{out}/ref/{v['id']}.wav")]
if need:
    d = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cuda:0", dtype=torch.bfloat16)
    for v in need:
        seed(v["seed"])
        w, sr = d.generate_voice_design(text=v["ref_text"], instruct=v["instruct"], language="English")
        sf.write(f"{out}/ref/{v['id']}.wav", w[0], sr)
        print("ref", v["id"], round(len(w[0]) / sr, 2), flush=True)
    del d
    torch.cuda.empty_cache()

b = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cuda:0", dtype=torch.bfloat16)
prompts = {}
for v in voices:
    prompts[v["id"]] = b.create_voice_clone_prompt(ref_audio=f"{out}/ref/{v['id']}.wav", ref_text=v["ref_text"])
for i, line in enumerate(lines):
    for t in range(takes):
        p = f"{out}/takes/{line['id']}_{t}.wav"
        if os.path.exists(p):
            continue
        seed(1000 + 37 * i + t)
        w, sr = b.generate_voice_clone(text=line["text"], language="English", voice_clone_prompt=prompts[line["voice"]])
        sf.write(p, w[0], sr)
        print("take", line["id"], t, round(len(w[0]) / sr, 2), flush=True)
