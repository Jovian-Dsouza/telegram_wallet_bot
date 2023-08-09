import sqlite3

class DB:
    def __init__(self, database):
        # Create or connect to an SQLite database
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        # Create a table to store encrypted private keys
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                user_id INTEGER PRIMARY KEY,
                encrypted_private_key STRING
            )
        ''')
    
    def __del__(self):
        self.connection.close()

    def store_encrypted_private_key(self, user_id, encrypted_private_key):
        self.cursor.execute('INSERT INTO wallets (user_id, encrypted_private_key) VALUES (?, ?)', (user_id, encrypted_private_key))
        self.connection.commit()

    def get_encrypted_private_key(self, user_id):
        self.cursor.execute('SELECT encrypted_private_key FROM wallets WHERE user_id = ?', (user_id,))
        encrypted_private_key = self.cursor.fetchone()
        return encrypted_private_key[0] if encrypted_private_key else None

if __name__ == "__main__":
    db = DB("wallets.db")
    