import sqlite3
from flask import *
import bcrypt
from models.doctor import Doctor

medications = []
#creates the patient
class Patient:
    def __init__(self):
        self.conn = sqlite3.connect('./healthdb.db')
        self.cur = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS patients (name TEXT, email TEXT PRIMARY KEY, pass TEXT, weight TEXT, height TEXT, age TEXT, gender TEXT, medical_history TEXT, doctor_and_medicines TEXT)')
        self.conn.commit()

    def create(self, name, email, hashed_password, weight, height, age, gender, medical_history):
        self.cur.execute('INSERT INTO patients VALUES (?,?,?,?,?,?,?,?,?)', (name, email, hashed_password, weight, height, age, gender, medical_history, ""))
        self.conn.commit()


    def login(self, email, password):
        self.cur.execute('SELECT pass FROM patients WHERE email=(?)', (email,))
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
            

    def bookdoctor(self, doctor_email):
        pat_email = session['auth']
        self.cur.execute('SELECT doctor_and_medicines FROM patients WHERE email = ?', (pat_email,))
        patient_data = self.cur.fetchone()

        if patient_data:
            doctors_and_meds = json.loads(patient_data[0]) if patient_data[0] else []
            doctors_and_meds.append({doctor_email,[]})
            self.cur.execute('UPDATE patients SET doctor_and_medicines = ? WHERE email = ?', (json.dumps(doctors_and_meds), pat_email,))
            self.conn.commit()
            result = Doctor().addpatient(doctor_email, pat_email)
            return result
        
    def viewprofile(self, pat_email):
        pat_email = session['auth']
        self.cur.execute('SELECT * FROM patients WHERE email = ?', (pat_email,))
        patient_data = self.cur.fetchone()

        if patient_data:
            result = {}
            result['name'] = patient_data[0]
            result['email'] = patient_data[1]
            result['weight'] = patient_data[3]
            result['height'] = patient_data[4]
            result['age'] = patient_data[5]
            result['gender'] = patient_data[6]
            result['medical_history'] = patient_data[7]

            return result
        else:
            return []