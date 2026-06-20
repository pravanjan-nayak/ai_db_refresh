# ============================================================
# Oracle MCP Server 
#
# Updates:
#   - Registered functions directly instead of fragile lambdas.
#   - Added an automatic markdown block extractor inside sop_execute_tool
#     to catch 'action_template: None' payloads by mining the 'content' string.
#   - Added safe handling (**kwargs) to prevent unexpected key exceptions.
# ============================================================

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

# ── Existing tools (unchanged) ───────────────────────────────────────────────

def health_tool():
    return {"status": "MCP server running"}

registry.register("health", health_tool)
registry.register("query", query_tool)


# ── SOP Diagnostic Tool ───────────────────────────────────────────────────────

def sop_diagnose_tool(question: str, **kwargs):
    try:
        from workflows.sop_matcher import match_sop
        from workflows.sop_executor import run_sop_diagnostic

        match = match_sop(question)

        if not match.get("matched"):
            return {
                "success": False,
                "route": "sop",
                "error": "No SOP matched for this question.",
                "rows": [],
                "columns": [],
                "row_count": 0
            }

        sop_content = match.get("content", "")
        sop_name = match.get("task", "unknown")

        result = run_sop_diagnostic(
            sop_name=sop_name, 
            content=sop_content, 
            question=question
        )

        # Add SOP match metadata for the frontend layer
        result["route"] = "sop"
        result["matched"] = True
        result["title"] = match.get("title")
        result["confidence"] = match.get("confidence")
        result["sop_content"] = sop_content

        return result

    except Exception as e:
        import traceback
        return {
            "success": False,
            "route": "sop",
            "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
            "rows": [],
            "columns": [],
            "row_count": 0
        }

registry.register("sop_diagnose", sop_diagnose_tool)


# ── SOP Execute Tool ─────────────────────────────────────────────────────────

def sop_execute_tool(action_template: str = None, selected_row: dict = None, sop_name: str = None, approved_by: str = "DBA", **kwargs):
    try:
        from workflows.sop_executor import run_sop_action

        # FIX: Parse the action SQL block out of markdown if action_template is missing/None
        if not action_template and "content" in kwargs and kwargs["content"]:
            raw_content = kwargs["content"]
            if "# ACTION_SQL_START" in raw_content and "# ACTION_SQL_END" in raw_content:
                try:
                    parts = raw_content.split("# ACTION_SQL_START")
                    action_block = parts[1].split("# ACTION_SQL_END")[0]
                    action_template = action_block.strip()
                    print(f"[SERVER SERVER-FIX] Successfully extracted fallback action_template from markdown configuration text.")
                except Exception as parse_err:
                    print(f"[SERVER ERROR] Failed parsing fallback template from content: {parse_err}")

        # Fail safely if neither strategy extracted valid templates
        if not action_template:
            return {
                "success": False,
                "route": "sop",
                "error": "Execution aborted: The action_template argument was None and fallback markdown extraction failed.",
                "action_sql": "",
                "message": "No valid SQL pipeline instructions located."
            }

        # Dispatch string template payload to execution worker
        result = run_sop_action(
            action_template=action_template,
            selected_row=selected_row,
            sop_name=sop_name,
            approved_by=approved_by,
        )
        result["route"] = "sop"
        return result

    except Exception as e:
        import traceback
        return {
            "success": False,
            "route": "sop",
            "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
            "action_sql": "",
            "message": "Action execution failed."
        }

registry.register("sop_execute", sop_execute_tool)


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "MCP Server is running"}


@app.post("/mcp/execute")
def execute_tool(request: dict):
    try:
        print(f"[SERVER] Incoming Request: {request}")
        result = router.handle(request)
        print(f"[SERVER] Outgoing Result: {result}")
        return result
    except Exception as e:
        print(f"[SERVER ERROR] Execution handler failed: {e}")
        return {"success": False, "error": str(e)}