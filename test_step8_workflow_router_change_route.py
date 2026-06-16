from workflow_router import detect_change_request_route

test_inputs = [
    "add 10 gb datafile to USERS tablespace",
    "add datafile to USERS tablespace",
    "extend tablespace USERS by 5 gb",
    "show active sessions",
    "how to kill blocking session"
]

print("STEP 8 ROUTER TEST RESULT")
print("-" * 60)

for text in test_inputs:
    result = detect_change_request_route(text)
    print(f"INPUT: {text}")
    print(f"OUTPUT: {result}")
    print("-" * 60)