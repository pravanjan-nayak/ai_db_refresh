from db.dba_tasks import DBA_TASKS
from tools.db_tools import run_dba_task
from ai_agent import (
    generate_expdp_command,
    generate_rman_full_backup_command,
    dba_reasoning_answer
)

def route_query(question):
    q = question.lower()

    # ---------------------------------------------------------
    # 1. Direct task name match
    # ---------------------------------------------------------
    for task_name in DBA_TASKS:
        if task_name.replace("_", " ") in q:
            if task_name == "logical_backup":
                return generate_expdp_command(q)
            if task_name == "physical_backup":
                return generate_rman_full_backup_command(q)
            return run_dba_task(task_name)

    # ---------------------------------------------------------
    # 2. Alias match
    # ---------------------------------------------------------
    for task_name, info in DBA_TASKS.items():
        aliases = info.get("aliases", [])
        for alias in aliases:
            if alias in q:
                if task_name == "logical_backup":
                    return generate_expdp_command(q)
                if task_name == "physical_backup":
                    return generate_rman_full_backup_command(q)
                return run_dba_task(task_name)

    # ---------------------------------------------------------
    # 3. Keyword fallback for backup commands
    # ---------------------------------------------------------
    if "logical backup" in q or "export" in q:
        return generate_expdp_command(q)

    if "full backup" in q or "rman" in q or "physical backup" in q:
        return generate_rman_full_backup_command(q)

    # ---------------------------------------------------------
    # 4. Category fallback
    # ---------------------------------------------------------
    for task_name, info in DBA_TASKS.items():
        if info["category"] in q:
            return run_dba_task(task_name)

    # ---------------------------------------------------------
    # 5. FINAL FALLBACK → AI DBA reasoning
    # ---------------------------------------------------------
    return dba_reasoning_answer(question)
