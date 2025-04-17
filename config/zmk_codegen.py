#!/usr/bin/env python3
import json, re, argparse
from typing import Dict

def parse_key_positions(path: str) -> Dict[str,int]:
    txt = open(path, encoding="utf‑8").read()
    # gather every bindings = < … > ;
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', txt, re.DOTALL)
    if not blocks:
        raise RuntimeError("no bindings block in " + path)
    pat   = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    pos, nxt = {}, 0
    for blk in blocks:               # file order → physical order
        for _, letter in pat.findall(blk):
            if letter not in pos:
                pos[letter] = nxt
                nxt += 1
    return pos

def main():
    ap = argparse.ArgumentParser(description="word‑>chord → ZMK combos overlay")
    ap.add_argument("--map",    default="mapping.json")
    ap.add_argument("--keymap", default="totem.keymap")
    ap.add_argument("--out",    default="combos.keymap")
    args = ap.parse_args()

    mapping = json.load(open(args.map, encoding="utf‑8"))
    key_pos = parse_key_positions(args.keymap)

    valid, skipped = {}, []
    for w, chord in mapping.items():
        s = chord.upper() if isinstance(chord,str) else "".join(chord).upper()
        if all(c in key_pos for c in s):
            valid[w] = s
        else:
            skipped.append(w)
    if skipped:
        print(f"Skipped {len(skipped)} words w/ unsupported keys")

    with open(args.out,"w",encoding="utf‑8") as f:
        f.write("/ {\n    combos {\n"
                '        compatible = "zmk,combos";\n'
                '        #binding-cells = <2>;\n\n')
        for word, s in valid.items():
            pos  = " ".join(str(key_pos[c]) for c in s)
            kps  = "\n".join(f"                &kp {c}" for c in word.upper())
            f.write(f"        combo_{word} {{\n"
                    f"            key-positions = <{pos}>;\n"
                    f"            bindings = <\n{kps}\n            >;\n"
                    f"        }};\n\n")
        f.write("    };\n};\n")

    print(f"Wrote {len(valid)} combos to {args.out}")

if __name__ == "__main__":
    main()
