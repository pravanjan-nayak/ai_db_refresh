# ============================================================
# FILE:    workflows\sops\blocking_session.md
# ACTION:  REPLACE THE ENTIRE EXISTING FILE WITH THIS
# LOCATION: C:\AI Agents\OracleAIDBAAgent-main\OracleAIDBAAgent-main\workflows\sops\blocking_session.md
# ============================================================
# NAME: blocking_session
# TITLE: Blocking Session Troubleshooting SOP
# KEYWORDS: blocking session, blocked session, lock issue, session blocking, who is blocking, lock troubleshooting
# DESCRIPTION: Identify blocking and blocked sessions and take corrective action.
# DIAGNOSTIC_SQL_START
SELECT s1.sid AS blocking_sid,
       s1.serial# AS blocking_serial,
       s1.username AS blocking_user,
       s1.machine AS blocking_machine,
       s2.sid AS blocked_sid,
       s2.serial# AS blocked_serial,
       s2.username AS blocked_user,
       s2.machine AS blocked_machine,
       s2.event
FROM v$lock l1
JOIN v$session s1 ON l1.sid = s1.sid
JOIN v$lock l2 ON l1.id1 = l2.id1 AND l1.id2 = l2.id2
JOIN v$session s2 ON l2.sid = s2.sid
WHERE l1.block = 1
  AND l2.request > 0
# DIAGNOSTIC_SQL_END
# ACTION_REQUIRED: true
# ACTION_TEMPLATE: ALTER SYSTEM KILL SESSION '{blocking_sid},{blocking_serial}' IMMEDIATE
# APPROVAL_REQUIRED: true

# Blocking Session Troubleshooting SOP

## Purpose
Identify blocking and blocked sessions in Oracle Database and determine the safest corrective action.

## Preconditions
- Confirm database name and environment
- Check whether the issue is production-critical
- Ensure DBA access is available
- Inform application team if major blocking is observed

## Step 1: Identify blocking and blocked sessions
Run the diagnostic to list all blocking/blocked session pairs.

## Step 2: Kill the blocking session
Select the blocking row from the results, then click **Approve & Execute**.
The system will run:
```sql
ALTER SYSTEM KILL SESSION '{blocking_sid},{blocking_serial}' IMMEDIATE
```

## Caution
- Always kill the **blocking** session, not the blocked one
- Confirm with the application team before killing in production
