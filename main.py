import argparse
import io
import os
import re

from telegram import Update, constants
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, Application, CallbackQueryHandler, filters, MessageHandler

import database
import managecalendar
import mytelegram
import truffe
import weekdays
from accred import Accred
from env import get_env_variables

PORT = int(os.environ.get('PORT', 5000))
ENV = get_env_variables()['ENV']
HEROKU_PATH = get_env_variables()['HEROKU_PATH']
TOKEN = get_env_variables()['TOKEN']
SUPPORT_GROUP_ID = get_env_variables()['SUPPORT_GROUP_ID']

RESERVATION_MENU_MESSAGE = "Choisissez une reservation :"

DEFAULT_CONTACT = "logistique@agepoly.ch"

commands = {
    "start": {"description": "Point d'entrée du bot, indispensable pour l'utiliser", "accred": Accred.NONE},
    "forget": {"description": "Supprimer toutes les informations me concernant", "accred": Accred.EXTERNAL},
    "help": {"description": "Voir tout ce que je peux faire avec ce bot", "accred": Accred.EXTERNAL},
    "contact": {"description": "Contacter l'Équipe Logistique", "accred": Accred.EXTERNAL},
    "join": {"description": "Obtenir une nouvelle accréditation", "accred": Accred.EXTERNAL},
    "reservations": {"description": "Voir la liste des reservations", "accred": Accred.TEAM_MEMBER},
    "pdf": {"description": "Générer le pdf des réservations de la demi-journée en cours", "accred": Accred.TEAM_MEMBER},
    "calendar": {"description": "Actualiser le calendrier", "accred": Accred.TEAM_LEADER},
    "clearcalendar": {"description": "Vider le calendrier", "accred": Accred.TEAM_LEADER},
}


async def not_in_group(update: Update) -> bool:
    """Check if the update is a group."""
    if update.effective_chat.type == constants.ChatType.PRIVATE:
        return True
    else:
        await update.message.reply_text("Cette commande ne peut être utilisée que dans un échange privé avec le bot.")
        return False

def can_use_command(update: Update, accred: Accred) -> bool:
    """Check if the user can use the command."""
    return database.has_privilege(update.effective_user.id, accred) > 0


async def warn_cannot_use_command(update: Update, accred: Accred, context: CallbackContext = None) -> None:
    """Warn the user that he cannot use this command."""
    can_use = database.has_privilege(update.effective_user.id, accred)
    text = ""
    if can_use == -1:
        text += "Tu n'es pas enregistré·e. Merci d'utiliser /start pour t'enregistrer\n"
        text += f"Si cela ne fonctionne toujours pas, tu peux nous contacter via {DEFAULT_CONTACT}."
    if not can_use:
        text += "Tu n'as pas le droit d'utiliser cette commande.\n"
        text += "Si tu penses qu'il s'agit d'une erreur, merci de nous contacter en utilisant /contact."
    if text != "":
        if context is None:
            await update.message.reply_text(text)
        else:
            await context.bot.send_message(chat_id=update.effective_user.id, text=text)
    return


async def invalid_command(update: Update, context: CallbackContext) -> any:
    """Executed when an invalid command is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    await update.message.reply_text(
        "Invalid command. Send me /help to know what you can do! If you think this is an error, please contact us "
        "using /contact.")
    return


async def start(update: Update, context: CallbackContext) -> any:
    """Send a message when the command /start is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    user_id = update.message.from_user.id
    if not database.user_exists(user_id):
        database.register_user(user_id, update.effective_user.first_name, update.effective_user.last_name,
                               update.effective_user.username)
    text = "Bonjour ! Je suis le bot de l'Équipe Logistique de l'AGEPoly,\n"
    text += "Je sers de point de contact centralisé pour toutes vos questions et remarques concernant la logistique opérationnelle de l'AGEPoly.\n"
    text += "Sachez que beaucoup d'informations sont disponibles dans <a href='https://wiki2.agepoly.ch/logistique'>notre wiki</a>, merci donc de vérifier que la réponse à votre question ne s'y trouve pas déjà !\n"
    text += "Si besoin, n'hésitez pas à nous contacter en envoyant /contact.\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return


async def forget(update: Update, context: CallbackContext) -> any:
    """Executed when the command /forget is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    if not await not_in_group(update):
        return
    if not can_use_command(update, commands["forget"]["accred"]):
        await warn_cannot_use_command(update, commands["forget"]["accred"])
        return
    database.forget_user(update.effective_user.id)
    await update.message.reply_text("You have been forgotten. You can now use /start to get registered again.")
    return


async def help_command(update: Update, context: CallbackContext) -> any:
    """Send a message when the command /help is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    if not can_use_command(update, commands["help"]["accred"]):
        await warn_cannot_use_command(update, commands["help"]["accred"])
        return
    text = "Here is a list of all the commands you can use:\n"
    for command in filter(lambda x: can_use_command(update, commands[x]["accred"]), commands):
        text += f"/{command} - {commands[command]['description']}\n"
    await update.message.reply_text(text)
    return


