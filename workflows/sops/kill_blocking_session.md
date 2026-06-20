# NAME: kill_blocking_session
# TITLE: Oracle Database Blocking Session Eviction SOP
# KEYWORDS: kill blocking session, show blockers, fix deadlock, remove lock, terminate blocker session
# DESCRIPTION: Automatically detects row/table level locking chains, isolates the root user blocker and their offending SQL query, and evicts the session to restore transaction flow.
# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_MODE: sequential
# STOP_ON_ERROR: true

# DIAGNOSTIC_SQL_START
SELECT 
    TO_CHAR(s1.sid) AS BLOCKER_SID,
    TO_CHAR(s1.serial#) AS SERIAL_NUM,
    s1.username AS BLOCKING_USER,
    s1.machine AS HOST_MACHINE,
    s1.program AS APPLICATION,
    NVL(q.sql_text, 'No Active SQL (Transaction Left Open)') AS BLOCKING_SQL,
    COUNT(s2.sid) AS NUMBER_OF_WAITER_SESSIONS,
    MAX(s2.seconds_in_wait) AS MAX_WAIT_TIME_SECS,
    'FAIL: Active blocking lock chain detected!' AS VALIDATION_STATUS
FROM v$session s1
JOIN v$session s2 ON s1.sid = s2.blocking_session
LEFT JOIN v$sqlarea q ON s1.sql_id = q.sql_id
WHERE s1.type = 'USER'
GROUP BY s1.sid, s1.serial#, s1.username, s1.machine, s1.program, q.sql_text
UNION ALL
SELECT 
    'N/A' AS BLOCKER_SID, 
    'N/A' AS SERIAL_NUM, 
    'N/A' AS BLOCKING_USER, 
    'N/A' AS HOST_MACHINE, 
    'N/A' AS APPLICATION, 
    'N/A' AS BLOCKING_SQL,
    0 AS NUMBER_OF_WAITER_SESSIONS, 
    0 AS MAX_WAIT_TIME_SECS, 
    'PASS: No blocking sessions found' AS VALIDATION_STATUS 
FROM DUAL 
WHERE NOT EXISTS (
    SELECT 1 
    FROM v$session b1
    JOIN v$session b2 ON b1.sid = b2.blocking_session
    WHERE b1.type = 'USER'
)
# DIAGNOSTIC_SQL_END
# ACTION_TEMPLATE: ALTER SYSTEM KILL SESSION '{BLOCKER_SID},{SERIAL_NUM}' IMMEDIATE
# ---
# SELECT sid, username, status FROM v$session WHERE sid = {BLOCKER_SID}

## Purpose
This standard operating procedure automates the identification and rapid removal of high-risk exclusive data row locks that cause application timeouts, database thread exhaustion, and cascading connection pool spikes.