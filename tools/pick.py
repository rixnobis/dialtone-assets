#!/usr/bin/env python3
# Chooses one take per line from a transcript of every take (JSON: {path: {"text": ..., "dur": ...}}),
# preferring the take whose transcript matches the line word for word, then the shortest of those.
#
#   python3 tools/pick.py analysis.json > picks.json
import json, os, re, sys
from difflib import SequenceMatcher

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lines = json.load(open(os.path.join(root, "lines.json")))
takes = json.load(open(sys.argv[1]))


def words(s):
    return re.sub(r"[^a-z ]", "", s.lower().replace("-", " ")).split()


picks = {}
for line in lines:
    best = None
    for path, info in takes.items():
        name = os.path.basename(path)
        if not re.fullmatch(re.escape(line["id"]) + r"_\d+\.wav", name):
            continue
        score = SequenceMatcher(None, words(line["text"]), words(info["text"])).ratio()
        key = (round(score, 3), -info["dur"])
        if best is None or key > best[0]:
            best = (key, name, info["text"])
    if best is None:
        print(f"no take for {line['id']}", file=sys.stderr)
        continue
    picks[line["id"]] = {"take": best[1], "match": best[0][0], "heard": best[2]}
    if best[0][0] < 1:
        print(f"{line['id']}: best take {best[1]} heard {best[2]!r} ({best[0][0]})", file=sys.stderr)
json.dump(picks, open(sys.stdout.fileno(), "w"), indent=1)
