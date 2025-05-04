from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Email, Phone, Profile, PasswordResetSafetyModel
from organizations.models import Organization
from .utilities.debacles import phone_or_email


class CreateUserSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text='Leave empty if no change needed',
        style={'input_type': 'password', 'placeholder': 'Password'}
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    string = serializers.CharField()



    def validate(self, data):
        if phone_or_email(data['string']):
            data['phone_number'] = data['string']
            serializer = AddPhoneSerializer(data = data, request = self.context['request'])
            if serializer.is_valid():
                try:
                    has_account = Phone.objects.get(phone_number= data['phone_number'])
                    raise serializers.ValidationError("According to Wyzcon, a user is registered under this email already")
                except Phone.DoesNotExist:
                    self.serializer_retainer = serializer
                    return data
            else : raise serializers.ValidationError("phone number entered is not valid")
        elif phone_or_email(data['string']) == False:
            data['email'] = data['string']
            serializer = AddEmailSerializer(data = data, request = self.context['request'])
            if serializer.is_valid():
                try:
                    has_account = Email.objects.get(email = data['email'])
                    raise serializers.ValidationError("According to Wyzcon, a user is registered under this email already")
                except Email.DoesNotExist:
                    self.serializer_retainer = serializer
                    return data
            else:
                raise serializers.ValidationError("email entered is not valid")
        else:
            raise serializers.ValidationError("no valid stuff")

    def _get_next_username_and_email(self):
        d = self.validated_data
        f = d['first_name']
        l = d['last_name']
        counter = 0
        while(True):
            try:
                self.Meta.model.objects.get(username = f'{f}.{l}{counter}')
                counter += 1
            except User.DoesNotExist:
                username = f'{f}.{l}{counter}'
                email = f'{f}.{l}{counter}@wyzcon.com'
                return username, email

    def create(self, validated_data):

        data = validated_data
        username, email = self._get_next_username_and_email()
        user = User.objects.create(username = username,
                                email = email,
                                first_name = data['first_name'],
                                last_name = data['last_name'])
        user.set_password(data['password'])
        user.save()
        self.serializer_retainer.create(user)
        return user

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'string', 'password', )


class AddEmailSerializer(serializers.ModelSerializer):
        def __init__(self, *args, **kwargs):
            self.request= kwargs.pop('request')
            super(AddEmailSerializer,self).__init__(*args, **kwargs)



        def validate(self, data):
            try:
                has_account = Email.objects.get(email = data['email'])
                raise serializers.ValidationError("According to Wyzcon, a user is registered under this email already")
            except Email.DoesNotExist:
                return data

        def create(self, user):
            data = self.validated_data
            email = Email.objects.create(user=user, email = data['email'])
            email.email_and_save(request=self.request)
            return email

        class Meta:
            model = Email
            fields = ('email', )


class AddPhoneSerializer(serializers.ModelSerializer):
        def __init__(self, *args, **kwargs):
            self.request= kwargs.pop('request')
            super(AddPhoneSerializer,self).__init__(*args, **kwargs)



        def validate(self, data):

            try:
                has_account = Phone.objects.get(phone_number = data['phone_number'])
                raise serializers.ValidationError("According to Wyzcon, a user is registered under this phone already")
            except Phone.DoesNotExist:
                return data

        def create(self, user):
            data = self.validated_data
            phone = Phone.objects.create(phone_number = data['phone_number'], user = user)
            phone.save()
            return phone

        class Meta:
            model = Phone
            fields = ('phone_number', )

class UserSerializer(serializers.HyperlinkedModelSerializer):
    emails = serializers.SerializerMethodField('em')
    phones = serializers.SerializerMethodField('ph')
    organizations = serializers.SerializerMethodField('org')
    permissions = serializers.SerializerMethodField('perms')
    act_status = serializers.SerializerMethodField("status")
    stacks = serializers.SerializerMethodField("get_stack")


    def em(self, bro):
        instance = EmailSerializer(bro.emails.all(), many=True)
        return instance.data

    def ph(self, bro):
        instance = PhoneSerializer(bro.phones.all(), many=True)
        return instance.data

    def org(self, bro):
        from orgs.utilities import get_user_involved_organizations as gei
        seen_list = list()
        orgs = list()
        for org in gei(bro):
            if org["pk"] not in seen_list:
                orgs.append(org)
                seen_list.append(org["pk"])
        return orgs

    def perms(self, bro):
        from perms.utilities import GeneratePerms as G
        return G.get_user_perms(bro)

    def get_stack(self, bro):
        stack_dict = dict()
        for org_user in bro.organizations_organizationuser.all():
            if hasattr(org_user, "permission_retainer"):
                stack_dict[org_user.organization.pk] = org_user.permission_retainer.stack_level
        return stack_dict
    

    def status(self, bro):
        return bro.act_status.active


    class Meta:
        model = User
        fields = ['pk', 'username', 'first_name', 'last_name', 'emails', 'phones', 'organizations', 'permissions', 'act_status', 'stacks']

class EmailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Email
        fields = ['email', 'verified_date']

class PhoneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Phone
        fields = ['phone_number', 'verified_date']

