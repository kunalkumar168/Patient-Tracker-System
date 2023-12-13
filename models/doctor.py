import sqlite3
from flask import *
import bcrypt
from datetime import datetime

#patients will be JSON

class Doctor:
    def __init__(self):
        self.conn = sqlite3.connect('./healthdb.db')
        self.cur = self.conn.cursor()
        self.setup_db()
        
    def setup_db(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS doctors (email TEXT PRIMARY KEY, pass TEXT, name TEXT, specialization TEXT, experience TEXT)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS doctor_availability (doctor_email TEXT,day TEXT, start_time TEXT, end_time TEXT, FOREIGN KEY (doctor_email) REFERENCES doctors(email))')
        self.conn.commit()

    def create(self, name, email, hashed_password, specialization, experience):
        self.cur.execute('INSERT INTO doctors VALUES (?,?,?,?,?)', (email, hashed_password, name, specialization, experience))
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

    def getdoclist(self, first_name, last_name, specialization):
        try:
            if first_name and last_name and specialization:
                # Fetch data when all three variables are present
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ? AND name LIKE ? AND specialization=?", (f"%{first_name}%", f"%{last_name}%", specialization))
            elif first_name and last_name:
                # Fetch data when both first_name and last_name are present
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ? AND name LIKE ?", (f"%{first_name}%", f"%{last_name}%"))
            elif first_name and specialization:
                # Fetch data when first_name and specialization are present
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ? AND specialization=?", (f"%{first_name}%", specialization))
            elif last_name and specialization:
                # Fetch data when last_name and specialization are present
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ? AND specialization=?", (f"%{last_name}%", specialization))
            elif first_name:
                # Fetch data when only first_name is present
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ?", (f"%{first_name}%",))
            elif last_name:
                # Fetch data when only last_name is present
                self.cur.execute("SELECT * FROM doctors WHERE name LIKE ?", (f"%{last_name}%",))
            elif specialization:
                # Fetch data when only specialization is present
                self.cur.execute("SELECT * FROM doctors WHERE specialization=?", (specialization,))
            else:
                # Fetch all data when no variable is present
                self.cur.execute("SELECT * FROM doctors")
                
            rows = self.cur.fetchall()
            if rows:
                final = []
                for doctor_data in rows:
                    result = {}
                    result['name'] = doctor_data[2]
                    result['email'] = doctor_data[0]
                    result['specialization'] = doctor_data[3]
                    result['experience'] = doctor_data[4]
                    final.append(result)
                return final
            else:
                return []
        except sqlite3.Error as error:
            print(error)
            return str(error)
        
    def viewprofile(self, doc_email):
        self.cur.execute('SELECT * FROM doctors WHERE email = ?', (doc_email,))
        doctor_data = self.cur.fetchone()
        if doctor_data:
            result = {}
            try:
                first, second = [str(i) for i in doctor_data[2].split(' ')]
            except:
                first, second = doctor_data[2], None
            result['first_name'] = first
            result['second_name'] = second
            result['email'] = doctor_data[0]
            result['specialization'] = doctor_data[3]
            result['experience'] = doctor_data[4]
            return result
        else:
            return []
        
    def getallappointments(self, doc_email):
        self.cur.execute('SELECT * FROM appointment WHERE doctor_email = ?', (doc_email,))
        doctor_data = self.cur.fetchall()

        appointments = []
        for appointment in doctor_data:
            result = {}
            result['patient_email'] = appointment[1]
            self.cur.execute('SELECT * FROM patients WHERE email = ?', (result['patient_email'],))
            result['patient_name'] = self.cur.fetchone()[0] 
            result['date'] = appointment[3]
            result['time'] = appointment[4]
            result['date'] = datetime.strptime(result['date'], "%Y-%m-%d").strftime("%m/%d/%Y")            
            result['time'] = datetime.strptime(result['time'], "%H:%M").strftime("%I:%M %p")
            result['reason'] = appointment[5]
            result['prescription'] = appointment[6]
            result['status'] = appointment[7]
            appointments.append(result)

        return appointments

    def getinfo(self, doc_email):
        self.cur.execute('SELECT * FROM doctors WHERE email = ?', (doc_email,))
        doctor_data = self.cur.fetchone()
        if doctor_data:
            result = {}
            result['name'] = doctor_data[2]
            result['email'] = doctor_data[0]
            result['specialization'] = doctor_data[3]
            result['experience'] = doctor_data[4]
            return result
        else:
            return []
        
    def editpatient(self, pat_email, doc_email, prescription, status):
        self.cur.execute("SELECT * FROM appointment WHERE patient_email=? AND doctor_email=?", (pat_email, doc_email))
        result = self.cur.fetchall()
        if result:
            self.cur.execute('UPDATE appointment SET prescription = ?, status = ? WHERE patient_email=? AND doctor_email=?', (prescription, status, pat_email, doc_email))
            self.conn.commit()

    def pendingrequest(self, pat_email, doc_email, accept=None, reject=None):
        self.cur.execute("SELECT * FROM appointment WHERE patient_email=? AND doctor_email=?", (pat_email, doc_email))
        result = self.cur.fetchall()
        if result:
            if reject:
                status = 'started'
                self.cur.execute('DELETE from appointment WHERE status=? AND patient_email=? AND doctor_email=?', (status, pat_email, doc_email))
            elif accept:
                status = 'inprogress'
                self.cur.execute('UPDATE appointment SET status = ? WHERE patient_email=? AND doctor_email=?', (status, pat_email, doc_email))
            self.conn.commit()

    def viewpatientreports(self, pat_email, doc_email):
        self.cur.execute('SELECT * FROM report WHERE patient_email=? AND doctor_email=?', (pat_email,doc_email))
        reports = self.cur.fetchall()
        results = []
        if reports:
            for report in reports:
                result = {}
                result['report_name'] = report[3]
                result['file_path'] = report[4]
                results.append(result)
        
        return results

    def set_availability(self, email, date, start_time, end_time):
            try:
                self.cur.execute('INSERT INTO doctor_availability (doctor_email, day, start_time, end_time) VALUES (?, ?, ?, ?)', (email, date, start_time, end_time))
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print("An error occurred:", e)
                return False

    def get_availability(self, email):
        try:
            self.cur.execute('SELECT day, start_time, end_time FROM doctor_availability WHERE doctor_email = ?', (email,))
            availability = self.cur.fetchall()
            return availability  # List of tuples (date, start_time, end_time)
        except sqlite3.Error as e:
            print("An error occurred:", e)
            return []

    def get_available_times_for_date(self, email, date):
        self.cur.execute('SELECT start_time, end_time FROM doctor_availability WHERE doctor_email = ? AND day = ?', (email, date))
        times = self.cur.fetchall()
        return times  # Or format this as needed
    
    def deleteDoctor(self, doc_email):
        self.cur.execute('DELETE FROM doctors WHERE email=?', (doc_email,))
        self.conn.commit()

    def delete_Doctor_availability(self, doctor_email, day, start_time, end_time):
        self.cur.execute('DELETE FROM doctor_availability WHERE doctor_email=? and day=? and start_time=? and end_time=?', (doctor_email, day, start_time, end_time))
        self.conn.commit()