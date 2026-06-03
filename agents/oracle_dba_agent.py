# agents/oracle_dba_agent.py

import re

from langchain_community.chat_models import ChatOllama


class OracleDBAAgent:

    def __init__(self):

        self.llm = ChatOllama(
            model="llama3:instruct",
            temperature=0
        )

    def clean_sql(self, sql_text):

        if not sql_text:
            return ""

        sql = sql_text.strip()

        # Remove markdown code fences
        sql = re.sub(
            r"```sql",
            "",
            sql,
            flags=re.IGNORECASE
        )

        sql = re.sub(
            r"```",
            "",
            sql
        )

        sql = sql.strip()

        # Remove trailing semicolon
        if sql.endswith(";"):
            sql = sql[:-1]

        return sql.strip()

    def generate_sql(self, question):

        prompt = f"""
You are a Senior Oracle DBA.

Convert the user's request into a single executable Oracle SQL statement.

Rules:
1. Return ONLY SQL.
2. Do NOT explain anything.
3. Do NOT use markdown.
4. Do NOT use ```sql blocks.
5. Do NOT add comments.
6. Do NOT add a semicolon.
7. Return exactly one Oracle SQL statement.
8. Use Oracle data dictionary views when appropriate.

Examples:

Question:
show all tables in hr schema

Output:
SELECT table_name
FROM all_tables
WHERE owner = 'HR'

Question:
show active sessions

Output:
SELECT sid,
       serial#,
       username,
       status
FROM v$session
WHERE username IS NOT NULL

Question:
show invalid objects

Output:
SELECT owner,
       object_name,
       object_type
FROM dba_objects
WHERE status = 'INVALID'

User Question:
{question}
"""

        response = self.llm.invoke(prompt)

        sql = self.clean_sql(
            response.content
        )

        print("\n========== GENERATED SQL ==========")
        print(sql)
        print("===================================\n")

        return sql