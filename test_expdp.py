# test_expdp.py

from executors.expdp_executor import run_expdp

result = run_expdp(
    username="system",
    password="password",
    service="orclpdb",
    schema="HR",
    dumpfile="hr_test.dmp"
)

print(result)