async def contact_command(update: Update, context: CallbackContext) -> any:
    """Executed when the command /contact is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    if not await not_in_group(update):
        return
    if not can_use_command(update, commands["contact"]["accred"]):
        await warn_cannot_use_command(update, commands["contact"]["accred"])
        return
    await update.message.reply_text(
        f"Envoyez-moi le message que vous voulez, il sera transmis à l'Équipe Logistique qui vous répondra au plus vite !\nAssurez-vous cependant d'avoir bien vérifié que la réponse à votre question ne se trouve pas dans <a href='https://wiki2.agepoly.ch/logistique'>le wiki</a> !", parse_mode=ParseMode.HTML)
    return


async def handle_messages(update: Update, context: CallbackContext) -> any:
    """Handle messages."""
    # Is starts with '/' then it is a failed command attempt
    pattern = r'^\/.*'
    if update.message.text is not None and re.match(pattern, update.message.text):
        return await invalid_command(update, context)

    database.log_message(update.effective_user.id, update.message.text)
    # If the user is not registered, he cannot use the bot
    if not database.user_exists(update.effective_user.id):
        await update.message.reply_text(
            "Il faut être enregistré·e pour pouvoir discuter avec nous ! Merci d'utiliser /start pour t'enregistrer")
        return
    # If the message is an answer to a contact message, send it back to the user
    message = update.message
    reply_to = message.reply_to_message

    if message.chat_id == SUPPORT_GROUP_ID:
        original_message = database.get_original_message(reply_to.id) if reply_to is not None else None
        if original_message is not None:
            copy_message_id = (await message.copy(chat_id=original_message["chat_id"],
                                                  reply_to_message_id=original_message["original_id"])).message_id
            database.add_message(message.id, copy_message_id, message.chat_id, message.text, reply_to.id)
        elif message.chat_id != SUPPORT_GROUP_ID:
            await message.reply_text(
                "Je n'ai pas retrouvé le message original et ne peux donc pas transmettre la réponse :(")
    else:
        original_message_id = None
        if reply_to is not None:
            original_message_id = database.get_original_message(reply_to.id)["original_id"]
        if message.text is not None:
            # If there is text, we can edit it
            copy_message_id = (await message.copy(chat_id=SUPPORT_GROUP_ID,
                                                  reply_to_message_id=original_message_id)).message_id
            text = f"<b>{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}</b> {'(@'+message.from_user.username+')' if message.from_user.username else ''}\n{message.text}"
            await context.bot.edit_message_text(chat_id=SUPPORT_GROUP_ID, message_id=copy_message_id,
                                                text=text, parse_mode=ParseMode.HTML,
                                                #reply_markup=mytelegram.get_close_ticket_keyboard(update)
                                                )
            database.add_message(message.id, copy_message_id, message.chat_id, message.text,
                                 reply_to.id if reply_to else None)
        else:
            # If there is no text, we cannot edit it and have to forward the message if we are not replying
            if original_message_id is not None:
                copy_message_id = (await message.copy(chat_id=SUPPORT_GROUP_ID,
                                                      reply_to_message_id=original_message_id)).message_id
                database.add_message(message.id, copy_message_id, message.chat_id, None,
                                     reply_to.id)
            else:
                new_message_id = (await message.forward(chat_id=SUPPORT_GROUP_ID)).id
                database.add_message(message.id, new_message_id, message.chat_id, None)
    return


async def join(update: Update, context: CallbackContext) -> any:
    """Executed when the command /join is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    if not await not_in_group(update):
        return
    if not can_use_command(update, commands["join"]["accred"]):
        await warn_cannot_use_command(update, commands["join"]["accred"])
        return
    text = "Si tu es un·e membre d'une équipe ou CdD, tu peux avoir accès à plus de commandes avec ce bot !\n"
    text += "Pour cela, il faut cliquer sur le bouton le plus bas qui correspond à ton rôle dans l'AGEPoly. " \
            "Ta demande sera ensuite modérée au plus vite !\n"
    text += "Si tu n'es pas supposé·e avoir de droits, merci de choisir 'Externe' pour ne pas nous spammer 😉\n"
    await update.message.reply_text(text, reply_markup=mytelegram.get_join_keyboard(update.effective_user.id))
    return


