#!/usr/bin/env python3
"""Fail if README.zh.md drifts structurally from README.md.

The two files must have the same sections, links, images, code blocks and list
items, in the same order. Prose is allowed to differ (it is translated).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN, ZH = ROOT / "README.md", ROOT / "README.zh.md"

URL = re.compile(r"""(?:\]\(|src=["']|href=["'])([^)"'\s]+)""")
ITEM = re.compile(r"^\s*(?:[-*]|\d+\.)\s")


def skeleton(text):
    lines = text.splitlines()[1:]  # line 1 is the language switcher
    sections, cur, fenced, fence, in_quote = [], None, False, [], False
    for ln in lines:
        if ln.strip().startswith("```"):
            if fenced:
                cur["code"].append("\n".join(fence))
                fence = []
            fenced = not fenced
            continue
        if fenced:
            fence.append(ln)
            continue
        m = re.match(r"^(#{2,6})\s", ln)
        if m:
            cur = {"level": len(m.group(1)), "heading": ln, "urls": [], "items": 0,
                   "quotes": 0, "code": []}
            sections.append(cur)
            continue
        if cur is None:
            cur = {"level": 0, "heading": "(header)", "urls": [], "items": 0,
                   "quotes": 0, "code": []}
            sections.append(cur)
        # internal anchors are translated with the headings, so only compare that they exist
        cur["urls"] += ["#anchor" if u.startswith("#") else u for u in URL.findall(ln)]
        cur["items"] += bool(ITEM.match(ln))
        is_quote = ln.lstrip().startswith(">")
        cur["quotes"] += is_quote and not in_quote  # count blocks, not wrapped lines
        in_quote = is_quote
    return sections


def main():
    en, zh = skeleton(EN.read_text()), skeleton(ZH.read_text())
    errors = []
    if len(en) != len(zh):
        errors.append(f"section count differs: README.md has {len(en)}, README.zh.md has {len(zh)}")
    for i, (a, b) in enumerate(zip(en, zh), 1):
        name = a["heading"]
        if a["level"] != b["level"]:
            errors.append(f"[{name}] heading level differs from zh '{b['heading']}'")
        if a["urls"] != b["urls"]:
            only_en = [u for u in a["urls"] if u not in b["urls"]]
            only_zh = [u for u in b["urls"] if u not in a["urls"]]
            errors.append(f"[{name}] links/images differ (zh section '{b['heading']}'). "
                          f"missing in zh: {only_en or 'none, order differs'}; extra in zh: {only_zh or 'none'}")
        if a["items"] != b["items"]:
            errors.append(f"[{name}] list item count differs: en {a['items']}, zh {b['items']}")
        if a["quotes"] != b["quotes"]:
            errors.append(f"[{name}] blockquote count differs: en {a['quotes']}, zh {b['quotes']}")
        if a["code"] != b["code"]:
            errors.append(f"[{name}] code blocks differ")
    if errors:
        print("README.md and README.zh.md are out of sync:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print("\nUpdate README.zh.md to match README.md (or the reverse), then commit again.",
              file=sys.stderr)
        return 1
    print("README parity OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
