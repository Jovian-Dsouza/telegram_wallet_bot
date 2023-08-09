from web3 import Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from eth_account import Account
from eth_account.signers.local import LocalAccount

from db_helper import DB

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

class Wallet:
    def __init__(self, network_url, encryption_key, chain_id=97, database="wallets.db"):
        self.w3 = Web3(Web3.HTTPProvider(network_url))
        self.w3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
        self.chain_id = chain_id

        self.encryption_key = encryption_key
        self.db = DB(database)

    def create_wallet(self):
        account = self.w3.eth.account.create()
        private_key = account._private_key.hex()
        address = account.address
        return private_key, address

    def get_account_from_private_key(self, private_key):
        return Account.from_key(private_key)

    def get_account(self, user_id):
        # Check if the user already has a wallet
        encrypted_private_key = self.db.get_encrypted_private_key(user_id)
        if encrypted_private_key:
            decrypted_private_key = decrypt_private_key(encrypted_private_key, self.encryption_key)
            account = self.get_account_from_private_key(decrypted_private_key)
            return account
        else:
            private_key, address = self.create_wallet()
            # Encrypt the private key
            encrypted_private_key = encrypt_private_key(private_key, self.encryption_key)
            # Store the encrypted private key in the database
            self.db.store_encrypted_private_key(user_id, encrypted_private_key)
            return self.get_account_from_private_key(private_key)
            
    def get_balance(self, address):
        # Get the balance in Wei (smallest unit of BNB)
        balance_wei = self.w3.eth.get_balance(address)
        # Convert Wei to BNB (1 BNB = 10^18 Wei)
        balance_bnb = self.w3.from_wei(balance_wei, 'ether')
        return balance_bnb
    
    def send(self, sender_account, recipient_address, amount, gas_limit=None, gas_price=None):
        amount_wei =  self.w3.to_wei(amount, 'ether') # amount in wei
        if gas_limit is None:
            gas_limit = self.w3.eth.estimate_gas({
                'to': recipient_address,
                'value': amount_wei
            })
        
        if gas_price is None:
            gas_price = self.w3.eth.generate_gas_price()

        transaction = {
            'nonce': self.w3.eth.get_transaction_count(sender_account.address),
            'to': recipient_address,
            'value': amount_wei,
            'gas': gas_limit, 
            'gasPrice': gas_price,
            'chainId': self.chain_id
        }

        # Sign the transaction
        signed_transaction = self.w3.eth.account.sign_transaction(transaction, self.w3.to_hex(sender_account._private_key))

        # # Send the transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        tx_hash = self.w3.to_hex(tx_hash)

        reciept = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        status = "Successful" if reciept['status'] == 1 else "Failed"
        print(f"Transaction {tx_hash} is {status}")