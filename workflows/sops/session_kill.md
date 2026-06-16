
# NAME: session_kill
# TITLE: Oracle Session Kill SOP
# KEYWORDS: kill session, terminate session, remove session, disconnect session, hanging session, stuck session
# DESCRIPTION: Identify and terminate an Oracle database session safely.
# DIAGNOSTIC_SQL_START
SELECT sid,
       serial#,
       username,
       status,
       machine,
       program,
       module,
       sql_id,
       event,
       blocking_session
FROM v$session
WHERE username IS NOT NULL
ORDER BY status, username
# DIAGNOSTIC_SQL_END
# ACTION_REQUIRED: true
# ACTION_TEMPLATE: ALTER SYSTEM KILL SESSION '{sid},{serial#}' IMMEDIATE
# APPROVAL_REQUIRED: true

# Oracle Session Kill SOP

## Purpose
This SOP is used to identify and terminate an Oracle database session safely when the session is hung, blocking other sessions, or consuming abnormal resources.

## Preconditions
- Confirm the correct database and instance
- Validate business impact before killing the session
- If production, confirm with application owner or relevant support team
- Ensure you have DBA privileges

## Step 1: Identify the session
Run the diagnostic query to list sessions by SID, SERIAL#, username, machine, status, and program.

## Step 2: Kill the session
Select the target session from the results, then click **Approve & Execute**.
The system will run:
```sql
ALTER SYSTEM KILL SESSION '{sid},{serial#}' IMMEDIATE
```

## Step 3: Verify
Re-run the diagnostic. If the session no longer appears, it was successfully terminated.

## Caution
- Never kill SYS or background sessions (PMON, SMON, LGWR, etc.)
- Always confirm the username and machine before killing
- In RAC, you may need to include the instance number
