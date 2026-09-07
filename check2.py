import ast, re
lines = open("D:/cogni-2-main/cognidata/backend/app/api/routes/viz.py", encoding="utf-8").readlines()
print("Lines:", len(lines))
# Show lines 588-600
for i in range(587, 600):
    print(f"{i+1}: {repr(lines[i].rstrip())}")
print("---")
# Check for any broken/incomplete lines
for i, line in enumerate(lines):
    stripped = line.rstrip()
    # Look for lines ending mid-string or mid-paren that are not continuations
    if stripped.endswith("pad=20,") or stripped.endswith("template=\"plotl"):
        print(f"BROKEN at {i+1}: {repr(stripped)}")
src = "".join(lines)
try:
    ast.parse(src)
    print("AST: OK")
except SyntaxError as e:
    print(f"AST ERROR line {e.lineno}: {e.msg}")
    for i in range(max(0,e.lineno-3), min(len(lines), e.lineno+2)):
        print(f"  {i+1}: {repr(lines[i].rstrip())}")
