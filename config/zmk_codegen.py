#!/usr/bin/env python3
import re
import json
import argparse
from typing import Dict

__doc__ = """
Generate a ZMK devicetree overlay with both macros and combos from mapping.json.
Usage:
  python zmk_codegen.py --map mapping.json --keymap totem.keymap --out combos_and_macros.keymap
"""

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def parse_key_positions(keymap_file: str) -> Dict[str, int]:
    """
    Scan every `bindings = < … > ;` block and assign the first occurrence of
    each printable letter to an incrementing position index – the order ZMK
    expects for key‑positions.
    """
    text = open(keymap_file, "r", encoding="utf-8").read()
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', text, flags=re.DOTALL)
    if not blocks:
        raise RuntimeError(f"No `bindings = < … >;` blocks found in {keymap_file}")

    pattern = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    key_pos: Dict[str, int] = {}
    next_idx = 0

    for block in blocks:                       # file order preserves row order
        for _, letter in pattern.findall(block):
            if letter not in key_pos:
                key_pos[letter] = next_idx
                next_idx += 1

    if not key_pos:
        raise RuntimeError("No A‑Z keys found in any bindings block")

    return key_pos

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="Generate ZMK combo+macro overlay")
    ap.add_argument("--map",    default="mapping.json",  help="word→chord JSON")
    ap.add_argument("--keymap", default="totem.keymap",  help="Totem .keymap DT")
    ap.add_argument("--out",    default="combos_and_macros.keymap",
                    help="output overlay file")
    args = ap.parse_args()

    # load mapping
    with open(args.map, "r", encoding="utf-8") as f:
        raw_mapping = json.load(f)

    # discover physical positions
    key_positions = parse_key_positions(args.keymap)

    # keep only chords whose every letter exists on this board
    good_map, skipped = {}, []
    for word, chord in raw_mapping.items():
        c = chord.upper() if isinstance(chord, str) else "".join(chord).upper()
        if all(ch in key_positions for ch in c):
            good_map[word] = c
        else:
            skipped.append(word)

    if skipped:
        print(f"Skipped {len(skipped)} words with unsupported keys.")

    # ── write overlay ─────────────────────────────────────────────────────────
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("/ {\n")
        # macros
        f.write("    behaviors {\n        #binding-cells = <0>;\n\n")
        for word, chord in good_map.items():
            mname = f"macro_{word}"
            f.write(f"        {mname}: {mname} {{\n")      # ← label added here
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
        for word, chord in good_map.items():
            positions = " ".join(str(key_positions[ch]) for ch in chord)
            f.write(f"        combo_{word} {{\n")
            f.write(f"            key-positions = <{positions}>;\n")
            f.write(f"            bindings = < &macro_{word} >;\n")
            f.write("        };\n\n")
        f.write("    };\n};\n")

    print(f"Wrote overlay to {args.out}  ({len(good_map)} combos)")

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
