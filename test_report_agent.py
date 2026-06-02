from workflows.schema_refresh import (
    create_schema_refresh_plan
)

workflow = create_schema_refresh_plan(
    source_tns="orclpdb",
    target_tns="uatagent",
    username="system",
    password="tiger",
    schema_name="HR"
)

print(workflow["report"])