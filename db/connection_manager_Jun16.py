import oracledb

from config.environments import get_environment
from config.oracle_config import TNS_ADMIN

# Tell python-oracledb where tnsnames.ora is located
oracledb.defaults.config_dir = TNS_ADMIN


def get_connection(env_name):

    env = get_environment(env_name)

    if not env:
        raise Exception(
            f"Unknown environment: {env_name}"
        )

    conn = oracledb.connect(
        user="system",
        password="tiger",
        dsn=env["tns"]
    )

    return conn