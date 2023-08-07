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
import sqlite3

from web3 import Web3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from eth_account import Account
from eth_account.signers.local import LocalAccount

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Create or connect to an SQLite database
db_connection = sqlite3.connect('wallets.db')
db_cursor = db_connection.cursor()
# Create a table to store encrypted private keys
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS wallets (
        user_id INTEGER PRIMARY KEY,
        encrypted_private_key STRING
    )
''')


def create_wallet():
    account = w3.eth.account.create()
    private_key = account._private_key.hex()
    address = account.address
    return private_key, address

def encrypt_private_key(private_key, encryption_key):
    cipher_suite = Fernet(encryption_key)
    encrypted_private_key = cipher_suite.encrypt(bytes(private_key, 'utf-8'))
    return encrypted_private_key

def decrypt_private_key(encrypted_private_key, encryption_key):
    cipher_suite = Fernet(encryption_key)
    decrypted_private_key = cipher_suite.decrypt(encrypted_private_key)
    return decrypted_private_key.decode()

def generate_encryption_key(password, salt=None):
    if salt is None:
        salt = os.urandom(16)  # Generate a random salt
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        iterations=100000,  # Choose an appropriate iteration count
        salt=salt,
        length=16
    )
    key = Fernet.generate_key()
    derived_key = kdf.derive(password.encode())

    return key

def store_encrypted_private_key(user_id, encrypted_private_key):
    db_cursor.execute('INSERT INTO wallets (user_id, encrypted_private_key) VALUES (?, ?)', (user_id, encrypted_private_key))
    db_connection.commit()

def get_encrypted_private_key(user_id):
    db_cursor.execute('SELECT encrypted_private_key FROM wallets WHERE user_id = ?', (user_id,))
    encrypted_private_key = db_cursor.fetchone()
    return encrypted_private_key[0] if encrypted_private_key else None


def get_account_from_private_key(private_key):
    return Account.from_key(private_key)


def get_encrypted_private_key(user_id):
    db_cursor.execute('SELECT encrypted_private_key FROM wallets WHERE user_id = ?', (user_id,))
    encrypted_private_key = db_cursor.fetchone()
    return encrypted_private_key[0] if encrypted_private_key else None

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.message.from_user.id
    user = update.effective_user

    # Check if the user already has a wallet
    encrypted_private_key = get_encrypted_private_key(user_id)

    if encrypted_private_key:
        decrypted_private_key = decrypt_private_key(encrypted_private_key, encryption_key)
        account = get_account_from_private_key(decrypted_private_key)
        await update.message.reply_text(f'Your wallet address: {account.address}')
    else:
        private_key, address = create_wallet()

        # Encrypt the private key
        encrypted_private_key = encrypt_private_key(private_key, encryption_key)

        # Store the encrypted private key in the database
        store_encrypted_private_key(user_id, encrypted_private_key)

        await update.message.reply_text(f'Congratulations! Your new wallet address: {address}')


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

    # # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    db_connection.close()


if __name__ == "__main__":
    # Connect to BSC node (you can replace this with your preferred BSC node URL)
    w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org'))

    # Generate an encryption key (use a more secure method)
    encryption_key = os.getenv('ENCRYPTION_KEY')
    if encryption_key is None:
        encryption_key = generate_encryption_key('super_secure_password')
        print(f"NEW Encryption key generated: {encryption_key.decode}")
    main()