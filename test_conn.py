import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

print("oracledb version:", oracledb.__version__)
print("thin mode      :", oracledb.is_thin_mode())

user     = os.getenv("DB_USER", "SYS")
password = os.getenv("DB_PASSWORD") or os.getenv("ORCLPDB_PASSWORD")
dsn      = os.getenv("DB_DSN") or os.getenv("ORCLPDB_DSN")

print("USER           :", repr(user))
print("DSN            :", repr(dsn))
print("PASSWORD length:", len(password) if password else None)

try:
    conn = oracledb.connect(user=user, password=password, dsn=dsn, mode=oracledb.SYSDBA)
    print(">>> CONNECTED OK")
    conn.close()
except Exception as e:
    print(">>> FAILED:", e)