# Choose up to 3 takes per line from asr.json: transcript match >= 0.85, no long lead-in, plausible length.
# Rank: match first, then closeness to the line's median take duration (outlier takes are usually rushed or stretched).
import json, sys, statistics as st, collections
from textmatch import match
lines = {l["id"]: l for l in json.load(open(sys.argv[1]))}
asr = json.load(open(sys.argv[2])); K = int(sys.argv[3]) if len(sys.argv) > 3 else 3
by = collections.defaultdict(list)
for f, r in asr.items():
    lid, t = f[:-4].rsplit("_", 1); by[lid].append((int(t), f, r))
import os
MIN = float(os.environ.get("MIN", "0.85"))
picks, short, fails = {}, 0, []
for lid, l in lines.items():
    cs = by.get(lid, [])
    if not cs: fails.append((lid, "no takes")); continue
    md = st.median(r["dur"] for _, _, r in cs)
    ok = []
    for t, f, r in cs:
        m = match(r["text"], l["text"])
        if m >= MIN and 0.4 <= r["dur"] <= 7.5 and r["dur"] <= 2.2 * md:  # lead-in silence is trimmed by make_bank
            ok.append((-m, abs(r["dur"] - md), t, f, round(m, 3), r))
    ok.sort()
    if not ok: fails.append((lid, [ (round(match(r['text'], l['text']),2), r['text']) for _, _, r in cs])); continue
    if len(ok) < K: short += 1
    picks[lid] = [dict(take=f, match=m, dur=r["dur"], heard=r["text"]) for _, _, t, f, m, r in ok[:K]]
json.dump(picks, open(sys.argv[4] if len(sys.argv) > 4 else "picks-v2.json", "w"), indent=1)
print(len(picks), "lines picked,", short, "with fewer than", K, "good takes,", len(fails), "with none")
for x in fails[:40]: print("FAIL", x)
