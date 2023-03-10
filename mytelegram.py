import telegram
from telegram import Update
from telegram.ext import CallbackContext

import database
import truffe
from accred import Accred
from main import DEFAULT_CONTACT

MAX_RES_PER_PAGE = 10


def get_reservations_keyboard(states: list, page: int, displaying_all_res: bool = False) -> (
        telegram.InlineKeyboardMarkup, int):
    """Returns a keyboard with the reservations of the given states, starting at the given page."""
    res_list = truffe.get_res_pk_info(states)
    keyboard = []
    while len(res_list) <= page * MAX_RES_PER_PAGE:
        page -= 1
    disp = "all" if displaying_all_res else "def"
    for res in res_list[page * MAX_RES_PER_PAGE: (page + 1) * MAX_RES_PER_PAGE]:
        keyboard.append([telegram.InlineKeyboardButton(res[1], callback_data='_'.join([str(res[0]), disp, str(page)]))])

    # If we are already displaying all the reservations, we add a button to go back to the default view
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            telegram.InlineKeyboardButton("⬅️", callback_data=f"page_{disp}_{page - 1}")
        )
    if displaying_all_res:
        navigation_buttons.append(
            telegram.InlineKeyboardButton("Voir validées", callback_data=f"page_def_{page}")
        )
    else:
        navigation_buttons.append(
            telegram.InlineKeyboardButton("Voir Toutes", callback_data=f"page_all_{page}")
        )
    if len(res_list) > (page + 1) * MAX_RES_PER_PAGE:
        navigation_buttons.append(
            telegram.InlineKeyboardButton("➡️", callback_data=f"page_{disp}_{page + 1}")
        )
    keyboard.append(navigation_buttons)
    return telegram.InlineKeyboardMarkup(keyboard), page


def get_one_res_keyboard(res_pk: int, page: int, displaying_all_res: bool) -> telegram.InlineKeyboardMarkup:
    """Returns a keyboard with the reservation page and the loan agreement"""
    disp = "all" if displaying_all_res else "def"
    keyboard = [
        [
            telegram.InlineKeyboardButton("Page du prêt", url=truffe.get_reservation_page_url_from_pk(res_pk)),
            telegram.InlineKeyboardButton("Convention", url=truffe.get_agreement_url_from_pk(res_pk))],
        [
            telegram.InlineKeyboardButton("⬅️", callback_data='_'.join(["reservations", disp, str(page)])),
            telegram.InlineKeyboardButton("Get PDF", callback_data=f"agreement_{res_pk}"),
        ]
    ]
    return telegram.InlineKeyboardMarkup(keyboard)


def get_join_keyboard(user_id: int) -> telegram.InlineKeyboardMarkup:
    """Returns a keyboard with the link to join the group"""
    keyboard = [
        [telegram.InlineKeyboardButton(str(accred), callback_data="_".join(["ask", str(accred.value), str(user_id)]))]
        for accred in Accred]
    return telegram.InlineKeyboardMarkup(keyboard)


async def send_join_request(update: Update, context: CallbackContext, accred_req: Accred, accred_validator: Accred) -> None:
    """Sends a message to the group to ask for the user to join the group"""
    user = update.effective_user
    keyboard = [
        [telegram.InlineKeyboardButton(f"Accred {user.first_name} as {accred_req}", callback_data="_".join(["ok", str(accred_req.value), str(user.id)]))],
        [telegram.InlineKeyboardButton("Deny", callback_data="_".join(["no", str(accred_req.value), str(user.id)]))]
    ]
    ids = database.get_users_by_accred_extended(accred_validator.value)
    if ids:
        for chat_id in ids:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{user.first_name} ({user.id}) souhaite obtenir le rôle de {accred_req}!\n"
                     f"Son username est @{user.username}.\n" if user.username else ""
                     f"Son rôle actuel est {Accred(database.get_accred(user.id))}.\n",
                reply_markup=telegram.InlineKeyboardMarkup(keyboard)
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Aucun administrateur n'est enregistré pour le moment. "
                 f"Merci d'envoyer un email à {DEFAULT_CONTACT} pour que cela soit réglé."
        )
