#!/usr/bin/env python3
import re
import json
import argparse
from typing import Dict

__doc__ = """
Generate a ZMK devicetree overlay that contains:
  • one behavior‑macro per word
  • one combo per chord that calls its macro
Usage:
  python zmk_codegen.py --map mapping.json --keymap totem.keymap \
                        --out combos_and_macros.keymap
"""

# ── helpers ──────────────────────────────────────────────────────────────────
def parse_key_positions(keymap_file: str) -> Dict[str, int]:
    text = open(keymap_file, "r", encoding="utf-8").read()
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', text, flags=re.DOTALL)
    if not blocks:
        raise RuntimeError(f"No `bindings = < … >;` blocks in {keymap_file}")

    pat = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    pos: Dict[str, int] = {}
    next_idx = 0
    for blk in blocks:                        # file order = physical order
        for _, letter in pat.findall(blk):
            if letter not in pos:
                pos[letter] = next_idx
                next_idx += 1
    if not pos:
        raise RuntimeError("No A–Z keys found in any bindings block")
    return pos

# ── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="Generate ZMK combo+macro overlay")
    ap.add_argument("--map",    default="mapping.json")
    ap.add_argument("--keymap", default="totem.keymap")
    ap.add_argument("--out",    default="combos_and_macros.keymap")
    args = ap.parse_args()

    with open(args.map, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    key_pos = parse_key_positions(args.keymap)

    good, skipped = {}, []
    for word, chord in mapping.items():
        s = chord.upper() if isinstance(chord, str) else "".join(chord).upper()
        if all(c in key_pos for c in s):
            good[word] = s          # <-- dict
        else:
            skipped.append(word)    # <-- list

    if skipped:
        print(f"Skipped {len(skipped)} words (letters not on board)")

    # ── write overlay ───────────────────────────────────────────────────────
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("/ {\n")
        # macros
        f.write("    behaviors {\n        #binding-cells = <0>;\n\n")
        for word, chord in good.items():
            lbl = f"macro_{word}"
            f.write(f"        {lbl}: {lbl} {{\n")
            f.write('            compatible = "zmk,behavior-macro";\n')
            f.write("            #binding-cells = <0>;\n")
            f.write("            bindings = <\n")
            for ch in chord:
                f.write(f"                &kp {ch}\n")
            f.write("            >;\n        };\n\n")
        f.write("    };\n\n")

        # combos
        f.write("    combos {\n")
        f.write('        compatible = "zmk,combos";\n')
        f.write("        #binding-cells = <2>;\n\n")
        for word, chord in good.items():
            positions = " ".join(str(key_pos[c]) for c in chord)
            f.write(f"        combo_{word} {{\n")
            f.write(f"            key-positions = <{positions}>;\n")
            f.write(f"            bindings = < &macro_{word} 0 0 >;\n")
            f.write("        };\n\n")
        f.write("    };\n};\n")

    print(f"Wrote overlay to {args.out}  ({len(good)} combos)")

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
