from workflows.sop_matcher import match_sop

test_inputs = [
    "how to kill session in oracle",
    "who is blocking my database session",
    "show invalid objects in schema HR",
    "show me top 2 index in size"
]

for item in test_inputs:
    result = match_sop(item)
    print("-" * 50)
    print("Input:", item)
    print("Matched:", result["matched"])
    print("Task:", result["task"])
    print("Route:", result["route"])
    print("Confidence:", result["confidence"])
    print("Description:", result["description"])
