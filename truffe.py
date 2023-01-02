import requests

from env import get_environment_variables

TRUFFE_TOKEN = get_environment_variables()['TRUFFE_TOKEN']


# Enum of states as str
class State:
    DRAFT = '0_draft'
    ASKING = '1_asking'
    ONLINE = '2_online'
    # Will need to be updated if more states are added


def _get_json_from_truffe() -> any:
    """Returns a json of all the reservations"""
    infos = ['asking_unit_name', 'contact_telegram', 'start_date', 'end_date', 'contact_phone', 'reason', 'remarks',
             'agreement']
    url = "https://truffe2.agepoly.ch/logistics/api/supplyreservations?" + '&'.join(infos)

    headers = {"Accept": "application/json", "Authorization": "Bearer " + TRUFFE_TOKEN}
    reservations = requests.get(url, headers=headers)

    return reservations.json()


def _get_all_reservations_from_truffe() -> list[dict]:
    """Returns a list of all the reservations"""
    return _get_json_from_truffe()['supplyreservations']


def _get_specific_states_reservations_from_truffe(*states) -> list[dict]:
    """Returns a list of all the reservations with one of the given states"""
    reservations = _get_all_reservations_from_truffe()
    return list(filter(lambda res: res['state'] in states, reservations))


def _get_res_pk_name_from_list(res_list: list[dict]) -> list[tuple[str, str]]:
    """Returns a list of tuples of the form (pk, name) from a list of reservations"""
    return [(str(res['pk']), res['asking_unit_name']) for res in res_list]


def _remove_external_difference(res_list: list[dict]) -> list[dict]:
    """Remove the difference between a reservation of an external unit and a reservation of an internal unit"""
    # fill the asking_unit_name field of the dict with the concatenation of the asking_external_unit and the
    # asking_external_person
    for res in res_list:
        if res['asking_unit_name'] is None:
            res['asking_unit_name'] = res['asking_external_unit'] + ' (' + res['asking_external_person'] + ')'
    return res_list


def get_res_pk_name_from_truffe(*states) -> list[tuple[str, str]]:
    """Returns a list of tuples of the form (pk, name) from a list of reservations with one of the given states"""
    return _get_res_pk_name_from_list(_remove_external_difference(_get_specific_states_reservations_from_truffe(*states)))
