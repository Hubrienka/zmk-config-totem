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

def parse_key_positions(keymap_file: str) -> Dict[str, int]:
    """
    Scan *every* `bindings = < … > ;` block in the .keymap and assign a
    zero‑based position number to each printable letter the first time it
    appears, walking left‑to‑right, top‑to‑bottom – exactly the order ZMK
    expects for key‑positions.
    """
    text = open(keymap_file, "r", encoding="utf-8").read()

    # find every bindings = < … > ;  (non‑greedy so each block is separate)
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', text, flags=re.DOTALL)

    if not blocks:
        raise RuntimeError(f"No `bindings = < … >;` blocks found in {keymap_file}")

    pattern = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')

    key_pos: Dict[str, int] = {}
    next_index = 0

    # walk blocks in file order so physical order is preserved
    for block in blocks:
        for _, letter in pattern.findall(block):
            if letter not in key_pos:
                key_pos[letter] = next_index
                next_index += 1

    if not key_pos:
        raise RuntimeError("No alpha keys (A‑Z) found in any bindings block")

    return key_pos


def main():
    p = argparse.ArgumentParser(description="Generate ZMK combos+macros overlay")
    p.add_argument("--map",    default="mapping.json",
                   help="Word→chord JSON (from chordgen.py)")
    p.add_argument("--keymap", default="totem.keymap",
                   help="Your Totem .keymap devicetree file")
    p.add_argument("--out",    default="combos_and_macros.keymap",
                   help="Output overlay file")
    args = p.parse_args()

    # Load word→chord mapping
    with open(args.map, 'r', encoding='utf-8') as f:
        raw_mapping = json.load(f)

    # Discover each letter’s numeric position on your Totem
    key_positions = parse_key_positions(args.keymap)

    # Filter mapping to entries fully supported by key_positions
    valid_mapping = {}
    skipped = []
    for word, chord in raw_mapping.items():
        chord_str = chord.upper() if isinstance(chord, str) else "".join(chord).upper()
        if all(c in key_positions for c in chord_str):
            valid_mapping[word] = chord_str
        else:
            skipped.append(word)

    if skipped:
        sample = ", ".join(skipped[:10])
        print(f"Skipped {len(skipped)} entries (unsupported keys): {sample}{'...' if len(skipped)>10 else ''}")

    # Write overlay
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write("/ {\n")
        # --- behaviors (macros) ---
        f.write("    behaviors {\n")
        f.write("        #binding-cells = <0>;\n\n")
        for word, chord_str in valid_mapping.items():
            mname = f"macro_{word}"
            f.write(f"        {mname} {{\n")
            f.write('            compatible = "zmk,behavior-macro";\n')
            f.write("            #binding-cells = <0>;\n")
            f.write("            bindings = <\n")
            for c in chord_str:
                f.write(f"                &kp {c}\n")
            f.write("            >;\n")
            f.write("        };\n\n")
        f.write("    };\n\n")

        # --- combos ---
        f.write("    combos {\n")
        f.write('        compatible = "zmk,combos";\n')
        f.write("        #binding-cells = <2>;\n\n")
        for word, chord_str in valid_mapping.items():
            cname = f"combo_{word}"
            positions = " ".join(str(key_positions[c]) for c in chord_str)
            f.write(f"        {cname} {{\n")
            f.write(f"            key-positions = <{positions}>;\n")
            f.write(f"            bindings = < &macro_{word} >;\n")
            f.write("        };\n\n")
        f.write("    };\n")
        f.write("};\n")

    print(f"Wrote ZMK macros & combos overlay to {args.out} ({len(valid_mapping)} entries).")

if __name__ == "__main__":
    main()
