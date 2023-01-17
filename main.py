import argparse
import io
import os

from telegram import Update, constants, CallbackQuery
from telegram.ext import CallbackContext, CommandHandler, Application, CallbackQueryHandler

import database
import managecalendar
import mytelegram
import truffe
from accred import Accred
from env import get_env_variables

PORT = int(os.environ.get('PORT', 5000))
ENV = get_env_variables()['ENV']
HEROKU_PATH = get_env_variables()['HEROKU_PATH']
TOKEN = get_env_variables()['TOKEN']

RESERVATION_MENU_MESSAGE = "Choisissez une reservation:"


def can_use_command(update: Update, accred: Accred) -> bool:
    """Check if the user can use the command."""
    return database.has_privilege(update.effective_user.id, accred) > 0


async def warn_cannot_use_command(update: Update, accred: Accred, context: CallbackContext = None) -> None:
    """Warn the user that he cannot use this command."""
    can_use = database.has_privilege(update.effective_user.id, accred)
    text = ""
    if can_use == -1:
        text += "You are not registered. Please use /start to get registered.\n"
        text += "If it is still not working, please contact us via logistique@agepoly.ch."
    if not can_use:
        text += "You don't have the right (anymore ?) to use this command.\n"
        text += "If you think this is an error, please contact us using /contact."
    if text != "":
        if context is None:
            await update.message.reply_text(text)
        else:
            await context.bot.send_message(chat_id=update.effective_user.id, text=text)
    return


async def start(update: Update, context: CallbackContext) -> any:
    """Send a message when the command /start is issued."""
    user_id = update.message.from_user.id
    if not database.user_exists(user_id):
        database.register_user(user_id, update.effective_user.first_name, update.effective_user.last_name,
                               update.effective_user.username)
    text = "Hello! I'm the Logistic's helper bot.\n"
    text += "send me /reservations to get the list of your reservations."
    await update.message.reply_text(text)
    return


async def forget(update: Update, context: CallbackContext) -> any:
    """Executed when the command /forget is issued."""
    if not can_use_command(update, Accred.EXTERNAL):
        await warn_cannot_use_command(update, Accred.EXTERNAL)
        return
    database.forget_user(update.effective_user.id)
    await update.message.reply_text("You have been forgotten. You can now use /start to get registered again.")
    return


async def help_command(update: Update, context: CallbackContext) -> any:
    """Send a message when the command /help is issued."""
    if not can_use_command(update, Accred.EXTERNAL):
        await warn_cannot_use_command(update, Accred.EXTERNAL)
        return
    await update.message.reply_text('Help!')
    return


async def contact_command(update: Update, context: CallbackContext) -> any:
    """Executed when the command /contact is issued."""
    if not can_use_command(update, Accred.EXTERNAL):
        await warn_cannot_use_command(update, Accred.EXTERNAL)
        return
    await update.message.reply_text("Not implemented yet. Contact @eliorpap to report this issue.")
    return


async def join(update: Update, context: CallbackContext) -> any:
    """Executed when the command /join is issued."""
    if not can_use_command(update, Accred.EXTERNAL):
        await warn_cannot_use_command(update, Accred.EXTERNAL)
        return
    text = "Si tu es un membre d'une équipe ou CdD, tu peux avoir accès à plus de commandes avec ce bot !\n"
    text += "Pour cela il faut cliquer sur le bouton le plus bas qui correspond à ton rôle dans l'AGEPoly. " \
            "Ta demande sera ensuite modérée au plus vite !\n"
    text += "Si tu n'es pas supposé avoir de droits, merci choisir 'Externe' pour ne pas nous spammer 😉\n"
    await update.message.reply_text(text, reply_markup=mytelegram.get_join_keyboard(update.effective_user.id))
    return


async def get_reservations(update: Update, context: CallbackContext) -> any:
    """Send a list of buttons when the command /reservations is issued."""
    if not can_use_command(update, Accred.TEAM_MEMBER):
        await warn_cannot_use_command(update, Accred.TEAM_MEMBER)
        return
    keyboard, page = mytelegram.get_reservations_keyboard(truffe.DEFAULT_ACCEPTED_STATES, 0)
    await update.message.reply_text(f"{RESERVATION_MENU_MESSAGE} (page {page + 1})", reply_markup=keyboard)
    return


async def update_calendar(update: Update, context: CallbackContext) -> any:
    """Executed when the command /calendar is issued."""
    if not can_use_command(update, Accred.TEAM_LEADER):
        await warn_cannot_use_command(update, Accred.TEAM_LEADER)
        return
    done = managecalendar.refresh_calendar(truffe.get_reservations())
    if done:
        await update.message.reply_text('Le calendrier a été mis à jour! 📅')
    else:
        await update.message.reply_text('Erreur lors de la mise à jour du calendrier. 😢')
    return


