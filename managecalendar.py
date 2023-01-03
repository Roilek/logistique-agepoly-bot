import datetime
import json
import httplib2

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import truffe
from main import DEFAULT_ACCEPTED_STATES

PATH = "credentials.json"
service_account_name = 'logistique-agepoly-google-bot@logistique-agepoly-bot.iam.gserviceaccount.com'
calendarId = '2a170d5a2dab3f933c7f075246f74582f5fa9cb38de6be5225a5461df3e22206@group.calendar.google.com'
TIMEZONE = 'Europe/Zurich'
EVENT_LOCATION = "Boutique de l'AGEPoly, sur l'Esplanade"


def get_calendar():
    """Connect to the Google Calendar API using a service account."""
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.load(open(PATH)),
                                                                   scopes=['https://www.googleapis.com/auth/calendar'])
    http = httplib2.Http()
    http = credentials.authorize(http)
    calendar = build(serviceName='calendar', version='v3', http=http)
    return calendar


def create_event(title, description, start, location=EVENT_LOCATION, timezone=TIMEZONE) -> dict:
    """Create an event in the Google Calendar."""
    event = {
        'summary': title,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': (datetime.datetime.fromisoformat(start) + datetime.timedelta(hours=1)).isoformat(),
            'timeZone': timezone,
        },
    }
    return event


def add_events_to_calendar(events: list, calendar=get_calendar()) -> None:
    """Add events to the Google Calendar."""
    for event in events:
        calendar.events().insert(calendarId=calendarId, body=event).execute()
        print(f"Event {event['summary']} added to the calendar.")


def update_calendar(reservations: list[dict]):
    """Update the Google Calendar with the events from Truffe."""
    # create events
    events = [create_event(reservation['title'], truffe.get_agreement_url_from_pk(reservation['pk']),
                           reservation['start_date'],
                           ) for reservation in reservations]
    # Create the calendar once and use it for all events
    calendar = get_calendar()
    # add events to the calendar
    add_events_to_calendar(events, calendar)


def delete_all_events():
    """Delete all events from the Google Calendar."""
    calendar = get_calendar()
    events = calendar.events().list(calendarId=calendarId).execute()
    for event in events['items']:
        calendar.events().delete(calendarId=calendarId, eventId=event['id']).execute()
        print(f"Event {event['summary']} deleted from the calendar.")


def hard_refresh():
    """Delete all events from the Google Calendar and add all events from Truffe."""
    delete_all_events()
    update_calendar()
