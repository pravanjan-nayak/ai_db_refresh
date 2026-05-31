from workflows.schema_refresh import (
    create_schema_refresh_plan
)

result = create_schema_refresh_plan(
    "DEV",
    "UAT",
    "HR"
)

print(result)