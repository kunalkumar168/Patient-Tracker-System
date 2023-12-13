from unittest.mock import MagicMock
import pytest
from server import app
from models.patient import Patient
from models.doctor import Doctor
from models.appointments import Appointment
from models.medicine import Medicine
from models.reports import ReportFile

# The first version test was planned to set up dummy data for testing by using db when setting up the app, 
# but many modifications were needed to the existing code, so the test was conducted with hard code first.
@pytest.fixture
def client():

    with app.test_client() as client:
        test_patient = client.post('/create-patient', data={
            'name': 'testPatient1',
            'email': 'testpat1@example.com',
            'password': 'testpat1123',
            'weight': '70',
            'height': '175',
            'gender': 'Male',
            'age': '30',
            'medical_history': 'None'
        })
        test_doctor = client.post('/create-doctor', data={
            'name': 'testDoctor1',
            'email': 'testdoc1@example.com',
            'password': 'testdoc1123',
            'specialization': 'Cardiology',
            'experience': '10'
        })

        yield client

        Patient().deletePatient('testpat1@example.com')
        Doctor().deleteDoctor('testdoc1@example.com')

def test_registration(client):
    response_success1 = client.post('/create-patient', data={
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'password': 'password123',
        'weight': '70',
        'height': '175',
        'gender': 'Male',
        'age': '30',
        'medical_history': 'None'
    })
    assert response_success1.status_code == 302
    print("wrokigngn")
    response_failure1 = client.post('/create-patient', data={
        'name': '', 
        'email': 'invalid-email',  
        'password': 'pass'  
    })
    assert response_failure1.status_code == 400

    response_success2 = client.post('/create-doctor', data={
        'name': 'Dr. Smith',
        'email': 'dr.smith@example.com',
        'password': 'password123',
        'specialization': 'Cardiology',
        'experience': '10'
    })
    assert response_success2.status_code == 302

    response_failure2 = client.post('/create-doctor', data={
        'name': '',
        'email': 'invalid-email',
        'password': '123'
    })
    assert response_failure2.status_code == 400

    Patient().deletePatient('john.doe@example.com')
    Doctor().deleteDoctor('dr.smith@example.com')

def test_login(client):

    response_success1 = client.post('/login', data={
        'email': 'testpat1@example.com',
        'password': 'testpat1123'
    })
    assert response_success1.status_code == 302

    response_failure1 = client.post('/login', data={
        'email': 'testpat1@example.com',
        'password': 'wrongpassword'
    })
    assert response_failure1.status_code == 200

    response_success2 = client.post('/login', data={
        'email': 'testdoc1@example.com',
        'password': 'testdoc1123'
    })
    assert response_success2.status_code == 302

    response_failure2 = client.post('/login', data={
        'email': 'testpat1@example.com',
        'password': 'incorrect'
    })
    assert response_failure2.status_code == 200

def test_logout(client):
    with client.session_transaction() as session:
        session['auth'] = 'testpat1@example.com'
        session['user_type'] = 'Patient'

    response = client.get('/logout')
    assert response.status_code == 302

def test_landing_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Login' in response.data 
    assert b'Patient Tracker System' in response.data 
    assert b'EliteKoders Team' in response.data 

def test_dashboard(client):
    with client.session_transaction() as session1:
        session1['auth'] = 'testpat1@example.com'  
        session1['user_type'] = 'Patient'

    response = client.get('/patient-dashboard')
    assert response.status_code == 200
    assert b'Hi, testPatient1' in response.data 

    with client.session_transaction() as session2:
        session2['auth'] = 'testdoc1@example.com'  
        session2['user_type'] = 'Doctor'

    response = client.get('/doctor-dashboard')
    assert response.status_code == 200
    assert b'Hi, testDoctor1' in response.data  

