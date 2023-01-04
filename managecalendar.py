import datetime
import json
import httplib2

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

from env import get_environment_variables
import truffe

CALENDAR_ID = get_environment_variables()['CALENDAR_ID']
PATH = "credentials.json"

TIMEZONE = 'Europe/Zurich'
EVENT_LOCATION = "Boutique de l'AGEPoly, sur l'Esplanade"
BOOKED_TIME = 60  # minutes


def get_calendar() -> any:
    """Connect to the Google Calendar API using a service account."""
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json.load(open(PATH)),
        scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
    )
    http = httplib2.Http()
    http = credentials.authorize(http)
    calendar = build(serviceName='calendar', version='v3', http=http)
    return calendar


def create_event(title: str, description: str, start: str, location: str = EVENT_LOCATION,
                 timezone: str = TIMEZONE) -> dict:
    """Create an event in the Google Calendar."""
    time_end_event = datetime.datetime.fromisoformat(start) + datetime.timedelta(minutes=BOOKED_TIME)
    time_end_event = time_end_event.isoformat()
    event = {
        'summary': title,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': time_end_event,
            'timeZone': timezone,
        },
    }
    return event


def add_events_to_calendar(events: list, calendar=get_calendar()) -> None:
    """Add events to the Google Calendar."""
    events_ids = []
    for event in events:
        inserted = calendar.events().insert(calendarId=CALENDAR_ID, body=event).execute()
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
    # Group reservations by date
    grouped_reservations = {}
    for reservation in reservations:
        event_date = remove_minutes(reservation[date_type])
        if event_date not in grouped_reservations:
            grouped_reservations[event_date] = []
        grouped_reservations[event_date].append(reservation)

    # Create events
    for date, reservations in grouped_reservations.items():
        title = f"{len(reservations)} {'Prêt' if is_start_date else 'Rendu'}{'s' if len(reservations) > 1 else ''}"
        description = ""
        # Add reservations to the description
        for reservation in reservations:
            description += '\n'.join([
                reservation['asking_unit_name'],
                reservation['agreement'],
                "\t" + reservation['contact_phone'],
                "\t" + reservation['contact_telegram']
            ])
            description += '\n\n'
        event = create_event(title, description, date)
        events.append(event)
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
    try:
        events_ids = json.load(open('events_ids.txt'))
    except FileNotFoundError:
        events_ids = []
    # Delete events
    for id in events_ids:
        calendar.events().delete(calendarId=CALENDAR_ID, eventId=id).execute()
        print(f"Event with id {id} deleted from the calendar.")
    # Write back an empty list of events ids
    with open('events_ids.txt', 'w') as file:
        file.write(json.dumps([]))
    print("All events deleted from the calendar.")
    return


def hard_refresh(reservations: list[dict]):
    """Delete all events from the calendar and add the new ones."""
    delete_all_events()
    update_calendar_grouped(reservations)
    return
