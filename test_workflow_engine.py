from workflow_engine import start_workflow

low = start_workflow(
    "health_check"
)

print("\nLOW RISK")
print(low)

critical = start_workflow(
    "schema_refresh"
)

print("\nCRITICAL RISK")
print(critical)