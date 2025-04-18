#!/usr/bin/env python3
import json, re, argparse, os

def parse_key_positions(path):
    txt = open(path, encoding="utf-8").read()
    blocks = re.findall(r'bindings\s*=\s*<([^>]+?)>;', txt, re.DOTALL)
    pat    = re.compile(r'&(kp|mt|lt)\s+(?:\S+\s+)?([A-Z])\b')
    pos, idx = {}, 0
    for blk in blocks:
        for _, letter in pat.findall(blk):
            if letter not in pos:
                pos[letter] = idx
                idx += 1
    return pos

def main():
    p = argparse.ArgumentParser(
        description="Generate mapping.h from mapping.json + your keymap")
    p.add_argument("--map",    default="mapping.json",
                   help="word→chord JSON")
    p.add_argument("--keymap", default="totem.keymap",
                   help=".keymap DTS file")
    p.add_argument("--out",    default="mapping.h",
                   help="Generated C header (will create directories as needed)")
    args = p.parse_args()

    # ensure the output directory exists
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    m      = json.load(open(args.map,    encoding="utf-8"))
    keypos = parse_key_positions(args.keymap)

    entries = []
    for w, chord in m.items():
        s = chord.upper() if isinstance(chord, str) else "".join(chord).upper()
        mask = 0
        for c in s:
            if c not in keypos:
                mask = None
                break
            mask |= 1 << keypos[c]
        if mask is not None:
            entries.append((mask, w))

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("""#pragma once
#include <stdint.h>
#include <stddef.h>

struct chord_entry {
    uint32_t mask;
    const char *word;
};

static const struct chord_entry chords[] = {
""")
        for mask, w in entries:
            f.write(f"    {{ 0x{mask:08X}, \"{w}\" }},\n")
        f.write("""};
#define NUM_CHORDS (sizeof(chords)/sizeof(chords[0]))
""")
    print(f"Wrote {len(entries)} entries to {args.out}")

if __name__ == "__main__":
    main()
