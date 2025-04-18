#!/usr/bin/env python3
import json, re, argparse
from typing import Dict, List

def parse_key_positions(path: str) -> Dict[str,int]:
    """Scan every bindings = <…>; block to assign 0‑based positions to each letter key."""
    txt = open(path, encoding="utf-8").read()
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', txt, re.DOTALL)
    pat   = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    pos = {}
    idx = 0
    for blk in blocks:
        for _, letter in pat.findall(blk):
            if letter not in pos:
                pos[letter] = idx
                idx += 1
    return pos

def main():
    p = argparse.ArgumentParser(
        description="Generate a minimal ZMK devicetree overlay with up to TOP combos by frequency."
    )
    p.add_argument("--map",
                   default="mapping.json",
                   help="Word→chord JSON (from chordgen.py)")
    p.add_argument("--words",
                   default="5000-words.txt",
                   help="Frequency‑ordered word list")
    p.add_argument("--keymap",
                   default="totem.keymap",
                   help="Your Totem .keymap devicetree file")
    p.add_argument("--top",
                   type=int,
                   default=None,
                   help="Keep only the first N entries from the frequency list")
    p.add_argument("--out",
                   default="combos.keymap",
                   help="Output overlay file")
    args = p.parse_args()

    # load the chord mapping
    mapping = json.load(open(args.map, encoding="utf-8"))
    # load your frequency‑ordered list
    freq_list = [w.strip() for w in open(args.words, encoding="utf-8") if w.strip()]
    # discover key positions
    key_pos = parse_key_positions(args.keymap)

    kept = {}
    for w in freq_list:
        if w not in mapping:
            continue
        chord = mapping[w].upper() if isinstance(mapping[w], str) else "".join(mapping[w]).upper()
        # only include combos for which all keys exist on your board
        if all(c in key_pos for c in chord):
            kept[w] = chord
            if args.top and len(kept) >= args.top:
                break

    # write out the devicetree overlay
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("/ {\n    combos {\n")
        f.write('        compatible = "zmk,combos";\n')
        f.write("        #binding-cells = <2>;\n\n")
        for w, chord in kept.items():
            # key‑positions = <i j k>;
            positions = " ".join(str(key_pos[c]) for c in chord)
            # bindings = < &kp A &kp B &kp C >;
            binds = " ".join(f"&kp {c}" for c in chord)
            f.write(f"        combo_{w} {{\n")
            f.write(f"            key-positions = <{positions}>;\n")
            f.write(f"            bindings      = < {binds} >;\n")
            f.write("        };\n\n")
        f.write("    };\n};\n")

    print(f"Wrote {len(kept)} combos → {args.out}")

if __name__ == "__main__":
    main()
