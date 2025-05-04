from django.shortcuts import render
from rest_framework import status, viewsets, permissions, views, generics
from .engine import Builder
from rest_framework.response import Response
from .serializers import NotificationSerializer

class GetUserNotifications(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer

    def list(self, request, last):
        query = Builder.user_unreads(request.user)
        if query.count() >= last + 5:
            query = query[last : last + 5]
        else:
            query =  query[last : query.count()]
        # Note the use of `get_queryset()` instead of `self.queryset`

        serializer = self.serializer_class(query, many=True)
        print(serializer.data)
        return Response(serializer.data)

class GetUserResponses(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer

    def list(self, request, last):
        query = Builder.user_unrespondeds(request.user)

        if query.count() >= last + 5:
            query = query[last : last + 5]
        else:
            query =  query[last : query.count()]
        # Note the use of `get_queryset()` instead of `self.queryset`

        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data)
