import oracledb

from config.oracle_config import TNS_ADMIN

oracledb.defaults.config_dir = TNS_ADMIN


def get_connection(
    username,
    password,
    tns_alias
):

    conn = oracledb.connect(
        user=username,
        password=password,
        dsn=tns_alias
    )

    return conn