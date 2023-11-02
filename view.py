import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('healthdb.py')  # Replace 'your_database.db' with your database file

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Example: View all the tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

# Example: View the contents of a table
cursor.execute("SELECT * FROM patients;")  # Replace 'YourTableName' with the name of your table
rows = cursor.fetchall()
for row in rows:
    print(row)

# Commit the changes and close the connection
conn.close()