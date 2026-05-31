from tools.query_tool import QueryTool

tool = QueryTool()

result = tool.run("""
SELECT username
FROM dba_users
ORDER BY username
""")

print(result.head())