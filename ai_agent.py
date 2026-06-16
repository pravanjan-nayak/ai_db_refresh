from langchain_community.chat_models import ChatOllama
import re
import json

try:
    import pandas as pd
except ImportError:
    pd = None


# ---------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------
llm = ChatOllama(
    model="llama3:instruct",
    # model="llama3.1",
    temperature=0
)


# ---------------------------------------------------------
# Helper: Convert result into LLM-friendly compact text
# ---------------------------------------------------------
def _format_result_for_llm(data, max_rows=20):
    """
    Convert DB result into a compact JSON/text form for explanation.
    Supports pandas DataFrame, list, dict, or plain text.
    """
    try:
        if pd is not None and isinstance(data, pd.DataFrame):
            if data.empty:
                return "[]"
            return data.head(max_rows).to_json(orient="records", default_handler=str)

        if isinstance(data, list):
            if not data:
                return "[]"
            return json.dumps(data[:max_rows], default=str, indent=2)

        if isinstance(data, dict):
            return json.dumps(data, default=str, indent=2)

        if data is None:
            return "[]"

        return str(data)

    except Exception as e:
        return f"Unable to format result: {str(e)}"


# ---------------------------------------------------------
# Explain successful query result
# ---------------------------------------------------------
def explain_result(question, data):
    """
    Explain returned database result in a grounded DBA-oriented way.
    Only explains what is visible in the result.
    """
    formatted_data = _format_result_for_llm(data)

    prompt = f"""
You are an Oracle DBA assistant.

User question:
{question}

Database result:
{formatted_data}

Rules:
1. Explain ONLY using the database result provided above.
2. Do NOT assume missing rows, columns, or facts.
3. If the result is empty, reply exactly: No rows matched the query.
4. Keep the answer concise, clear, and DBA-focused.
5. Do not invent Oracle objects or additional context.

Provide a short and practical explanation.
"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip() if response and response.content else ""

        print("\n===== LLM RESPONSE =====")
        print(content if content else "[EMPTY RESPONSE]")
        print("========================\n")

        if content:
            return content

        if formatted_data == "[]":
            return "No rows matched the query."

        return "Query executed successfully. Please review the returned rows."

    except Exception as e:
        print("\n===== LLM ERROR IN explain_result =====")
        print(str(e))
        print("=======================================\n")

        if formatted_data == "[]":
            return "No rows matched the query."

        return "Query executed successfully. Please review the returned rows."


# ---------------------------------------------------------
# Explain unmatched / failed fallback query
# ---------------------------------------------------------
def explain_unmatched_or_failed_query(user_question, generated_sql=None, db_error=None):
    """
    Provide DBA-oriented explanation when:
    - the user question does not match predefined repository/tasks
    - or LLM-generated SQL fails
    - or fallback cannot determine correct query

    This is useful instead of showing only raw Oracle execution errors.
    """
    prompt = f"""
You are an expert Oracle DBA assistant.

The user's request did not match the predefined DBA repository exactly,
or the generated SQL failed during execution.

User question:
{user_question}

Generated SQL:
{generated_sql if generated_sql else "N/A"}

Database error:
{db_error if db_error else "N/A"}

Your job:
1. Politely explain that the input is not matched exactly to the predefined DBA repository.
2. Interpret what the user likely means from an Oracle DBA point of view.
3. Explain the Oracle concept briefly in simple language.
4. If possible, suggest a corrected SQL/query approach.
5. Do NOT pretend the failed SQL is correct.
6. Keep the answer practical, concise, and DBA-focused.

Preferred response style:
- Start with: "Your input is not currently matched to the predefined DBA repository."
- Then explain likely DBA meaning.
- Then explain how Oracle DBAs usually handle it.
- Then provide a corrected example query if possible.
"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip() if response and response.content else ""

        print("\n===== LLM FALLBACK EXPLANATION =====")
        print(content if content else "[EMPTY RESPONSE]")
        print("====================================\n")

        if content:
            return content

    except Exception as e:
        print("\n===== LLM ERROR IN explain_unmatched_or_failed_query =====")
        print(str(e))
        print("==========================================================\n")

    # Static fallback if LLM fails
    return (
        "Your input is not currently matched to the predefined DBA repository. "
        "From an Oracle DBA perspective, this looks like a custom analysis request. "
        "The generated SQL could not be executed successfully, so please review the "
        "appropriate Oracle data dictionary views and use the correct metadata source "
        "for this requirement."
    )


# ---------------------------------------------------------
# Schema extractor
# ---------------------------------------------------------
def extract_schema(question, default="HR"):
    q = question.lower()

    # match "backup HR schema" or "export HR schema"
    m = re.search(r"(backup|export)\s+([a-zA-Z0-9_]+)", q)
    if m:
        return m.group(2).upper()

    # match "HR schema"
    m2 = re.search(r"([a-zA-Z0-9_]+)\s+schema", q)
    if m2:
        return m2.group(1).upper()

    return default.upper()


# ---------------------------------------------------------
# Generate expdp command
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Generate RMAN full backup command
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Generic DBA reasoning answer for non-SQL questions
# ---------------------------------------------------------
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

    try:
        response = llm.invoke(prompt)
        return response.content.strip() if response and response.content else (
            "This appears to be a DBA reasoning question. Please review Oracle dictionary views, "
            "monitoring steps, and best practices relevant to the request."
        )

    except Exception as e:
        print("\n===== LLM ERROR IN dba_reasoning_answer =====")
        print(str(e))
        print("=============================================\n")

        return (
            "This appears to be a DBA reasoning question. Please review Oracle dictionary views, "
            "monitoring steps, and best practices relevant to the request."
        )


# ---------------------------------------------------------
# (Edge browser metadata below — ignored by Python)
# ---------------------------------------------------------
