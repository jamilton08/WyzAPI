def authenticate(email_or_phone_number):
    from .utilities.debacles import phone_or_email
    from .models import Phone, Email
    if email_or_phone_number is None:
        return None
    if phone_or_email(email_or_phone_number):
        if email_or_phone_number[0] != "+":
            email_or_phone_number = "+" + email_or_phone_number
            print(email_or_phone_number)
        p = Phone.objects.filter(phone_number = email_or_phone_number).first()
        if p is None:
            return None
        else:
            return p.user

    elif phone_or_email(email_or_phone_number) == False:
        e = Email.objects.filter(email = email_or_phone_number).first()
        if e is None:
            return None
        else:
            return  e.user
