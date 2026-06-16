# ============================================================
# FILE:    oraclemcp\server.py
# ACTION:  REPLACE THE ENTIRE EXISTING FILE WITH THIS
# LOCATION: C:\AI Agents\OracleAIDBAAgent-main\OracleAIDBAAgent-main\oraclemcp\server.py
#
# What changed vs your original:
#   - Fixed the incorrect syntax where tuples were being passed into run_sop_diagnostic
#   - Now correctly passes dynamic parameters (sop_name, sop_content, question)
#   - Preserved all other existing tool routes and FastAPI endpoint bindings
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

registry.register("health", lambda: health_tool())
registry.register("query", query_tool)


# ── NEW: SOP Diagnostic Tool ─────────────────────────────────────────────────
# Runs the DIAGNOSTIC_SQL from the matched SOP .md file against real Oracle.
# Returns live rows. No action is taken yet.

def sop_diagnose_tool(question: str):
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

        # Fixed: Now passes variables directly into the parameters instead of string tuples
        result = run_sop_diagnostic(
            sop_name=sop_name, 
            content=sop_content, 
            question=question
        )

        # Add SOP match info for the UI
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


registry.register("sop_diagnose", lambda question: sop_diagnose_tool(question))


# ── NEW: SOP Execute Tool ─────────────────────────────────────────────────────
# Fires the action SQL only after DBA clicks Approve in the UI.

def sop_execute_tool(action_template: str, selected_row: dict, sop_name: str, approved_by: str = "DBA"):
    try:
        from workflows.sop_executor import run_sop_action

        result = run_sop_action(
            action_template=action_template,
            selected_row=selected_row,
            sop_name=sop_name,
            approved_by=approved_by
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


registry.register(
    "sop_execute",
    lambda action_template, selected_row, sop_name, approved_by="DBA":
        sop_execute_tool(action_template, selected_row, sop_name, approved_by)
)


# ── FastAPI endpoints (unchanged) ────────────────────────────────────────────

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
        return {"success": False, "error": str(e)}