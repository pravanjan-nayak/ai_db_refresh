# NAME: convert_noncdb_to_pdb
# TITLE: Oracle L3 Dynamic Non-CDB to PDB Conversion via DB Link
# KEYWORDS: convert non-cdb, migrate non-cdb to pdb, adopt non-cdb, plug database
# DESCRIPTION: Dynamically creates a transient DB Link from the CDB to any target standalone non-CDB, clones its structure natively, plugs it in as a managed PDB, and verifies status.
# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_MODE: sequential
# STOP_ON_ERROR: true

# DIAGNOSTIC_SQL_START
SELECT 
    UPPER(NVL(:pdb_name, 'UATAGENT')) AS SOURCE_NONCDB,
    'localhost:1521/' || LOWER(NVL(:pdb_name, 'UATAGENT')) AS DYNAMIC_CONNECTION_STRING,
    CASE 
        WHEN (SELECT cdb FROM v$database) = 'YES' THEN 'PASS: Connected to CDB. Ready to route remote pull for ' || UPPER(NVL(:pdb_name, 'UATAGENT'))
        ELSE 'FAIL: Wrong execution context. This SOP must be executed from the primary CDB.'
    END AS VALIDATION_STATUS
FROM DUAL
# DIAGNOSTIC_SQL_END
# ACTION_TEMPLATE: CREATE PUBLIC DATABASE LINK temp_migrate_link CONNECT TO sys IDENTIFIED BY "Athu!2023" USING '{DYNAMIC_CONNECTION_STRING}'
# ---
# CREATE PLUGGABLE DATABASE {SOURCE_NONCDB} FROM NON_CDB@temp_migrate_link FILE_NAME_CONVERT = NONE COPY
# ---
# DROP PUBLIC DATABASE LINK temp_migrate_link
# ---
# ALTER PLUGGABLE DATABASE {SOURCE_NONCDB} OPEN READ WRITE
# ---
# SELECT name, open_mode, total_size, recovery_status FROM v$pdbs WHERE name = '{SOURCE_NONCDB}'