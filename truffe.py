import enum
import time

import requests
import telegram

from env import get_environment_variables

TRUFFE_TOKEN = get_environment_variables()['TRUFFE_TOKEN']

last_update = None
truffe_cache = {}

STATE_MAPPING = {
    '0_draft': 'en brouillon',
    '1_asking': 'en cours de validation',
    '2_online': 'validée',
}
MARKDOWN_VERSION = 2


# Enum of states as str
class State(enum.Enum):
    DRAFT = '0_draft'
    ASKING = '1_asking'
    ONLINE = '2_online'

    # Will need to be updated if more states are added

    @classmethod
    def all_names(cls):
        return [state.name for state in cls]

    @classmethod
    def all_values(cls):
        return [state.value for state in cls]

    @classmethod
    def translate(cls, value):
        return STATE_MAPPING[value]


def _remove_external_difference(res_list: list[dict]) -> list[dict]:
    """Remove the difference between a reservation of an external unit and a reservation of an internal unit"""
    # fill the asking_unit_name field with the concatenation of the asking_external_unit and the asking_external_person
    for res in res_list:
        if res['asking_unit_name'] is None:
            res['asking_unit_name'] = res['asking_external_unit'] + ' (' + res['asking_external_person'] + ')'
    return res_list


def _get_json_from_truffe() -> any:
    """Returns a json of all the reservations"""
    # Refresh truffe cache every 10 minutes
    global last_update
    global truffe_cache
    if last_update is None or last_update + 60 < time.time():
        infos = ['asking_unit_name', 'contact_telegram', 'start_date', 'end_date', 'contact_phone', 'reason', 'remarks',
                 'agreement']
        url = "https://truffe2.agepoly.ch/logistics/api/supplyreservations?" + '&'.join(infos)

        headers = {"Accept": "application/json", "Authorization": "Bearer " + TRUFFE_TOKEN}
        reservations = requests.get(url, headers=headers)
        truffe_cache = reservations.json()
        last_update = time.time()

    return truffe_cache


def _get_all_reservations_from_truffe(aggregate_external=False) -> list[dict]:
    """Returns a list of all the reservations"""
    reservations = _get_json_from_truffe()['supplyreservations']
    return _remove_external_difference(reservations) if aggregate_external else reservations


def _get_specific_states_reservations_from_truffe(states: list) -> list[dict]:
    """Returns a list of all the reservations with one of the given states
    :param states:
    """
    reservations = _get_all_reservations_from_truffe(True)
    return list(filter(lambda res: res['state'] in states, reservations))


def _get_res_pk_name_from_list(res_list: list[dict]) -> list[tuple[int, str]]:
    """Returns a list of tuples of the form (pk, name) from a list of reservations"""
    return [(res['pk'], res['asking_unit_name']) for res in res_list]


def get_res_pk_name_from_truffe(states: list) -> list[tuple[int, str]]:
    """Returns a list of tuples of the form (pk, name) from a list of reservations with one of the given states"""
    return _get_res_pk_name_from_list(_get_specific_states_reservations_from_truffe(states))


def _get_reservation_from_truffe(data: str) -> dict:
    """Returns a reservation's dict from its pk"""
    reservations = _get_specific_states_reservations_from_truffe(State.all_values())
    return list(filter(lambda res: res['pk'] == int(data), reservations))[0]


def get_formatted_reservation_relevant_info_from_pk(pk: str) -> str:
    """Returns a formatted string with the relevant information of a reservation from its pk"""
    reservation = _get_reservation_from_truffe(pk)

    # Create dict with relevant information
    infos = {
        "status": {
            "Reservation": reservation['state']
        },
        "practical_infos": {
            "Nom de la réservation": reservation['title'],
            "Nom de l'unité": reservation['asking_unit_name'],
            "Téléphone": reservation['contact_phone'],
            "Telegram": reservation['contact_telegram'],
            "Date d'emprunt": reservation['start_date'],
            "Date de rendu": reservation['end_date'],
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
        formatted_info += f'{telegram.helpers.escape_markdown(value,MARKDOWN_VERSION)}\n'
    formatted_info += '\n'
    for key, value in infos["comments"].items():
        if value is not None:
            formatted_info += f'*{key}*\n{telegram.helpers.escape_markdown(value,MARKDOWN_VERSION)}\n'
            formatted_info += '\n'

    return formatted_info


def get_agreement_link_from_pk(pk: str) -> str:
    """Returns the link to the agreement of a reservation from its pk"""
    reservation = _get_reservation_from_truffe(pk)
    return reservation['agreement']
