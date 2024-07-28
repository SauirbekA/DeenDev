import sqlite3

# Create a new SQLite database (or connect to an existing one)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create a table to store user phone numbers
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, phone_number TEXT)''')

conn.commit()
conn.close()
