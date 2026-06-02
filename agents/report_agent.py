class ReportAgent:

    def generate_report(
        self,
        workflow
    ):

        report = []

        report.append(
            "SCHEMA REFRESH PLAN"
        )

        report.append(
            "=" * 60
        )

        report.append(
            f"Source Environment : {workflow.get('source_tns', workflow.get('source_env'))}"
        )

        report.append(
            f"Target Environment : {workflow.get('target_tns', workflow.get('target_env'))}"
        )

        report.append(
            f"Schema Name        : {workflow.get('schema_name')}"
        )

        report.append("")

        source = workflow.get(
            "source_schema",
            {}
        )

        target = workflow.get(
            "target_schema",
            {}
        )

        report.append(
            f"Source Database    : {source.get('database')}"
        )

        report.append(
            f"Target Database    : {target.get('database')}"
        )

        report.append("")

        report.append(
            f"Source Objects     : {source.get('object_count', 0)}"
        )

        report.append(
            f"Target Objects     : {target.get('object_count', 0)}"
        )

        report.append("")

        report.append(
            f"Risk Level         : {workflow.get('risk_level', 'NOT_EVALUATED')}"
        )

        report.append(
            f"Workflow Status    : {workflow.get('status')}"
        )

        report.append("")

        report.append(
            f"Approval Required  : {workflow.get('approval_required', False)}"
        )

        report.append(
            f"Drop Required      : {workflow.get('drop_required', False)}"
        )

        report.append("")

        if workflow.get(
            "approval_message"
        ):

            report.append(
                "APPROVAL MESSAGE"
            )

            report.append(
                "-" * 60
            )

            report.append(
                workflow["approval_message"]
            )

            report.append("")

        if workflow.get(
            "drop_script"
        ):

            report.append(
                "DROP SCRIPT"
            )

            report.append(
                "-" * 60
            )

            report.append(
                workflow["drop_script"]
            )

            report.append("")

        report.append(
            "EXECUTION PLAN"
        )

        report.append(
            "-" * 60
        )

        for step in workflow.get(
            "execution_plan",
            []
        ):

            report.append(
                f"• {step}"
            )

        report.append("")

        report.append(
            "EXPORT COMMAND"
        )

        report.append(
            "-" * 60
        )

        report.append(
            workflow.get(
                "expdp_command",
                "Not Generated"
            )
        )

        report.append("")

        report.append(
            "IMPORT COMMAND"
        )

        report.append(
            "-" * 60
        )

        report.append(
            workflow.get(
                "impdp_command",
                "Not Generated"
            )
        )

        report.append("")

        if workflow.get("errors"):

            report.append(
                "ERRORS"
            )

            report.append(
                "-" * 60
            )

            for error in workflow.get(
                "errors",
                []
            ):

                report.append(
                    f"• {error}"
                )

            report.append("")

        return "\n".join(
            report
        )