async def clear_calendar(update: Update, context: CallbackContext) -> any:
    """Executed when the command /clearcalendar is issued."""
    if not can_use_command(update, Accred.TEAM_LEADER):
        await warn_cannot_use_command(update, Accred.TEAM_LEADER)
        return
    done = managecalendar.clear_calendar()
    if done:
        await update.message.reply_text('Le calendrier a été vidé! 📅')
    else:
        await update.message.reply_text('Erreur lors du vidage du calendrier. 😢')
    return


async def manage_external_callbacks(update: Update, context: CallbackContext, query: CallbackQuery) -> bool:
    """Manage the callback queries from the external users."""
    data = query.data
    if data[:3] == "ask":
        if int(data[4]) == Accred.EXTERNAL.value:
            await query.edit_message_text("Merci pour ton honnêteté 😉 En tant qu'externes tu peux faire de grandes "
                                          "choses, jette à oeil à /help pour en savoir plus !")
        else:
            await mytelegram.send_join_request(update, context, Accred(int(data[4])), Accred.TEAM_LEADER)
            await query.edit_message_text("Merci pour ta demande ! Ton rôle sera modéré au plus vite !")
    elif data[:2] == "ok":
        requester_id = int(data[5:])
        database.update_accred(requester_id, Accred(int(data[3])))
        await query.edit_message_text("Le rôle a été modifié !")
        await context.bot.send_message(chat_id=requester_id,
                                       text="Ta demande a été acceptée et ton rôle a été modifié !")
    elif data[:2] == "no":
        await context.bot.send_message(chat_id=int(data[5:]),
                                       text="Ta demande a été refusée. Si tu penses qu'il s'agit d'une erreur tu peux nous contacter avec /contact !")
        await query.edit_message_text("Le reste inchangé. La personne qui a fait la demande a été prévenue.")
        pass
    else:
        return False
    return True


async def manage_log_callbacks(update: Update, context: CallbackContext, query: CallbackQuery) -> bool:
    """Manage the callback queries from the log team."""
    data = query.data
    if data == "reservations":
        keyboard, page = mytelegram.get_reservations_keyboard(truffe.DEFAULT_ACCEPTED_STATES, 0)
        await query.edit_message_text(text=f"{RESERVATION_MENU_MESSAGE} (page {page + 1})", reply_markup=keyboard)
    elif data[0:5] == "page_":
        state = data[5:8]
        state_list = truffe.DEFAULT_ACCEPTED_STATES if state == "def" else truffe.EXTENDED_ACCEPTED_STATES
        page = int(data[9:])
        keyboard, page = mytelegram.get_reservations_keyboard(state_list, page, displaying_all_res=(state == "all"))
        await query.edit_message_text(text=f"{RESERVATION_MENU_MESSAGE} (page {page + 1})", reply_markup=keyboard)
    elif data.isdigit():
        await develop_specific_reservations(update, context)
    elif data[:10] == "agreement_":
        pk = int(data[10:])
        document = io.BytesIO(truffe.get_agreement_pdf_from_pk(pk))
        await context.bot.send_document(chat_id=query.message.chat_id, document=document, filename='agreement.pdf')
    else:
        return False
    return True


async def callback_query_handler(update: Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and triggers actions accordingly."""

    query = update.callback_query
    await query.answer()

    if can_use_command(update, Accred.EXTERNAL):
        if await manage_external_callbacks(update, context, query):
            return
    if can_use_command(update, Accred.TEAM_MEMBER):
        if await manage_log_callbacks(update, context, query):
            return
    text = "Cette fonctionnalité n'est pas implémentée ou tu n'as plus les droits pour utiliser ce menu.\n"
    text += "Si tu penses que c'est une erreur, essaie d'acquérir de nouveaux droits avec /join puis contacte " \
            "nous si l'erreur persiste !"
    await query.edit_message_text(text)
    return


async def develop_specific_reservations(update: Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and send the corresponding reservation information."""
    query = update.callback_query
    await query.answer()

    pk = int(query.data)

    # Get the reservation description
    text = truffe.get_formatted_reservation_relevant_info_from_pk(pk)

    await query.edit_message_text(text=text, parse_mode=constants.ParseMode.MARKDOWN_V2,
                                  reply_markup=mytelegram.get_one_res_keyboard(pk))
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
    application.add_handler(CommandHandler('reservations', get_reservations))
    application.add_handler(CommandHandler('calendar', update_calendar))
    application.add_handler(CommandHandler('clearcalendar', clear_calendar))

    application.add_handler(CallbackQueryHandler(callback_query_handler))

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
    # asyncio.run(managecalendar.refresh_calendar(truffe.get_reservations()))
    main()
