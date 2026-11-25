# Pick one delivery reference per (voice, group) from moods/analysis.json.
# Gates (vs that voice's own neutral-sentence clones, median over seeds): transcript match >= 0.9,
# centroid within +-20% (timbre held), F0 within 0.7..1.45 x neutral. Score per group:
#   up   = spread(p90/p10) gain + F0 gain     hot = rms gain (dB/6) + spread gain
#   low  = -F0 change - pace change (slower)  hush = -rms (dB/6) - F0 change*0.5
import json, sys, statistics as st, collections
from textmatch import match
S = json.load(open(sys.argv[2]))["sentences"]
an = json.load(open(sys.argv[1]))
rows = collections.defaultdict(list)
for p, r in an.items():
    f = p.split("/")[-1][:-4]; vg, s = f.rsplit("_s", 1); v, g = vg.rsplit("_", 1)
    if not r.get("f0_med"): continue
    r = dict(r, seed=int(s), m=match(r["text"], S[g]), spread=(r["f0_p90"] / r["f0_p10"]) if r.get("f0_p10") else 1,
             pace=len(S[g].split()) / max(r["dur"], 0.1))
    rows[(v, g)].append(r)
pick, rep = {}, []
for (v, g), cs in sorted(rows.items()):
    if g == "neutral": continue
    nz = [r for r in rows[(v, "neutral")] if r["m"] >= 0.9]
    if not nz: rep.append(f"{v} {g}: no neutral baseline"); continue
    N = {k: st.median(r[k] for r in nz) for k in ("f0_med", "centroid", "rms_db", "spread", "pace")}
    best = None
    for r in cs:
        if r["m"] < 0.9 or not (0.8 <= r["centroid"] / N["centroid"] <= 1.2) or not (0.7 <= r["f0_med"] / N["f0_med"] <= 1.45): continue
        df = r["f0_med"] / N["f0_med"] - 1; ds = r["spread"] - N["spread"]; dr = (r["rms_db"] - N["rms_db"]) / 6; dp = r["pace"] / N["pace"] - 1
        sc = {"up": ds + df, "hot": dr + ds, "low": -df - dp, "hush": -dr - 0.5 * df}[g]
        if best is None or sc > best[0]: best = (sc, r, dict(f0=round(df * 100), spread=round(ds, 2), rms=round(dr * 6, 1), pace=round(dp * 100)))
    if best and best[0] > 0:
        pick[f"{v}_{g}"] = dict(seed=best[1]["seed"], score=round(best[0], 3), delta=best[2])
        rep.append(f"{v} {g}: s{best[1]['seed']} score {best[0]:.2f} {best[2]}")
    else: rep.append(f"{v} {g}: NO candidate beats neutral -> use neutral ref")
json.dump(pick, open("mood-picks.json", "w"), indent=1); print("\n".join(rep))
