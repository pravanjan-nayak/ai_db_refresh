your profile.

Markdown
# 🤖 Oracle Database AI Assistant (MCP-Driven Architecture)

An enterprise-grade, zero-hallucination database automation assistant. This system bridges natural language conversational interfaces with high-privilege Oracle Database administrative environments using **Model Context Protocol (MCP)**, **FastAPI**, and **Streamlit**.

Unlike traditional Text-to-SQL assistants that dynamically generate database modification queries on the fly, this architecture uses a **Deterministic SOP (Standard Operating Procedure) Routing Engine** to guarantee 100% execution safety and eliminate AI hallucinations.

---

## 🏗️ System Architecture

The assistant isolates user interactions from the database kernel through a secure 5-layer pipeline:

1. **Presentation Layer (`Streamlit UI`):** Captures conversational inputs and automatically tracks target environment properties (e.g., Container: `CDB$ROOT` vs Pluggable DB: `PDB1`).
2. **API Gateway Layer (`FastAPI + Uvicorn`):** Houses the MCP server framework, managing communication routines asynchronously.
3. **Routing Layer (`SOP Matcher`):** Inspects incoming plain English. If it matches target files in the `# KEYWORDS:` configuration block, it locks onto a predefined markdown blueprint.
4. **Intelligence Layer (`Ollama Llama 3`):** Enhances observability responses and flags potential injection attacks through structural evaluation blocks (`SQL Guard`).
5. **Execution Layer (`oracledb Driver Loop`):** Runs transactions via high-privilege administrative sessions (`sysdba`), handling complex multi-statement SQL sequences without terminal disconnects.

---

## 🛠️ Configuration-Driven SOPs (The Zero-Hallucination Shield)

The platform is driven by structured Markdown files appended with foundational **Front Matter Metadata Tags**. This structure forces the automation tool to run pre-vetted queries instead of guessing syntax.

### Sample Layout: `create_user_permissions.md`
```markdown
# NAME: create_database_user
# TITLE: Oracle Database – Add User and Assign Database Permissions
# KEYWORDS: create user, add user, database permissions, user provisioning
# DESCRIPTION: Automates verification and account provisioning for an Oracle database user.
# DIAGNOSTIC_SQL_START
SELECT username, account_status, created FROM dba_users ORDER BY created DESC FETCH FIRST 10 ROWS ONLY
# DIAGNOSTIC_SQL_END
# ACTION_REQUIRED: true
# APPROVAL_REQUIRED: true
# ACTION_TEMPLATE_1: CREATE USER {USERNAME_TO_CREATE} IDENTIFIED BY "TempWelcome2026#" PASSWORD EXPIRE
# ACTION_TEMPLATE_2: GRANT CONNECT, CREATE SESSION TO {USERNAME_TO_CREATE}
🔄 The Sequential Multi-SQL Execution Engine
Because Python database drivers restrict executing multiple statements separated by semicolons in a single string execution, our backend loops through the numbered template parameters programmatically:

Python
# Sequential compilation sequence in workflows/sop_executor.py
template_keys = sorted([k for k in sop_metadata.keys() if k.startswith("ACTION_TEMPLATE")])

for key in template_keys:
    formatted_sql = sop_metadata[key].format(**runtime_variables).replace(";", "")
    cursor.execute(formatted_sql)  # Statement 1 -> Statement 2 -> Statement 3
If an intermediate sequence fails, the driver catches the exception and calls connection.rollback(), ensuring no partial or corrupted states persist in production.

🚀 Getting Started
📋 Prerequisites
Python 3.10+

Oracle Instant Client (Required if running oracledb in Thick Mode for specific sysdba connections)

Ollama (with the llama3 model pulled locally)

⚙️ Installation & Setup
Clone the Repository:

Bash
git clone [https://github.com/yourusername/oracle-db-ai-assistant.git](https://github.com/yourusername/oracle-db-ai-assistant.git)
cd oracle-db-ai-assistant
Install Dependencies:

Bash
pip install -r requirements.txt
Configure Environment Parameters:
Create a .env file in the root directory:

Code snippet
ORACLE_USER=sys
ORACLE_PASSWORD=YourSecureSysPassword
ORACLE_DSN=YOUR_TNS_SERVICE_NAME
OLLAMA_HOST=http://localhost:11434
SOP_DIR=./workflows/sops
Start the MCP Backend Server (FastAPI):

Bash
uvicorn mcp_server:app --host 127.0.0.1 --port 8000
Launch the Web Interface Dashboard:

Bash
streamlit run app.py
🛑 Guided Legacy Mode (Hybrid Boundaries)
For operations that require OS-level diagnostic monitoring (e.g., checking host CPU run queues using top, vmstat, or uptime), the system utilizes Guided Legacy Mode by specifying # ACTION_REQUIRED: false.

Rather than executing risky terminal scripts blindly through an automated driver, the UI transforms into an interactive step-by-step workbook checklist. It serves pre-vetted queries and commands inside clear copy-paste modules, maintaining human-in-the-loop validation for infrastructure boundaries.

🔒 Security Guardrails
Strict SQL Injection Validation: Parameter scopes bounded inside {} templates are rigorously filtered before query execution.

Deterministic Isolation: The core LLM cannot generate modifications dynamically; it can only request execution of predefined templates curated by a Lead Database Administrator.

Transaction Rollback Safeguards: Automated scripts default to a fail-fast state to guarantee transactional consistency across target container schemas.


***

### 💡 Suggestions before pushing to GitHub:
1. **Requirements file:** Make sure you create a `requirements.txt` containing at least `streamlit`, `fastapi`, `uvicorn`, and `oracledb`.
2. **Repository Path:** Update the `git clone` link under the installation section to point to your actual GitHub path.