# NAME: add_user
# TITLE: Oracle Database Add User and Assign Permissions SOP
# KEYWORDS: add user, create user, grant connect, oracle provisioning
# DESCRIPTION: Securely provisions a new user with baseline application developer roles and standard quotas.
# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_MODE: sequential
# STOP_ON_ERROR: true

# DIAGNOSTIC_SQL_START
SELECT 
    UPPER(:username) AS TARGET_USERNAME,
    CASE 
        WHEN COUNT(*) > 0 THEN 'FAIL: User already exists!'
        ELSE 'PASS: Username is not available'
    END AS VALIDATION_STATUS,
    COUNT(*) AS CURRENT_COUNT
FROM dba_users
WHERE username = UPPER(:username)
# DIAGNOSTIC_SQL_END

## Operational Summary
This SOP checks whether an Oracle schema already exists. If it passes (`VALIDATION_STATUS = PASS`), the automated deployment pipeline executes a sequence of statements to safely provision the profile, set an expiring password, and grant default developer roles.

## Automated Action Pipeline Sequence
# ACTION_SQL_START
CREATE USER {TARGET_USERNAME} IDENTIFIED BY "TempPass_2026!" PASSWORD EXPIRE DEFAULT TABLESPACE USERS
---
ALTER USER {TARGET_USERNAME} QUOTA 50M ON USERS
---
GRANT CONNECT, CREATE SESSION TO {TARGET_USERNAME}
---
GRANT CREATE TABLE, CREATE VIEW, CREATE SEQUENCE TO {TARGET_USERNAME}
# ACTION_SQL_END

## Verification Verification Checkpoints (Post-Execution)
1. Verify the account status is set to `EXPIRED` (forcing immediate user reset on first login):
   ```sql
   SELECT username, account_status, default_tablespace FROM dba_users WHERE username = '{TARGET_USERNAME}';