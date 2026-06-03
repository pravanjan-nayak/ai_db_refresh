FORBIDDEN = [
    "DROP",
    "TRUNCATE",
    "DELETE",
    "ALTER",
    "GRANT",
    "REVOKE"
]


def validate_sql(sql):

    sql_upper = sql.upper()

    for keyword in FORBIDDEN:

        if keyword in sql_upper:
            raise Exception(
                f"Unsafe SQL detected: {keyword}"
            )

    return True