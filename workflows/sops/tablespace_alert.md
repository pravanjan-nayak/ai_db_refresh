# ============================================================
# FILE:    workflows\sops\tablespace_alert.md
# ACTION:  REPLACE THE ENTIRE EXISTING FILE WITH THIS
# LOCATION: C:\AI Agents\OracleAIDBAAgent-main\OracleAIDBAAgent-main\workflows\sops\tablespace_alert.md
# ============================================================
# NAME: tablespace_alert
# TITLE: Tablespace Monitoring SOP
# KEYWORDS: tablespace usage, tablespace full, free space, tablespace alert, check tablespace, tablespace monitoring
# DESCRIPTION: Check tablespace usage and available free space.
# DIAGNOSTIC_SQL_START
SELECT tablespace_name,
       ROUND(used_space * 8192 / 1073741824, 2) AS used_gb,
       ROUND(tablespace_size * 8192 / 1073741824, 2) AS total_gb,
       ROUND(used_percent, 2) AS used_percent
FROM dba_tablespace_usage_metrics
ORDER BY used_percent DESC
# DIAGNOSTIC_SQL_END
# ACTION_REQUIRED: false
# APPROVAL_REQUIRED: false

# Tablespace Monitoring SOP

## Purpose
Check tablespace usage, free space, and identify tablespaces approaching capacity limits.

## Preconditions
- Ensure DBA privileges are available
- Confirm whether monitoring covers permanent, temporary, or undo tablespaces

## Step 1: Check tablespace usage
Run the diagnostic to see used GB, total GB, and usage percentage for all tablespaces.

## Step 2: Review results
- Tablespaces above 85% require immediate attention
- Consider adding a datafile or enabling autoextend

## Caution
- TEMP and UNDO tablespaces may show high usage under load — check active sessions first
