import pytest
from server import app
# from models import Doctor, Appointment  # Import necessary models


# https://docs.python.org/3/library/pydoc.html
# update -requirements.txt



@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test the home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login(client):
    """Test the login functionality."""
    response = client.post('/login', data={'email': 'test@example.com', 'password': 'testpassword'})
    assert response.status_code in [200, 302]
    # Add more assertions based on expected behavior

def test_patient_registration(client):
    """Test patient registration route."""
    response = client.post('/create-patient', data={
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'testpass',
        'weight': '70',
        'height': '170',
        'gender': 'Male',
        'age': '30',
        'medical_history': 'None'
    })
    assert response.status_code in [200, 302]
    # Add more assertions to check the outcome

def test_view_dashboard(client):
    # Simulate login
    with client.session_transaction() as session:
        session['auth'] = 'user@example.com'
        session['user_type'] = 'Patient'  # or 'Doctor'

    response = client.get('/patient-dashboard' if session['user_type'] == 'Patient' else '/doctor-dashboard')
    assert response.status_code == 200
    # Check for specific dashboard elements

def test_update_profile(client):
    # Simulate login
    with client.session_transaction() as session:
        session['auth'] = 'user@example.com'
        session['user_type'] = 'Patient'

    response = client.post('/edit_patient/user@example.com', data={
        'name': 'Updated Name',
        'email': 'user@example.com',
        # Other profile fields
    })
    assert response.status_code in [200, 302]
    # Verify profile update

# def test_upload_document(client):
#     with client.session_transaction() as session:
#         session['auth'] = 'patient@example.com'
    
#     data = {
#         'file': (BytesIO(b'my file contents'), 'test_file.jpg'),
#         'report_name': 'Test Report'
#     }
#     response = client.post('/upload-report', data=data, content_type='multipart/form-data')
#     assert response.status_code in [200, 302]
#     # Check if the file upload is successful

def test_book_appointment(client):
    """Test booking an appointment."""
    # Login as a patient first if authentication is required
    client.post('/login', data={'email': 'patient@example.com', 'password': 'password'})
    response = client.post('/book_doctor/doctor1@example.com/Doctor1', data={
        'date': '2023-04-01',
        'time': '10:00',
        'reason': 'Checkup'
    })
    assert response.status_code in [200, 302]
    # Check for successful booking indication
def test_book_appointment2(client):
    # Simulate a patient being logged in
    with client.session_transaction() as session:
        session['auth'] = 'patient@example.com'
        session['user_type'] = 'Patient'

    # Test booking an appointment
    response = client.post('/book_doctor/doctor1@example.com/Doctor1', data={
        'date': '2023-04-02',
        'time': '10:00',
        'reason': 'Consultation'
    })
    assert response.status_code in [200, 302]
    # Assert that the appointment was successfully created

# def test_doctor_availability(client):
#     response = client.get('/get_doctor_availability/doctor1@example.com')
#     assert response.status_code == 200
#     # Add assertions to check the content of the response

def test_cancel_appointment(client):
    with client.session_transaction() as session:
        session['auth'] = 'patient@example.com'
    
    # Assuming an endpoint to cancel an appointment
    response = client.get('/cancel_appointment/doctor_email@example.com/cancel')
    assert response.status_code in [200, 302]
    # Check if the appointment is canceled successfully

def test_logout(client):
    """Test the logout functionality."""
    response = client.get('/logout')
    assert response.status_code in [200, 302]
    # Check if the session is cleared

def test_logout2(client):
    with client.session_transaction() as session:
        session['auth'] = 'user@example.com'
        session['user_type'] = 'Patient'

    response = client.get('/logout')
    assert response.status_code in [200, 302]
    assert 'auth' not in session

def test_doctor_reviews_patient_info(client):
    with client.session_transaction() as session:
        session['auth'] = 'doctor@example.com'

    response = client.get('/patient_info/patient_email@example.com')
    assert response.status_code == 200
    assert b"Patient Information" in response.data

def test_set_doctor_availability(client):
    # You need to simulate a doctor being logged in
    with client.session_transaction() as session:
        session['auth'] = 'doctor1@example.com'
        session['user_type'] = 'Doctor'

    # Test setting availability
    response = client.post('/set_availability', data={
        'date': '2023-04-01',
        'start_time': '09:00',
        'end_time': '17:00'
    })
    assert response.status_code in [200, 302]
    # Additional assertions can be made based on the response or database state

def test_view_prescription(client):
    # Simulate a patient being logged in
    with client.session_transaction() as session:
        session['auth'] = 'patient@example.com'
        session['user_type'] = 'Patient'

    # Test viewing prescription
    response = client.get('/patient_prescription/doctor1@example.com')
    assert response.status_code == 200
    assert b'Prescription' in response.data  # Check for prescription content

def test_overlapping_appointments(client):
    # Create an appointment
    client.post('/create_appointment', data={...})

    # Try to create an overlapping appointment
    response = client.post('/create_appointment', data={...})
    assert response.status_code == 400  # Assuming you return 400 for bad requests
    assert b"overlap" in response.data