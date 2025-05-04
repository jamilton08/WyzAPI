from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, views, mixins, generics
from rest_framework.permissions import AllowAny
from .models import Active, Email, Phone
from django.contrib.auth.models import User
from .serializers import UserSerializer, ObtainTokenSerializer, ProfileSerializer, InvolvementSerializer
from perms.decorators import second_level_perms
from organizations.models import Organization
from rest_framework_simplejwt.tokens import RefreshToken
from  .token_utils import token_expiries
from rest_framework_simplejwt import views as jwt_views
from rest_framework.parsers import JSONParser,  MultiPartParser, FormParser
from django.views import View



@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    from .serializers import CreateUserSerializer
    print(request.data)
    if request.method == 'POST':
        context ={'request':request}
        serializer = CreateUserSerializer(data=request.data, context=context )
        print("are you here")
        if serializer.is_valid():
            user = serializer.create(serializer.validated_data)

            data={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email':user.email
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def activate(request, uidb64, token, euid64):
    from django.shortcuts import redirect
    from django.contrib.auth import login, authenticate
    from django.utils.encoding import force_str
    from django.utils.http import urlsafe_base64_decode
    from .token import account_activation_token
    from datetime import datetime
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        euid = force_str(urlsafe_base64_decode(euid64))
        user = User.objects.get(pk=uid)
        email = Email.objects.get(email=euid)
        print(email.email)
        print(user)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist, Email.DoesNotExist):
        user = None
        email = None
        print("here we are")
    print(account_activation_token.check_token(user, token))
    if user is not None and email is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        act = user.act_status
        print("this is something ie heeeeeere")
        act.active = True
        email.verified_date = datetime.now()
        user.save()
        email.save()
        act.save()

        return redirect("http://localhost:3000/auth/login")
    else:
        return redirect("http://localhost:3000/auth/pricing")

@api_view(['POST'])
def add_email(request):
    from .serializers import AddEmailSerializer
    if request.method == 'POST':
        context ={'request':request}
        serializer = AddEmailSerializer(data=request.data, request = request )
        if serializer.is_valid():
            user = User.objects.get(pk = 53)
            email = serializer.create(user)
            data = {"email" : email.email}
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def add_phone(request, *args, **kwargs):
    from .serializers import AddPhoneSerializer
    if request.method == 'POST':
        context ={'request':request}
        serializer = AddPhoneSerializer(data=request.data, request = request )
        if serializer.is_valid():
            user = User.objects.get(pk = 46)
            phone = serializer.create(user)
            data = {"phone_number" : phone.phone_number.as_e164}
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PUT'])
def resend_email_conformation(request, *args, **kwargs):
    if request.method == "PUT":
        confirmiation_email(request.user, request, request.data['email'])
        return Response("broski", status=status.HTTP_202_ACCEPTED)
    return Response( status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_entity(request, *args, **kwargs):
    from .serializers import CommTransactionSerializer
    if request.method == "PUT":
        serializer = CommTransactionSerializer(data = request.data, request = request)
        if serializer.is_valid():
            serializer.change()
            return Response("broski", status=status.HTTP_202_ACCEPTED)
    return Response( status=status.HTTP_400_BAD_REQUEST)



@api_view(['PUT'])
def request_code(request):
    try:
        phone_pk = request.data['phone']
        p =  Phone.objects.get(pk = phone_pk)
        p.code.save()
        data = { "code": p.code.code}
        return Response(data, status=status.HTTP_202_ACCEPTED)
    except Phone.DoesNotExist:
        return Response(" you have the wrong pk my guy, that shit dont exist.... scaaaaaaam ", status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

#this is a test method to see authorization

@api_view(['POST'])
@second_level_perms(content = Organization, perm_type = "A")
def bro(request, *args, **kwargs):

    return Response("broski", status=status.HTTP_202_ACCEPTED)


class ObtainTokenView(views.APIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = ObtainTokenSerializer

    def post(self, request, *args, **kwargs):
        from .login_backend import authenticate
        from .utilities.debacles import phone_or_email



        context ={'request':request}
        print(request.data)

        serializer = self.serializer_class(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        email_or_phone_number = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = authenticate(email_or_phone_number)
        if user is None or not user.check_password(password):
            print("is the problem her")

            return Response({'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        # Generate the JWT token
        refresh = RefreshToken.for_user(user)
        print(type(refresh))
        return token_expiries(refresh)


class RefreshCustom(jwt_views.TokenRefreshView):
    def post(self, request, *args, **kwargs):
        original_request= super(RefreshCustom, self).post(request, args, kwargs)
        print(token_expiries(original_request).data)
        return token_expiries(original_request)



class LoggedInUserViewSet(viewsets.ReadOnlyModelViewSet):

    def retrieve(self, request):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=request.user.pk)
        serializer = UserSerializer(user)
        print(serializer.data)
        return Response(serializer.data)



@api_view(['GET'])
def get_involvements(request, *args, **kwargs):
    from auths.utilities.collectables import CollectUserInvolvement
    org = Organization.objects.get(pk = kwargs["org"])
    c = CollectUserInvolvement(request.user,  org)
    serializer = InvolvementSerializer(c.collect(), many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)

class ProfileUpdate(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     generics.GenericAPIView):
    """
     List all restaurant, or create a restaurant
    """
    #permission_classes = (permissions.IsAuthenticatedOrReadO        nly,)
    parser_classes = (JSONParser, MultiPartParser, FormParser,)
    serializer_class = ProfileSerializer



    def post(self, request, *args, **kwargs):
        print(request.data)
        print(request)
        serializer = self.serializer_class(data = request.data)
        if serializer.is_valid():
            serializer.update(request)
            return Response( status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(View):
    def get(self, request, *args, **kwargs):
        from django.http import HttpResponse
        return HttpResponse("hello world")

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_forgotten_password_trans(request):
    print("lako")
    from .serializers import InitiateResetSerializer
    if request.method == 'POST':
        serializer = InitiateResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.initialize_reset()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_token(request, token):
    from .models import  PasswordResetSafetyModel
    print(token)
    if PasswordResetSafetyModel.token_verify(token):
        return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([AllowAny])
def password_reset(request):
    from .serializers import ResetPasswordSerializer
    if request.method == "PUT":
        serializer = ResetPasswordSerializer(data = request.data)
        if serializer.is_valid():
            serializer.reset()
            return Response( status=status.HTTP_202_ACCEPTED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
