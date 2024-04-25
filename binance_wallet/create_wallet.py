from web3 import Web3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import os
import sqlite3
from eth_account import Account
from eth_account.signers.local import LocalAccount

# Connect to BSC node (you can replace this with your preferred BSC node URL)
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org'))

# Create or connect to an SQLite database
db_connection = sqlite3.connect('wallets.db')
db_cursor = db_connection.cursor()

# Create a table to store encrypted private keys
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS wallets (
        address TEXT PRIMARY KEY,
        encrypted_private_key BLOB
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

def store_encrypted_private_key(address, encrypted_private_key):
    db_cursor.execute('INSERT INTO wallets (address, encrypted_private_key) VALUES (?, ?)', (address, encrypted_private_key))
    db_connection.commit()

def get_encrypted_private_key(address):
    db_cursor.execute('SELECT encrypted_private_key FROM wallets WHERE address = ?', (address,))
    encrypted_private_key = db_cursor.fetchone()
    return encrypted_private_key[0] if encrypted_private_key else None

if __name__ == '__main__':
    private_key, address = create_wallet()
    print(f'Private Key: {private_key}')
    print(f'Address: {address}')
    print("Web3 connected ",w3.is_connected())

    password = "super_secure_password"  # Replace with a strong password
    encryption_key = generate_encryption_key(password)
    print(encryption_key, "=>", len(encryption_key))

    # Encrypt the private key
    encrypted_private_key = encrypt_private_key(private_key, encryption_key)
    print(f"Encrypted private key: {encrypted_private_key}")

    # Store the encrypted private key in the database
    store_encrypted_private_key(address, encrypted_private_key)

    # Retrieve the encrypted private key from the database
    retrieved_encrypted_private_key = get_encrypted_private_key(address)


    if retrieved_encrypted_private_key:
        # Decrypt the private key
        decrypted_private_key = decrypt_private_key(retrieved_encrypted_private_key, encryption_key)
        print(f'Decrypted Private Key: {decrypted_private_key}')
        acct = Account.from_key(decrypted_private_key)
        print("Retrived Address:", acct.address)
    else:
        print(f'No encrypted private key found for address: {address}')

    db_connection.close()