import sqlite3
from flask import *
import bcrypt

#patients will be JSON

class Doctor:
    def __init__(self):
        self.conn = sqlite3.connect('./healthdb.db')
        self.cur = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS doctors (email TEXT PRIMARY KEY, pass TEXT, name TEXT, specialization TEXT, experience TEXT, patient_emails TEXT)')
        self.conn.commit()

    def create(self, name, email, hash, specialization, experience):
        self.cur.execute('INSERT INTO doctors VALUES (?,?,?,?)', (email, hash, name, specialization, experience, ""))
        self.conn.commit()


    def login(self, email, password):
        self.cur.execute('SELECT pass FROM doctors WHERE email=(?)', (email,))
        hash_check = self.cur.fetchone()
        if hash_check == None:
            return None
        else:
            hashed_password = hash_check[0]
            if bcrypt.checkpw(password, hashed_password):
                session['auth'] = email
                return "Log"
            else:
                return "WrongPass"


    def addpatient(self, doc_email, pat_email):
        self.cur.execute('SELECT patient_emails FROM doctors WHERE email=?', (doc_email,))
        doc_data = self.cur.fetchone()

        if doc_data:
            patient_emails = json.loads(doc_data[0]) if doc_data[0] else []
            patient_emails.append(pat_email)
            self.cur.execute('UPDATE doctors SET patient_emails=? WHERE email=?', (json.dumps(patient_emails), doc_email))
            self.conn.commit()
            return "Success"

    def editpatient(self, pat_email, prescription):
        doc_email = session['auth']
        self.cur.execute('SELECT patient_emails FROM doctors WHERE email=?', (doc_email,))
        result = self.cur.fetchone()
        if result:
            patients = json.loads(result[0]) if result[0] else []
            if pat_email in patients:
                self.cur.execute('SELECT doctor_and_medicines FROM patients WHERE email = ?', (pat_email,))
                patient_data = self.cur.fetchone()
                if patient_data:
                    doctors_and_meds = json.loads(patient_data[0]) if patient_data[0] else []
                    if doctors_and_meds and pat_email in doctors_and_meds:
                        doctors_and_meds[pat_email] = prescription
                        self.cur.execute('UPDATE patients SET doctor_and_medicines = ? WHERE email = ?', (json.dumps(doctors_and_meds), pat_email,))
                        self.conn.commit()
                        return "Success"
        return None

    def getdoclist(self, first_name, last_name, specialization):
        doc_email = session['auth']
        try:
            if first_name:
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ?", first_name)
            elif last_name:
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ?", last_name)
            elif specialization:
                self.cur.execute("SELECT * FROM doctors WHERE specialization=?", specialization)
            else:
                self.cur.execute("SELECT * FROM doctors")
                
            rows = self.cur.fetchall()
            return rows
        except sqlite3.Error as error:
            print(error)
            return str(error)
        
    def fetchpathistory(self, pat_email):
        doc_email = session['auth']
        try:
            self.cur.execute('SELECT patient_emails FROM doctors WHERE email=?', (doc_email,))
            doc_data = self.cur.fetchone()
            result = []

            if doc_data:
                patient_emails = json.loads(doc_data[0]) if doc_data[0] else []
                if pat_email in patient_emails:
                    self.cur.execute('SELECT medical_history FROM patients WHERE email=?', (pat_email,))
                    res = self.cur.fetchone()
                    result.append({"medical_history":res[0]})
                    self.cur.execute('SELECT doctor_and_medicines FROM patients WHERE email = ?', (pat_email,))
                    doc_med = self.cur.fetchone()
                    if doc_med:
                        doctors_and_meds = json.loads(doc_med[0]) if doc_med[0] else []
                        if doctors_and_meds and pat_email in doctors_and_meds:
                            result.append({"current_medicine":doctors_and_meds[pat_email]})
            return result
        except sqlite3.Error as error:
            print(error)
            return str(error)