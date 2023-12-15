from datetime import datetime, timedelta
from flask import *
import bcrypt
import sqlite3
import os
from models.patient import Patient
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

# Initialize the database
with app.app_context():
    db.init_app(app)
    Patient().setup_db()
    Appointment().setup_db()
    Doctor().setup_db()
    ReportFile().setup_db()

# ---------------------------------- Common Section ------------------------------------------

@app.route('/')
def index():
    """
    Render the main login page.

    Returns:
        Flask Response: Rendered template for the login page.
    """
    return render_template('login.html')

def find_user_type(email):
    """
    Find the type of user (Patient or Doctor) based on the email.

    Args:
        email (str): User's email address.

    Returns:
        str or None: User type ('Patient' or 'Doctor') if found, None otherwise.
    """
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
    """
    Handle user login.

    Returns:
        Flask Response: Redirects to the appropriate dashboard based on user type.
    """
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
    """
    Handle user logout.

    Returns:
        Flask Response: Redirects to the main login page.
    """
    session.pop('auth', None)
    session.pop('user_type', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Render the registration page and handle user registration.

    Returns:
        Flask Response: Rendered template for registration or redirection to specific registration page.
    """
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
    """
    Render the patient dashboard.

    Returns:
        Flask Response: Rendered template for the patient dashboard.
    """
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
    """
    Render the patient registration page and handle patient registration.

    Returns:
        Flask Response: Rendered template for patient registration or redirection to registration page.
    """
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

@app.route('/edit_health_records', methods=['GET', 'POST'])
def edit_health_records():
    """
    Render the page for editing patient health records and handle the update.

    Returns:
        Flask Response: Rendered template for editing health records.
    """
    if 'auth' in session and session['user_type'] == 'Patient':
        if request.method == 'POST':
            patient_email = session['auth']
            new_weight = request.form.get('weight')
            new_height = request.form.get('height')
            new_age = request.form.get('age')
            new_gender = request.form.get('gender')
            new_medical_history = request.form.get('medical_history')

            try:
                Patient().edit_health_records(patient_email, new_weight, new_height, new_age, new_gender, new_medical_history)
                flash('Health records updated successfully!', 'success')
            except sqlite3.Error as error:
                flash(f'Failed to update health records. Error: {str(error)}', 'failure')

        return render_template('patients/edit_health_records.html')
    else:
        return redirect(url_for('login'))

@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    """
    Render the page for booking an appointment and handle the appointment creation.

    Returns:
        Flask Response: Rendered template for booking an appointment.
    """
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
    """
    Render the page for booking a specific doctor and handle the appointment creation.

    Args:
        doctor_email (str): Email of the selected doctor.
        doctor_name (str): Name of the selected doctor.

    Returns:
        Flask Response: Rendered template for booking a specific doctor.
    """
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
    """
    Render the page displaying the prescription for a specific patient.

    Args:
        doctor_email (str): Email of the doctor.

    Returns:
        Flask Response: Rendered template for displaying patient prescription.
    """
    if 'auth' in session:
        patient_email = session['auth']
        patient_info = Patient().getprescription(patient_email, doctor_email)
        return render_template('patients/patient_prescription.html', patient_info=patient_info)
    
@app.route('/cancel_appointment/<string:doctor_email>/<action>', methods=['GET'])
def cancel_appointment(doctor_email, action):
    """
    Cancel or reschedule an appointment for a patient with a specific doctor.

    Args:
        doctor_email (str): Email of the doctor.
        action (str): Action to perform, either 'cancel' or 'reschedule'.

    Returns:
        Flask Response: Redirects to the patient dashboard after performing the action.
    """
    if 'auth' in session:
        patient_email = session['auth']
        if action.lower() == 'cancel':
            Patient().cancelappointment(patient_email, doctor_email)

    return redirect(url_for('patient_dashboard'))

@app.route('/edit_appointment/<string:doctor_email>', methods=['GET', 'POST'])
def edit_appointment(doctor_email):
    """
    Render the page for editing an appointment and handle the update.

    Args:
        doctor_email (str): Email of the selected doctor.

    Returns:
        Flask Response: Rendered template for editing an appointment.
    """
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
    """
    Handle the uploading of medical reports by patients.

    Returns:
        Flask Response: Redirects to the patient dashboard after handling the upload.
    """
    if request.method == 'POST':
        if 'auth' in session:
            patient_email = session['auth']
            file = request.files['file']
            name = request.form['report_name']
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(file_path)

            try:
                ReportFile().create(patient_email=patient_email, doctor_email=None, report_name=name, file_path=file_path)
                flash('Reports were uploaded!', 'success')
            except sqlite3.Error as error:
                flash('Reports were not uploaded. Try again!', 'failue')
    else:
        if 'auth' in session:
            patient_email = session['auth']
            reports = Patient().getpatientreports(pat_email=patient_email)
            return render_template('patients/upload_reports.html', files=reports)
        
    return redirect(url_for('patient_dashboard'))
        
@app.route('/serve-report/<path:file_path>')
def serve_report(file_path):
    """
    Serve a medical report file.

    Args:
        file_path (str): Path to the report file.

    Returns:
        Flask Response: Serves the report file.
    """
    if 'auth' in session:
        return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(file_path), as_attachment=False)
    
    return redirect(url_for('upload_reports'))

@app.route('/delete-report/<path:report_name>', methods=['POST'])
def delete_report(report_name):
    """
    Delete a medical report for a patient.

    Args:
        report_name (str): Name of the report to delete.

    Returns:
        Flask Response: Redirects to the upload reports page after handling the deletion.
    """
    if 'auth' in session:
        patient_email = session['auth']
        try:
            Patient().deletereport(pat_email=patient_email, report_name=report_name)
        except sqlite3.Error as error:
            flash('Reports were not uploaded. Try again!', 'failue')
    
    return redirect(url_for('upload_reports'))

@app.route('/get_doctor_availability/<string:doctor_email>')
def get_doctor_availability(doctor_email):
    """
    Get the availability of a doctor for a selected date.

    Args:
        doctor_email (str): Email of the doctor.

    Returns:
        JSON Response: Availability information in FullCalendar event format.
    """
    selected_date = request.args.get('selected_date')

    # Fetch the availability from the database for the selected date
    availability = Doctor().getavailabilityfordate(doctor_email, selected_date)

    # Convert to FullCalendar event format
    events = [
        {
            'start_time': f"{start_time}",
            'end_time': f"{end_time}",
        } for date, start_time, end_time in availability
    ]

    return jsonify(events)
# # --------------------------------- Doctor Components -------------------------------------------


@app.route('/doctor-dashboard')
def doctor_dashboard():
    """
    Render the doctor's dashboard.

    Returns:
        Flask Response: Rendered template for the doctor's dashboard.
    """
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
    """
    Render the page for doctor registration and handle the doctor registration process.

    Returns:
        Flask Response: Rendered template for doctor registration or redirects to registration completion.
    """
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
    """
    Render the page displaying information about a specific doctor.

    Args:
        doctor_email (str): Email of the doctor.

    Returns:
        Flask Response: Rendered template for displaying doctor information.
    """
    doctor_info = Doctor().getinfo(doctor_email)
    return render_template('doctors/doctor_info.html', doctor_info=doctor_info)


@app.route('/patient_info/<string:patient_email>', methods=['GET'])
def patient_info(patient_email):
    """
    Render the page displaying information about a specific patient.

    Args:
        patient_email (str): Email of the patient.

    Returns:
        Flask Response: Rendered template for displaying patient information.
    """
    if 'auth' in session:
        doctor_email = session['auth']
        patient_info = Patient().getinfo(patient_email)
        patient_reports = Doctor().viewpatientreports(pat_email=patient_email, doc_email=doctor_email)
        return render_template('patients/patient_info.html', patient_info=patient_info, patient_reports=patient_reports)

@app.route('/edit_patient/<string:patient_email>/<string:patient_name>', methods=['GET', 'POST'])
def edit_patient(patient_email, patient_name):
    """
    Render the page for editing patient information and handle the update.

    Args:
        patient_email (str): Email of the patient.
        patient_name (str): Name of the patient.

    Returns:
        Flask Response: Rendered template for editing patient information.
    """
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
    """
    Handle pending requests for a patient.

    Args:
        patient_email (str): Email of the patient.
        action (str): Action to perform, either 'accept' or 'reject'.

    Returns:
        Flask Response: Redirects to the doctor's dashboard after handling the request.
    """
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
    """
    Render the page for setting the availability of a doctor and handle the availability update.

    Returns:
        Flask Response: Rendered template for setting doctor availability or redirects to availability completion.
    """
    if request.method == 'POST':
        email = session['auth']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        doctor = Doctor().setavailability(email, date, start_time, end_time)
        if doctor:
            flash('Availability set successfully!', 'success')
        else:
            flash('Failed to set availability. Please try again.', 'error')

        return redirect(url_for('set_availability'))

    return render_template('doctors/set_availability.html')

# # --------------------------------- Main Function -------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)