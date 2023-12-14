from unittest.mock import MagicMock
import pytest
from server import app
from io import BytesIO
from werkzeug.datastructures import FileStorage
from models.patient import Patient
from models.doctor import Doctor
from models.appointments import Appointment
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
        'email': 'patient1@example.com'
    }
    assert patient1info['name'] == expected_data['name']
    assert patient1info['email'] == expected_data['email']

def test_set_availability(client):
    with client.session_transaction() as session:
        session['auth'] = 'testdoc1@example.com'
    
    response = client.post('/set_availability', data = {
        'date' : '2023-12-13', 
        'start_time' : '09:00',
        'end_time' : '09:30',
    })
    assert response.status_code in [200, 302]
    doctorinfo = Doctor().getavailabilityfordate('testdoc1@example.com', '2023-12-13')
    events = [
        {
            'date' : f"{date}",
            'start_time': f"{start_time}",
            'end_time': f"{end_time}",
        } for date, start_time, end_time in doctorinfo
    ]
    expected_data = {
        'date': '2023-12-13',
        'start_time': '09:00',
        'end_time': '09:30',
    }
    assert( events[0] == expected_data)

def test_edit_health_records(client):
    with client.session_transaction() as session:
        session['auth'] = 'testpat1@example.com'
        session['user_type'] = 'Patient'

    response = client.post('/edit_health_records', data = {
        'weight' : '150',
        'height': '175',
        'age': '35',
        'gender': 'male',
        'medical_history': 'nothing new',
    })
    assert response.status_code == 200
    patient_email = 'testpat1@example.com' 
    patientinfo = Patient().getinfo(patient_email)
    expected_data = {
        'name': 'testPatient1',
        'email': 'testpat1@example.com',
        'weight' : '150',
        'height': '175',
        'age': '35',
        'gender': 'male',
        'medical_history': 'nothing new',
    }
    assert patientinfo==expected_data

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
    doctor_email = 'testdoc123@example.com'
    Doctor().setavailability(doctor_email, day, '10:00', '10:30')
    Doctor().setavailability(doctor_email, day, '14:00', '14:30')

    available_times = Doctor().getavailabletimesfordate(doctor_email, day)

    expected_times = [
        ('10:00', '10:30'),
        ('14:00', '14:30')
    ]
    assert available_times == expected_times
    Doctor().deletedoctoravailability(doctor_email, day, '10:00')
    Doctor().deletedoctoravailability(doctor_email, day, '14:00')

# This will use existing dummy data.
def test_create_appointment():
    doctor_email = 'testdoc1@example.com'
    patient_email = 'testpat1@example.com'
    appointment_date = '2023-12-25'
    appointment_time = '09:30'
    reason = 'test'
    Doctor().setavailability(doctor_email, appointment_date, appointment_time, '10:00')
    Appointment().create(patient_email, doctor_email, appointment_date, appointment_time, reason)
    patientinfo = Patient().getallappointments(patient_email)

    expected_data = {
        'doctor_name': 'testDoctor1',
        'doctor_email': 'testdoc1@example.com',
        'date': '12/25/2023',
        'time': '09:30 AM'
    }
    assert patientinfo[0]['doctor_name'] == expected_data['doctor_name']
    assert patientinfo[0]['doctor_email'] == expected_data['doctor_email']
    assert patientinfo[0]['date'] == expected_data['date']
    assert patientinfo[0]['time'] == expected_data['time']

    Patient().deleteappointment(patient_email,doctor_email)
    Doctor().deletedoctoravailability(doctor_email, appointment_date, appointment_time)

def test_cancel_appointment(): 
    doctor_email = 'doctor1@example.com'
    patient_email = 'patient1@example.com'
    appointment_date = '2023-12-13'
    appointment_time = '10:00'
    Doctor().setavailability(doctor_email, appointment_date, appointment_time, '10:30')

    patient_email = 'patient1@example.com'
    doctor_email_to_delete = 'doctor1@example.com'
    appointment_date_to_delete = '12/13/2023'
    appointment_time_to_delete = '10:00 AM'
    reason = 'cancel test'

    Appointment().create(patient_email, doctor_email, appointment_date, appointment_time, reason)

    # Confirm the appointment is initially present
    initial_appointments = Patient().getallappointments(patient_email)
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
    Patient().deleteappointment(patient_email,doctor_email)
    Doctor().deletedoctoravailability(doctor_email, appointment_date, appointment_time)

