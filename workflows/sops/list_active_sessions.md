# ============================================================
# FILE:    workflows\sops\list_active_sessions.md
# ACTION:  REPLACE THE ENTIRE EXISTING FILE WITH THIS
# LOCATION: C:\AI Agents\OracleAIDBAAgent-main\OracleAIDBAAgent-main\workflows\sops\list_active_sessions.md
# ============================================================
# NAME: list_active_sessions
# TITLE: Active Session Check SOP
# KEYWORDS: active sessions, show active sessions, current sessions, running sessions, session activity
# DESCRIPTION: Check active Oracle database sessions and review session details.
# DIAGNOSTIC_SQL_START
SELECT sid,
       serial#,
       username,
       status,
       machine,
       program,
       sql_id,
       event,
       last_call_et AS seconds_active
FROM v$session
WHERE status = 'ACTIVE'
  AND username IS NOT NULL
ORDER BY seconds_active DESC
# DIAGNOSTIC_SQL_END
# ACTION_REQUIRED: false
# APPROVAL_REQUIRED: false

# Active Session Check SOP

## Purpose
Identify active sessions in Oracle Database for troubleshooting or operational monitoring.

## Preconditions
- Ensure privileges to query v$session
- Confirm whether all sessions or a specific schema is required

## Step 1: List active sessions
Run the diagnostic to see all currently active sessions sorted by how long they have been running.

## Step 2: Review long-running sessions
Sessions with high `seconds_active` may be candidates for investigation or killing using the Session Kill SOP.
