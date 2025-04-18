#!/usr/bin/env python3
import json, re, argparse
from typing import Dict

def parse_key_positions(path: str) -> Dict[str, int]:
    """
    Scan every `bindings = < ... >;` block in the .keymap and assign
    a zero-based position number to each printable letter the first
    time it appears, in file order (left→right, top→bottom).
    """
    txt = open(path, encoding="utf-8").read()
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', txt, flags=re.DOTALL)
    if not blocks:
        raise RuntimeError(f"No `bindings = < ... >;` blocks found in {path}")
    pat = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    pos: Dict[str, int] = {}
    nxt = 0
    for blk in blocks:
        for _, letter in pat.findall(blk):
            if letter not in pos:
                pos[letter] = nxt
                nxt += 1
    return pos

def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate a ZMK devicetree overlay with macros + combos"
    )
    p.add_argument("--map",    default="mapping.json",
                   help="Word→chord JSON (from chordgen.py)")
    p.add_argument("--keymap", default="totem.keymap",
                   help="Your Totem .keymap devicetree file")
    p.add_argument("--words",  default="5000-words.txt",
                   help="Original frequency‑ordered word list")
    p.add_argument("--out",    default="combos_and_macros.keymap",
                   help="Output overlay file")
    p.add_argument("--top",    type=int, default=None,
                   help="Keep only the first N entries (frequency‑ordered)")
    args = p.parse_args()

    # Load mapping and key positions
    mapping  = json.load(open(args.map,    encoding="utf-8"))
    key_pos  = parse_key_positions(args.keymap)

    # Re‑read the original word list to preserve frequency order
    word_list = [
      w.strip() for w in open(args.words, encoding="utf-8")
      if w.strip()
    ]

    # Select only those words that exist in mapping and whose chord
    # letters are all present on the board.  Stop at --top if given.
    kept = []
    for w in word_list:
        if w not in mapping:
            continue
        chord_raw = mapping[w]
        chord_up = (chord_raw.upper()
                    if isinstance(chord_raw, str)
                    else "".join(chord_raw).upper())
        if all(c in key_pos for c in chord_up):
            kept.append((w, chord_up))
            if args.top and len(kept) >= args.top:
                break

    # Write out a single overlay with both behaviors (macros) and combos
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("/ {\n")
        # --- behaviors section ---
        f.write("    behaviors {\n")
        f.write("        #binding-cells = <0>;\n\n")
        for w, chord in kept:
            macro = f"macro_{w}"
            f.write(f"        {macro} {{\n")
            f.write('            compatible = "zmk,behavior-macro";\n')
            f.write("            #binding-cells = <0>;\n")
            f.write("            bindings = <\n")
            for c in chord:
                f.write(f"                &kp {c}\n")
            f.write("            >;\n")
            f.write("        };\n\n")
        f.write("    };\n\n")

        # --- combos section ---
        f.write("    combos {\n")
        f.write('        compatible = "zmk,combos";\n')
        f.write("        #binding-cells = <2>;\n\n")
        for w, chord in kept:
            combo = f"combo_{w}"
            positions = " ".join(str(key_pos[c]) for c in chord)
            f.write(f"        {combo} {{\n")
            f.write(f"            key-positions = <{positions}>;\n")
            f.write(f"            bindings      = < &macro_{w} >;\n")
            f.write("        };\n\n")
        f.write("    };\n")
        f.write("};\n")

    print(f"Wrote {len(kept)} macros & combos → {args.out}")

if __name__ == "__main__":
    main()
