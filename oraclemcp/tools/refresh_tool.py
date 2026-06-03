from workflows.schema_refresh_workflow import SchemaRefreshWorkflow

def refresh_tool(**params):

    wf = SchemaRefreshWorkflow()

    return wf.execute(**params)