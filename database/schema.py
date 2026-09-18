import sqlite3

#connect to database
connection = sqlite3.connect("database/database.db")

# create cursor
cursor = connection.cursor()

#create user table
cursor.execute("""
CREATE TABLE IF NOT EXISTS USER (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               email UNIQUE NOT NULL,
               password TEXT NOT NULL

               )
""")

# save chenges
connection.commit()

#close database
connection.close()

print("Database created succesfully!")
