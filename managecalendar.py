import datetime
import json
import httplib2

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import truffe

PATH = "credentials.json"
service_account_name = 'logistique-agepoly-google-bot@logistique-agepoly-bot.iam.gserviceaccount.com'
calendarId = '7a63d1e921dd31c1ed7cdfbb92a155170742e85a658ed5a1b0bd610502e18dd2@group.calendar.google.com'
TIMEZONE = 'Europe/Zurich'
EVENT_LOCATION = "Boutique de l'AGEPoly, sur l'Esplanade"
BOOKED_TIME = 60 # minutes


def get_calendar() -> any:
    """Connect to the Google Calendar API using a service account."""
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.load(open(PATH)),
                                                                   scopes=['https://www.googleapis.com/auth/calendar',
                                                                           'https://www.googleapis.com/auth/calendar'
                                                                           '.events'])
    http = httplib2.Http()
    http = credentials.authorize(http)
    calendar = build(serviceName='calendar', version='v3', http=http)
    return calendar


def create_event(title: str, description: str, start: str, location: str = EVENT_LOCATION,
                 timezone: str = TIMEZONE) -> dict:
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
            'dateTime': (datetime.datetime.fromisoformat(start) + datetime.timedelta(minutes=BOOKED_TIME)).isoformat(),
            'timeZone': timezone,
        },
    }
    return event


def add_events_to_calendar(events: list, calendar=get_calendar()) -> None:
    """Add events to the Google Calendar."""
    events_ids = []
    for event in events:
        inserted = calendar.events().insert(calendarId=calendarId, body=event).execute()
        events_ids.append(inserted['id'])
        print(f"Event {event['summary']} added to the calendar.")
    # Save event ids to a file
    with open('events_ids.txt', 'w') as file:
        file.write(json.dumps(events_ids))
    return


def update_calendar_individual_res(reservations: list[dict]) -> None:
    """Add events to the Google Calendar."""
    # Prêts
    events = [create_event("Prêt " + reservation['asking_unit_name'], reservation['agreement'],
                           reservation['start_date'],
                           ) for reservation in reservations]
    # Rendus
    events += [create_event("Rendu " + reservation['asking_unit_name'], reservation['agreement'],
                            reservation['end_date'],
                            ) for reservation in reservations]
    # Create the calendar once and use it for all events
    calendar = get_calendar()
    # add events to the calendar
    add_events_to_calendar(events, calendar)
    return


def remove_minutes(date: str) -> str:
    """Remove minutes from a date."""
    return datetime.datetime.fromisoformat(date).replace(minute=0, second=0).isoformat()


def create_groupe(reservations: list[dict], is_start_date: bool) -> list[dict]:
    """Create a timeslot group in the Google Calendar."""
    events = []
    date_type = "start_date" if is_start_date else "end_date"
    grouped_reservations = {}
    for reservation in reservations:
        event_date = remove_minutes(reservation[date_type])
        if event_date not in grouped_reservations:
            grouped_reservations[event_date] = []
        grouped_reservations[event_date].append(reservation)
    # for event_date, reservations in grouped_reservations.items():
    #     title = "Prêts " if is_start_date else "Rendus "
    #     # title += ", ".join([reservation['asking_unit_name'] for reservation in reservations])
    #     description = "descrpition"
    #     events.append(create_event(title, description, event_date))
    # return events

    for date in grouped_reservations:
        events.append(create_event(str(len(grouped_reservations[date])) + (" Prêt(s)" if is_start_date else " Rendu(s)"),
                                   '\n'.join(
                                       [
                                           '\n'.join([reservation['asking_unit_name'], reservation['agreement'],
                                                      reservation['contact_phone'], reservation['contact_telegram']])
                                           for reservation in grouped_reservations[date]
                                       ]
                                   ),
                                   date))
    return events


def update_calendar_grouped(reservations: list[dict]) -> None:
    """Add events to the Google Calendar."""
    # Prêts
    events = create_groupe(reservations, True)
    # Rendus
    events += create_groupe(reservations, False)
    # Create the calendar once and use it for all events
    calendar = get_calendar()
    # Add events to the calendar
    add_events_to_calendar(events, calendar)
    return


def delete_all_events() -> None:
    """Delete all events from the Google Calendar."""
    calendar = get_calendar()
    # print(calendar)
    # events = calendar.events().list(calendarId=calendarId).execute()
    # print(calendar.events().list(calendarId=calendarId))
    # print(events)
    # Get event ids from the file if it exists
    try:
        with open('events_ids.txt', 'r') as file:
            events_ids = json.loads(file.read())
    except FileNotFoundError:
        events_ids = []
    # Delete events
    for id in events_ids:
        calendar.events().delete(calendarId=calendarId, eventId=id).execute()
        print(f"Event with id {id} deleted from the calendar.")
    # Write back an empty list of events ids
    with open('events_ids.txt', 'w') as file:
        file.write(json.dumps([]))
    print("All events deleted from the calendar.")
    return


def hard_refresh(reservations: list[dict]):
    """Delete all events from the calendar and add the new ones."""
    delete_all_events()
    # update_calendar_individual_res(reservations)
    update_calendar_grouped(reservations)
    return
