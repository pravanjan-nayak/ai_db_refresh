from config.environments import get_environment

print(get_environment("DEV"))

print(get_environment("PROD"))

print(get_environment("TEST"))

print(get_environment("UAT"))