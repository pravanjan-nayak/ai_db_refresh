import json
import re
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(
    model="llama3:instruct",
    temperature=0
)

def create_plan(question):
    prompt = f"""
You are an Oracle DBA planner.
Your job is to analyze a DBA request, classify it, and extract any database or PDB names provided in the query.

Possible Categories:
DATABASE_STATUS
ACTIVE_SESSIONS
TOP_SQL
TABLESPACE_USAGE
CONVERT_NONCDB_TO_PDB
EXPDP
RMAN

You must return a valid JSON object ONLY, with exactly two keys: "category" and "pdb_name". Do not include markdown code blocks or any extra text.

Question:
{question}
"""

    response = llm.invoke(prompt)
    clean_content = response.content.strip()
    
    try:
        # Try parsing the clean LLM response
        return json.loads(clean_content)
    except Exception:
        # 🚀 BULLETPROOF BACKUP: If JSON parsing fails, use regex directly on the user's original question
        match = re.search(r"(?:convert non-cdb to pdb|migrate)\s+(\w+)", question, re.IGNORECASE)
        extracted_name = match.group(1).upper() if match else "UNKNOWN"
        
        return {
            "category": "CONVERT_NONCDB_TO_PDB", 
            "pdb_name": extracted_name
        }