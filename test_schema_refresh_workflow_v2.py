# test_schema_refresh_workflow_v2.py

from workflows.schema_refresh_workflow import (
    SchemaRefreshWorkflow
)

workflow = (
    SchemaRefreshWorkflow()
)

result = workflow.execute(
    source_tns="orclpdb",
    target_tns="uatagent",
    username="system",
    password="tiger",
    schema_name="HR",
    approved=True
)

print("\nSUCCESS")
print(result["success"])

print("\nVERIFICATION")
print(result["verification"])

print("\nSTATUS")
print(
    result["workflow"]["status"]
)

if result["errors"]:

    print("\nERRORS")

    print(
        result["errors"]
    )