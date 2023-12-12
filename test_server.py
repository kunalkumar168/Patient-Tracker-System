import pytest
from server import app
# from models import Doctor, Appointment  # Import necessary models




# https://docs.python.org/3/library/pydoc.html
# update -requirements.txt






# # Setup for the Flask test client
# @pytest.fixture
# def client():
#     app = create_app({'TESTING': True})
#     with app.test_client() as client:
#         yield client

# # Example Test Cases
# def test_home_page(client):
#     """Test the home page loads correctly."""
#     response = client.get('/')
#     assert response.status_code == 200
#     assert b"Welcome" in response.data  # Check for specific content

# def test_doctor_availability(client):
#     """Test the doctor availability endpoint."""
#     response = client.get('/get_doctor_availability/doctor@example.com')
#     assert response.status_code == 200
#     # Add more assertions based on expected response data

# def test_doctor_availability(client):
#     response = client.get('/get_doctor_availability/doctor1@example.com')
#     assert response.status_code == 200
#     # Add assertions to check the content of the response

# def test_create_appointment(client):
#     response = client.post('/create_appointment', data={'patient_email': '...', 'doctor_email': '...', 'date': '...', 'time': '...', 'reason': '...'})
#     assert response.status_code == 200
#     # Check response data or database state

# def test_overlapping_appointments(client):
#     # Create an appointment
#     client.post('/create_appointment', data={...})

#     # Try to create an overlapping appointment
#     response = client.post('/create_appointment', data={...})
#     assert response.status_code == 400  # Assuming you return 400 for bad requests
#     assert b"overlap" in response.data


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

def test_logout(client):
    """Test the logout functionality."""
    response = client.get('/logout')
    assert response.status_code in [200, 302]
    # Check if the session is cleared