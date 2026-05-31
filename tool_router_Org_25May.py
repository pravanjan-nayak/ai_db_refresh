from db_tools import (
get_database_status,
get_active_sessions,
get_tablespace_usage,
get_top_sql,
get_top_waits,
get_db_summary
)

def route_query(question):

    question = question.lower()
    
    if "database status" in question or "status" in question:
        return get_database_status()
    
    elif "session" in question:
        return get_active_sessions()
    
    elif "tablespace" in question:
        return get_tablespace_usage()
    
    elif "sql" in question or "top sql" in question:
        return get_top_sql()

    elif "wait" in question or "top wait" in question:
        return get_top_waits()

    else:
        return "I don't know how to answer that."