import sqlite3

con = sqlite3.connect("bookings.sqlite3")
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]

for t in tables:
    cur = con.execute(f"SELECT * FROM {t}")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(f"\n=== {t} ({len(rows)} rows) ===")
    print(" | ".join(cols))
    for row in rows:
        print(" | ".join(str(x) for x in row))