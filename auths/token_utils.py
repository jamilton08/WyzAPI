def token_expiries(refresh):

    from datetime import datetime, timedelta
    from wyzcon.settings import SIMPLE_JWT
    from rest_framework.response import Response
    from rest_framework import status
    from rest_framework_simplejwt.tokens import RefreshToken
    epoch = datetime(1970,1,1)
    access_e = (datetime.now() + SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']) - epoch
    refresh_e = (datetime.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']) - epoch
    a_seconds = access_e.total_seconds()
    r_seconds = refresh_e.total_seconds()
    if type(refresh) == RefreshToken:
        at = str(refresh.access_token)
        rt = str(refresh)
    else:
        at = str(refresh.data["access"])
        rt = str(refresh.data["refresh"])
    return Response({
    'accessToken': at,
    'accessTokenExpire':int(a_seconds),
    'refreshToken': rt,
    'refreshTokenExpire':int(r_seconds),
    }, status=status.HTTP_200_OK)
