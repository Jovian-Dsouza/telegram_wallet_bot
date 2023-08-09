#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
"""
Wallet bot on Telegram
"""

import logging
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os

from web3_helper import *

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

## Environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.message.from_user.id
    account = wallet.get_account(user_id)
    await update.message.reply_text(f'Your wallet address: {account.address}')
    

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /balance is issued."""
    user_id = update.message.from_user.id
    account = wallet.get_account(user_id)
    balance = wallet.get_balance(account.address)
    await update.message.reply_text(f"Account Address: {account.address}\nWallet Balance: {balance} BNB")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance_command))

    # # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    # Connect to BSC node (you can replace this with your preferred BSC node URL)
    mainnet = 'https://bsc-dataseed.binance.org'
    testnet = 'https://bsc-testnet.publicnode.com'
    wallet = Wallet(testnet, ENCRYPTION_KEY)
    main()