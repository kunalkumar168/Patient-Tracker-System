from datetime import datetime, timedelta
from flask import *
import bcrypt
import sqlite3
import os
from models.patient import Patient
from models.medicine import Medicine
from models.doctor import Doctor
from models.appointments import Appointment
from models.reports import ReportFile
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthdb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = './files/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy()

# Intialise the database
with app.app_context():
    db.init_app(app)
    Patient().setup_db()
    Appointment().setup_db()
    Doctor().setup_db()
    Medicine().setup_db()
    ReportFile().setup_db()

# ---------------------------------- Common Section ------------------------------------------

@app.route('/')
def index():
    return render_template('login.html')

def find_user_type(email):
    conn = sqlite3.connect('./healthdb.db')
    cur = conn.cursor()
    cur.execute('SELECT pass FROM patients WHERE email=(?)', (email,))
    hash_check = cur.fetchone()
    if hash_check == None:
        cur.execute('SELECT pass FROM doctors WHERE email=(?)', (email,))
        hash_check = cur.fetchone()
        if hash_check == None:
            return None
        else:
            return "Doctor"
    else:
        return "Patient"

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user_type = find_user_type(email)
    if user_type == "Patient":
        login = Patient().login(email, password.encode('utf-8'))
    elif user_type == "Doctor":
        login = Doctor().login(email, password.encode('utf-8'))
    else:
        return render_template('login.html')
    
    error = None
    if(login == None):
        error = "No user exists"
    elif(login == "WrongPass"):
        error = 'Invalid Credentials. Please try again.'
    else:
        session['auth'] = email
        session['user_type'] = user_type
        if user_type=='Patient':
            return redirect(url_for('patient_dashboard'))
        else:
            return redirect(url_for('doctor_dashboard'))
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('auth', None)
    session.pop('user_type', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        if role == 'patient':
            return redirect(url_for('register_patient'))
        elif role == 'doctor':
            return redirect(url_for('register_doctor'))
    return render_template('register.html')

# # --------------------------------- Patient Components -------------------------------------------

@app.route('/patient-dashboard')
def patient_dashboard():
    if 'auth' in session and session['user_type'] == 'Patient':
        email = session['auth']
        patient_details = Patient().viewprofile(email)
        session['first_name'] = patient_details['first_name']
        appointments = Patient().getallappointments(email)
        return render_template('dashboard/patient_dashboard.html', patient_details=patient_details, appointments=appointments)
    else:
        return redirect(url_for('login'))
    
@app.route('/create-patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        weight = request.form['weight']
        height = request.form['height']
        gender = request.form['gender']
        age = request.form['age']
        medical_history = request.form['medical_history']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        #name, email, hash, weight, height, age, gender, medications, medical_history, doc_email
        try:
            Patient().create(name, email, hashed_password, weight, height, age, gender, medical_history)
            flash('Patient registered successfully!', 'success')
            return redirect(url_for('register_patient'))
        except sqlite3.Error as error:
            if 'UNIQUE constraint failed' in str(error):
                flash('User already exists!', 'failure')
                return redirect(url_for('register_patient'))
            else:
                flash(f"User with email {email} created!", 'failure')
                return redirect(url_for('register_patient'))
    return render_template('patients/register_patient.html')

@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    doctors = []
    if request.method == 'POST':
        if 'auth' in session:
            search_doctor = any(i in request.form for i in ['first_name', 'last_name', 'specialization'])
            if search_doctor:
                first_name = request.form['first_name']
                last_name = request.form['last_name']
                specialization = request.form['specialization']
                doctors = Doctor().getdoclist(first_name, last_name, specialization)

    return render_template('patients/book_appointment.html', doctors=doctors)

@app.route('/book_doctor/<string:doctor_email>/<string:doctor_name>', methods=['GET', 'POST'])
def book_doctor(doctor_email, doctor_name):

    if request.method == 'POST':

        if 'auth' in session:
            patient_email = session['auth']
            date = request.form.get('date')
            time = request.form.get('time')
            reason = request.form.get('reason')

            selected_reports = request.form.getlist('selected_reports')
            if selected_reports:
                try:
                    for report_name in selected_reports:
                        Patient().sharereportswithdoctors(pat_email=patient_email, doc_email=doctor_email, report_name=report_name)
                except sqlite3.Error as error:
                    flash('Failed to associate reports with the appointment. Try again!', 'failure')

            try:
                Appointment().create(patient_email, doctor_email, date, time, reason)
                flash('Appointment created successfully!', 'success')
            except sqlite3.Error as error:
                if 'UNIQUE constraint failed' in str(error):
                    flash('Appointment can\'t be booked. Try again!', 'failure')
            except Exception as error:
                flash(str(error), 'failure')

    files = []
    if 'auth' in session:
        patient_email = session['auth']
        files = Patient().getpatientreports(pat_email=patient_email)

    return render_template('patients/book_doctor.html', doctor_email=doctor_email, doctor_name=doctor_name, files=files)

@app.route('/patient_prescription/<string:doctor_email>', methods=['GET'])
def patient_prescription(doctor_email):
    if 'auth' in session:
        patient_email = session['auth']
        patient_info = Patient().getprescription(patient_email, doctor_email)
        return render_template('patients/patient_prescription.html', patient_info=patient_info)
    
@app.route('/cancel_appointment/<string:doctor_email>/<action>', methods=['GET'])
def cancel_appointment(doctor_email, action):
    if 'auth' in session:
        patient_email = session['auth']
        if action.lower() == 'cancel':
            Patient().cancelappointment(patient_email, doctor_email)

    return redirect(url_for('patient_dashboard'))

@app.route('/edit_appointment/<string:doctor_email>', methods=['GET', 'POST'])
def edit_appointment(doctor_email):
    patient_name = None
    if request.method == 'POST':
        if 'auth' in session:
            patient_email = session['auth']
            patient_data = Patient().getinfo(patient_email)
            patient_name = patient_data['name']
            date = request.form.get('new_date')
            time = request.form.get('new_time')
            try:
                Patient().editappointment(patient_email, doctor_email, date, time)
                flash('Appointment updated successfully!', 'success')
            except sqlite3.Error as error:
                flash('Appointment can\'t be updated. Try again!', 'failue')
    else:
        if 'auth' in session:
            patient_email = session['auth']
            patient_data = Patient().getinfo(patient_email)
            patient_name = patient_data['name']
    
    return render_template('patients/edit_appointment.html', doctor_email=doctor_email, patient_name=patient_name)
    

@app.route('/upload-report', methods=['GET', 'POST'])
def upload_reports():
    if request.method == 'POST':
        if 'auth' in session:
            patient_email = session['auth']
            file = request.files['file']
            name = request.form['report_name']
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(file_path)

            try:
                ReportFile().create(patient_email=patient_email, doctor_email=None, report_name=name, file_path=file_path)
                flash('Reports was uploaded!', 'success')
            except sqlite3.Error as error:
                flash('Reports was not uploaded. Try again!', 'failue')
    else:
        if 'auth' in session:
            patient_email = session['auth']
            reports = Patient().getpatientreports(pat_email=patient_email)
            return render_template('patients/upload_reports.html', files=reports)
        
    return redirect(url_for('patient_dashboard'))
        
@app.route('/serve-report/<path:file_path>')
def serve_report(file_path):
    if 'auth' in session:
        return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(file_path), as_attachment=False)
    
    return redirect(url_for('upload_reports'))

@app.route('/delete-report/<path:report_name>', methods=['POST'])
def delete_report(report_name):
    if 'auth' in session:
        patient_email = session['auth']
        try:
            Patient().deletereport(pat_email=patient_email, report_name=report_name)
        except sqlite3.Error as error:
            flash('Reports was not uploaded. Try again!', 'failue')
    
    return redirect(url_for('upload_reports'))

@app.route('/get_doctor_availability/<string:doctor_email>')
def get_doctor_availability(doctor_email):
    # Fetch the availability from the database
    availability = Doctor().get_availability(doctor_email)
    unavailable = Appointment().get_appointment_unavailable(doctor_email)

    # Convert to FullCalendar event format
    events = [
        {
            'title': 'Available',
            'start': f"{date}T{start_time}",
            'end': f"{date}T{end_time}",
            'color': '#3788d8',
        } for date, start_time, end_time in availability
    ]

    for date, time in unavailable:
        start_datetime = datetime.strptime(f"{date}T{time}", "%Y-%m-%dT%H:%M")
        end_datetime = start_datetime + timedelta(hours=1)   # Add one hour to the start time
        events.append({
            'title': 'Unavailable',
            'start': start_datetime.strftime("%Y-%m-%dT%H:%M"),
            'end': end_datetime.strftime("%Y-%m-%dT%H:%M"),
            'color': '#ff0000',  # Red color for unavailable times
            'rendering': 'background',
        })

    return jsonify(events)
# # --------------------------------- Doctor Components -------------------------------------------


@app.route('/doctor-dashboard')
def doctor_dashboard():
    if 'auth' in session and session['user_type'] == 'Doctor':
        email = session['auth']
        doctor_details = Doctor().viewprofile(email)
        session['first_name'] = doctor_details['first_name']
        appointments = Doctor().getallappointments(email)
        return render_template('dashboard/doctor_dashboard.html', doctor_details=doctor_details, appointments=appointments)
    else:
        return redirect(url_for('login'))
    
@app.route('/create-doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        specialization = request.form['specialization']
        experience = request.form['experience']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        #name, email, hash, specialization, experience
        try:
            Doctor().create(name, email, hashed_password, specialization, experience)
            flash('Doctor registered successfully!', 'success')
            return redirect(url_for('register_doctor'))
        except sqlite3.Error as error:
            if 'UNIQUE constraint failed' in str(error):
                flash('User already exists!', 'failure')
                return redirect(url_for('register_doctor'))
            else:
                flash(f"User with email {email} created!", 'failure')
                return redirect(url_for('register_doctor'))
    return render_template('doctors/register_doctor.html')

@app.route('/doctor_info/<string:doctor_email>', methods=['GET'])
def doctor_info(doctor_email):
    doctor_info = Doctor().getinfo(doctor_email)
    return render_template('doctors/doctor_info.html', doctor_info=doctor_info)


@app.route('/patient_info/<string:patient_email>', methods=['GET'])
def patient_info(patient_email):
     if 'auth' in session:
        doctor_email = session['auth']
        patient_info = Patient().getinfo(patient_email)
        patient_reports = Doctor().viewpatientreports(pat_email=patient_email, doc_email=doctor_email)
        return render_template('patients/patient_info.html', patient_info=patient_info, patient_reports=patient_reports)

@app.route('/edit_patient/<string:patient_email>/<string:patient_name>', methods=['GET', 'POST'])
def edit_patient(patient_email, patient_name):
    if request.method == 'POST':
        if 'auth' in session:
            doctor_email = session['auth']
            prescription = request.form['prescription']
            status = request.form['status']
            try:
                Doctor().editpatient(patient_email, doctor_email, prescription, status)
                flash(f"Added prescription successfully!", 'success')
            except sqlite3.Error as error:
                flash(f"Edit unsuccessful. Try again!", 'failure')
    
    return render_template('doctors/edit_patient_appointment.html', patient_email=patient_email, patient_name=patient_name)

@app.route('/pending_request/<string:patient_email>/<action>', methods=['GET'])
def pending_request(patient_email, action):
    if 'auth' in session:
        doctor_email = session['auth']
        accept = 'accept' if action.lower()=='accept' else None
        reject = 'reject' if action.lower()=='reject' else None
        try:
            Doctor().pendingrequest(patient_email, doctor_email, accept, reject)
            flash(f"Performed request successfully!", 'success')
        except sqlite3.Error as error:
            flash(f"Action unsuccessful. Try again!", 'failure')
    
    return redirect(url_for('doctor_dashboard'))

@app.route('/set_availability', methods=['GET', 'POST'])
def set_availability():
    if request.method == 'POST':
        email = session['auth']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        doctor = Doctor()
        if doctor.set_availability(email, date, start_time, end_time):
            flash('Availability set successfully!', 'success')
        else:
            flash('Failed to set availability. Please try again.', 'error')

        return redirect(url_for('set_availability'))

    return render_template('doctors/set_availability.html')

# # --------------------------------- Main Function -------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)