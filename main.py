import telegram
from telegram.ext import CallbackContext, CommandHandler, Application, CallbackQueryHandler

from env import get_environment_variables

import truffe
from truffe import State

TOKEN = get_environment_variables()['TOKEN']

ACCEPT_DEFAULT_RESERVATIONS = [
    State.ONLINE.value,
    State.ASKING.value,
    State.DRAFT.value
]


async def start(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi!')


async def help_command(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message when the command /help is issued."""
    await update.message.reply_text('Help!')


async def get_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Send a list of buttons when the command /reservations is issued."""
    keyboard = []
    buttons = truffe.get_res_pk_name_from_truffe(ACCEPT_DEFAULT_RESERVATIONS)
    for button in buttons:
        keyboard.append([telegram.InlineKeyboardButton(button[1], callback_data=button[0])])
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose:', reply_markup=reply_markup)


async def develop_specific_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Detects that a button has been pressed and send the corresponding reservation informations."""
    query = update.callback_query
    await query.answer()
    text = truffe.get_formatted_reservation_relevant_info_from_pk(query.data)
    await query.edit_message_text(text=text, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('reservations', get_reservations))

    application.add_handler(CallbackQueryHandler(develop_specific_reservations))
    application.run_polling()


if __name__ == '__main__':
    main()
