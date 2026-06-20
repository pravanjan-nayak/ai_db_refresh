# NAME: startup_pdb
# TITLE: Oracle Database Pluggable Database (PDB) Startup SOP
# KEYWORDS: startup pdb, open pdb, start pluggable database, alter pluggable database open, open pluggable database, open pdb
# DESCRIPTION: Safely opens a closed or mounted Pluggable Database (PDB) to read-write mode.
# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_MODE: sequential
# STOP_ON_ERROR: true
# DB_CONTEXT: CDB_ROOT

# DIAGNOSTIC_SQL_START
SELECT
    SYS_CONTEXT('USERENV','CON_NAME') AS CONNECTED_CONTAINER,
    name AS TARGET_PDB,
    open_mode AS CURRENT_OPEN_MODE,
    CASE
        WHEN open_mode = 'READ WRITE' THEN 'INFO: PDB already open (no action needed)'
        ELSE 'PASS: PDB can be started'
    END AS VALIDATION_STATUS
FROM v$pdbs
WHERE name <> 'PDB$SEED'
ORDER BY name
# DIAGNOSTIC_SQL_END

## Operational Summary
This SOP lists every pluggable database (except the seed) with its current open mode,
so the operator can select the PDB to start. For a PDB that is not already in READ WRITE
mode, the action pipeline opens it and then saves its open state so the change survives a
future restart of the container database. All commands run from the CDB root, because a
closed PDB's own service is not available to connect to directly.

## Automated Action Pipeline Sequence
# ACTION_SQL_START
BEGIN
  EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE {TARGET_PDB} OPEN READ WRITE';
END;
---
BEGIN
  EXECUTE IMMEDIATE 'ALTER PLUGGABLE DATABASE {TARGET_PDB} SAVE STATE';
END;
---
SELECT name, open_mode, restricted FROM v$pdbs WHERE name = '{TARGET_PDB}'
# ACTION_SQL_END

## Verification Checkpoints (Post-Execution)
1. Confirm the selected PDB now reports OPEN_MODE = READ WRITE (the final step re-queries v$pdbs).
2. The SAVE STATE step ensures the PDB will re-open automatically the next time the CDB restarts.
3. If a PDB that was already open is selected, Oracle returns ORA-65019 (already open) — this is expected and harmless.