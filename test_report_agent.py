from workflows.schema_refresh import (
    create_schema_refresh_plan
)

from agents.report_agent import (
    ReportAgent
)

workflow = create_schema_refresh_plan(
    "DEV",
    "UAT",
    "HR"
)

agent = ReportAgent()

report = agent.generate_report(
    workflow
)

print(report)