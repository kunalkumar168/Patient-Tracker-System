import sqlite3
from flask import *
import bcrypt

#creates the appointment
class Appointment:
    def __init__(self):
        self.conn = sqlite3.connect('./healthdb.db')
        self.cur = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS appointment (apt_id TEXT PRIMARY KEY, patient_email TEXT, doctor_email TEXT, date TEXT, time TEXT, reason TEXT, prescription TEXT, status TEXT)')
        self.conn.commit()

    def get_id(self):
        self.cur.execute('SELECT MAX(apt_id) FROM appointment;')
        result = self.cur.fetchone()[0]
        return str(int(result)+1) if result else 1
    
    def get_appointment_unavailable(self, doctor_email):
        query = 'SELECT date, time FROM appointment WHERE doctor_email = ? AND (status = ?);'
        self.cur.execute(query, (doctor_email, 'inprogress'))
        result = self.cur.fetchall()
        return result

    def create(self, patient_email, doctor_email, date, time, reason):
        apt_id = self.get_id()
        self.cur.execute('INSERT INTO appointment VALUES (?,?,?,?,?,?,?,?)', (apt_id, patient_email, doctor_email, date, time, reason, "", "started"))
        self.conn.commit()
    


    # combine with create function;
    def book_appointment(self, doctor_email, patient_email, date, time):
        # Check doctor's availability logic
        # Assuming time is a datetime object
        day = date.strftime("%A")  # Gets the weekday name
        self.cur.execute('SELECT * FROM doctor_availability WHERE doctor_email = ? AND day = ? AND start_time <= ? AND end_time >= ?', (doctor_email, day, time, time))
        if self.cur.fetchone():
            # Doctor is available, proceed with booking logic
            pass
        else:
            # Doctor is not available
            pass