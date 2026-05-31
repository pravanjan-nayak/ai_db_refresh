def requires_approval(risk_level):

    high_risk = [
        "HIGH",
        "CRITICAL"
    ]

    return risk_level in high_risk


def check_user_approval(user_input):

    if not user_input:
        return False

    return user_input.strip().upper() == "YES"