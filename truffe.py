import requests
from main import TRUFFE_TOKEN


def get_reservations_from_truffe() -> any:
    """Returns a JSON of all the 0_draft, 1_asking, 2_online reservations"""
    infos = ['asking_unit_name', 'contact_telegram', 'start_date', 'end_date', 'contact_phone', 'reason', 'remarks','agreement']
    url = "https://truffe2.agepoly.ch/logistics/api/supplyreservations?" + '&'.join(infos)

    headers = {"Accept": "application/json", "Authorization": "Bearer " + TRUFFE_TOKEN}
    resp = requests.get(url, headers=headers)
    return resp.json()

