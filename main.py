import time

import telegram
from telegram.ext import CallbackContext, CommandHandler, Application, CallbackQueryHandler

import os

from env import get_environment_variables

import truffe
import mytelegram
import managecalendar

PORT = int(os.environ.get('PORT', 5000))
ENV = get_environment_variables()['ENV']
HEROKU_PATH = get_environment_variables()['HEROKU_PATH']
TOKEN = get_environment_variables()['TOKEN']

async def start(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /start is issued."""
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
    await update.message.reply_text('Please choose:',
                                    reply_markup=mytelegram.get_keyboard_for_res_list(truffe.DEFAULT_ACCEPTED_STATES))
    return


async def update_calendar(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /calendar is issued."""
    done = managecalendar.hard_refresh(truffe.get_reservations())
    if done:
        await update.message.reply_text('Le calendrier a été mis à jour! 📅')
    else:
        await update.message.reply_text('Erreur lors de la mise à jour du calendrier. 😢')
    return


async def callback_query_handler(update: telegram.Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and triggers actions accordingly."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "reservations":
        await query.edit_message_text(
            text="Please choose:",
            reply_markup=mytelegram.get_keyboard_for_res_list(truffe.DEFAULT_ACCEPTED_STATES)
        )
    elif data.isdigit():
        await develop_specific_reservations(update, context)
    elif data == "display_all_res":
        await query.edit_message_text(
            text="Please choose:",
            reply_markup=mytelegram.get_keyboard_for_res_list(truffe.EXTENDED_ACCEPTED_STATES, displaying_all_res=True)
        )
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
                                  reply_markup=mytelegram.get_reservation_keyboard(pk))
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

    application.add_handler(CallbackQueryHandler(callback_query_handler))
    time.sleep(5)
    print(HEROKU_PATH + TOKEN)
    print("Bot starting...")
    if os.environ.get('ENV') == 'TEST':
        application.run_polling()
    elif os.environ.get('ENV') == 'PROD':
        application.run_webhook(listen="0.0.0.0",
                                port=int(PORT),
                                url_path=TOKEN)
        application.bot.setWebhook(HEROKU_PATH + TOKEN)
    return


if __name__ == '__main__':
    main()
