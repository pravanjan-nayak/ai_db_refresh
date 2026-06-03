from oraclemcp.registry import ToolRegistry


class MCPRouter:

    def __init__(self, registry):
        self.registry = registry

    def handle(self, request):

        tool = request.get("tool")
        params = request.get("params", {})

        return self.registry.execute(tool, params)