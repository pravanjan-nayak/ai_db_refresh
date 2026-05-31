from db.connection_manager import (
    get_connection
)

for env in [

    "DEV",

    "UAT"

]:

    conn = get_connection(
        env
    )

    cursor = conn.cursor()

    cursor.execute(
        "select name from v$database"
    )

    result = cursor.fetchone()

    print(
        env,
        result[0]
    )

    conn.close()