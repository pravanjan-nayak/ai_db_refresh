from config.oracle_config import (
    IMPDP_PATH
)
import subprocess

def run_impdp(
        username,
        password,
        service,
        schema,
        dumpfile):

    cmd = (
        f"impdp {username}/{password}@{service} "
        f"schemas={schema} "
        f"directory=DATA_PUMP_DIR "
        f"dumpfile={dumpfile}"
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
        "stderr": result.stderr
    }