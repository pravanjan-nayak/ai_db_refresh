# NAME: add_user
# TITLE: Oracle Database Add User and Assign Permissions SOP
# KEYWORDS: add user, create user, new user, assign privileges, grant access, create oracle user, user permissions, add database user, grant connect, grant read, grant write, create user dummy
# DESCRIPTION: Create a new Oracle database user and assign appropriate privileges based on an approved request.

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

# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_TEMPLATE: CREATE USER {TARGET_USERNAME} IDENTIFIED BY "TempPass_2026!" PASSWORD EXPIRE DEFAULT TABLESPACE USERS QUOTA 50M ON USERS

# Oracle Database – Add User and Assign Permissions SOP
**Version:** 2.0  |  **Ticket Type:** Automated Provisioning Request

---

## Purpose
Create a new user in an Oracle Database automatically. Ensures controlled access provisioning in compliance with security and operational standards.

---

## Automated Execution Instructions
1. Run the live diagnostic query above to confirm availability.
2. Review the generated validation data panel row.
3. If **VALIDATION_STATUS** reads `PASS: Username is not available`,select the row checkbox in the interactive UI.
4. Click **"Approve & Execute"** to instantly build and apply your missing user profile configurations.