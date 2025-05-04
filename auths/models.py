from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from .utilities.comm import confirmiation_email
from . import managers
from datetime import datetime, timedelta
from Filesystem.pather import PathGenerator
from django.utils.translation import gettext_lazy as _
from cryptography.fernet import Fernet
from decouple import config


class Profile(models.Model, PathGenerator):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name = "profile_user")
    profile_pic = models.ImageField(upload_to =PathGenerator.pattern_gather, null = True, blank = True)
    path_pattern = [('user', 'first_name'), ('user','last_name' )]


class Verified(models.Model):
    verified_date= models.DateTimeField(blank = True, null = True)
    def is_verified(self):
        return  verified_date is None
    class Meta:
        abstract = True


class Email(Verified, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emails')
    email = models.EmailField(max_length=254)

    def email_and_save(self,*args, **kwargs):
        confirmiation_email(self.user, kwargs.pop('request'), self.email) # this will get erased when sending email is ready for production
        return self.save(*args, **kwargs)

    class Meta:
        default_related_name = "email"
        db_table = "email"

class Phone(Verified, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "phones")
    phone_number = PhoneNumberField()
    active = models.BooleanField(default = False)
    class Meta:
        default_related_name = "phone"
        db_table = "phone"

class Active(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name = "act_status")
    locked_out = models.BooleanField(default = False)
    active = models.BooleanField(default = False)

class RandCodeModel(models.Model):
    phone = models.OneToOneField(Phone,on_delete=models.CASCADE, related_name='code' )
    created = models.DateTimeField(auto_now_add=True)
    code = models.IntegerField()
    #content_type = models.ForeignKey(ContentType,on_delete=models.CASCADE, related_name='reset_code')
    resolved = models.BooleanField()
    #object_id = models.IntegerField()
    #content_object = GenericForeignKey('content_type', 'object_id')

    objects = managers.TextCodeManager()


    def _generate_code(self):
        from random import Random
        code = Random().randint(168374, 963728)
        return code

    def _unique_code(self):
        while True:
            code = self._generate_code()
            if not self.__class__.objects.filter(code = code):
                return code

    def expire_time(self, minutes):
        expire = self.created + timedelta(minutes = minutes)
        return expire

    def is_valid(self, minutes):
        return bool(self.expire_time(minutes) < datetime.now())

    #def get_instance(self):
        #model_instance  = self.content_type.get_object_for_this_type(pk = self.object_id)
        #return model_instance
    #@classmethod
    #def get_model_class_content(cls, instance):
        #content = ContentType.objects.get_for_model(instance.__class__)
        #return content

    @classmethod
    def creates(cls, instance):
        code_instance = {
                        'code':cls.unique_code(),
                        'resolved':False,
                        }
        inst = cls.objects.create(**code_instance)
        return inst


    def save(self, *args, **kwargs):
        from twilio.rest import Client
        self.created = datetime.now()
        self.code = self._unique_code()
        self.resolved = False
        account_sid = config('TWILIO_ACCOUNT_SID')
        auth_token = config('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        message = client.messages.create(
                                        body=f'Hi, your test result is {str(self.code)}. Great job',
                                        from_= config('TWILIO_PHONE_NUMBER'),
                                        to=self.phone.phone_number.as_e164
                                    )

        print(message.sid)
        return super(RandCodeModel, self).save()

class PasswordResetSafetyModel(models.Model):
    class CommType(models.TextChoices):
            EMAIL = "E", _("email")
            PHONE = "P", _("phone")

    created = models.DateTimeField(auto_now_add=True)
    accessed = models.DateTimeField(blank = True, null = True)
    comm_type = models.CharField(
            max_length=2,
            choices=CommType.choices,
            default=CommType.EMAIL,
        )
    comm_pk = models.IntegerField()
    key = models.BinaryField( blank = True, null = True)
    token = models.BinaryField( blank = True, null = True)




    def build_entity(self):
        if self.comm_type == "E":
            return  Email.objects.get(pk = self.comm_pk).email
        else:
            return  Phone.objects.get(pk = self.comm_pk).phone_number

    @classmethod
    def type_form(cls, word):
        return word[0].upper()


    @classmethod
    def retrieve_instance(cls, token):
        try:
            return cls.objects.get(token = token)
        except cls.DoesNotExist:
            return None


    @classmethod
    def encode_format(cls, entity):
        from .utilities.debacles import phone_or_email
        p_o_e = phone_or_email(entity)
        entity_type = "phone" if p_o_e else "email"
        entity_pk = Phone.objects.get(phone_number = entity).pk if p_o_e else Email.objects.get(email = entity).pk
        return  "{}:{}".format(entity_type, entity_pk)



    @classmethod
    def forgot_password_encrypt(cls, pre_encoded_message):
        key = Fernet.generate_key()
        fernet = Fernet(key)

        encMessage = fernet.encrypt(pre_encoded_message.encode())

        return encMessage, key

    @classmethod
    def replace_or_create(cls, entity):
        pre = cls.encode_format(entity)
        comm, pk  = cls.decode(pre)
        return  cls.objects.filter(comm_type = cls.type_form(comm), comm_pk = int(pk)).count() > 0

    @classmethod
    def create(cls, entity):
        ec = cls.encode_format(entity)
        comm, pk  = cls.decode(ec)
        type_format = cls.type_form(comm)
        if cls.replace_or_create(entity):
            print("is this happening")
            cls.objects.filter(comm_type = type_format, comm_pk = int(pk)).delete()
        instance = cls.objects.create(comm_type = type_format, comm_pk = pk)
        instance.save()
        return instance



    @classmethod
    def token_verify(cls, raw_token):
        raw_token_b = bytes(raw_token, 'utf-8')
        instance = cls.retrieve_instance(raw_token_b)
        if instance is None:
            print("here")
            return bool(0)
        if instance.expire():
            print("there")
            cls.objects.filter(pk = instance.pk).delete()
            return bool(0)
        if instance.accessed is not None:
            return bool(0)
        instance.accessed = datetime.now()
        instance.save()
        return bool(1)


    @classmethod
    def get_instance(cls, token):
        try :
            obj = cls.objects.get()
        except cls.DoesNotExist :
            return None
        return obj

    def  access(self):
        return  obj.accessed is None and not  self.expire()



    def expire(self):
        import pytz
        utc=pytz.UTC
        return bool(utc.localize(datetime.now()) > self.created + timedelta(minutes = 50))

    @classmethod
    def decrypt(cls, encMessage, key):
        fernet = Fernet(key)
        return fernet.decrypt(encMessage).decode()

    @classmethod
    def decode(cls, message):
        print(str(message))
        decodedMessage = str(message).split(":")

        return decodedMessage[0], decodedMessage[1]

    def get_object(self):
        if self.comm_type == "E":
            return Email.objects.get(email = self.comm_pk)
        else:
            return Phone.objects.get(phone_number = self.comm_pk)

    def generate_link(self):
        cls = self.__class__
        encoded_ent, key = cls.forgot_password_encrypt(cls.encode_format(self.build_entity()))
        self.key = key
        self.token = encoded_ent
        self.save()
        return "http://localhost:3000/reset-page/{}".format(str(encoded_ent, encoding = 'utf-8'))


    #def sendText(self):


#class PasswordTextResets(models.Model):
    #user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset')
    #phone_ins = models.ForeignKey(PhoneNumberRetainer, on_delete=models.CASCADE, related_name='password_text')





#class ExtendTokens(models.Model):
    #token = models.ForeignKey(ResetPasswordToken, on_delete=models.CASCADE, related_name='token_extend')
    #used=models.BooleanField()

    #def is_delete(self, minutes):
    #    import pytz
    #    utc=pytz.UTC
    #    expire_time =  self.token.created_at + timedelta(minutes = minutes)

        #return bool(utc.localize(datetime.now()) > expire_time)