# This will use existing dummy data.
def test_doctor_reviews_patient_info(client):
    with client.session_transaction() as session:
        session['auth'] = 'doctor1@example.com'

    response = client.get('/patient_info/patient1@example.com')
    assert response.status_code == 200
    assert b"Patient Information" in response.data

    patient1info = Patient().getinfo('patient1@example.com')
    expected_data = {
        'name': 'Patient1',
        'email': 'patient1@example.com',
        'weight': '160',
        'height': '175',
        'age': '30',
        'gender': 'male',
        'medical_history': 'Slight backache'
    }
    assert patient1info == expected_data

# This will use existing dummy data.
def test_view_patient_reports():
    pat_email = 'patient1@example.com'
    doc_email = 'doctor1@example.com'

    expected_reports = [
        {'report_name': 'CBC(Complete Blood Count)', 'file_path': './files/CBC-Test-Results.jpg'},
        {'report_name': 'Blood Sugar', 'file_path': './files/Blood-Sugar-Report.jpg'}
    ]
    patient_reports = Doctor().viewpatientreports(pat_email, doc_email)

    assert patient_reports == expected_reports

# This will use existing dummy data.
def test_get_available_times_for_date():
    day = '2023-12-13'
    doctor_email = 'doctor1@example.com'

    available_times = Doctor().get_available_times_for_date(doctor_email, day)

    expected_times = [
        ('09:30', '11:50'),
        ('14:00', '17:00')
    ]
    assert available_times == expected_times

# This will use existing dummy data.
def test_create_appointment():
    doctor_email = 'doctor1@example.com'
    patient_email = 'patient1@example.com'
    appointment_date = '2023-12-13'
    appointment_time = '09:30'
    reason = 'test'

    # Assuming is_doctor_available returns True if the doctor is available
    Appointment().create(patient_email, doctor_email, appointment_date, appointment_time, reason)
    appointments = Patient().getallappointments(patient_email)

    expected_appointment_data = [
        {'doctor_email': 'doctor1@example.com', 'status': 'completed'},
        {'doctor_email': 'doctor2@example.com', 'status': 'inprogress'},
        {'doctor_email': 'doctor3@example.com', 'status': 'started'},
        {'doctor_email': 'doctor1@example.com', 'status': 'started'}  # Newly added data
    ]

    # Check if each expected appointment is in the returned data
    for expected_appointment in expected_appointment_data:
        assert any(appointment['doctor_email'] == expected_appointment['doctor_email'] and 
                   appointment['status'] == expected_appointment['status'] 
                   for appointment in appointments), f"Appointment with doctor {expected_appointment['doctor_email']} and status {expected_appointment['status']} not found"
    
    Patient().cancelappointment(patient_email,doctor_email)


def test_cancel_appointment(): 
    doctor_email = 'doctor1@example.com'
    patient_email = 'patient1@example.com'
    appointment_date = '2023-12-13'
    appointment_time = '10:00'

    patient_email = 'patient1@example.com'
    doctor_email_to_delete = 'doctor1@example.com'
    appointment_date_to_delete = '12/13/2023'
    appointment_time_to_delete = '10:00 AM'
    reason = 'cancel test'

    Appointment().create(patient_email, doctor_email, appointment_date, appointment_time, reason)

    # Confirm the appointment is initially present
    initial_appointments = Patient().getallappointments(patient_email)
    print(initial_appointments)
    assert any(appointment['doctor_email'] == doctor_email_to_delete and 
               appointment['date'] == appointment_date_to_delete and
               appointment['time'] == appointment_time_to_delete
               for appointment in initial_appointments), "Appointment to be deleted is not initially present"

    Patient().cancelappointment(patient_email,doctor_email)

    updated_appointments = Patient().getallappointments(patient_email)
    assert not any(appointment['doctor_email'] == doctor_email_to_delete and 
                   appointment['date'] == appointment_date_to_delete and
                   appointment['time'] == appointment_time_to_delete
                   for appointment in updated_appointments), "Appointment was not successfully deleted"


