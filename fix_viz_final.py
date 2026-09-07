path = "D:/cogni-2-main/cognidata/backend/app/api/routes/viz.py"
raw = open(path, "rb").read()
if raw.startswith(b"\xef\xbb\xbf"):
    raw = raw[3:]
src = raw.decode("utf-8")
lines = src.splitlines(keepends=True)
print("Input lines:", len(lines))

# Strategy:
# 1. Keep lines 0..590 (up to but not including the broken chord block at line 591)
# 2. Replace the broken chord block with a clean version
# 3. Keep lines from the second copy (882 onwards) up to the second HTTPException (line 1131)
#    but insert them BEFORE the first else+return block
# 4. Add the final else+return+except

# Find the broken chord start (line 591 = index 590, the go.Figure(go.Sankey line)
# Find the first else: at same indent level after the broken block
# The broken block is lines 591-594 (indices 590-593)
# Line 595 starts the duplicate "Advanced / AI-Era" section

# Find where the first clean return block is (line 876 = index 875)
first_return_idx = 875  # fig.update_layout(height=480...)

# Find where the second copy starts (line 882 = index 881)
second_copy_start = 881  # comment line

# Find the second HTTPException (line 1131 = index 1130)
second_except_idx = 1130

# Build the clean file:
# Part 1: lines 0..589 (before broken chord)
part1 = lines[:590]

# Part 2: clean chord block replacement
clean_chord = '''        elif ct in ("chord", "chord diagram"):
            import plotly.graph_objects as go, numpy as np
            cat_cols = df.select_dtypes(include="object").columns.tolist()
            if len(cat_cols) >= 2:
                src_col, tgt_col = cat_cols[0], cat_cols[1]
                val_col = y if y and y in df.columns and pd.api.types.is_numeric_dtype(df[y]) else None
                flows = df.groupby([src_col, tgt_col])[val_col].sum().reset_index() if val_col else df.groupby([src_col, tgt_col]).size().reset_index(name="count")
                flow_vals = flows[val_col if val_col else "count"].tolist()
                nodes = list(pd.unique(flows[[src_col, tgt_col]].values.ravel()))
                node_idx = {n: i for i, n in enumerate(nodes)}
                mx = max(flow_vals) or 1
                fig = go.Figure(go.Sankey(
                    arrangement="circular",
                    node=dict(label=nodes, pad=20, thickness=15,
                              color=px.colors.qualitative.Plotly[:len(nodes)]),
                    link=dict(
                        source=[node_idx[s] for s in flows[src_col]],
                        target=[node_idx[t] for t in flows[tgt_col]],
                        value=flow_vals,
                        color=[f"rgba(99,102,241,{min(0.8, v/mx):.2f})" for v in flow_vals],
                    )
                ))
                fig.update_layout(title=req.title, template="plotly_dark")
            else:
                fig = px.bar(df, x=x, y=y, **kwargs)

'''

# Part 3: the second copy of charts (lines 882..1129, skipping the comment header)
# These are the clean Advanced/AI-Era charts
# Skip the comment line (881) and take from 882 to just before the second else+return
# Find the second "else:" + return block
second_else_idx = None
for i in range(second_copy_start, second_except_idx):
    if lines[i].strip() == "else:" and i > 1100:
        second_else_idx = i
        break

if second_else_idx is None:
    # Find it differently - look for the last else: before the second HTTPException
    for i in range(second_except_idx - 1, second_copy_start, -1):
        if lines[i].strip() == "else:":
            second_else_idx = i
            break

print(f"Second else at line {second_else_idx+1}")

# Part 3: advanced charts from second copy (skip the comment, take elif blocks)
part3 = lines[second_copy_start+1:second_else_idx]  # skip comment, stop before else

# Part 4: final else + return + except
part4 = [
    "        else:\n",
    "            fig = px.bar(df, x=x, y=y, **kwargs)\n",
    "\n",
    "        fig.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))\n",
    '        return {"plotly_json": json.loads(fig.to_json()), "title": req.title}\n',
    "    except Exception as e:\n",
    '        raise HTTPException(422, f"Chart error: {e}")\n',
]

# Combine
result = part1 + [clean_chord] + part3 + part4
final_src = "".join(result)

import ast
try:
    ast.parse(final_src)
    print("Syntax OK")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno}: {e.msg}")
    flines = final_src.splitlines()
    for i in range(max(0,e.lineno-3), min(len(flines), e.lineno+2)):
        print(f"  {i+1}: {repr(flines[i])}")

open(path, "w", encoding="utf-8", newline="\n").write(final_src)
print("Written:", len(final_src.splitlines()), "lines")
