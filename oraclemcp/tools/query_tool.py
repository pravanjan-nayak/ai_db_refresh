from workflow_router import WorkflowRouter

router = WorkflowRouter()

def query_tool(question):
    return router.route_query(question)

##added temprarily for testing - will remove later
from workflow_router import WorkflowRouter

router = WorkflowRouter()

def query_tool(question):
    print(f"[MCP] Received question: {question}")

    result = router.route_query(question)

    print(f"[MCP] Result: {result}")

    return result