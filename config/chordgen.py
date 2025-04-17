# chordgen.py
"""
Generate a chord mapping (word → chord) from a word list.
"""

import re
import itertools
import json
from typing import List, Dict, Set

# === SPECIAL MAPPINGS ===
special_entries = [
    ("delete_word", ["[BSPC]", "H"]),
    ("ing", ["I", "N", "G"]),
    ("ed",  ["E", "D"]),
    ("ly",  ["L", "Y"]),
    ("ment", ["M", "E", "N", "T"]),
    ("ship", ["S", "H", "I", "P"]),
    ("ness", ["N", "E", "S", "S"]),
    ("un", ["U", "N"]),
    ("re", ["R", "E"]),
    ("able", list("ABLE")),
    ("al", list("AL")),
    ("en", list("EN")),
    ("er", list("ER")),
    ("est", list("EST")),
    ("ful", list("FUL")),
    ("hood", list("HOOD")),
    ("ion", list("ION")),
    ("ity", list("ITY")),
    ("ive", list("IVE")),
    ("less", list("LESS")),
    ("ous", list("OUS")),
    ("es", list("ES")),
    ("y", list("Y")),
    ("ism", list("ISM")),
    ("ist", list("IST")),
    ("ty", list("TY")),
    ("ry", list("RY")),
    ("house", list("HOUSE")),
    ("maker", list("MAKER")),
    ("dom", list("DOM")),
    ("ward", list("WARD")),
    ("d", list("D"))
]
special_keys = {w for w,_ in special_entries}

# === LAYOUT ===
col_map = { 'B':1,'N':1,'X':1, 'F':2,'S':2,'V':2, 'L':3,'H':3,'J':3,
            'K':4,'T':4,'D':4, 'Q':5,'M':5,'Z':5, 'P':6,'Y':6,
            'G':7,'C':7,'W':7, 'O':8,'A':8, 'U':9,'E':9, 'I':10, 'R':11 }
col_order = {
    1:["B","N","X"],2:["F","S","V"],3:["L","H","J"],
    4:["K","T","D"],5:["Q","M","Z"],6:["P","Y"],
    7:["G","C","W"],8:["O","A"],9:["U","E"],10:["I"],11:["R"]
}
left_set = set("BNXFSVLHJKTDQMZ")
right_set = set("PYGCWOAUEI")


def has_conflict(chord: str) -> bool:
    groups = {}
    for c in chord.upper():
        if c not in col_map:
            continue
        col = col_map[c]
        groups.setdefault(col, []).append(c)
    for col, letters in groups.items():
        if len(letters) > 1:
            idx = [col_order[col].index(l) for l in letters]
            if max(idx) - min(idx) > 1:
                return True
    return False


def is_same_hand(chord: str) -> bool:
    letters = [c for c in chord.upper() if c in left_set or c in right_set]
    return not letters or all(c in left_set for c in letters) or all(c in right_set for c in letters)


def normalize(chord: str) -> str:
    return "".join(sorted(chord.upper()))


def get_short_candidates(word: str) -> List[str]:
    unique = []
    for c in word.upper():
        if c in col_map and c not in unique:
            unique.append(c)
    if len(unique) < 2:
        return []
    perms = set(itertools.permutations(unique))
    cands = []
    for p in perms:
        s = "".join(p)
        if not has_conflict(s) and (not is_same_hand(s) or sum(1 for x in s if x != 'R') <= 4):
            cands.append(s)
    return cands


def is_compound_word(word: str, mapping: Dict[str, str]) -> bool:
    lw = word.lower()
    if len(lw) < 7:
        return False
    for pre in ["anti","auto","post","pre","re"]:
        if lw.startswith(pre) and lw[len(pre):] in mapping:
            return True
    for suf in ["ing","ed","ly","ion","ment"]:
        if lw.endswith(suf) and lw[:-len(suf)] in mapping:
            return True
    return False


def generate_chord(word: str, assigned: Set[str], reserved: Set[str]) -> str:
    uniq = []
    for c in word.upper():
        if c in col_map and c not in uniq:
            uniq.append(c)
    for L in (3, 4):
        if L > len(uniq):
            continue
        for perm in itertools.permutations(uniq, L):
            s = "".join(perm)
            if normalize(s) in assigned | reserved:
                continue
            if has_conflict(s):
                continue
            if is_same_hand(s) and sum(1 for x in s if x != 'R') > 4:
                continue
            return s
    return None


def build_mapping(words_file: str) -> Dict[str, str]:
    with open(words_file) as f:
        words = [w.strip() for w in f if w.strip()]
    reserved = set()
    for w in words:
        if len(w) == 3:
            cands = get_short_candidates(w)
            if len(cands) == 1:
                reserved.add(normalize(cands[0]))
    mapping = {}
    assigned = set()
    for w, ch in special_entries:
        s = "".join(ch)
        mapping[w] = s
        assigned.add(normalize(s))
    for w in words:
        if len(w) <= 1 or w in mapping or is_compound_word(w, mapping):
            continue
        if len(w) == 2:
            f = "".join(c for c in w.upper() if c in col_map)
            if len(f) >= 2:
                mapping[w] = f
                assigned.add(normalize(f))
        else:
            c = generate_chord(w, assigned, reserved)
            if c:
                mapping[w] = c
                assigned.add(normalize(c))
    return mapping

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--words", default="5000-words.txt")
    p.add_argument("--out", default="mapping.json")
    args = p.parse_args()
    m = build_mapping(args.words)
    with open(args.out, "w") as f:
        json.dump(m, f, indent=2)
    print(f"Saved mapping ({len(m)}) to {args.out}")