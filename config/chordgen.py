#!/usr/bin/env python3
"""
Generate a word→chord mapping that:
 • keeps your fixed macros & multi‑letter affixes,
 • assigns one chord per stem (in frequency order),
 • then only assigns chords to full words that *cannot* be built from stem+affix or as stem1+stem2 compounds,
 • and skips any non‑alphabetic “words” (e.g. middle‑class).
"""

import itertools, json, re
from pathlib import Path
from typing import Dict, List, Set

# 1) fixed chords (macros + affixes, all ≥2 letters)
special_entries = [
    ("delete_word", ["[BSPC]", "H"]),

    # suffixes
    ("ing",   ["I","N","G"]),
    ("ed",    ["E","D"]),
    ("er",    ["E","R"]),
    ("ly",    ["L","Y"]),
    ("ment",  ["M","E","N","T"]),
    ("ness",  ["N","E","S","S"]),
    ("ship",  ["S","H","I","P"]),
    ("able",  ["A","B","L","E"]),
    ("ion",   ["I","O","N"]),
    ("ity",   ["I","T","Y"]),
    ("ous",   ["O","U","S"]),
    ("est",   ["E","S","T"]),
    ("ive",   ["I","V","E"]),
    ("less",  ["L","E","S","S"]),

    # prefixes
    ("un",    ["U","N"]),
    ("re",    ["R","E"]),
    ("pre",   ["P","R","E"]),
    ("anti",  ["A","N","T","I"]),
]
special_words = {w for w,_ in special_entries}

# 2) affix application rules
affix_rules = {
    "ing":  {"type":"suffix","drop_e":True,"double_cvc":True},
    "ed":   {"type":"suffix","drop_e":True,"double_cvc":True},
    "er":   {"type":"suffix","drop_e":True,"double_cvc":True},
    "ly":   {"type":"suffix"},
    "ment": {"type":"suffix"},
    "ness": {"type":"suffix","change_y_i":True},
    "ship": {"type":"suffix"},
    "able": {"type":"suffix","drop_e":True},
    "ion":  {"type":"suffix","change_y_i":True},
    "ity":  {"type":"suffix","change_y_i":True},
    "ous":  {"type":"suffix"},
    "est":  {"type":"suffix"},
    "ive":  {"type":"suffix","drop_e":True},
    "less": {"type":"suffix"},
    "un":   {"type":"prefix"},
    "re":   {"type":"prefix"},
    "pre":  {"type":"prefix"},
    "anti": {"type":"prefix"},
}
_vowels = set("aeiou")

# 3) physical constraints
col_map = {
    'B':1,'N':1,'X':1,'F':2,'S':2,'V':2,'L':3,'H':3,'J':3,
    'K':4,'T':4,'D':4,'Q':5,'M':5,'Z':5,'P':6,'Y':6,
    'G':7,'C':7,'W':7,'O':8,'A':8,'U':9,'E':9,'I':10,'R':11
}
col_order = {
    1:["B","N","X"],2:["F","S","V"],3:["L","H","J"],
    4:["K","T","D"],5:["Q","M","Z"],6:["P","Y"],
    7:["G","C","W"],8:["O","A"],9:["U","E"],10:["I"],11:["R"]
}
_left  = set("BNXFSVLHJKTDQMZ")
_right = set("PYGCWOAUEI")

def conflict(ch: str) -> bool:
    """True if any two keys in the same column are >1 position apart, or if a char isn't on the map."""
    groups: Dict[int, List[str]] = {}
    for c in ch:
        if c not in col_map:
            return True
        groups.setdefault(col_map[c], []).append(c)
    for col, ks in groups.items():
        if len(ks) > 1:
            indices = [col_order[col].index(k) for k in ks]
            if max(indices) - min(indices) > 1:
                return True
    return False

def same_hand(ch: str) -> bool:
    ks = [c for c in ch if c in _left or c in _right]
    return not ks or all(k in _left for k in ks) or all(k in _right for k in ks)

def normalize(ch: str) -> str:
    return "".join(sorted(ch))

