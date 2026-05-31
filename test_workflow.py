from workflow_router import route_query

question = "show me active sessions"

response = route_query(question)

print("\nPLAN:")
print(response["plan"])

print("\nRESULT:")
print(response["result"])