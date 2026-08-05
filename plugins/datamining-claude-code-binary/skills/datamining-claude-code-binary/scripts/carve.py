#!/usr/bin/env python3
"""Carve byte windows out of the Claude Code native binary.

The embedded app JS is minified to a SINGLE line, so line-based grep -A/-B context
is useless. Find a byte offset for a literal marker, then read a fixed byte window
around it. Some regions are UTF-16 (chars space-interleaved) or raw binary tables —
if a window is garbled, nudge --at by a few KB.

Examples:
  carve.py "$(locate-claude-binary.sh)" --find 'tengu_' --limit 30
  carve.py "$(locate-claude-binary.sh)" --at 41234567 --len 4000 --back 500
"""
import argparse
import re
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary")
    ap.add_argument("--find", help="literal byte string to locate; prints byte offsets")
    ap.add_argument("--limit", type=int, default=20, help="max offsets to print (--find)")
    ap.add_argument("--at", type=int, help="byte offset to carve a window from")
    ap.add_argument("--len", type=int, default=2000, dest="length", help="window bytes after --at")
    ap.add_argument("--back", type=int, default=0, help="window bytes before --at")
    args = ap.parse_args()

    with open(args.binary, "rb") as f:
        data = f.read()

    if args.find is not None:
        offs = [m.start() for m in re.finditer(re.escape(args.find.encode()), data)]
        for o in offs[: args.limit]:
            print(o)
        if not offs:
            print("(no match)", file=sys.stderr)
            return 1
        print(f"(showing {min(args.limit, len(offs))} of {len(offs)} matches)", file=sys.stderr)
        return 0

    if args.at is not None:
        start = max(0, args.at - args.back)
        sys.stdout.buffer.write(data[start : args.at + args.length])
        sys.stdout.buffer.write(b"\n")
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
