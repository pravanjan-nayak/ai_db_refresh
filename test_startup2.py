import os, traceback, oracledb
from dotenv import load_dotenv
load_dotenv()

def connect():
    return oracledb.connect(user=os.getenv("CDB_USER","SYS"),
                            password=os.getenv("CDB_PASSWORD"),
                            dsn=os.getenv("CDB_DSN"), mode=oracledb.SYSDBA)

OPEN  = "BEGIN EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ORCLPDB OPEN READ WRITE'; END;"
CLOSE = "BEGIN EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ORCLPDB CLOSE IMMEDIATE'; END;"

def attempt(title, do_open):
    conn = connect(); cur = conn.cursor()
    cur.execute(CLOSE); conn.commit()          # ensure MOUNTED first
    print(f"\n=== {title} ===")
    try:
        do_open(conn, cur); conn.commit(); print(">>> OK")
    except Exception:
        print(">>> FAILED:"); traceback.print_exc()
    finally:
        try: conn.close()
        except: pass

# A) EXACTLY like your app: probe v$database, then OPEN on the SAME cursor
def a(conn, cur):
    cur.execute("SELECT cdb FROM v$database"); cur.fetchone()
    cur.execute(OPEN)
attempt("A: same cursor, right after SELECT cdb FROM v$database (mimics your app)", a)

# B) candidate fix: probe on the cursor, but run OPEN on a FRESH cursor
def b(conn, cur):
    cur.execute("SELECT cdb FROM v$database"); cur.fetchone()
    cur2 = conn.cursor()
    cur2.execute(OPEN)
attempt("B: OPEN on a fresh cursor", b)