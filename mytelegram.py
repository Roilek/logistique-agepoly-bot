import telegram

import truffe


def get_keyboard_for_res_list(states: list, displaying_all_res: bool = False) -> telegram.InlineKeyboardMarkup:
    """Returns a keyboard with all the reservations with one of the given states"""
    res_list = truffe.get_res_pk_info(states)
    keyboard = []
    for res in res_list:
        keyboard.append([telegram.InlineKeyboardButton(res[1], callback_data=res[0])])
    # if we are already displaying all the reservations, we add a button to go back to the default view
    if displaying_all_res:
        keyboard.append(
            [telegram.InlineKeyboardButton("Voir uniquement les demandes validées", callback_data="reservations")])
    else:
        keyboard.append(
            [telegram.InlineKeyboardButton("Voir les demandes non validées", callback_data="display_all_res")])
    return telegram.InlineKeyboardMarkup(keyboard)


def get_reservation_keyboard(res_pk: int) -> telegram.InlineKeyboardMarkup:
    """Returns a keyboard with the reservation page and the loan agreement"""
    keyboard = [
        [
            telegram.InlineKeyboardButton("Page du prêt", url=truffe.get_reservation_page_url_from_pk(res_pk)),
            telegram.InlineKeyboardButton("Convention", url=truffe.get_agreement_url_from_pk(res_pk))],
        [
            telegram.InlineKeyboardButton("⬅️", callback_data="reservations")
        ]
    ]
    return telegram.InlineKeyboardMarkup(keyboard)