async def get_reservations(update: Update, context: CallbackContext) -> any:
    """Send a list of buttons when the command /reservations is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    if not await not_in_group(update):
        return
    if not can_use_command(update, commands["reservations"]["accred"]):
        await warn_cannot_use_command(update, commands["reservations"]["accred"])
        return
    keyboard, page = mytelegram.get_reservations_keyboard(truffe.DEFAULT_ACCEPTED_STATES, 0)
    await update.message.reply_text(f"{RESERVATION_MENU_MESSAGE} (page {page + 1})", reply_markup=keyboard)
    return


async def get_pdf(update: Update, context: CallbackContext) -> any:
    """Send a pdf with all the pdfs of the current half day"""
    database.log_command(update.effective_user.id, update.message.text)
    if not await not_in_group(update):
        return
    if not can_use_command(update, commands["pdf"]["accred"]):
        await warn_cannot_use_command(update, commands["pdf"]["accred"])
        return

    # Args processing
    args = context.args
    states = truffe.DEFAULT_ACCEPTED_STATES
    day = None
    mor = None
    fut = True
    for arg in args:
        if arg in ("a", "all"):
            states = truffe.EXTENDED_ACCEPTED_STATES
        elif arg in ("0", "am", "matin", "morning"):
            mor = True
        elif arg in ("1", "pm", "après-midi", "afternoon"):
            mor = False
        elif arg in ("o", "old"):
            fut = False
        else:
            wd = weekdays.Weekday.of(arg)
            if wd is not None:
                day = int(wd)

    # response to the user and pdf generation
    wait_message = await update.message.reply_text("PDF en génération. Merci de patienter...")
    pks_list = list(map(lambda res: res['pk'], truffe.get_reservations_half_day(states, day, mor, fut)))
    if len(pks_list) > 0:
        agreements = truffe.get_agreements_pdf_merged_from_pks(pks_list)
        await update.message.reply_document(agreements, filename="agreements.pdf",
                                            reply_markup=mytelegram.delete_message_keyboard(update, "Supprimer le PDF"))
    else:
        await update.message.reply_text("Il n'y a pas de réservations pour cette demi-journée.")
    await wait_message.delete()


async def update_calendar(update: Update, context: CallbackContext) -> any:
    """Executed when the command /calendar is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    if not await not_in_group(update):
        return
    if not can_use_command(update, commands["calendar"]["accred"]):
        await warn_cannot_use_command(update, commands["calendar"]["accred"])
        return
    done = managecalendar.refresh_calendar(truffe.get_reservations())
    if done:
        await update.message.reply_text('Le calendrier a été mis à jour! 📅')
    else:
        await update.message.reply_text('Erreur lors de la mise à jour du calendrier. 😢')
    return


async def clear_calendar(update: Update, context: CallbackContext) -> any:
    """Executed when the command /clearcalendar is issued."""
    database.log_command(update.effective_user.id, update.message.text)
    if not await not_in_group(update):
        return
    if not can_use_command(update, commands["clearcalendar"]["accred"]):
        await warn_cannot_use_command(update, commands["clearcalendar"]["accred"])
        return
    done = managecalendar.clear_calendar()
    if done:
        await update.message.reply_text('Le calendrier a été vidé! 📅')
    else:
        await update.message.reply_text('Erreur lors du vidage du calendrier. 😢')
    return


async def manage_external_callbacks(update: Update, context: CallbackContext, args: list[str]) -> bool:
    """Manage the callback queries from the external users."""
    query = update.callback_query
    if args[0] == "ask":
        if int(args[1]) == Accred.EXTERNAL.value:
            await query.edit_message_text("Merci pour ton honnêteté 😉 En tant qu'externes tu peux faire de grandes "
                                          "choses, jette à oeil à /help pour en savoir plus !")
        else:
            await mytelegram.send_join_request(update, context, Accred(int(args[1])), Accred.TEAM_LEADER)
            await query.edit_message_text("Merci pour ta demande ! Ton rôle sera modéré au plus vite !")
    elif args[0] == "ok":
        requester_id = int(args[2])
        database.update_accred(requester_id, Accred(int(args[1])))
        await query.edit_message_text("Le rôle a été modifié !")
        await context.bot.send_message(chat_id=requester_id,
                                       text="Ta demande a été acceptée et ton rôle a été modifié !")
    elif args[0] == "no":
        await context.bot.send_message(chat_id=int(args[2]),
                                       text=f"Ta demande d'accréditation en tant que {Accred(int(args[1]))} a été "
                                            f"refusée. Si tu penses qu'il s'agit d'une erreur tu peux nous contacter "
                                            f"avec /contact !")
        await query.edit_message_text("Le rôle reste inchangé. La personne qui a fait la demande a été prévenue.")
    elif args[0] == "delete":
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    else:
        return False
    return True


