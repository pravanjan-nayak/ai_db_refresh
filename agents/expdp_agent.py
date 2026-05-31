from config.datapump_config import (
    DATAPUMP_DIRECTORY,
    DEFAULT_DUMP_EXTENSION,
    DEFAULT_EXPORT_LOG_SUFFIX
)


class ExpdpAgent:

    def generate_command(
        self,
        schema_name
    ):

        schema_name = schema_name.upper()

        dump_file = (
            schema_name +
            DEFAULT_DUMP_EXTENSION
        )

        log_file = (
            schema_name +
            DEFAULT_EXPORT_LOG_SUFFIX
        )

        command = (
            f"expdp system/password "
            f"schemas={schema_name} "
            f"directory={DATAPUMP_DIRECTORY} "
            f"dumpfile={dump_file} "
            f"logfile={log_file}"
        )

        return command