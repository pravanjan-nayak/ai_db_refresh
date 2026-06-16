from workflows.sop_matcher import match_sop

test_inputs = [
    "how to kill session in oracle",
    "who is blocking my session",
    "show invalid objects in HR",
    "show tablespace usage",
    "random custom request"
]

for item in test_inputs:
    result = match_sop(item)

    print("-" * 60)
    print("Input      :", item)
    print("Matched    :", result.get("matched"))
    print("Task       :", result.get("task"))
    print("Title      :", result.get("title"))
    print("Confidence :", result.get("confidence"))
    print("Description:", result.get("description"))
