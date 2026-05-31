from agents.planner_agent import create_plan
from agents.executor_agent import execute_plan


def route_query(question):

    plan = create_plan(question)

    result = execute_plan(plan)

    return {
        "plan": plan,
        "result": result
    }