from executors.expdp_executor import ExpdpExecutor

def expdp_tool(username, password, tns_alias, schema_name):

    executor = ExpdpExecutor()

    return executor.execute(
        username=username,
        password=password,
        tns_alias=tns_alias,
        schema_name=schema_name
    )