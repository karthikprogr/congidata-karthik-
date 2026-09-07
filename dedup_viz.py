import re

path = "D:/cogni-2-main/cognidata/backend/app/api/routes/viz.py"
src = open(path, encoding="utf-8").read()
lines = src.splitlines(keepends=True)

# Find all elif ct in blocks with their line ranges
# Strategy: parse into blocks, keep only the LAST occurrence of each ct signature
# (the last ones are the cleanest/most complete versions)

block_starts = []
for i, line in enumerate(lines):
    if re.match(r"\s+elif ct in \(", line):
        block_starts.append(i)

# For each block, find its extent (until next elif/else at same indent level)
def get_block_end(lines, start):
    indent = len(lines[start]) - len(lines[start].lstrip())
    for i in range(start + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped:
            continue
        curr_indent = len(lines[i]) - len(lines[i].lstrip())
        if curr_indent <= indent and (stripped.startswith("elif ") or stripped.startswith("else:")):
            return i
    return len(lines)

# Extract signature from elif line
def get_sig(line):
    m = re.search(r'elif ct in \((.+?)\)', line)
    return m.group(1) if m else line.strip()

# Build blocks
blocks = []
for start in block_starts:
    end = get_block_end(lines, start)
    sig = get_sig(lines[start])
    blocks.append((sig, start, end))

# Find duplicates - keep last occurrence, remove earlier ones
from collections import defaultdict
sig_occurrences = defaultdict(list)
for sig, start, end in blocks:
    sig_occurrences[sig].append((start, end))

# Collect line ranges to REMOVE (all but the last occurrence)
lines_to_remove = set()
for sig, occurrences in sig_occurrences.items():
    if len(occurrences) > 1:
        # Remove all but the last
        for start, end in occurrences[:-1]:
            for i in range(start, end):
                lines_to_remove.add(i)

print(f"Removing {len(lines_to_remove)} lines from {len([s for s,o in sig_occurrences.items() if len(o)>1])} duplicate blocks")

# Write clean file
clean_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
open(path, "w", encoding="utf-8").write("".join(clean_lines))

import ast
ast.parse(open(path, encoding="utf-8").read())
final_lines = open(path, encoding="utf-8").readlines()
print(f"Clean file: {len(final_lines)} lines, syntax OK")
