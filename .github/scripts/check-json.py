#!/usr/bin/env python3
"""Parse every config in this repo, including the ones that are JSON with comments.

VS Code and Zed both accept `//` comments and trailing commas, and nothing else here would
notice a config that stopped parsing -- the editor simply falls back to its defaults and says
nothing. Stripping comments with a regex is what this replaces: a commented-out line containing
a quoted string breaks a naive stripper, and both of those exist in this repo already.
"""

from __future__ import annotations

import json
import re
import sys


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments, leaving anything inside a string literal alone."""
    out: list[str] = []
    i, n = 0, len(text)
    in_string = escaped = False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
            i += 1
        elif c == '"':
            in_string = True
            out.append(c)
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def main(paths: list[str]) -> int:
    failed = 0
    for path in paths:
        try:
            json.loads(re.sub(r",(\s*[}\]])", r"\1", strip_comments(open(path).read())))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  ✗ {path}: {exc}", file=sys.stderr)
            failed += 1
        else:
            print(f"  ✓ {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
