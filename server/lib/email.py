from email_validator import validate_email, EmailNotValidError

def normalize_email(email: str) -> str:
    try:
        return validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        return ""