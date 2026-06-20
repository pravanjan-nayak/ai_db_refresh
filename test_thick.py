import os, traceback, oracledb
from dotenv import load_dotenv
load_dotenv()

oracledb.init_oracle_client()                 # enable Thick mode (uses your Oracle client libs)
print("thin mode:", oracledb.is_thin_mode())  # should now print False

conn = oracledb.connect(user=os.getenv("CDB_USER","SYS"),
                        password=os.getenv("CDB_PASSWORD"),
                        dsn=os.getenv("CDB_DSN"), mode=oracledb.SYSDBA)
cur = conn.cursor()
cur.execute("BEGIN EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ORCLPDB CLOSE IMMEDIATE'; END;"); conn.commit()
print("closed -> MOUNTED")
try:
    cur.execute("BEGIN EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE ORCLPDB OPEN READ WRITE'; END;"); conn.commit()
    print(">>> OPEN OK in THICK mode")
except Exception:
    traceback.print_exc()
conn.close()