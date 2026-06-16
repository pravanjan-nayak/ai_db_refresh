DBA_TASKS = {

    # ============================
    # DATABASE & INSTANCE STATUS
    # ============================
    "database_status": {
        "category": "status",
        "description": "Database name, version, open mode, instance status",
        "aliases": [
            "db status", "database status", "instance status",
            "show database", "show instance"
        ],
        "query": """
            SELECT a.name, b.version, a.open_mode, b.status, b.host_name, b.startup_time
            FROM v$database a, v$instance b
        """
    },

    "instance_parameters": {
        "category": "config",
        "description": "Initialization parameters",
        "aliases": ["parameters", "init parameters", "db parameters"],
        "query": "SELECT name, value FROM v$parameter"
    },

    "database_uptime": {
        "category": "status",
        "description": "Database uptime",
        "aliases": [
            "uptime", "db uptime", "instance uptime",
            "how long up", "when was database started"
        ],
        "query": """
            SELECT
                startup_time,
                TRUNC(SYSDATE - startup_time) AS days,
                TRUNC(MOD((SYSDATE - startup_time) * 24, 24)) AS hours,
                TRUNC(MOD((SYSDATE - startup_time) * 24 * 60, 60)) AS minutes
            FROM v$instance
        """
    },

    # ============================
    # SESSIONS & CONNECTIONS
    # ============================
    "active_sessions": {
        "category": "sessions",
        "description": "Active sessions",
        "aliases": [
            "active sessions", "current sessions",
            "connected users", "active users", "session list"
        ],
        "query": """
            SELECT sid, serial#, username, status, machine, program
            FROM v$session
            WHERE status = 'ACTIVE' and username IS NOT NULL
        """
    },

    "blocking_sessions": {
        "category": "sessions",
        "description": "Blocking sessions",
        "aliases": [
            "who is blocking", "blocking", "blocked sessions",
            "blocking sessions", "find blockers", "session blocking",
            "blocking tree"
        ],
        "query": """
            SELECT blocking_session, sid, serial#, username, event
            FROM v$session
            WHERE blocking_session IS NOT NULL
        """
    },

    "session_count": {
        "category": "sessions",
        "description": "Total sessions by status",
        "aliases": ["session count", "count sessions", "session summary"],
        "query": """
            SELECT status, COUNT(*) AS count
            FROM v$session
            GROUP BY status
        """
    },

    # ============================
    # TABLESPACE & STORAGE
    # ============================
    "tablespace_usage": {
        "category": "storage",
        "description": "Tablespace usage",
        "aliases": [
            "tablespace usage", "storage usage", "space usage",
            "tablespace free", "tablespace used"
        ],
        "query": """
            SELECT tablespace_name, used_percent
            FROM dba_tablespace_usage_metrics
        """
    },

    "datafile_usage": {
        "category": "storage",
        "description": "Datafile size and usage",
        "aliases": ["datafile usage", "datafile size", "file usage"],
        "query": """
            SELECT file_name, bytes/1024/1024 AS size_mb, autoextensible
            FROM dba_data_files
        """
    },

    "temp_usage": {
        "category": "storage",
        "description": "Temporary tablespace usage",
        "aliases": ["temp usage", "temp tablespace", "temp free"],
        "query": """
            SELECT tablespace_name, used_blocks, free_blocks
            FROM v$temp_space_header
        """
    },

    # ============================
    # PERFORMANCE & WAITS
    # ============================
    "top_waits": {
        "category": "performance",
        "description": "Top wait events",
        "aliases": [
            "wait events", "top waits", "why slow",
            "database slow", "performance issue", "slow database"
        ],
        "query": """
            SELECT event, total_waits,
                   time_waited/100 AS time_waited_seconds,
                   average_wait/100 AS avg_wait_seconds
            FROM v$system_event
            WHERE wait_class <> 'Idle'
            ORDER BY time_waited DESC
            FETCH FIRST 10 ROWS ONLY
        """
    },

    "top_sql": {
        "category": "performance",
        "description": "Top SQL by elapsed time",
        "aliases": [
            "top sql", "slow sql", "high cpu sql",
            "expensive queries", "top queries"
        ],
        "query": """
            SELECT sql_id, executions, elapsed_time
            FROM v$sql
            ORDER BY elapsed_time DESC
            FETCH FIRST 10 ROWS ONLY
        """
    },

    "buffer_cache_hit_ratio": {
        "category": "performance",
        "description": "Buffer cache hit ratio",
        "aliases": ["buffer cache", "hit ratio", "cache hit ratio"],
        "query": """
            SELECT
                (1 - (phy.value / (lob.value + dir.value))) * 100 AS hit_ratio
            FROM
                v$sysstat phy,
                v$sysstat lob,
                v$sysstat dir
            WHERE
                phy.name = 'physical reads'
                AND lob.name = 'session logical reads'
                AND dir.name = 'db block gets'
        """
    },

    # ============================
    # MEMORY
    # ============================
    "sga_components": {
        "category": "memory",
        "description": "SGA component sizes",
        "aliases": ["sga", "sga usage", "memory components"],
        "query": "SELECT component, current_size/1024/1024 AS size_mb FROM v$sga_dynamic_components"
    },

    "pga_usage": {
        "category": "memory",
        "description": "PGA usage",
        "aliases": ["pga", "pga usage", "process memory"],
        "query": "SELECT name, value/1024/1024 AS mb FROM v$pgastat"
    },

    # ============================
    # I/O & FILESYSTEM
    # ============================
    "datafile_io": {
        "category": "io",
        "description": "Datafile I/O statistics",
        "aliases": ["datafile io", "file io", "io stats"],
        "query": """
            SELECT file#, phyrds, phywrts, readtim, writetim
            FROM v$filestat
        """
    },

    "tablespace_io": {
        "category": "io",
        "description": "Tablespace I/O",
        "aliases": ["tablespace io", "io tablespace"],
        "query": """
            SELECT ts.name, fs.phyrds, fs.phywrts
            FROM v$tablespace ts
            JOIN v$filestat fs ON ts.ts# = fs.ts#
        """
    },

    # ============================
    # SECURITY
    # ============================
    "invalid_users": {
        "category": "security",
        "description": "Users with expired or locked accounts",
        "aliases": ["invalid users", "locked users", "expired users", "security issues"],
        "query": """
            SELECT username, account_status
            FROM dba_users
            WHERE account_status <> 'OPEN'
        """
    },

    "privileged_users": {
        "category": "security",
        "description": "Users with DBA privileges",
        "aliases": ["privileged users", "dba users", "admin users"],
        "query": """
            SELECT grantee
            FROM dba_role_privs
            WHERE granted_role = 'DBA'
        """
    },

    # ============================
    # BACKUP & RECOVERY
    # ============================
    "rman_backup_status": {
        "category": "backup",
        "description": "RMAN backup status",
        "aliases": ["rman status", "backup status", "rman backup", "backup report"],
        "query": """
            SELECT session_key, input_type, status, start_time, end_time
            FROM v$rman_status
            ORDER BY start_time DESC
        """
    },

    "archivelog_status": {
        "category": "backup",
        "description": "Archive log generation",
        "aliases": ["archivelog", "archive log", "redo logs", "archive status"],
        "query": """
            SELECT name, sequence#, applied
            FROM v$archived_log
            ORDER BY sequence# DESC
        """
    },

    # ============================
    # LOGICAL BACKUP (expdp)
    # ============================
    "logical_backup": {
        "category": "backup",
        "description": "Generate Data Pump (expdp) command for logical backup",
        "aliases": [
            "logical backup", "take logical backup", "expdp",
            "data pump", "datapump", "export", "schema export",
            "export schema", "backup schema", "logical export"
        ],
        "query": None
    },

    # ============================
    # PHYSICAL BACKUP (RMAN)
    # ============================
    "physical_backup": {
        "category": "backup",
        "description": "Generate RMAN command for full database backup",
        "aliases": [
            "full backup", "rman backup", "physical backup",
            "database backup", "rman full backup", "take full backup"
        ],
        "query": None
    }
}

