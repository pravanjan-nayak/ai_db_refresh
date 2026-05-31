ENVIRONMENTS = {

    "DEV": {

        "tns": "orclpdb",

        "risk": "LOW"
    },

    "UAT": {

        "tns": "uatagent",

        "risk": "MEDIUM"
    },

    "PROD": {

        "tns": "prod",

        "risk": "CRITICAL"
    }
}


def get_environment(
    env_name
):

    return ENVIRONMENTS.get(
        env_name.upper()
    )