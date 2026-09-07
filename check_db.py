import sqlite3, os

db_path = r'cognidata/backend/cognidata.db'
print('DB exists:', os.path.exists(db_path))
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print(f'Tables ({len(tables)}):')
    for t in tables:
        count = conn.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
        cols = [c[1] for c in conn.execute(f'PRAGMA table_info({t[0]})').fetchall()]
        print(f'  {t[0]}: {count} rows | cols: {cols}')
    conn.close()
else:
    print('DB does not exist yet')
