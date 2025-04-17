# chordgen.py
"""
Generate a word‑→‑chord mapping for ZMK/QMK, but keep the entry‑count small by
*not* emitting a chord for any word that can be typed with an existing stem
plus one of the stock affix chords.

The affix chords live in `special_entries` – add/remove there only.
"""

import itertools, json, re
from pathlib import Path
from typing import Dict, List, Set

# ────────────────────────── 1. fixed chords (prefixes/suffixes etc.) ──────────
special_entries = [
    # editing helpers
    ("delete_word", ["[BSPC]", "H"]),

    # suffixes (★ add / change here only)
    ("ing",  list("ING")),
    ("ed",   list("ED")),
    ("ly",   list("LY")),
    ("ment", list("MENT")),
    ("ness", list("NESS")),
    ("ship", list("SHIP")),
    ("able", list("ABLE")),
    ("ion",  list("ION")),
    ("ity",  list("ITY")),
    ("ous",  list("OUS")),
    ("est",  list("EST")),
    ("ive",  list("IVE")),
    ("less", list("LESS")),
    ("y",    list("Y")),
    ("s",    list("S")),

    # prefixes
    ("un",   list("UN")),
    ("re",   list("RE")),
    ("pre",  list("PRE")),
    ("anti", list("ANTI")),
]
special_words = {w for w, _ in special_entries}

prefixes   = [w for w, _ in special_entries if len(w) >= 2 and not w[-1].isalpha()]
suffixes   = [w for w, _ in special_entries if w not in prefixes]

# ────────────────────────── 2. physical layout constraints ────────────────────
col_map = {  # column numbers on Totem (or Voyager) – adjust if yours differs
    'B': 1, 'N': 1, 'X': 1,
    'F': 2, 'S': 2, 'V': 2,
    'L': 3, 'H': 3, 'J': 3,
    'K': 4, 'T': 4, 'D': 4,
    'Q': 5, 'M': 5, 'Z': 5,
    'P': 6, 'Y': 6,
    'G': 7, 'C': 7, 'W': 7,
    'O': 8, 'A': 8,
    'U': 9, 'E': 9,
    'I': 10,
    'R': 11,          # thumb
}
col_order = {
    1:["B","N","X"],2:["F","S","V"],3:["L","H","J"],
    4:["K","T","D"],5:["Q","M","Z"],6:["P","Y"],
    7:["G","C","W"],8:["O","A"],9:["U","E"],10:["I"],11:["R"]
}
left  = set("BNXFSVLHJKTDQMZ")
right = set("PYGCWOAUEI")

def same_hand(ch: str) -> bool:
    keys = [c for c in ch if c in left or c in right]
    return not keys or all(k in left for k in keys) or all(k in right for k in keys)

def conflict(ch: str) -> bool:
    groups = {}
    for c in ch:
        if c not in col_map:
            return True
        groups.setdefault(col_map[c], []).append(c)
    for col, ks in groups.items():
        if len(ks) > 1:
            idx = [col_order[col].index(k) for k in ks]
            if max(idx) - min(idx) > 1:
                return True
    return False

def normalize(ch: str) -> str:
    return "".join(sorted(ch))

# ────────────────────────── 3. chord generation helpers ───────────────────────
def gen_candidates(word: str) -> List[str]:
    uniq = []
    for c in word.upper():
        if c in col_map and c not in uniq:
            uniq.append(c)
    length = len(uniq)
    if length < 2:
        return []
    target_lengths = (
        [length] if length <= 4 else
        [3]       if length <= 6 else
        [3, 4]
    )
    cand: List[str] = []
    for L in target_lengths:
        for perm in itertools.permutations(uniq, L):
            s = "".join(perm)
            if conflict(s):
                continue
            if same_hand(s) and sum(1 for k in s if k != 'R') > 4:
                continue
            cand.append(s)
    return cand

# ────────────────────────── 4. word‑analysis helpers ──────────────────────────
def split_affix(word: str) -> List[str] | None:
    """Return [stem, affix] or [prefix, stem] if it *cleanly* splits, else None."""
    lw = word.lower()
    for suf in suffixes:
        if lw.endswith(suf) and len(lw) > len(suf) + 2:
            return [lw[:-len(suf)], suf]
    for pre in prefixes:
        if lw.startswith(pre) and len(lw) > len(pre) + 2:
            return [pre, lw[len(pre):]]
    return None

# false‑positive guard: stems shorter than 3 or containing digits, etc.
def is_good_stem(stem: str) -> bool:
    return len(stem) >= 3 and stem.isalpha()

# ────────────────────────── 5. main build routine ─────────────────────────────
def build_mapping(word_file: str) -> Dict[str, str]:
    words = [w.strip() for w in Path(word_file).read_text().splitlines() if w.strip()]
    mapping: Dict[str, str] = {}

    # ❶ insert fixed chords first
    taken: Set[str] = set()
    for w, chord in special_entries:
        chord_str = "".join(chord)
        mapping[w] = chord_str
        taken.add(normalize(chord_str))

    # ❷ first pass – create chords for every *stem* (unique base word)
    stems: Set[str] = set()
    for w in words:
        parts = split_affix(w)            # split if affix present
        stem = parts[0] if parts else w
        if not is_good_stem(stem):
            continue
        stems.add(stem.lower())

    # preserve frequency order
    for w in words:
        lw = w.lower()
        if lw not in stems or lw in mapping:
            continue
        for cand in gen_candidates(lw):
            if normalize(cand) not in taken:
                mapping[lw] = cand
                taken.add(normalize(cand))
                break

    # ❸ second pass – only keep whole words that *cannot* be typed as stem+affix
    for w in words:
        lw = w.lower()
        if lw in mapping or lw in special_words:
            continue
        split = split_affix(lw)
        if split and all(p in mapping for p in split):
            # stem already has a chord, affix is special -> skip whole word
            continue
        # else allocate a chord for the full word
        for cand in gen_candidates(lw):
            if normalize(cand) not in taken:
                mapping[lw] = cand
                taken.add(normalize(cand))
                break

    return mapping

# ────────────────────────── 6. CLI ────────────────────────────────────────────
if __name__ == "__main__":
    import argparse, textwrap
    ap = argparse.ArgumentParser(
        description="Generate a compact mapping.json (stem+affix aware).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        The resulting mapping:
          •  fixed affix chords from `special_entries`
          •  one chord for each uncovered *stem*
          •  a chord for a full word only when stem+affix does not exist
        """)
    )
    ap.add_argument("--words", default="5000-words.txt")
    ap.add_argument("--out",   default="mapping.json")
    args = ap.parse_args()

    m = build_mapping(args.words)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, sort_keys=True)

    print(f"Saved mapping with {len(m):,} entries to {args.out}")
