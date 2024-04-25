from web3_helper import *

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    testnet = 'https://bsc-testnet.publicnode.com'
    wallet = Wallet(testnet, ENCRYPTION_KEY)

    private_key = os.getenv('PRIVATE_KEY1')
    account = wallet.get_account_from_private_key(private_key)
    balance = wallet.get_balance(account.address)
    print(f"Account Address: {account.address}\nWallet Balance: {balance} BNB")

    recipient_address = "0x8db7e2f504c915A0aC40176581775c72186F888B"
    wallet.send(account, recipient_address, 0.01)

    balance = wallet.get_balance(account.address)
    print(f"Account Address: {account.address}\nWallet Balance: {balance} BNB")