def test_get_prescription(client):
    # Assuming test data is already in the database
    patient_email = 'testpat1@example.com'
    doctor_email = 'testdoc1@example.com'

    Doctor().setavailability('testdoc1@example.com', '2023-12-24', '10:00', '10:30')
    Appointment().create('testpat1@example.com', 'testdoc1@example.com', '2023-12-24', '10:00', 'issue')
    # Successful Prescription Retrieval
    result = Patient().getprescription(patient_email, doctor_email)
    assert result is not None
    assert result['prescription'] == ''

    # Retrieval when no prescription is available
    result = Patient().getprescription('nonpatient@example.com', doctor_email)
    assert result == {}
    Patient().deleteappointment(patient_email,doctor_email)
    Doctor().deletedoctoravailability(doctor_email, '2023-12-24', '10:00')

def test_get_patient_reports(client):
    # Assuming test data is already in the database
    patient_email = 'patient1@example.com'

    # When Reports are Available
    reports = Patient().getpatientreports(patient_email)
    assert len(reports) > 0
    assert reports[0]['patient_email'] == patient_email

    # When No Reports are Available
    reports = Patient().getpatientreports('unknown_patient@example.com')
    assert len(reports) == 0

def test_share_reports_with_doctors(client):
    # Assuming test data is already in the database
    patient_email = 'patient1@example.com'
    doctor_email = 'doctor1@example.com'
    report_name = 'CBC(Complete Blood Count)'

    # Successful Report Sharing
    initial_report_count = len(Patient().getpatientreports(patient_email))
    Patient().sharereportswithdoctors(patient_email, doctor_email, report_name)
    updated_report_count = len(Patient().getpatientreports(patient_email))
    assert updated_report_count == initial_report_count  # assuming sharing doesn't remove the report

    # Attempt to Share Non-Existent Report
    Patient().sharereportswithdoctors(patient_email, doctor_email, 'Non-existent Report')
    # Check if there are no changes in the reports
    assert len(Patient().getpatientreports(patient_email)) == updated_report_count

def test_get_id(client):
    # Assuming test data is already in the database
    report_file = ReportFile()

    # Scenario: Reports already exist
    existing_max_id = report_file.get_id()
    assert isinstance(existing_max_id, str)
    assert existing_max_id.isdigit()

def test_create_report(client):
    report_file = ReportFile()
    patient_email = 'patient1@example.com'
    doctor_email = 'doctor1@example.com'
    report_name = 'New Report'
    file_path = '/path/to/new/report'

    # Create a new report
    report_file.create(patient_email, doctor_email, report_name, file_path)

    Patient().deletereport(patient_email, report_name)

def test_getdoclist(client):
    doctor = Doctor()

    # Assuming there are doctors in the database
    doctor_list = doctor.getdoclist('John', 'Doe', 'Cardiology')
    doctor_list = doctor.getdoclist('Doc', 'tor1', 'Internal Medicine')
    doctor_list = doctor.getdoclist('Doc', 'Doe', 'Cardiology')
    doctor_list = doctor.getdoclist('q', 'Doe', 'Cardiology')
    doctor_list = doctor.getdoclist('Doc', 'pe', 'Cardiology')
    doctor_list = doctor.getdoclist('Doc', 'Doe', 'none')
    doctor_list = doctor.getdoclist('mm', 'm', 'none')
    doctor_list = doctor.getdoclist('Doc', 'q', 'none')
    doctor_list = doctor.getdoclist('q', 'do', 'none')
    assert isinstance(doctor_list, list)


def test_getdoclist1(client):
    # Assuming there are doctors in the database
    doctor = Doctor()

    result1 = doctor.getdoclist('John', 'Doe', 'Cardiology')
    assert isinstance(result1, list)


    result2 = doctor.getdoclist('Doc', 'tor1', '')
    assert isinstance(result2, list)


    result3 = doctor.getdoclist('Doc', '', 'Cardiology')
    assert isinstance(result3, list)


    result4 = doctor.getdoclist('', 'Doe', 'Cardiology')
    assert isinstance(result4, list)


    result5 = doctor.getdoclist('Doc', '', '')
    assert isinstance(result5, list)

    result6 = doctor.getdoclist('', 'Doe', '')
    assert isinstance(result6, list)

    result7 = doctor.getdoclist('', '', 'Cardiology')
    assert isinstance(result7, list)

    result8 = doctor.getdoclist('', '', '')
    assert isinstance(result8, list)


