import os, traceback, oracledb
from dotenv import load_dotenv
load_dotenv()

print("oracledb:", oracledb.__version__, "| thin mode:", oracledb.is_thin_mode())

conn = oracledb.connect(
    user=os.getenv("CDB_USER", "SYS"),
    password=os.getenv("CDB_PASSWORD"),
    dsn=os.getenv("CDB_DSN"),
    mode=oracledb.SYSDBA,
)
cur = conn.cursor()

def state():
    cur.execute("SELECT open_mode FROM v$pdbs WHERE name = 'ORCLPDB'")
    print("   ORCLPDB open_mode =", cur.fetchone()[0])

def run(label, sql):
    print(f"\n=== {label} ===\n   SQL: {sql}")
    try:
        cur.execute(sql); conn.commit(); print("   >>> OK")
    except Exception:
        print("   >>> FAILED — full traceback below:"); traceback.print_exc()

state()
run("CLOSE (wrapped)", "BEGIN EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ORCLPDB CLOSE IMMEDIATE'; END;")
state()
run("OPEN bare",    "ALTER PLUGGABLE DATABASE ORCLPDB OPEN READ WRITE")
state()
run("CLOSE (wrapped)", "BEGIN EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ORCLPDB CLOSE IMMEDIATE'; END;")
state()
run("OPEN wrapped", "BEGIN EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ORCLPDB OPEN READ WRITE'; END;")
state()

cur.close(); conn.close()