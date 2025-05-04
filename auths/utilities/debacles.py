from cryptography.fernet import Fernet
from ..models import Phone, Email

#will return
def phone_or_email(string):
    if string[1:].isnumeric() and string[0] == "+":
        return True
    elif "@" and "." in string:
        return False
    else:
        return None
