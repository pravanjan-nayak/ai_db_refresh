from agents.planner_agent import create_plan


question = "show me all active users"

plan = create_plan(question)

print(plan)