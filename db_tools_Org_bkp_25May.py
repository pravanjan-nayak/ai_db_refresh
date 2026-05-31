import pandas as pd
from db_connection import get_connection

def get_database_status():
    conn = get_connection()

    query = """
    SELECT a.name, b.version, a.open_mode, b.status, b.host_name, b.startup_time
    FROM v$database a, v$instance b
    """
    
    df = pd.read_sql(query, conn)
    
    conn.close()
    
    return df


def get_active_sessions():
    conn = get_connection()

    query = """
    SELECT sid, username, status
    FROM v$session
    WHERE status = 'ACTIVE'
    """
    
    df = pd.read_sql(query, conn)
    
    conn.close()
    
    return df


def get_tablespace_usage():
    conn = get_connection()

    query = """
    SELECT tablespace_name, used_percent
    FROM dba_tablespace_usage_metrics
    """
    
    df = pd.read_sql(query, conn)
    
    conn.close()
    
    return df


def get_top_sql():
    conn = get_connection()

    query = """
    SELECT sql_id, executions, elapsed_time
    FROM v$sql
    FETCH FIRST 5 ROWS ONLY
    """
    
    df = pd.read_sql(query, conn)
    
    conn.close()
    
    return df

 
def get_top_waits():
    conn = get_connection()

    query = """
    SELECT
    event,
    total_waits,
    time_waited/100 AS time_waited_seconds,
    average_wait/100 AS avg_wait_seconds
    FROM
    v$system_event
    WHERE
    wait_class <> 'Idle'
    ORDER BY
    time_waited DESC
    FETCH FIRST 5 ROWS ONLY
    """
    
    df = pd.read_sql(query, conn)
    
    conn.close()
    
    return df

def get_db_summary():
    summary = {}

    try:
        summary["database_status"] = get_database_status()
    except Exception as e:
        summary["database_status"] = f"Error: {str(e)}"

    try:
        summary["top_waits"] = get_top_waits()
    except Exception as e:
        summary["top_waits"] = f"Error: {str(e)}"

    try:
        summary["active_sessions"] = get_active_sessions()
    except Exception as e:
        summary["active_sessions"] = f"Error: {str(e)}"

    try:
        summary["tablespace"] = get_tablespace_usage()
    except Exception as e:
        summary["tablespace"] = f"Error: {str(e)}"

    try:
        summary["top_sql"] = get_top_sql()
    except Exception as e:
        summary["top_sql"] = f"Error: {str(e)}"

    return summary