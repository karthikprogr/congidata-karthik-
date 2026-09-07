path = "D:/cogni-2-main/cognidata/backend/app/api/routes/viz.py"
raw = open(path, "rb").read()
if raw.startswith(b"\xef\xbb\xbf"): raw = raw[3:]
src = raw.decode("utf-8")
lines = src.splitlines()
print("Lines:", len(lines))

# Find all HTTPException lines
for i, l in enumerate(lines):
    if "raise HTTPException(422" in l:
        print(f"HTTPException at line {i+1}")
    if "node=dict(label=nodes, pad=20," == l.strip():
        print(f"Broken pad=20 at line {i+1}")
    if "elif ct == .bubble" in l:
        print(f"Bubble at line {i+1}: {l.strip()}")