import re
from typing import Optional, Tuple, Dict


def normalize_question(question: str) -> str:
    """
    Normalize user question for matching.
    """
    return re.sub(r"\s+", " ", question.strip().lower())


def extract_schema_name(question: str) -> Optional[str]:
    """
    Extract schema name from questions like:
    - show all tables in HR
    - list tables for schema SCOTT
    - invalid objects in APPS
    """
    q = normalize_question(question)

    patterns = [
        r"(?:in|for|from)\s+schema\s+([a-zA-Z0-9_#$]+)",
        r"show all tables in\s+([a-zA-Z0-9_#$]+)",
        r"list tables in\s+([a-zA-Z0-9_#$]+)",
        r"show tables in\s+([a-zA-Z0-9_#$]+)",
        r"invalid objects in\s+([a-zA-Z0-9_#$]+)",
        r"objects in\s+([a-zA-Z0-9_#$]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return match.group(1).upper()

    return None


def find_task_by_alias(question: str) -> Optional[str]:
    """
    Match user question against DBA_TASKS aliases.
    Returns task key if matched, else None.
    """
    q = normalize_question(question)

    # exact alias or contained alias matching
    for task_name, task_data in DBA_TASKS.items():
        aliases = task_data.get("aliases", [])
        for alias in aliases:
            alias_norm = normalize_question(alias)
            if alias_norm == q or alias_norm in q:
                return task_name

    return None


def match_known_task(question: str) -> Tuple[Optional[str], Optional[str], Dict]:
    """
    Returns:
        (task_name, sql, meta)

    meta example:
        {
            "confidence": 0.99,
            "category": "status",
            "description": "Database name..."
        }
    """
    q = normalize_question(question)

    # ---------------------------------------------------
    # 1) Special handling for schema-based dynamic queries
    # ---------------------------------------------------

    # show all tables in HR
    if "show all tables" in q or "list tables" in q or "show tables" in q:
        schema = extract_schema_name(question)
        if schema:
            sql = f"""
                SELECT owner, table_name
                FROM dba_tables
                WHERE owner = '{schema}'
                ORDER BY table_name
            """
            return "tables_in_schema", sql.strip(), {
                "confidence": 0.98,
                "category": "objects",
                "description": f"All tables in schema {schema}",
                "schema": schema
            }

    # invalid objects in HR
    if "invalid objects" in q:
        schema = extract_schema_name(question)
        if schema:
            sql = f"""
                SELECT owner, object_name, object_type, status
                FROM dba_objects
                WHERE status = 'INVALID'
                  AND owner = '{schema}'
                ORDER BY owner, object_type, object_name
            """
            return "invalid_objects_schema", sql.strip(), {
                "confidence": 0.98,
                "category": "security",
                "description": f"Invalid objects in schema {schema}",
                "schema": schema
            }

    # ---------------------------------------------------
    # 2) Generic alias-based matching from existing DBA_TASKS
    # ---------------------------------------------------
    matched_task = find_task_by_alias(question)

    if matched_task:
        task_info = DBA_TASKS[matched_task]
        sql = task_info.get("query")

        # If query is None (logical backup / physical backup), let caller decide
        if sql:
            return matched_task, sql.strip(), {
                "confidence": 0.95,
                "category": task_info.get("category"),
                "description": task_info.get("description")
            }

        return matched_task, None, {
            "confidence": 0.90,
            "category": task_info.get("category"),
            "description": task_info.get("description"),
            "action_only": True
        }

    # ---------------------------------------------------
    # 3) No known match
    # ---------------------------------------------------
    return None, None, {"confidence": 0.0}
