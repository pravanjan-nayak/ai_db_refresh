from config.oracle_config import (
    EXPDP_PATH
)

import subprocess


class ExpdpExecutor:

    def run(
        self,
        username,
        password,
        tns_alias,
        schema_name
    ):

        command = (
            f'"{EXPDP_PATH}" '
            f'{username}/{password}@{tns_alias} '
            f'schemas={schema_name} '
            f'directory=DATA_PUMP_DIR '
            f'dumpfile={schema_name}.dmp '
            f'logfile={schema_name}_exp.log'
        )

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command.replace(
                password,
                "***"
            )
        }