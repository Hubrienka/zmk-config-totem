#!/usr/bin/env python3
import json, re, argparse
from typing import Dict


def parse_key_positions(path: str) -> Dict[str, int]:
    txt = open(path, encoding="utf-8").read()
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', txt, re.DOTALL)
    pat    = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    pos, nxt = {}, 0
    for blk in blocks:
        for _, letter in pat.findall(blk):
            if letter not in pos:
                pos[letter] = nxt; nxt += 1
    return pos


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate combos overlay")
    ap.add_argument("--map",    default="mapping.json")
    ap.add_argument("--keymap", default="totem.keymap")
    ap.add_argument("--out",    default="combos.keymap")
    ap.add_argument("--top",    type=int, default=None,
                    help="keep only the first N entries (frequency‑ordered)")
    args = ap.parse_args()

    mapping  = json.load(open(args.map, encoding="utf-8"))
    key_pos  = parse_key_positions(args.keymap)

    # honour original frequency order by reading the word list again
    word_list = [w.strip() for w in open("5000-words.txt", encoding="utf-8") if w.strip()]

    kept = {}
    for w in word_list:
        if w not in mapping:
            continue
        chord_up = mapping[w].upper() if isinstance(mapping[w], str) else "".join(mapping[w]).upper()
        if all(c in key_pos for c in chord_up):
            kept[w] = chord_up
        if args.top and len(kept) >= args.top:
            break

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("/ {\n    combos {\n"
                '        compatible = "zmk,combos";\n        #binding-cells = <2>;\n\n')
        for w, chord in kept.items():
            pos = " ".join(str(key_pos[c]) for c in chord)
            binds = " ".join(f"&kp {c}" for c in chord)
            f.write(f"        combo_{w} {{\n"
                    f"            key-positions = <{pos}>;\n"
                    f"            bindings      = < {binds} >;\n"
                    f"        }};\n\n")
        f.write("    };\n};\n")

    print(f"Wrote {len(kept)} combos → {args.out}")


if __name__ == "__main__":
    main()
