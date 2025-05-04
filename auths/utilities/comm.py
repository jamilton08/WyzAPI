from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from auths.token import account_activation_token
from django.urls import reverse
from django.core.mail import EmailMessage
from decouple import config

def confirmiation_email(user, request, email):
    path = reverse('activate',args=[urlsafe_base64_encode(force_bytes(user.pk)),account_activation_token.make_token(user), urlsafe_base64_encode(force_bytes(email)) ])
    url = request.build_absolute_uri(path)

    print(url)

    msg = EmailMessage(from_email = "NoReply@wyzqon.com",to = [email])
    msg.template_id = config("TWILIO_TEMPLATE_ID")
    msg.dynamic_template_data={"where": url}
    msg.send(fail_silently=False)


def context_text(context, _from, to):
    from twilio.rest import Client
    account_sid = config("TWILIO_ACCOUNT_SID")
    auth_token = config("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)

    message = client.messages.create(
                                    body=context["context"],
                                    from_=_from,
                                    to=to
                                )

def context_email( email, temp_id, **context):

    print(context)
    msg = EmailMessage(from_email = "NoReply@wyzqon.com",to = [email])
    msg.template_id = temp_id
    msg.dynamic_template_data=context
    msg.send(fail_silently=False)
