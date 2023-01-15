import asyncio
import io
import os

import telegram
from telegram.ext import CallbackContext, CommandHandler, Application, CallbackQueryHandler

import database
import managecalendar
import mytelegram
import truffe
from env import get_env_variables

PORT = int(os.environ.get('PORT', 5000))
ENV = get_env_variables()['ENV']
HEROKU_PATH = get_env_variables()['HEROKU_PATH']
TOKEN = get_env_variables()['TOKEN']

RESERVATION_MENU_MESSAGE = "Choisissez une reservation:"


async def start(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /start is issued."""
    user_id = update.message.from_user.id
    if not database.user_exists(user_id):
        database.register_user(user_id, update.effective_user.first_name, update.effective_user.last_name,
                               update.effective_user.username)

    text = "Hello! I'm the Logistic's helper bot."
    text += "\n"
    text += "send me /reservations to get the list of your reservations."
    await update.message.reply_text(text)
    return


async def help_command(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')
    return


async def get_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Send a list of buttons when the command /reservations is issued."""
    keyboard, page = mytelegram.get_reservations_keyboard(truffe.DEFAULT_ACCEPTED_STATES, 0)
    await update.message.reply_text(f"{RESERVATION_MENU_MESSAGE} (page {page + 1})", reply_markup=keyboard)
    return


async def update_calendar(update: telegram.Update, context: CallbackContext) -> any:
    """Executed when the command /calendar is issued."""
    done = managecalendar.refresh_calendar(truffe.get_reservations())
    if done:
        await update.message.reply_text('Le calendrier a été mis à jour! 📅')
    else:
        await update.message.reply_text('Erreur lors de la mise à jour du calendrier. 😢')
    return


async def clear_calendar(update: telegram.Update, context: CallbackContext) -> any:
    """Executed when the command /clearcalendar is issued."""
    done = managecalendar.clear_calendar()
    if done:
        await update.message.reply_text('Le calendrier a été vidé! 📅')
    else:
        await update.message.reply_text('Erreur lors du vidage du calendrier. 😢')
    return


async def callback_query_handler(update: telegram.Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and triggers actions accordingly."""
    query = update.callback_query
    await query.answer()
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
        # create an `io.BytesIO` object with the file content
        file_bytes = b'Hello, World!'
        file = io.BytesIO(file_bytes)

        # send the file
        await context.bot.send_document(chat_id=query.message.chat_id, document=document, filename='agreement.pdf')
    else:
        await query.edit_message_text(text="Not implemented yet. Please contact @eliorpap to report this issue.")
    return


async def develop_specific_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and send the corresponding reservation informations."""
    query = update.callback_query
    await query.answer()

    pk = int(query.data)

    # Get the reservation description
    text = truffe.get_formatted_reservation_relevant_info_from_pk(pk)

    await query.edit_message_text(text=text, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                                  reply_markup=mytelegram.get_one_res_keyboard(pk))
    return


def main():
    """Start the bot."""
    print("Going live!")
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
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


if __name__ == '__main__':
    database.setup()
    # If in prod mode, we refresh the calendar every time the bot restarts
    if os.environ.get('ENV') == 'PROD':
        asyncio.create_task(managecalendar.refresh_calendar(truffe.get_reservations()))
    main()
