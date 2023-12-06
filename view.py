import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('healthdb.db')  # Replace 'your_database.db' with your database file

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# apt_id, patient_email, doctor_email = '2', 'dummypat@example.com', 'dummydoc@example.com'
# date, time, reason = 'mm/dd/yy', 'hh:tt:ss', 'some issue'

# cursor.execute('CREATE TABLE IF NOT EXISTS appointment (apt_id TEXT PRIMARY KEY, patient_email TEXT, doctor_email TEXT, date TEXT, time TEXT, reason TEXT, prescription TEXT, status TEXT)')
# conn.commit()

# cursor.execute('INSERT INTO appointment VALUES (?,?,?,?,?,?,?,?)', (apt_id, patient_email, doctor_email, date, time, reason, "", "inprogress"))
# conn.commit()

# Example: View all the tables in the database
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# print(cursor.fetchall())

# # Example: View the contents of a table
cursor.execute("SELECT * FROM appointment;")  # Replace 'YourTableName' with the name of your table
rows = cursor.fetchall()
for row in rows:
    print(row)

# Commit the changes and close the connection
conn.close()