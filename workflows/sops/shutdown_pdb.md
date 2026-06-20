# NAME: pdb_startup_shutdown
# TITLE: Pluggable Database (PDB) Startup and Shutdown Lifecycle SOP
# KEYWORDS: shutdown pdb, restart pdb, bounce pdb, close pluggable database, close pdb
# DESCRIPTION: Real-time automated connection verification, state validation, and lifecycle cycling of a specific Pluggable Database (PDB).
# DIAGNOSTIC_SQL_START
SELECT 
    p.con_id,
    p.name AS pdb_name,
    p.open_mode,
    p.restricted,
    (SELECT COUNT(*) FROM v$session s WHERE s.con_id = p.con_id AND s.type = 'USER' AND s.status = 'ACTIVE') AS active_user_sessions,
    (SELECT COUNT(*) FROM v$session s WHERE s.con_id = p.con_id AND s.type = 'USER') AS total_connected_users
FROM v$pdbs p
# DIAGNOSTIC_SQL_END
# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_TEMPLATE: ALTER PLUGGABLE DATABASE {PDB_NAME} CLOSE IMMEDIATE

# Pluggable Database (PDB) Startup and Shutdown SOP

## Purpose
This standard operating procedure provides a highly reliable, real-time automated workflow to evaluate user session counts, securely close, and subsequently open an Oracle Pluggable Database (PDB) without impacting neighboring tenants within the same Container Database (CDB).

## Preconditions & Safety Thresholds
1. **Target Identification:** Verify that your workspace data grid targets the specific Pluggable Database intended for maintenance, and not the root container (`CDB$ROOT`).
2. **Downtime Authorization:** Confirm that application owners tied explicitly to this pluggable container schema have suspended incoming jobs, application connections, and scheduled batch pools.

---

## Operational Execution Steps

### Step 1: Execute Real-Time PDB Diagnostic
Click the **"▶ Run Live Diagnostic on Oracle"** button inside the interactive AI Assistant dashboard.
- Analyze the `OPEN_MODE`, `ACTIVE_USER_SESSIONS`, and `TOTAL_CONNECTED_USERS` columns returned in the visual data grid table.
- **Go / No-Go Criteria:** If `ACTIVE_USER_SESSIONS` shows a count greater than `0`, check with application pools before executing. The automated button uses a fallback `CLOSE IMMEDIATE` directive to safely terminate lagging transactions if needed, but draining connections gracefully first is ideal.

### Step 2: Automated PDB Shutdown (Real-Time UI Execution)
Once you are ready to take the Pluggable Database offline for structural maintenance, schema tracking updates, or isolation tasks:
1. Select the target PDB checkbox row in your dashboard data grid.
2. Click **"🚀 Approve & Execute"**.
3. **What happens under the hood:** The framework reads the metadata template and issues:
   ```sql
   ALTER PLUGGABLE DATABASE {PDB_NAME} CLOSE IMMEDIATE;