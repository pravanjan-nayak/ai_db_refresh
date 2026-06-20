# NAME: create_tablespace
# TITLE: Oracle Database New Tablespace Creation & Verification SOP
# KEYWORDS: create tablespace, add new tablespace, make tablespace, provision storage tablespace
# DESCRIPTION: Automatically verifies storage availability, provisions a new tablespace, and returns the absolute data file path and max size limits upon completion.
# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_MODE: sequential
# STOP_ON_ERROR: true

# DIAGNOSTIC_SQL_START
SELECT 
    UPPER(:pdb_name) AS REQUESTED_TABLESPACE,
    CASE 
        WHEN (SELECT COUNT(*) FROM dba_tablespaces WHERE tablespace_name = UPPER(:pdb_name)) > 0 THEN 'FAIL: Tablespace already exists!'
        ELSE 'PASS: Name is available for allocation'
    END AS VALIDATION_STATUS,
    (SELECT SUBSTR(file_name, 1, INSTR(file_name, '/', -1)) FROM dba_data_files WHERE ROWNUM = 1) AS SUGGESTED_DATAFILE_DIR
FROM DUAL
# DIAGNOSTIC_SQL_END
# ACTION_TEMPLATE: CREATE TABLESPACE {REQUESTED_TABLESPACE} DATAFILE '{SUGGESTED_DATAFILE_DIR}{REQUESTED_TABLESPACE}01.dbf' SIZE 100M AUTOEXTEND ON NEXT 50M MAXSIZE 2G EXTENT MANAGEMENT LOCAL SEGMENT SPACE MANAGEMENT AUTO\n---\nSELECT f.tablespace_name, f.file_name AS physical_file_path, ROUND(f.bytes / (1024*1024), 2) AS current_size_mb, f.autoextensible, ROUND(f.maxbytes / (1024*1024), 2) AS max_size_mb FROM dba_data_files f WHERE f.tablespace_name = '{REQUESTED_TABLESPACE}'

## Purpose
This standard operating procedure automates the isolation, provisioning, and immediate operational verification of new data storage structures (Tablespaces) within an Oracle instance.