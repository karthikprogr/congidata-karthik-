import re

path = r"D:\cogni-2-main\cognidata\frontend\src\pages\Workspaces.jsx"
src = open(path, encoding="utf-8").read()

# Replace all minWidth values > 0 in S.input spreads inside flex rows
# Pattern: minWidth:NNN where NNN > 0
src = re.sub(r'minWidth:(\d+)', lambda m: 'minWidth:0' if int(m.group(1)) > 0 else m.group(0), src)

# Replace gap:8 with gap:6 in flex rows (tighter spacing)
src = src.replace('gap:8, flexWrap:"wrap"', 'gap:6, flexWrap:"wrap"')
src = src.replace('gap:8, flexWrap: "wrap"', 'gap:6, flexWrap:"wrap"')

# Ensure all buttons in flex rows have flexShrink:0 via whiteSpace:nowrap (already in S.btn)
# The S.btn already has whiteSpace:"nowrap" and flexShrink:0 from our earlier fix

open(path, "w", encoding="utf-8").write(src)
print("Lines:", len(src.splitlines()))
print("Done")
