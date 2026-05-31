import json
import re

from langchain_community.chat_models import ChatOllama


llm = ChatOllama(
    model="llama3:instruct",
    temperature=0
)


def create_workflow(question):

    prompt = f"""
You are an Oracle DBA workflow planner.

For schema refresh requests return JSON.

Example:

{{
  "workflow": "schema_refresh",
  "steps": [
    "validate_source",
    "export_schema",
    "import_schema",
    "validate_target"
  ]
}}

Question:
{question}

Return JSON only.
"""

    response = llm.invoke(prompt)

    raw_text = response.content

    print("RAW RESPONSE:")
    print(raw_text)

    # Extract JSON block
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)

    if not match:
        raise Exception(
            f"No JSON found in response:\n{raw_text}"
        )

    json_text = match.group()

    return json.loads(json_text)