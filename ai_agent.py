from langchain_community.chat_models import ChatOllama
import re

llm = ChatOllama(
    model="llama3:instruct",
    #model='llama3.1',
    temperature=0
)



def explain_result(question, data):

    prompt = f"""
You are an Oracle DBA assistant.

User question:
{question}

Database result:
{data}

Explain the result clearly for a DBA.
"""

    response = llm.invoke(prompt)

    # Print to command line
    print("\n===== LLM RESPONSE =====")
    print(response.content)
    print("========================\n")

    return response.content

### schema extractor + expdp generator + RMAN generator



def extract_schema(question, default="HR"):
    q = question.lower()
    # match "backup HR schema" or "export HR schema"
    m = re.search(r'(backup|export)\s+([a-zA-Z0-9_]+)', q)
    if m:
        return m.group(2).upper()

    # match "HR schema"
    m2 = re.search(r'([a-zA-Z0-9_]+)\s+schema', q)
    if m2:
        return m2.group(1).upper()

    return default.upper()


def generate_expdp_command(question):
    schema = extract_schema(question)

    command = f"""
expdp {schema}/{schema} DIRECTORY=DATA_PUMP_DIR \\
DUMPFILE={schema.lower()}_full_backup.dmp \\
LOGFILE={schema.lower()}_full_backup.log \\
SCHEMAS={schema}
""".strip()

    explanation = (
        f"This command performs a full logical backup of the {schema} schema using Oracle Data Pump (expdp). "
        "Run it from the OS on the database server or a client with access to DATA_PUMP_DIR."
    )

    return {
        "type": "logical_backup",
        "schema": schema,
        "command": command,
        "explanation": explanation
    }


def generate_rman_full_backup_command(question):
    command = """
rman target /

BACKUP DATABASE PLUS ARCHIVELOG
  FORMAT '/u01/backup/full_db_%d_%T_%U.bkp'
  TAG 'FULL_DB_BACKUP';
""".strip()

    explanation = (
        "This RMAN script performs a full physical backup of the entire database plus archivelogs. "
        "Run it from RMAN on the database server and adjust the FORMAT path to your backup location."
    )

    return {
        "type": "physical_backup",
        "command": command,
        "explanation": explanation
    }


def dba_reasoning_answer(question):
    prompt = f"""
You are an expert Oracle DBA.

The user is asking a natural-language DBA question that does not map to a predefined SQL task.

Provide:
1. A clear DBA explanation
2. SQL queries if needed
3. Steps to check or monitor
4. Best practices

User question:
{question}
"""

    response = llm.invoke(prompt)

    return response.content

# ---------------------------------------------------------
# (Edge browser metadata below — ignored by Python)
# ---------------------------------------------------------