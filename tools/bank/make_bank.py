#!/usr/bin/env python3
# Picked takes -> dialtone-assets: vag/<line>_<k>.vag (k = rank 0..2), voices.json, lines.json, manifest.json (version 2).
#   python3 make_bank.py TAKES_DIR picks-v2.json ASSETS_DIR
import json, os, sys, subprocess, struct, numpy as np
takes, picks, A = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
sys.path.insert(0, os.path.join(A, "tools")); import spu_adpcm
RATE = 8000
CHAIN = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,"
         "highpass=f=300,highpass=f=300,lowpass=f=3400,lowpass=f=3400,acompressor=threshold=-18dB:ratio=3:attack=5:release=80")
def vag(src, dst, name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-af", CHAIN, "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype="<i2").astype(float); x = x / max(1.0, np.abs(x).max()) * 30000
    body = spu_adpcm.encode(np.concatenate([np.zeros(28), np.round(x)]).astype(int))
    hdr = b"VAGp" + struct.pack(">IIII", 0x20, 0, len(body), RATE) + b"\0" * 12 + name.encode()[:16].ljust(16, b"\0")
    open(dst, "wb").write(hdr + body); return len(x) / RATE, len(body)
def one(w):
    lid, k, t = w; return (lid, k) + vag(f"{takes}/{t}", f"{A}/vag/{lid}_{k}.vag", f"{lid}_{k}")
if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    os.makedirs(f"{A}/vag", exist_ok=True)
    work = [(lid, k, p["take"]) for lid, ps in picks.items() for k, p in enumerate(ps)]
    with ProcessPoolExecutor(int(os.environ.get("J", "6"))) as ex: res = list(ex.map(one, work, chunksize=16))
    json.dump({f"{l}_{k}": [round(d, 2), b] for l, k, d, b in res}, open("vag-sizes.json", "w"))
    print(len(res), "vags,", sum(r[3] for r in res), "bytes ADPCM")
