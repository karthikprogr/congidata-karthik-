import re
src = open("D:/cogni-2-main/cognidata/backend/app/api/routes/viz.py", encoding="utf-8").read()
lines = src.splitlines()
print("Total lines:", len(lines))
# Find all elif ct in blocks
elifs = [(i+1, lines[i].strip()) for i, l in enumerate(lines) if "elif ct in" in l]
print("Total elif ct blocks:", len(elifs))
# Check for duplicates
from collections import Counter
counts = Counter(l for _, l in elifs)
for k, v in counts.items():
    if v > 1:
        print(f"DUPLICATE ({v}x): {k}")
# Check for broken pad=20 line
for i, line in enumerate(lines):
    if "pad=20," == line.strip() or line.strip().endswith("pad=20,"):
        print(f"Suspicious pad=20 at line {i+1}: {repr(line)}")
