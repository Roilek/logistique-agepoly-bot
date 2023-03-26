import enum
import time
import copy

import pytz
import requests
import telegram
import datetime

from env import get_env_variables

TRUFFE_TOKEN = get_env_variables()['TRUFFE_TOKEN']
TRUFFE_PATH = "https://truffe2.agepoly.ch/logistics/"
TRUFFE_CACHE_STALE = 60  # seconds

MARKDOWN_VERSION = 2

last_update = None
truffe_cache = {}


# Enum of states as str
class State(enum.Enum):
    DRAFT = '0_draft'
    ASKING = '1_asking'
    ONLINE = '2_online'

    # Will need to be updated if more states are added

    @classmethod
    def all_names(cls) -> list:
        return [state.name for state in cls]

    @classmethod
    def all_values(cls) -> list:
        return [state.value for state in cls]

    @classmethod
    def translate(cls, value) -> str:
        return STATE_MAPPING[value]


DEFAULT_ACCEPTED_STATES = [
    State.ONLINE.value,
]

EXTENDED_ACCEPTED_STATES = [
    State.ONLINE.value,
    State.ASKING.value,
    State.DRAFT.value,
]

STATE_MAPPING = {
    '0_draft': 'en brouillon ⚠️',
    '1_asking': 'en cours de validation ⚠️',
    '2_online': 'validée ✅',
}


def _remove_external_difference(res_list: list[dict]) -> list[dict]:
    """Remove the difference between a reservation of an external unit and a reservation of an internal unit"""
    # fill the asking_unit_name field with the concatenation of the asking_external_unit and the asking_external_person
    for res in res_list:
        if res['asking_unit_name'] is None:
            res['asking_unit_name'] = res['asking_external_unit'] + ' (' + res['asking_external_person'] + ')'
    return res_list


def _shift_time(date: str) -> str:
    """Shift a date to the current time zone"""
    return datetime.datetime.fromisoformat(date).isoformat()


def _manage_time_shift(res_list: list[dict[str, str]]) -> list[dict]:
    """Shift the dates of the reservations to the current time zone"""
    for res in res_list:
        res['start_date'] = _shift_time(res['start_date'])
        res['end_date'] = _shift_time(res['end_date'])
    return res_list


def _sort_by_date(res_list: list[dict]) -> list[dict]:
    """Sort a list of reservations by date"""
    return sorted(res_list, key=lambda res: res['start_date'])


def _extend_agreement(res_list: list[dict]) -> list[dict]:
    """Add the agreement field to the reservations"""
    for res in res_list:
        res['agreement'] = get_agreement_url_from_pk(res['pk'])
    return res_list


def _get_date(date: str) -> str:
    """Returns a string from a date in the format day/month"""
    return datetime.datetime.fromisoformat(date).replace(tzinfo=pytz.utc).astimezone(
        pytz.timezone('Europe/Zurich')).strftime("%d/%m")


def _get_time(date: str) -> str:
    """Returns a string from a date in the format hour:minutes"""
    return datetime.datetime.fromisoformat(date).replace(tzinfo=pytz.utc).astimezone(
        pytz.timezone('Europe/Zurich')).strftime("%H:%M")


def _get_datetime(date: str) -> str:
    """Returns a string from a date in the format day/month hour:minutes"""
    return datetime.datetime.fromisoformat(date).replace(tzinfo=pytz.utc).astimezone(
        pytz.timezone('Europe/Zurich')).strftime("%d/%m %H:%M")


def _get_json_from_truffe() -> any:
    """Returns a json of all the reservations"""
    # Refresh truffe cache every 10 minutes
    global last_update
    global truffe_cache
    if last_update is None or last_update + TRUFFE_CACHE_STALE < time.time():
        infos = ['asking_unit_name', 'contact_telegram', 'start_date', 'end_date', 'contact_phone', 'reason', 'remarks',
                 'agreement']
        url = f"{TRUFFE_PATH}api/supplyreservations?{'&'.join(infos)}"

        headers = {"Accept": "application/json", "Authorization": "Bearer " + TRUFFE_TOKEN}
        reservations = requests.get(url, headers=headers)
        truffe_cache = reservations.json()
        last_update = time.time()

    return copy.deepcopy(truffe_cache)


def get_reservations(states: list = DEFAULT_ACCEPTED_STATES,
                     aggregate_external: bool = True,
                     standardize_dates: bool = True,
                     extend_agreement: bool = True) -> list[dict]:
    """Returns a list of all the reservations with one of the given states"""
    reservations = _get_json_from_truffe()['supplyreservations']
    reservations = _remove_external_difference(reservations) if aggregate_external else reservations
    reservations = _manage_time_shift(reservations) if standardize_dates else reservations
    reservations = _sort_by_date(reservations)
    reservations = _extend_agreement(reservations) if extend_agreement else reservations
    return list(filter(lambda res: res['state'] in states, reservations))


def get_res_pk_info(states: list) -> list[tuple[int, str]]:
    """Returns a list of tuples (pk, title) of all the reservations with one of the given states"""
    res_list = get_reservations(states)
    short_infos = [(res['pk'], ' - '.join([_get_datetime(res['start_date']), res['title'], res['asking_unit_name']]))
                   for res in res_list]
    return short_infos


def get_formatted_reservation_relevant_info_from_pk(pk: int) -> str:
    """Returns a formatted string with the relevant information of a reservation from its pk"""
    reservations = get_reservations(State.all_values())
    reservation = list(filter(lambda res: res['pk'] == pk, reservations))[0]

    # Create dict with relevant information
    infos = {
        "status": {
            "Reservation": reservation['state']
        },
        "practical_infos": {
            "Nom de la réservation": f"Reservation : {reservation['title']}",
            "Nom de l'unité": f"Unité : {reservation['asking_unit_name']}",
            "Téléphone": f"Tel : {reservation['contact_phone']}",
            "Telegram": f"Telegram : {reservation['contact_telegram']}",
            "Date d'emprunt": f"Prêt le {_get_date(reservation['start_date'])} à {_get_time(reservation['start_date'])}",
            "Date de rendu": f"Rendu le {_get_date(reservation['end_date'])} à {_get_time(reservation['end_date'])}",
        },
        "comments": {
            "Commentaire entité": reservation['reason'],
            "Commentaire respo log": reservation['remarks']
        }
    }

    # Format the dict into a string
    formatted_info = ''
    for key, value in infos["status"].items():
        formatted_info += f"{key} {telegram.helpers.escape_markdown(State.translate(value), MARKDOWN_VERSION)}\n"
    formatted_info += '\n'
    formatted_info += '*Informations pratiques*\n'
    for key, value in infos["practical_infos"].items():
        formatted_info += f'{telegram.helpers.escape_markdown(value, MARKDOWN_VERSION)}\n'
    formatted_info += '\n'
    for key, value in infos["comments"].items():
        if value is not None:
            formatted_info += f'*{key}*\n{telegram.helpers.escape_markdown(value, MARKDOWN_VERSION)}\n'
            formatted_info += '\n'

    return formatted_info


def get_reservation_page_url_from_pk(pk: int) -> str:
    return f"{TRUFFE_PATH}supplyreservation/{pk}/"


def get_agreement_url_from_pk(pk: int) -> str:
    return f"{TRUFFE_PATH}loanagreement/{pk}/pdf/"


def get_agreement_pdf_from_pk(pk: int):
    url = f"{TRUFFE_PATH}loanagreement/{pk}/pdf/"
    response = requests.get(url)
    return response.content