async def manage_log_callbacks(update: Update, context: CallbackContext, args: list[str]) -> bool:
    """Manage the callback queries from the log team."""
    query = update.callback_query
    if args[0] == "reservations":
        state = args[1]
        state_list = truffe.DEFAULT_ACCEPTED_STATES if state == "def" else truffe.EXTENDED_ACCEPTED_STATES
        keyboard, page = mytelegram.get_reservations_keyboard(states=state_list,
                                                              page=int(args[2]),
                                                              displaying_all_res=(state == "all"))
        await query.edit_message_text(text=f"{RESERVATION_MENU_MESSAGE} (page {page + 1})", reply_markup=keyboard)
    elif args[0] == "page":
        state = args[1]
        state_list = truffe.DEFAULT_ACCEPTED_STATES if state == "def" else truffe.EXTENDED_ACCEPTED_STATES
        page = int(args[2])
        keyboard, page = mytelegram.get_reservations_keyboard(state_list, page, displaying_all_res=(state == "all"))
        await query.edit_message_text(text=f"{RESERVATION_MENU_MESSAGE} (page {page + 1})", reply_markup=keyboard)
    elif args[0].isdigit():
        pk = int(args[0])
        text = truffe.get_formatted_reservation_relevant_info_from_pk(pk)
        await query.edit_message_text(text=text, parse_mode=constants.ParseMode.MARKDOWN_V2,
                                      reply_markup=mytelegram.get_one_res_keyboard(pk,
                                                                                   page=int(args[2]),
                                                                                   displaying_all_res=(args[1] == "all")))
    elif args[0] == "agreement":
        pk = int(args[1])
        document = io.BytesIO(truffe.get_agreement_pdf_from_pk(pk))
        await context.bot.send_document(chat_id=query.message.chat_id, document=document, filename='agreement.pdf', reply_markup=mytelegram.delete_message_keyboard(update, "Supprimer le PDF"))
    else:
        return False
    return True


async def callback_query_handler(update: Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and triggers actions accordingly."""
    query = update.callback_query
    database.log_callback(update.effective_user.id, query.data)
    await query.answer()

    args = query.data.split('_')
    if can_use_command(update, Accred.EXTERNAL):
        if await manage_external_callbacks(update, context, args):
            return
    if can_use_command(update, Accred.TEAM_MEMBER):
        if await manage_log_callbacks(update, context, args):
            return
    text = "Cette fonctionnalité n'est pas implémentée ou tu n'as plus les droits pour utiliser ce menu.\n"
    text += "Si tu penses que c'est une erreur, essaie d'acquérir de nouveaux droits avec /join puis contacte " \
            "nous si l'erreur persiste !"
    await query.edit_message_text(text)
    return


def main() -> None:
    """Start the bot."""
    parser = argparse.ArgumentParser()
    parser.add_argument("function",
                        nargs='?',
                        help="The function to execute",
                        choices=["refresh_calendar", "expire_accreds"])
    args = parser.parse_args()

    if args.function == "refresh_calendar":
        managecalendar.refresh_calendar(truffe.get_reservations())
        return
    elif args.function == "expire_accreds":
        database.expire_accreds()
        return

    print("Going live!")
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('forget', forget))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('contact', contact_command))
    application.add_handler(CommandHandler('join', join))
    application.add_handler(CommandHandler(['reservations', 'res'], get_reservations))
    application.add_handler(CommandHandler('pdf', get_pdf))
    application.add_handler(CommandHandler('calendar', update_calendar))
    application.add_handler(CommandHandler('clearcalendar', clear_calendar))

    application.add_handler(CallbackQueryHandler(callback_query_handler))

    application.add_handler(MessageHandler(filters.COMMAND, invalid_command))
    application.add_handler(MessageHandler(filters.ALL & (~filters.StatusUpdate.ALL), handle_messages))

    print("Bot starting...")
    if os.environ.get('ENV') == 'TEST':
        application.run_polling()
    elif os.environ.get('ENV') == 'PROD':
        application.run_webhook(listen="0.0.0.0",
                                port=int(PORT),
                                webhook_url=HEROKU_PATH,
                                secret_token="tapontapon")
    return


def refresh_calendar() -> None:
    """Refresh the calendar."""
    print("Refreshing calendar...")
    managecalendar.refresh_calendar(truffe.get_reservations())
    return


if __name__ == '__main__':
    database.setup()
    main()
