from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google_auth_oauthlib.flow

from django.shortcuts import redirect
import os.path
import json
from datetime import datetime

OAuth_Creds = 'client_secret.json'
Scopes = ['https://www.googleapis.com/auth/calendar']

@api_view(['GET'])
def GoogleCalendarInitView(request):

    gate = google_auth_oauthlib.flow.Flow.from_client_secrets_file(OAuth_Creds, scopes=Scopes)
    gate.redirect_uri = 'http://localhost:8000/rest/v1/calendar/redirect/'

    #Generating OAuth2.0 URL
    authorization_url, state = gate.authorization_url(include_granted_scopes='true',access_type='offline')

    # Storing the Session State.
    request.session['state'] = state

    return redirect(authorization_url)

@api_view(['GET'])
def GoogleCalendarRedirectView(request):

    state = request.session.get('state')
    
    gate = google_auth_oauthlib.flow.Flow.from_client_secrets_file(OAuth_Creds, scopes=Scopes, state=state)
    gate.redirect_uri = 'http://localhost:8000/rest/v1/calendar/redirect/'

    #  fetching  the OAuth 2.0 tokens usig authorization server.
    authorization_response = request.get_full_path()
    gate.fetch_token(authorization_response=authorization_response)

    credentials = gate.credentials

    try:
        service = build('calendar', 'v3', credentials=credentials)

        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' denotes UTC time
        # Calling the Calendar API
        #All Events
        all_events_result = service.events().list(calendarId='primary').execute()
        all_events = all_events_result.get('items', [])
        #Upcoming Events
        upcoming_events_result = service.events().list(calendarId='primary',timeMin=now,singleEvents=True,orderBy='startTime').execute()
        upcoming_events = upcoming_events_result.get('items', [])

        if not all_events:
            return Response({'Message': 'No events found.'})
        else:

            all_events_list = []
            for event in all_events:
                event_dict = {
                    'event_id': event['id'],
                    'name': event['summary'],
                    'creator': event['creator'],
                    'organizer': event['organizer'],
                    'start_time': event['start'],
                    'end_time': event['end']
                }
                all_events_list.append(event_dict)
            upcoming_events_list = []
            for event in upcoming_events:
                event_dict = {
                    'event_id': event['id'],
                    'name': event['summary'],
                    'creator': event['creator'],
                    'organizer': event['organizer'],
                    'start_time': event['start'],
                    'end_time': event['end']
                }
                upcoming_events_list.append(event_dict)
            final_list= [{'Upcoming Events ':upcoming_events_list, 'All Events ':all_events_list}]
            return Response(final_list)

    except Exception as error:
        return Response({'Message': 'Found an Error : %s' % error})

    