def test_getallappointments(client):
    doctor = Doctor()
    doc_email = 'doctor1@example.com'

    appointments = doctor.getallappointments(doc_email)
    doctor.getinfo(doc_email)
    assert isinstance(appointments, list)
    for appointment in appointments:
        assert 'patient_email' in appointment
        assert 'patient_name' in appointment
        assert 'date' in appointment
        assert 'time' in appointment
        assert 'reason' in appointment
        assert 'prescription' in appointment
        assert 'status' in appointment

def test_editpatient(client):
    doctor = Doctor()
    doc_email = 'doctor2@example.com'
    pat_email = 'patient1@example.com'
    new_prescription = 'New Prescription'
    new_status = 'Completed'

    # Edit patient details
    doctor.editpatient(pat_email, doc_email, new_prescription, new_status)

    old_prescription = ''
    old_status = 'inprogress'

    doctor.editpatient(pat_email, doc_email, old_prescription, old_status)

def test_pendingrequest(client):
    doctor = Doctor()
    doc_email = 'doctor1@example.com'
    pat_email = 'patient3@example.com'

    # Set an appointment to pending status
    doctor.pendingrequest(pat_email, doc_email, accept=True)
    doctor.pendingrequest(pat_email, doc_email, reject=True)

def test_doctor_availability(client):
    doctor = Doctor()
    email = 'doctor3@example.com'
    date = '2023-12-25'
    start_time = '09:00'
    end_time = '09:30'

    # Set availability
    response = doctor.setavailability(email, date, start_time, end_time)
    assert response == True

    # Check availability
    availability = doctor.getavailabilityfordate(email, date)
    assert isinstance(availability, list)
    assert any(avail for avail in availability if avail[0] == date and avail[1] == start_time and avail[2] == end_time)

    doctor.deletedoctoravailability(email, date, start_time)

