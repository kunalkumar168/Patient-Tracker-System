from flask import *
import bcrypt
import sqlite3
import json
import os
import models.doctor as doctor
from models.patient import Patient
import models.medicine as medicine
from models.doctor import Doctor
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)
# ---------------------------------- Login Section ------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login-patient', methods=['GET'])
def login_pat():
    return render_template('login_pat.html')

@app.route('/login-patient', methods=['POST'])
def login():
    user_data = request.get_json()
    email = user_data['email']
    password = user_data['password']
    login = Patient().login(email, password.encode('utf-8'))
    if(login == None):
        return "No user exists"
    elif(login == "WrongPass"):
        return "Wrong password"
    else:
        session['auth'] = email
        return redirect(url_for('afterpatlogin'))

@app.route('/login-doctor', methods=['GET'])
def login_doc():
    return render_template('login_doc.html')

@app.route('/login-doctor', methods=['POST'])
def logindoctor():
    user_data = request.get_json()
    email = user_data['email']
    password = user_data['password']
    login = Doctor().login(email, password.encode('utf-8'))
    if (login == None):
        return "No user exists"
    elif (login == "WrongPass"):
        return "Wrong password"
    else:
        session['auth'] = email
        return redirect(url_for('afterdoclogin'))


@app.route('/create-patient', methods=['GET'])
def create_patient_form():
    return render_template('create-patient.html')

@app.route('/create-patient', methods=['POST'])
def createpatientfront():
    user_data = request.get_json()
    name = user_data['name']
    email = user_data['email']
    password = user_data['password']
    weight = user_data['weight']
    height = user_data['height']
    gender = user_data['gender']
    age = user_data['age']
    medical_history = user_data['medical_history']
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    #name, email, hash, weight, height, age, gender, medications, medical_history, doc_email
    try:
        Patient().create(name, email, hashed_password, weight, height, age, gender, medical_history)
        return "safe"
    except sqlite3.Error as error:
        if 'UNIQUE constraint failed' in str(error):
            return "User exists"
        else:
            return "User with email " + email + " created"
        
    
@app.route('/create-doctor', methods=['GET'])
def create_doctor_form():
    return render_template('create-doctor.html')

@app.route('/create-doctor', methods=['POST'])
def createdocfront():
    doc_data = request.get_json()
    email = doc_data['email']
    password = doc_data['password']
    hashed_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    name = doc_data['name']
    specialization = doc_data['specialization']
    experience = doc_data['experience']
    try:
        Doctor().create(name, email, hashed_pass, specialization, experience)
        return "done"
    except sqlite3.Error as error:
        if 'UNIQUE constraint failed' in str(error):
            return "User exists"
        else:
            return "User with email " + email + " created"
    
# --------------------------------- Patient Components -------------------------------------------

@app.route('/patient-info', methods=['GET'])
def afterpatlogin():
    if 'auth' in session:
        email = session['auth']
        patient_details = Patient().viewprofile(email)
        return render_template('view_pat_profile.html', patient_details=patient_details)
    else:
        return "User not logged in"

@app.route('/get-doctor-list', methods=['POST'])
def getdocforspecialization():
    req_data = request.get_json()
    first_name = req_data['first_name']
    last_name = req_data['last_name']
    specialization = req_data['specialization']
    doctors = Doctor().getdoclist(first_name, last_name, specialization)
    return viewdocfrompat(json.dumps(doctors))

@app.route('/get-doctor-list', methods=['GET'])
def viewdocfrompat(doctors):
    return render_template('doc_list.html', doctors=json.dumps(doctors))

@app.route('/add-doctor', methods=['POST'])
def adddoctor():
    if 'auth' not in session:
        abort(401)
    else:
        user_data = request.get_json()
        doctor_email = user_data['doctor_email']
        result = Patient.bookdoctor(doctor_email)
        return result

# @app.route('/patient-dashboard', methods=['GET'])
# def get_doc_list():
#     return render_template('view_doc_list.html')

# --------------------------------- Doctor Components -------------------------------------------

@app.route('/doctor-info', methods=['GET'])
def afterdoclogin():
    if 'auth' in session:
        email = session['auth']
        print(email)
        doctor_details = Doctor().viewprofile(email)
        return render_template('view_doc_profile.html', doctor_details=doctor_details)
    else:
        return "User not logged in"

@app.route('/edit-patient-doc', methods=['PATCH'])
def editpatientdoc():
    if 'auth' not in session:
        abort(401)
    else:
        user_data = request.get_json()
        doc_email = user_data['email']
        prescription = user_data['prescription']
        result = Doctor.editpatient(doc_email, prescription)
        return result
        #email, prescription

@app.route('/get-patient-data', methods=['GET'])
def fetch_patient():
    if 'auth' not in session:
        abort(401)
    else:
        patient_info = Patient.fetchdata()
        return patient_info


@app.route('/create-medicine', methods=['POST'])
def createmedicinefront():
    med_data = request.get_json()
    #id, name, mfg_date, exp_date, description, patient_email
    id = med_data['id']
    name = med_data['name']
    mfg_date = med_data['mfg_date']
    exp_date = med_data['exp_date']
    description = med_data['description']
    patient_email = med_data['patient_email']
    try:
        medicine.create(id, name, mfg_date, exp_date, description, patient_email)
        return "safe"
    except sqlite3.Error as error:
        if 'UNIQUE constraint failed' in str(error):
            return "Medicine exists"
        else:
            return "Medicine " + name + " created"

if __name__ == "__main__":
    app.run(debug=True)