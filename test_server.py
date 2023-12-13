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



