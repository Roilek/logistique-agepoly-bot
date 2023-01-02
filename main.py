import telegram
from telegram.ext import CallbackContext, Updater, CommandHandler, Application

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('TOKEN')
TRUFFE_TOKEN = os.environ.get('TRUFFE_TOKEN')


async def start(update: telegram.Update, context: CallbackContext) -> any:
    await update.message.reply_text('Hi!')
    return


async def help_command(update: telegram.Update, context: CallbackContext) -> any:
    await update.message.reply_text('Help!')
    return


async def get_reservations(update: telegram.Update, context: CallbackContext) -> any:
    """Send a message to the user with buttons to click"""
    keyboard = []
    buttons = [str(i) for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
    for button in buttons:
        keyboard.append([telegram.InlineKeyboardButton(button, callback_data=button)])
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return


def main():
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('reservations', get_reservations))
    application.run_polling()
    return


if __name__ == '__main__':
    main()
