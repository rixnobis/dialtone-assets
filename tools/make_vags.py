#!/usr/bin/env python3
# Turns the picked takes into VAGs for the game: silence trimmed off both ends, a telephone band
# (300-3400 Hz, these people are on the phone), peak-normalised, resampled to 8000 Hz mono and encoded
# to SPU ADPCM. Needs ffmpeg.
#
#   python3 tools/make_vags.py TAKES_DIR picks.json
#
# Writes vag/<line id>.vag and prints each line's length and size.
import json, os, struct, subprocess, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spu_adpcm  # noqa: E402

RATE = 8000
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
takes_dir, picks = sys.argv[1], json.load(open(sys.argv[2]))
os.makedirs(os.path.join(root, "vag"), exist_ok=True)
CHAIN = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,"
         "highpass=f=300,highpass=f=300,lowpass=f=3400,lowpass=f=3400,acompressor=threshold=-18dB:ratio=3:attack=5:release=80")
total = 0
for line_id, pick in picks.items():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(takes_dir, pick["take"]), "-af", CHAIN,
                          "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype="<i2").astype(float)
    x = x / max(1.0, np.abs(x).max()) * 30000
    # a leading silent block, as VAG files carry, then the line; the last block ends and mutes the voice
    body = spu_adpcm.encode(np.concatenate([np.zeros(28), np.round(x)]).astype(int))
    name = line_id.encode()[:16].ljust(16, b"\0")
    header = b"VAGp" + struct.pack(">IIII", 0x20, 0, len(body), RATE) + b"\0" * 12 + name
    with open(os.path.join(root, "vag", line_id + ".vag"), "wb") as f:
        f.write(header + body)
    total += len(body)
    print(f"{line_id:14s} {len(x) / RATE:5.2f} s {len(body):6d} bytes")
print(f"{len(picks)} lines, {total} bytes of ADPCM")
