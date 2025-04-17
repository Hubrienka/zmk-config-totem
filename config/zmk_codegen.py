#!/usr/bin/env python3
"""
zmk_codegen.py
==============

Turn the JSON produced by **chordgen.py** into a ZMK Devicetree overlay that
contains *only* the number of combos you can afford to keep in RAM.

Usage examples
--------------

# keep the 1 000 most‑frequent entries
python zmk_codegen.py --map mapping.json --keymap totem.keymap \
                      --limit 1000 --out combos.keymap

# generate *every* entry (old behaviour)
python zmk_codegen.py --map mapping.json --keymap totem.keymap \
                      --limit 0    --out combos.keymap
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing   import Dict, List, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# helper ─ parse the physical key positions from your .keymap ─────────────────
# ──────────────────────────────────────────────────────────────────────────────
_BIND_RE = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')

def parse_key_positions(keymap_file: Path) -> Dict[str, int]:
    text   = keymap_file.read_text(encoding="utf‑8")
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', text, re.DOTALL)
    if not blocks:
        raise RuntimeError(f"No `bindings = < … >;` blocks found in {keymap_file}")

    pos: Dict[str, int] = {}
    next_index = 0
    for block in blocks:                     # walk in file‑order → physical order
        for _, letter in _BIND_RE.findall(block):
            if letter not in pos:
                pos[letter] = next_index
                next_index += 1
    return pos


# ──────────────────────────────────────────────────────────────────────────────
# main ─ build the overlay ────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────
def build_overlay(mapping: Dict[str, str],
                  keypos: Dict[str, int],
                  keep:   int) -> Tuple[List[str], List[str]]:
    """Return (overlay_lines, skipped_words).  *keep*==0 → keep everything."""
    overlay: List[str] = []
    skipped: List[str] = []

    overlay.extend([
        "/ {",
        "    combos {",
        '        compatible = "zmk,combos";',
        "        #binding-cells = <2>;\n",
    ])

    count = 0
    for word, chord in mapping.items():
        if keep and count >= keep:
            break

        # chord may be either "APB" or ["A","P","B"]; normalise to str
        keys = chord.upper() if isinstance(chord, str) else "".join(chord).upper()

        if not all(k in keypos for k in keys):
            skipped.append(word)
            continue

        positions = " ".join(str(keypos[k]) for k in keys)
        bindings  = " ".join(f"&kp {k}" for k in keys)

        overlay.extend([
            f"        combo_{word} {{",
            f"            key-positions = <{positions}>;",
            f"            bindings      = < {bindings} >;",
            "        };",
            ""
        ])
        count += 1

    overlay.extend(["    };", "};", ""])
    return overlay, skipped


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate a ZMK combo overlay from a mapping.json file")
    ap.add_argument("--map",    default="mapping.json",
                    help="JSON produced by chordgen.py (default: %(default)s)")
    ap.add_argument("--keymap", default="totem.keymap",
                    help=".keymap file that matches your physical board")
    ap.add_argument("--limit",  type=int, default=1000,
                    help="How many entries to keep (0 = all)  [default: %(default)s]")
    ap.add_argument("--out",    default="combos.keymap",
                    help="Output overlay filename  [default: %(default)s]")
    args = ap.parse_args()

    mapping  = json.load(open(args.map, encoding="utf‑8"))
    keypos   = parse_key_positions(Path(args.keymap))
    overlay, skipped = build_overlay(mapping, keypos, args.limit)

    Path(args.out).write_text("\n".join(overlay), encoding="utf‑8")
    print(f"Wrote {len(overlay)-6} combos → {args.out}")  # -6: header/footer lines
    if skipped:
        print(f"Skipped {len(skipped)} words (keys not on board)")

if __name__ == "__main__":
    main()
