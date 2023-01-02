import telegram
from telegram.ext import CallbackContext, Updater, CommandHandler, Application

from env import get_environment_variables

import truffe
from truffe import State


TOKEN = get_environment_variables()['TOKEN']


async def start(update: telegram.Update, context: CallbackContext) -> any:
    await update.message.reply_text('Hi!')


async def help_command(update: telegram.Update, context: CallbackContext) -> any:
    await update.message.reply_text('Help!')


async def get_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message to the user with buttons to click"""
    keyboard = []
    buttons = truffe.get_res_pk_name_from_truffe(State.ONLINE)
    for button in buttons:
        keyboard.append([telegram.InlineKeyboardButton(button[1], callback_data=button[0])])
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose:', reply_markup=reply_markup)


def main():
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('reservations', get_reservations))
    application.run_polling()


if __name__ == '__main__':
    main()