def test_register_route(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert '<WrapperTestResponse streamed [200 OK]>' == str(response)

def test_register_post(client):
    response = client.post('/register',  data = {
        'role' : 'doctor'
    })
    assert response.status_code in [200, 302]

    response = client.post('/register',  data = {
        'role' : 'patient'
    })
    assert response.status_code in [200, 302]

def test_book_appointment_route(client):
    with client.session_transaction() as session:
        session['auth'] = 'testdoc1@example.com'

    response = client.post('/book-appointment', data={
        'first_name': 'testDoctor1', 
        'last_name': '',  
        'specialization': ''
    })
    assert response.status_code == 200
    assert('testDoctor1' in response.get_data(as_text=True))

def test_book_doctor_route(client):
    with client.session_transaction() as session:
        session['auth'] = 'patient1@example.com'

    response = client.get('/book_doctor/doctor1@example.com/Dr. Example')
    assert response.status_code in [200,302]

    # Simulate POST request to book an appointment
    response = client.post('/book_doctor/doctor@example.com/Dr. Example', data={
        'date': '2020-12-25',
        'time': '10:00',
        'reason': 'Regular Checkup',
        'selected_reports': 'Blood Sugar'
    })
    assert response.status_code in [200,302]  # wrong data

def test_patient_prescription_route(client):
    with client.session_transaction() as session:
        session['auth'] = 'patient1@example.com'

    response = client.get('/patient_prescription/doctor1@example.com')
    assert response.status_code in [200,302]

def test_cancel_appointment_route(client):
    with client.session_transaction() as session:
        session['auth'] = 'patient1@example.com'

    response = client.get('/cancel_appointment/doctor@example.com/cancel')
    assert response.status_code in [200,302]

def test_edit_appointment_route(client):
    with client.session_transaction() as session:
        session['auth'] = 'patient1@example.com'
        session['user_type'] = 'Patient'

    response = client.get('/edit_appointment/doctor@example.com')
    assert response.status_code in [200,302]

def test_edit_appointment_post(client):
    with client.session_transaction() as session:
        session['auth'] = 'testpat1@example.com'
        session['user_type'] = 'Patient'

    Doctor().setavailability('testdoc1@example.com', '2023-12-24', '10:00', '10:30')
    Appointment().create('testpat1@example.com', 'testdoc1@example.com', '2023-12-24', '10:00', 'issue')
    response = client.post('/edit_appointment/testdoc1@example.com', data={
        'new_date': '2023-12-25',
        'new_time': '09:00'
    })
    assert response.status_code in [200,302]
    patientinfo = Patient().getallappointments('testpat1@example.com')
    expected_data = {
        'doctor_name': 'testDoctor1',
        'doctor_email': 'testdoc1@example.com',
        'date': '12/25/2023',
        'time': '09:00 AM'
    }
    assert patientinfo[0]['doctor_name'] == expected_data['doctor_name']
    assert patientinfo[0]['doctor_email'] == expected_data['doctor_email']
    assert patientinfo[0]['date'] == expected_data['date']
    assert patientinfo[0]['time'] == expected_data['time']
    Patient().deleteappointment('testpat1@example.com', 'testdoc1@example.com')
    Doctor().deletedoctoravailability('testdoc1@example.com', '2023-12-25', '09:00')
    
def test_pending_request(client):
    with client.session_transaction() as session:
        session['auth'] = 'testdoc1@example.com'

    Doctor().setavailability('testdoc1@example.com', '2023-12-24', '10:00', '10:30')
    Appointment().create('testpat1@example.com', 'testdoc1@example.com', '2023-12-24', '10:00', 'issue')
    response = client.get('/pending_request/testpat1@example.com/accept')
    assert response.status_code in [200,302]
    doctorinfo = Doctor().getallappointments('testdoc1@example.com')
    expected_data = {
        'patient_name': 'testPatient1',
        'patient_email': 'testpat1@example.com',
        'date': '12/24/2023',
        'time': '10:00 AM',
        'reason': 'issue',
        'status': 'inprogress'
    }
    assert doctorinfo[0]['patient_name'] == expected_data['patient_name']
    assert doctorinfo[0]['patient_email'] == expected_data['patient_email']
    assert doctorinfo[0]['date'] == expected_data['date']
    assert doctorinfo[0]['time'] == expected_data['time']
    assert doctorinfo[0]['reason'] == expected_data['reason']
    assert doctorinfo[0]['status'] == expected_data['status']
    Patient().deleteappointment('testpat1@example.com', 'testdoc1@example.com')
    Doctor().deletedoctoravailability('testdoc1@example.com', '2023-12-25', '09:00')

def test_edit_patient(client):
    with client.session_transaction() as session:
        session['auth'] = 'testdoc1@example.com'

    Doctor().setavailability('testdoc1@example.com', '2023-12-24', '10:00', '10:30')
    Appointment().create('testpat1@example.com', 'testdoc1@example.com', '2023-12-24', '10:00', 'issue')
    response = client.post('/edit_patient/testpat1@example.com/testPatient1', data={
        'prescription': 'fully fit now',
        'status': 'completed'
    })
    assert response.status_code in [200,302]
    patientinfo = Patient().getallappointments('testpat1@example.com')
    expected_data = {
        'doctor_name': 'testDoctor1',
        'doctor_email': 'testdoc1@example.com',
        'date': '12/24/2023',
        'time': '10:00 AM',
        'prescription': 'fully fit now',
        'status': 'completed'
    }
    assert patientinfo[0]['doctor_name'] == expected_data['doctor_name']
    assert patientinfo[0]['doctor_email'] == expected_data['doctor_email']
    assert patientinfo[0]['date'] == expected_data['date']
    assert patientinfo[0]['time'] == expected_data['time']
    assert patientinfo[0]['prescription'] == expected_data['prescription']
    assert patientinfo[0]['status'] == expected_data['status']
    Patient().deleteappointment('testpat1@example.com', 'testdoc1@example.com')
    Doctor().deletedoctoravailability('testdoc1@example.com', '2023-12-25', '09:00')

def test_upload_reports_route(client):
    with client.session_transaction() as session:
        session['auth'] = 'patient1@example.com'

    response = client.get('/upload-report')
    assert response.status_code in [200,302]



def test_delete_report_route(client):
    with client.session_transaction() as session:
        session['auth'] = 'patient1@example.com'

    response = client.post('/delete-report/report.pdf')
    assert response.status_code in [200,302] 

def test_get_doctor_availability_route(client):
    response = client.get('/get_doctor_availability/doctor@example.com')
    assert response.status_code in [200,302]

def test_deleteData(client):
    Patient().deletePatient('testpat1@example.com')
    Doctor().deleteDoctor('testdoc1@example.com')
    patientinfo = Patient().getpatientreports('testpat1@example.com')
    doctorinfo = Doctor().getinfo('testdoc1@example.com')
    Patient().deleteappointment('testpat1@example.com', 'testdoc1@example.com')
    assert(len(patientinfo) == 0)
    assert(len(doctorinfo) == 0)