from __future__ import print_function

from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, views
from rest_framework.permissions import IsAuthenticated, AllowAny
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']

@permission_classes([AllowAny])
@api_view(['GET'])
def get_classrooms(request, *args, **kwargs):
    print("bro")
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('classroom', 'v1', credentials=creds)

        # Call the Classroom API
        results = service.courses().list(pageSize=10).execute()
        courses = results.get('courses', [])

        if not courses:
            print('No courses found.')
            return
        # Prints the names of the first 10 courses.
        print('Courses:')
        for course in courses:
            print(course['name'])

    except HttpError as error:
        print('An error occurred: %s' % error)

    return Response( status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_test(request):
        print("bro")
        """Shows basic usage of the Classroom API.
        Prints the names of the first 10 courses the user has access to.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('classroom', 'v1', credentials=creds)
            service1 = build('drive', 'v3', credentials=creds)

            # Call the Classroom API
            results = service.courses().list(pageSize=10).execute()
            results1 = service1.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
            items = results1.get('files', [])


            courses = results.get('courses', [])

            if not courses:
                print('No courses found.')
                return
            # Prints the names of the first 10 courses.
            print('Courses:')
            for course in courses:
                print(course['name'])
                print(course)
            for item in items:
                print(u'{0} ({1})'.format(item['name'], item['id']))

        except HttpError as error:
            print('An error occurred: %s' % error)

        return Response( status=status.HTTP_201_CREATED)
