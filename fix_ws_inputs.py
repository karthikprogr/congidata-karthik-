import re

path = r"D:\cogni-2-main\cognidata\frontend\src\pages\Workspaces.jsx"
src = open(path, encoding="utf-8").read()

# Fix 1: All inline form rows - ensure flexWrap and button visibility
# Replace all instances of gap:8, flexWrap:"wrap" that are missing minWidth:0 on inputs
# The key fix: any input inside a flex row needs minWidth:0 to allow shrinking

# Fix the invite row
src = src.replace(
    'style={{ ...S.input, flex:2, minWidth:180 }}',
    'style={{ ...S.input, flex:2, minWidth:0 }}'
)

# Fix the query save row  
src = src.replace(
    'style={{ ...S.input, flex:2, minWidth:140 }}',
    'style={{ ...S.input, flex:2, minWidth:0 }}'
)

# Fix the goal row
src = src.replace(
    'style={{ ...S.input, flex:2, minWidth:120 }}',
    'style={{ ...S.input, flex:2, minWidth:0 }}'
)

# Fix the webhook row
src = src.replace(
    'style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8 }} />',
    'style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />'
)

# Fix the changelog row
src = src.replace(
    'style={{ ...S.input, flex:3, minWidth:140 }}',
    'style={{ ...S.input, flex:3, minWidth:0 }}'
)

# Fix the metric row
src = src.replace(
    'style={{ ...S.input, flex:2, minWidth:120 }}',
    'style={{ ...S.input, flex:2, minWidth:0 }}'
)

# Fix the contract row
src = src.replace(
    'style={{ ...S.input, flex:2, minWidth:140 }}',
    'style={{ ...S.input, flex:2, minWidth:0 }}'
)

# Fix the report row
src = src.replace(
    'style={{ ...S.input, flex:2, minWidth:140 }}',
    'style={{ ...S.input, flex:2, minWidth:0 }}'
)

open(path, "w", encoding="utf-8").write(src)
print("Done")
