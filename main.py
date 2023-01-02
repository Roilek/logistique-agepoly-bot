import telegram
from telegram.ext import CallbackContext, Updater, CommandHandler, Application

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('TOKEN')


async def start(update: telegram.Update, context: CallbackContext) -> any:
    await update.message.reply_text('Hi!')
    return


async def help_command(update: telegram.Update, context: CallbackContext) -> any:
    await update.message.reply_text('Help!')
    return


def main():
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.run_polling()
    return


if __name__ == '__main__':
    main()
