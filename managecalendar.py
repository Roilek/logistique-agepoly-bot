import datetime
import json
import os

import httplib2

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import database
import env
import truffe
from env import get_env_variables

ENV = get_env_variables()['ENV']
CALENDAR_ID = get_env_variables()['CALENDAR_ID']
GSERVICE_CREDENTIALS = get_env_variables()['GSERVICE_CREDENTIALS']

TIMEZONE = 'Europe/Zurich'
EVENT_LOCATION = "Boutique de l'AGEPoly, sur l'Esplanade"
BOOKED_TIME = 60  # minutes


def _get_calendar() -> any:
    """Connect to the Google Calendar API using a service account."""
    # Try to connect the service account
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(GSERVICE_CREDENTIALS, ['https://www.googleapis.com/auth/calendar'])
        http_auth = credentials.authorize(httplib2.Http())
        calendar = build('calendar', 'v3', http=http_auth)
        print("Connected to the Google Calendar API.")
        return calendar
    except Exception as e:
        print("Failed to connect to the Google Calendar API.")
        print(e)
        return None


def _create_event(title: str, description: str, start: str, location: str = EVENT_LOCATION,
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


def _add_events_to_calendar(events: list, calendar: any = _get_calendar()) -> bool:
    """Add events to the Google Calendar."""
    if calendar is not None:
        # Add events to the calendar
        for event in events:
            event = calendar.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            database.add_event_id(event['id'])
            print(f"Event created: {event.get('summary')}")
        print("All events added to the calendar.")
        return True
    else:
        return False


def _update_calendar_individual_res(reservations: list[dict]) -> bool:
    """[DEPRECATED] Add events to the Google Calendar."""
    # Prêts
    events = [_create_event("Prêt " + reservation['asking_unit_name'], reservation['agreement'],
                            reservation['start_date'],
                            ) for reservation in reservations]
    # Rendus
    events += [_create_event("Rendu " + reservation['asking_unit_name'], reservation['agreement'],
                             reservation['end_date'],
                             ) for reservation in reservations]
    # Create the calendar once and use it for all events
    calendar = _get_calendar()
    # Add events to the calendar
    return _add_events_to_calendar(events, calendar)


def _remove_minutes(date: str) -> str:
    """Remove minutes from a date."""
    return datetime.datetime.fromisoformat(date).replace(minute=0, second=0).isoformat()


def _create_groupe(reservations: list[dict], is_start_date: bool) -> list[dict]:
    """Create a timeslot group in the Google Calendar."""
    events = []
    date_type = "start_date" if is_start_date else "end_date"
    # Group reservations by date
    grouped_reservations = {}
    for reservation in reservations:
        event_date = _remove_minutes(reservation[date_type])
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
        event = _create_event(title, description, date)
        events.append(event)
    return events


def _update_calendar_grouped(reservations: list[dict]) -> bool:
    """Add events to the Google Calendar."""
    # Prêts
    events = _create_groupe(reservations, True)
    # Rendus
    events += _create_groupe(reservations, False)
    # Create the calendar once and use it for all events
    calendar = _get_calendar()
    # Add events to the calendar
    return _add_events_to_calendar(events, calendar)


def clear_calendar() -> bool:
    """Delete all events from the Google Calendar."""
    calendar = _get_calendar()
    if calendar is not None:
        try:
            events_ids = database.get_event_ids()
        except FileNotFoundError:
            events_ids = []
        # Delete events
        for event_id in events_ids:
            # Attempt to delete the event
            try:
                calendar.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
                print(f"Event {event_id} deleted.")
            except Exception as e:
                print(f"Failed to delete event {event_id}.")
                print(e)
        print("All events deleted from the calendar.")
        database.clear_event_ids()
        return True
    else:
        return False


def refresh_calendar(reservations: list[dict]) -> bool:
    """Delete all events from the calendar and add the new ones."""
    done = clear_calendar()
    done &= _update_calendar_grouped(reservations)
    return done