class ProfileSerializer(serializers.ModelSerializer):

    def update(self, request):
        profile_pic = self.validated_data['profile_pic']
        instance = self.Meta.model.objects.get(user = request.user)
        instance.profile_pic = profile_pic
        instance.save()
        return profile_pic


    class Meta:
        model = Profile
        fields = ['profile_pic']
class OrganizationsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Organization
        fields = ['name']

class CurrentOrgUser(serializers.Serializer):
        def __init__(self, *args, **kwargs):
            self.user = kwargs.pop["user"]

class ObtainTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    class LoginPhoneSerializer(serializers.ModelSerializer):
            class Meta:
                model = Phone
                fields = ('phone_number', )

    class LoginEmailSerializer(serializers.ModelSerializer):
            class Meta:
                model = Email
                fields = ('email', )

    def validate(self, data):
        if phone_or_email(data['username']):
            data['phone_number'] = data['username']
            serializer = self.LoginPhoneSerializer(data = data)
            if serializer.is_valid():
                try:
                    Phone.objects.get(phone_number= data['phone_number'])
                    return data
                except Phone.DoesNotExist:
                    raise serializers.ValidationError("According to Wyzcon, a user is registered under this phone does not DoesNotExist")
            else :
                raise serializers.ValidationError("phone number entered is not valid")
        elif phone_or_email(data['username']) == False:
            data['email'] = data['username']
            serializer = self.LoginEmailSerializer(data = data)
            if serializer.is_valid():
                try:
                    Email.objects.get(email = data['email'])
                    return data
                except Email.DoesNotExist:
                    raise serializers.ValidationError("According to Wyzcon, a user is registered under this email does not exist")
            else:
                raise serializers.ValidationError("email entered is not valid")
        else:
            raise serializers.ValidationError("no valid stuff")

class InvolvementSerializer(serializers.Serializer):
    name = serializers.CharField()
    details = serializers.CharField()
    type = serializers.CharField()
    content = serializers.CharField()  # Assuming you want to serialize the class name as a string
    obj = serializers.IntegerField()



class CommTransactionSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        self.request= kwargs.pop('request')
        super(CommTransactionSerializer,self).__init__(*args, **kwargs)

    comm = serializers.CharField()
    new_comm = serializers.CharField()

    se = None


    def validate(self, data):
        comm_bool = phone_or_email(data["comm"])
        new_comm_bool = phone_or_email(data["new_comm"])
        data_s = dict()
        if comm_bool == True:
            e = Phone.objects.get(phone_number = data["comm"])
        elif comm_bool == False:
            e = Email.objects.get(email = data["comm"])

        else:
            raise serializers.ValidationError("This is nonoe of the communication methods")

        if e.user != self.request.user:
            raise serializers.ValidationError("Since the user is not attached to number it cannot use it as its communication device")

        if new_comm_bool is None:
            raise serializers.ValidationError("You must enter a valid phone or email")

        if new_comm_bool == True:
            data_s["phone_number"] = data["new_comm"]
            serializer = AddPhoneSerializer(data = data_s, request = self.request)

        if new_comm_bool == False:
            data_s["email"] = data["new_comm"]
            serializer = AddEmailSerializer(data = data_s, request = self.request)

        if not serializer.is_valid():
            raise serializers.ValidationError("{} is registered already".format("phone" if new_comm_bool else "email"))

        self.se = serializer

        return data


    def change(self):
        comm_bool = phone_or_email(self.data["comm"])

        if comm_bool:
            Phone.objects.get(phone_number = self.data["comm"]).delete()
        else:
            Email.objects.get(email = self.data["comm"]).delete()

        return self.se.create(self.request.user)

class InitiateResetSerializer(serializers.Serializer):
    comm = serializers.CharField()


    def validate(self, data):
        comm_bool = phone_or_email(data["comm"])
        data_s = dict()
        if comm_bool == True:
            try:
                e = Phone.objects.get(phone_number = data["comm"])
            except Phone.DoesNotExist:
                raise serializers.ValidationError("This is a non existent phone numbere  within wyzqon")
        elif comm_bool == False:
            try :
                e = Email.objects.get(email = data["comm"])
            except Phone.DoesNotExist:
                raise serializers.ValidationError("This is a non existent email within wyzqon")
        else:
            raise serializers.ValidationError("This is nonoe of the communication methods")

        return data


    def initialize_reset(self):
        from .utilities.comm  import context_text, context_email
        comm_bool = phone_or_email(self.data["comm"])
        context = PasswordResetSafetyModel.create(self.data["comm"])
        url = context = context.generate_link()

        if comm_bool:
            _from = "=19295383177"
            context_text(context, _from, self.data["comm"])
        else:
            context_email(self.data["comm"], "d-a4a8241cbcac4d3c8fbfd1e6adb810ba", where = context)


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()
    confirm_password =  serializers.CharField()

    obj = None


    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("password must be confirmed appropriately, meaning the confirm field must be the same as your password ")
        raw_token_b = bytes(data["token"], 'utf-8')
        instance = cls.retrieve_instance(raw_token_b)
        if instance is None:
            raise serializers.ValidationError("must be an existing token")
        obj = instance
        return data


    def reset(self):
        user = obj.get_object().user
        user.set_password(password)
        user.save()
