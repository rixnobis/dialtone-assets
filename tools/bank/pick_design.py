# Pick one designed reference per voice: transcript match >= 0.9, voiced >= 0.3, then F0 closest to target (log ratio).
import json, math, sys
from textmatch import match
cast = {c["id"]: c for c in json.load(open("cast.json"))}
an = json.load(open(sys.argv[1]))  # analyze.py output, keys are paths
by = {}
for p, r in an.items():
    f = p.split("/")[-1][:-4]; v, s = f.rsplit("_s", 1); by.setdefault(v, []).append((int(s), r))
pick, report = {}, []
for v, cs in sorted(by.items()):
    c = cast[v]; ok = []
    for s, r in cs:
        m = match(r["text"], c["ref_text"])
        if m >= 0.9 and (r.get("voiced") or 0) >= 0.3 and r.get("f0_med"):
            ok.append((abs(math.log(r["f0_med"] / c["f0"])), s, r, m))
    ok.sort(key=lambda x: x[0])
    line = f"{v} target {c['f0']} Hz: " + ", ".join(f"s{s}={r.get('f0_med')}Hz m{match(r['text'], c['ref_text']):.2f}" for s, r in sorted(cs))
    if ok:
        d, s, r, m = ok[0]; pick[v] = dict(seed=s, f0=r["f0_med"], match=round(m, 3), dur=r["dur"], off_pct=round((math.exp(d) - 1) * 100))
        line += f"  -> s{s} ({r['f0_med']} Hz, {pick[v]['off_pct']}% off)"
    else: line += "  -> NONE"
    report.append(line)
json.dump(pick, open("design-picks.json", "w"), indent=1)
print("\n".join(report))
