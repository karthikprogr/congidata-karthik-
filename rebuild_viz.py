# Read the clean disk version and write it back with a BOM-less UTF-8 encoding
# to force the editor to reload
import ast

path = "D:/cogni-2-main/cognidata/backend/app/api/routes/viz.py"
src = open(path, encoding="utf-8").read()

# Verify it is clean
ast.parse(src)

# Write back with explicit utf-8-sig then back to utf-8 to force editor refresh
import tempfile, os, shutil
tmp = path + ".tmp"
with open(tmp, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
shutil.move(tmp, path)

lines = src.splitlines()
print(f"Written: {len(lines)} lines, syntax OK")
print(f"Line 590: {lines[589]}")
print(f"Line 591: {lines[590]}")
print(f"Line 592: {lines[591]}")
print(f"Line 593: {lines[592]}")
