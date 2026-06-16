from workflow_router import WorkflowRouter

router = WorkflowRouter()

test_inputs = [
    "show active sessions",
    "how to kill session in oracle",
    "who is blocking my database session",
    "show invalid objects in schema HR",
    "show me top 2 index in size",
    ""
]

for item in test_inputs:
    print("=" * 80)
    print("INPUT:", repr(item))

    result = router.route_query(item)

    print("success     :", result.get("success"))
    print("route       :", result.get("route"))
    print("task        :", result.get("task"))
    print("confidence  :", result.get("confidence"))
    print("error       :", result.get("error"))
    print("sql         :", result.get("sql"))
    print("explanation :", str(result.get("explanation"))[:500])

    if result.get("result"):
        print("result      :", result.get("result"))