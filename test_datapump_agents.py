from agents.expdp_agent import ExpdpAgent
from agents.impdp_agent import ImpdpAgent

exp = ExpdpAgent()

imp = ImpdpAgent()

print("\nEXPDP")

print(
    exp.generate_command("HR")
)

print("\nIMPDP")

print(
    imp.generate_command("HR")
)