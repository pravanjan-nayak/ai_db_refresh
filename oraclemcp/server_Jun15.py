from fastapi import FastAPI
from oraclemcp.registry import ToolRegistry
from oraclemcp.router import MCPRouter
from fastapi.middleware.cors import CORSMiddleware

from oraclemcp.tools.query_tool import query_tool



app = FastAPI(title="Oracle MCP Server")

registry = ToolRegistry()
router = MCPRouter(registry)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Temporary test tool (IMPORTANT FOR DEBUGGING)
def health_tool():
    return {"status": "MCP server running"}

registry.register("health", lambda: health_tool())
registry.register("query", query_tool)

@app.get("/")
def root():
    return {"message": "MCP Server is running"}


@app.post("/mcp/execute")
def execute_tool(request: dict):

    try:
        print(f"[SERVER] Request: {request}")

        result = router.handle(request)

        print(f"[SERVER] Result: {result}")

        return result

    except Exception as e:

        print(f"[SERVER ERROR] {e}")

        return {
            "success": False,
            "error": str(e)
        }