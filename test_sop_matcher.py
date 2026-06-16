from workflows.sop_matcher import match_sop

test_inputs = [
    "how to kill session in oracle",
    "who is blocking my session",
    "show active sessions",
    "show tablespace usage",
    "startup database",
    "clone database",
    "random custom request"
]

for item in test_inputs:
    result = match_sop(item)

    print("-" * 70)
    print("Input      :", item)
    print("Matched    :", result.get("matched"))
    print("Route      :", result.get("route"))
    print("Task       :", result.get("task"))
    print("Title      :", result.get("title"))
    print("Confidence :", result.get("confidence"))
    print("Description:", result.get("description"))