# 4) generate all valid candidate chords for a word
def gen_candidates(word: str) -> List[str]:
    uniq = []
    for c in word.upper():
        if c in col_map and c not in uniq:
            uniq.append(c)
    L = len(uniq)
    if L < 2:
        return []
    lengths = [L] if L <= 4 else [3] if L <= 6 else [3,4]
    out: List[str] = []
    for n in lengths:
        for perm in itertools.permutations(uniq, n):
            s = "".join(perm)
            if conflict(s):
                continue
            if same_hand(s) and sum(1 for x in s if x!="R") > 4:
                continue
            out.append(s)
    return out

# 5) detect clean affix splits
def split_affix(word: str) -> List[str] or None:
    lw = word.lower()
    # suffix first
    for aff, rule in affix_rules.items():
        if rule["type"] == "suffix" and lw.endswith(aff) and len(lw) > len(aff) + 2:
            return [lw[:-len(aff)], aff]
    # then prefix
    for aff, rule in affix_rules.items():
        if rule["type"] == "prefix" and lw.startswith(aff) and len(lw) > len(aff) + 2:
            return [lw[len(aff):], aff]
    return None

def is_good_stem(stem: str) -> bool:
    return len(stem) >= 3 and stem.isalpha()

def apply_affix(stem: str, aff: str) -> str:
    rule = affix_rules[aff]
    if rule["type"] == "prefix":
        return aff + stem
    s = stem
    if rule.get("drop_e") and s.endswith("e") and not s.endswith("ee"):
        s = s[:-1]
    if rule.get("change_y_i") and s.endswith("y") and len(s)>1 and s[-2] not in _vowels:
        s = s[:-1] + "i"
    if rule.get("double_cvc") and re.match(r".*[^aeiou][aeiou][^aeiou]$", s):
        s += s[-1]
    return s + aff

def is_compound(word: str, mapping: Dict[str,str]) -> bool:
    lw = word.lower()
    for i in range(3, len(lw)-2):
        if lw[:i] in mapping and lw[i:] in mapping:
            return True
    return False

# 6) build routine
def build_mapping(words_file: str) -> Dict[str,str]:
    raw = Path(words_file).read_text().splitlines()
    words = [w.strip() for w in raw if w.strip().isalpha()]

    mapping: Dict[str,str] = {}
    taken: Set[str] = set()

    # ❶ inject fixed macros & affixes
    for w, ch in special_entries:
        s = "".join(ch)
        mapping[w] = s
        taken.add(normalize(s))

    # ❷ collect stems
    stems: Set[str] = set()
    for w in words:
        parts = split_affix(w)
        stem = parts[0] if parts else w.lower()
        if is_good_stem(stem):
            stems.add(stem)

    # ❸ first pass: one chord per stem
    for w in words:
        lw = w.lower()
        if lw in mapping or lw not in stems:
            continue
        for cand in gen_candidates(lw):
            if normalize(cand) not in taken:
                mapping[lw] = cand
                taken.add(normalize(cand))
                break

    # ❹ second pass: only full words that aren’t stem+affix or stem1+stem2
    for w in words:
        lw = w.lower()
        if lw in mapping or lw in special_words:
            continue

        sp = split_affix(lw)
        if sp and sp[0] in mapping and sp[1] in mapping:
            if apply_affix(sp[0], sp[1]) == lw:
                continue

        if is_compound(lw, mapping):
            continue

        for cand in gen_candidates(lw):
            if normalize(cand) not in taken:
                mapping[lw] = cand
                taken.add(normalize(cand))
                break

    return mapping

if __name__=="__main__":
    import argparse
    p = argparse.ArgumentParser(description="Stem+affix+compound‑aware chordgen")
    p.add_argument("--words", default="5000-words.txt")
    p.add_argument("--out",   default="mapping.json")
    args = p.parse_args()

    m = build_mapping(args.words)
    # preserve insertion (frequency) order in JSON
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

    print(f"Saved mapping with {len(m):,} entries to {args.out}")
