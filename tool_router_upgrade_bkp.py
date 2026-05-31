from dba_tasks import DBA_TASKS
from db_tools import run_dba_task

def route_query(question):
    q = question.lower()

    # 1. Direct match: "active sessions", "tablespace usage", etc.
    for task_name in DBA_TASKS:
        if task_name.replace("_", " ") in q:
            return run_dba_task(task_name)

    # 2. Category match: "performance", "storage", "sessions", etc.
    for task_name, info in DBA_TASKS.items():
        if info["category"] in q:
            return run_dba_task(task_name)

    # 3. Keyword match (optional)
    keywords = {
        "session": "active_sessions",
        "tablespace": "tablespace_usage",
        "wait": "top_waits",
        "sql": "top_sql",
        "status": "database_status",
        "performance": "top_waits",
        "memory": "sga_components",
        "backup": "rman_backup_status",
        "security": "invalid_users"
    }

    for word, task in keywords.items():
        if word in q:
            return run_dba_task(task)

    # 4. Fallback
    return run_dba_task("database_status")


from ai_agent import dba_reasoning_answer

def route_query(question):
    q = question.lower()

    # ... your existing matching logic ...

    # 5. FINAL FALLBACK → AI DBA reasoning
    return dba_reasoning_answer(question)

