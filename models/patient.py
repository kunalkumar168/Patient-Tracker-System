import sqlite3
from flask import *
import bcrypt
from datetime import datetime
from models.reports import ReportFile

class Patient:
    def __init__(self):
        self.conn = sqlite3.connect('./healthdb.db')
        self.cur = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS patients (name TEXT, email TEXT PRIMARY KEY, pass TEXT, weight TEXT, height TEXT, age TEXT, gender TEXT, medical_history TEXT)')
        self.conn.commit()

    def create(self, name, email, hashed_password, weight, height, age, gender, medical_history):
        self.cur.execute('INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)', (name, email, hashed_password, weight, height, age, gender, medical_history))
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
        
    def viewprofile(self, pat_email):
        pat_email = session['auth']
        self.cur.execute('SELECT * FROM patients WHERE email = ?', (pat_email,))
        patient_data = self.cur.fetchone()

        if patient_data:
            result = {}
            try:
                first, second = [str(i) for i in patient_data[0].split(' ')]
            except:
                first, second = patient_data[0], None
            result['first_name'] = first
            result['second_name'] = second
            result['email'] = patient_data[1]
            result['weight'] = patient_data[3]
            result['height'] = patient_data[4]
            result['age'] = patient_data[5]
            result['gender'] = patient_data[6]
            result['medical_history'] = patient_data[7]

            return result
        else:
            return []
        
    def getallappointments(self, pat_email):
        self.cur.execute('SELECT * FROM appointment WHERE patient_email = ?', (pat_email,))
        patient_data = self.cur.fetchall()

        appointments = []
        for appointment in patient_data:
            result = {}
            result['doctor_email'] = appointment[2]
            self.cur.execute('SELECT * FROM doctors WHERE email = ?', (result['doctor_email'],))
            result['doctor_name'] = self.cur.fetchone()[2] 
            result['date'] = appointment[3]
            result['time'] = appointment[4]
            result['date'] = datetime.strptime(result['date'], "%Y-%m-%d").strftime("%m/%d/%Y")            
            result['time'] = datetime.strptime(result['time'], "%H:%M").strftime("%I:%M %p")
            result['reason'] = appointment[5]
            result['prescription'] = appointment[6]
            result['status'] = appointment[7]
            appointments.append(result)

        return appointments
    
    def getprescription(self, pat_email, doc_email):
        self.cur.execute("SELECT * FROM appointment WHERE patient_email=? AND doctor_email=?", (pat_email, doc_email))
        patient_data = self.cur.fetchone()
        if patient_data:
            result = {}
            result['doctor_email'] = patient_data[2]
            self.cur.execute('SELECT * FROM doctors WHERE email = ?', (result['doctor_email'],))
            result['doctor_name'] = self.cur.fetchone()[2] 
            result['prescription'] = patient_data[6]
            result['status'] = patient_data[7]
            return result
        else:
            return {}
    
    def getinfo(self, pat_email):
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
        
    def editappointment(self, pat_email, doc_email, date, time):
        status = 'started'
        self.cur.execute('UPDATE appointment SET date = ?, time = ? WHERE status=? AND patient_email=? AND doctor_email=?', (date, time, status, pat_email, doc_email))
        self.conn.commit()

        
    def cancelappointment(self, pat_email, doc_email):
        status = 'started'
        self.cur.execute('DELETE FROM appointment WHERE status=? AND patient_email=? AND doctor_email=?', (status, pat_email, doc_email))
        self.conn.commit()    

    def getpatientreports(self, pat_email):
        self.cur.execute('SELECT * FROM report WHERE patient_email = ?', (pat_email,))
        patient_report = self.cur.fetchall()
        reports = []
        if patient_report:
            for report in patient_report:
                result = {}
                result['patient_email'] = report[1]
                result['doctor_email'] = report[2]
                result['report_name'] = report[3]
                result['file_path'] = report[4]
                reports.append(result)

        return reports
    
    def sharereportswithdoctors(self, pat_email, doc_email, report_name):
        self.cur.execute('SELECT * FROM report WHERE patient_email=? AND report_name=?', (pat_email,report_name))
        result = self.cur.fetchone()
        if result and result[2]==None:
            file_path = result[4]
            self.cur.execute('DELETE FROM report WHERE patient_email=? AND report_name=?', (pat_email,report_name))
            self.conn.commit()
            ReportFile().create(patient_email=pat_email, doctor_email=doc_email, report_name=report_name, file_path=file_path)

    def deletereport(self, pat_email, report_name):
        self.cur.execute('DELETE FROM report WHERE patient_email=? AND report_name=?', (pat_email,report_name))
        self.conn.commit()
            