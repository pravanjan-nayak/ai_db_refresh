from langchain_community.chat_models import ChatOllama

llm = ChatOllama(
    model="llama3:instruct",
    temperature=0
)


def create_plan(question):

    prompt = f"""
You are an Oracle DBA planner.

Your job is to classify a DBA request.

Possible outputs:

DATABASE_STATUS
ACTIVE_SESSIONS
TOP_SQL
TABLESPACE_USAGE
EXPDP
RMAN

Return ONLY one value.

Question:
{question}
"""

    response = llm.invoke(prompt)

    return response.content.strip()