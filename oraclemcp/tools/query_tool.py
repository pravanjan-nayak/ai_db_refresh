from workflow_router import WorkflowRouter

router = WorkflowRouter()

def query_tool(question):
    try:
        print(f"[MCP] Received question: {question}")

        result = router.route_query(question)

        print(f"[MCP] Result: {result}")

        return result
    except Exception as e:
        print(f"[MCP] Error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
