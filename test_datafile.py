# Run this standalone: python debug_datafile.py
# It will show exactly what v$datafile returns and which directory gets picked

from db.db_connection import get_connection
from collections import Counter
import os

conn = get_connection()
cursor = conn.cursor()

print("=== v$datafile for USERS ===")
cursor.execute("""
    SELECT v.name, v.bytes
    FROM   v$datafile v
    JOIN   v$tablespace t ON v.ts# = t.ts#
    WHERE  t.name = 'USERS'
    ORDER  BY v.name
""")
rows = cursor.fetchall()
for r in rows:
    print(f"  FILE: {r[0]}  SIZE: {round(r[1]/1073741824,2)} GB")

existing_files = [r[0] for r in rows]

print("\n=== Directory of each file ===")
for f in existing_files:
    print(f"  {os.path.dirname(f)}")

dir_counts = Counter(os.path.dirname(f) for f in existing_files)
print("\n=== Directory vote count ===")
for d, count in dir_counts.most_common():
    print(f"  {count} vote(s): {d}")

chosen = dir_counts.most_common(1)[0][0]
print(f"\n=== Chosen directory ===\n  {chosen}")

cursor.close()
conn.close()