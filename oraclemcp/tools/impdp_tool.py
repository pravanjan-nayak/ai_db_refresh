from executors.impdp_executor import ImpdpExecutor

def impdp_tool(username, password, tns_alias, schema_name):

    executor = ImpdpExecutor()

    return executor.execute(
        username=username,
        password=password,
        tns_alias=tns_alias,
        schema_name=schema_name
    )