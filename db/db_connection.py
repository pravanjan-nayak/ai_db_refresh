import os
import oracledb
from dotenv import load_dotenv

load_dotenv()


# Use Thick mode (Oracle Client libraries) to avoid the thin-mode ALTER PLUGGABLE DATABASE bug.
# Must run before any connection is created in the process.
try:
    oracledb.init_oracle_client()
except Exception:
    pass  # already initialized in this process


def get_connection(target_context="PDB"):
    """
    Fetches a precise database connection based on the target execution context.
    Options for target_context: "CDB_ROOT", "PDB", or "NON_CDB"
    """
    
    if target_context == "CDB_ROOT":
        db_user = os.getenv("CDB_USER", "SYS")
        db_password = os.getenv("CDB_PASSWORD")
        db_dsn = os.getenv("CDB_DSN")  # Hits 127.0.0.1:1521/orcl
        
    elif target_context == "NON_CDB":
        db_user = os.getenv("UATAGENT_USER", "SYS")
        db_password = os.getenv("UATAGENT_PASSWORD")
        db_dsn = os.getenv("UATAGENT_DSN")  # Hits 127.0.0.1:1521/uatagent
        
    else:  # Default to PDB context
        db_user = os.getenv("DB_USER", "SYS")
        db_password = os.getenv("DB_PASSWORD") or os.getenv("ORCLPDB_PASSWORD")
        db_dsn = os.getenv("DB_DSN") or os.getenv("ORCLPDB_DSN")  # Hits 127.0.0.1:1521/ORCLPDB

    if not db_password or not db_dsn:
        raise ValueError(f"[SECURITY ERROR] Missing credentials or DSN for context: {target_context}")

    # Establish connection with precise DSN routing to avoid Windows SID conflicts
    if db_user.upper() == "SYS":
        conn = oracledb.connect(
            user=db_user,
            password=db_password,
            dsn=db_dsn,
            mode=oracledb.SYSDBA
        )
    else:
        conn = oracledb.connect(
            user=db_user,
            password=db_password,
            dsn=db_dsn
        )

    # If we targeted the PDB via its direct service name, we are already there.
    # If using legacy fallbacks to root, seamlessly alter session context.
    if target_context == "PDB" and "ORCLPDB" not in db_dsn.upper():
        try:
            cursor = conn.cursor()
            cursor.execute("ALTER SESSION SET CONTAINER = ORCLPDB")
            cursor.close()
        except oracledb.DatabaseError as e:
            if "ORA-65049" in str(e) or "ORA-65011" in str(e):
                pass  # Bypass if legacy target was actually a standalone environment
            else:
                raise e

    return conn