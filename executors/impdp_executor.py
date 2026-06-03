from config.oracle_config import (
    IMPDP_PATH
)
import subprocess


class ImpdpExecutor:

    def run(self, username, password, tns_alias, schema_name, dumpfile=None):
        # Build default dumpfile name if not provided
        if dumpfile is None:
            dumpfile = f"{schema_name}.dmp"

        cmd = (
            f'"{IMPDP_PATH}" '
            f'{username}/{password}@{tns_alias} '
            f'schemas={schema_name} '
            f'directory=DATA_PUMP_DIR '
            f'dumpfile={dumpfile} '
            f'logfile={schema_name}_imp.log'
        )

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": cmd.replace(password, "***")
        }

    # Backwards-compatible execute API
    def execute(self, username, password, tns_alias, schema_name):
        return self.run(username, password, tns_alias, schema_name)