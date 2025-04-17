#!/usr/bin/env python3
"""
Convert mapping.json (word → chord) into a pure‑combo ZMK overlay.

Usage:
    python zmk_codegen.py --map mapping.json --keymap totem.keymap --out combos.keymap
"""
import json, re, argparse
from typing import Dict


def parse_key_positions(path: str) -> Dict[str, int]:
    """
    Scan every `bindings = < … > ;` block in your *.keymap file
    and record the first (left→right, top→bottom) numeric position
    of each printable letter A‑Z.
    """
    txt = open(path, encoding="utf-8").read()
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', txt, re.DOTALL)
    if not blocks:
        raise RuntimeError("No `bindings = <…>` block found in " + path)

    pat = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    pos, nxt = {}, 0
    for blk in blocks:                # preserve physical order
        for _, letter in pat.findall(blk):
            if letter not in pos:
                pos[letter] = nxt
                nxt += 1
    return pos


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate combos overlay from mapping.json")
    ap.add_argument("--map",    default="mapping.json")
    ap.add_argument("--keymap", default="totem.keymap")
    ap.add_argument("--out",    default="combos.keymap")
    args = ap.parse_args()

    mapping  = json.load(open(args.map, encoding="utf-8"))
    key_pos  = parse_key_positions(args.keymap)

    # keep only chords that use letters present on the board
    valid: Dict[str, str] = {}
    for word, chord in mapping.items():
        chord_str = chord if isinstance(chord, str) else "".join(chord)
        chord_up  = chord_str.upper()
        if all(c in key_pos for c in chord_up):
            valid[word] = chord_up

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(
            "/ {\n"
            "    combos {\n"
            '        compatible = "zmk,combos";\n'
            "        #binding-cells = <2>;\n\n"
        )
        for word, chord_up in valid.items():
            positions = " ".join(str(key_pos[c]) for c in chord_up)
            bindings  = " ".join(f"&kp {c}" for c in chord_up)
            f.write(
                f"        combo_{word} {{\n"
                f"            key-positions = <{positions}>;\n"
                f"            bindings      = < {bindings} >;\n"
                f"        }};\n\n"
            )
        f.write("    };\n};\n")

    print(f"Wrote {len(valid)} combos → {args.out}")


if __name__ == "__main__":
    main()
