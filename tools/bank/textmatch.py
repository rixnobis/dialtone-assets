import re, difflib
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
def n2w(n):
    n = int(n)
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + n2w(n % 100))
    return str(n)
# interjections whisper spells freely: fold each family to one token
FOLD = {}
for fam, ws in {"mm": "mm mmm mmmm mmh hmm hm hmmm mhm uh-huh mm-hmm mmhmm um umm uh er erm eh ehh huh", "ay": "ay aye ai",
                "yello": "yello yellow", "shh": "shh shhh shhhh sh", "ok": "ok okay", "oh": "oh ooh oo ohh", "ah": "ah ahh aah"}.items():
    for w in ws.split(): FOLD[w] = fam
SUB = [(r"\balright\b", "all right"), (r"\bknow\b", "no"), (r"\bgonna\b", "going to"), (r"\bgotta\b", "got to"), (r"\bya\b", "you"), (r"\by'all\b", "you"), (r"\bkay\b", "okay"), (r"\bgoodnight\b", "good night"), (r"\bgoodbye\b", "good bye")]
def norm(s):
    s = s.lower()
    for a_, b_ in SUB: s = re.sub(a_, b_, s)
    s = re.sub(r"\d+", lambda m: " " + n2w(m.group()) + " ", s)
    w = re.findall(r"[a-z']+(?:-[a-z']+)*", s)
    out = []
    for x in w:
        x = x.replace("'", "")
        if x in FOLD: out.append(FOLD[x]); continue
        out.extend(x.split("-"))
    # collapse repeats of an interjection ("mm mm") to one
    res = []
    for x in out:
        if res and x == res[-1] and x in FOLD.values(): continue
        res.append(x)
    return res
def match(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()
