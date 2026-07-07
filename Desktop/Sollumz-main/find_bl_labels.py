"""Find English UI strings in Sollumz source code."""
import re
import sys
from pathlib import Path

def is_chinese(s: str) -> bool:
    return any('\u4e00' <= c <= '\u9fff' for c in s)

def scan_file(path: Path):
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return
    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        if is_chinese(line):
            continue
        # Match common UI patterns
        m = re.search(r'(bl_label|bl_description)\s*=\s*"([^"]+)"', line)
        if m:
            yield (i, m.group(1), m.group(2), line.strip()[:120])
            continue
        m = re.search(r'(text\s*=|name\s*=|description\s*=|heading\s*=)\s*"([A-Z][^"]+)"', line)
        if m:
            s = m.group(2)
            if len(s) >= 3 and ' ' in s:  # only multi-word strings
                yield (i, m.group(1), s, line.strip()[:120])

if __name__ == '__main__':
    base = Path(sys.argv[1]).resolve()
    for p in sorted(base.rglob('*.py')):
        rel = p.relative_to(base)
        for lineno, key, s, raw in scan_file(p):
            print(f'{rel}|L{lineno}|{key}|{s}')
