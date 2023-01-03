import telegram
from telegram.ext import CallbackContext, CommandHandler, Application, CallbackQueryHandler

from env import get_environment_variables

import truffe
from truffe import State

import mytelegram

TOKEN = get_environment_variables()['TOKEN']

ACCEPT_DEFAULT_RESERVATIONS = [
    State.ONLINE.value,
    State.ASKING.value,
    State.DRAFT.value
]


async def start(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /start is issued."""
    text = "Hello! I'm the Logistic's helper bot."
    text += "\n"
    text += "send me /reservations to get the list of your reservations."
    await update.message.reply_text(text)


async def help_command(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')


async def get_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Send a list of buttons when the command /reservations is issued."""
    await update.message.reply_text('Please choose:',
                                    reply_markup=mytelegram.get_keyboard_for_res_list(ACCEPT_DEFAULT_RESERVATIONS))


async def callback_query_handler(update: telegram.Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and triggers actions accordingly."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "reservations":
        await query.edit_message_text(
            text="Please choose:",
            reply_markup=mytelegram.get_keyboard_for_res_list(ACCEPT_DEFAULT_RESERVATIONS)
        )
    elif data.isdigit():
        await develop_specific_reservations(update, context)
    else:
        await query.edit_message_text(text="Not implemented yet. Please contact @eliorpap to report this issue.")


async def develop_specific_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and send the corresponding reservation informations."""
    query = update.callback_query
    await query.answer()

    pk = int(query.data)

    # Get the reservation description
    text = truffe.get_formatted_reservation_relevant_info_from_pk(pk)

    await query.edit_message_text(text=text, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                                  reply_markup=mytelegram.get_reservation_keyboard(pk))


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('reservations', get_reservations))

    application.add_handler(CallbackQueryHandler(callback_query_handler))

    application.run_polling()


if __name__ == '__main__':
    main()
