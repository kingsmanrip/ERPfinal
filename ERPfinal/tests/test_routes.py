import pytest
from datetime import date, time
from flask import url_for, session
from app import app as flask_app
from models import db, User

def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_index_route(app, client):
    """Test the index route (dashboard)."""
    with app.app_context():
        # First login as the test user
        user = User(username="testuser")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        
        login_response = login(client, "testuser", "testpassword")
        assert b'Dashboard' in login_response.data or b'Login' in login_response.data
        
        # Now access the dashboard
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data

def test_employees_route(app, client):
    """Test the employees listing route."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        # Create test employees
        from datetime import date, timedelta
        from models import Employee, PaymentMethod
        
        employee1 = Employee(
            name="John Doe",
            employee_id_str="TEST-EMP-001",
            contact_details="john@example.com",
            pay_rate=25.0,
            payment_method_preference=PaymentMethod.CHECK,
            is_active=True,
            hire_date=date.today() - timedelta(days=90)
        )
        
        employee2 = Employee(
            name="Jane Smith",
            employee_id_str="TEST-EMP-002",
            contact_details="jane@example.com",
            pay_rate=28.0,
            payment_method_preference=PaymentMethod.CASH,
            is_active=True,
            hire_date=date.today() - timedelta(days=30)
        )
        
        db.session.add_all([employee1, employee2])
        db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        # Now access the employees page
        response = client.get('/employees', follow_redirects=True)
        assert response.status_code == 200
        assert b'Employees' in response.data
        # Check that sample employees are listed
        assert b'John Doe' in response.data
        assert b'Jane Smith' in response.data

def test_projects_route(app, client):
    """Test the projects listing route."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser") 
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        # Create test projects
        from datetime import date, timedelta
        from models import Project, ProjectStatus
        
        project1 = Project(
            name="Office Renovation",
            project_id_str="TEST-PRJ-001",
            client_name="ABC Corp",
            location="123 Business St",
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() + timedelta(days=20),
            contract_value=5000.0,
            description="Renovate office space",
            status=ProjectStatus.IN_PROGRESS
        )
        
        project2 = Project(
            name="Residential Painting",
            project_id_str="TEST-PRJ-002",
            client_name="Smith Family",
            location="456 Home Ave",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
            contract_value=2500.0,
            description="Paint living room and kitchen",
            status=ProjectStatus.PENDING
        )
        
        db.session.add_all([project1, project2])
        db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        # Now access the projects page
        response = client.get('/projects', follow_redirects=True)
        assert response.status_code == 200
        assert b'Projects' in response.data
        # Check that sample projects are listed
        assert b'Office Renovation' in response.data
        assert b'Residential Painting' in response.data

def test_add_employee_route(app, client):
    """Test adding a new employee."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        # Get the form page
        response = client.get('/employee/add', follow_redirects=True)
        assert response.status_code == 200
        assert b'Add Employee' in response.data
        
        # Submit the form with valid data
        employee_data = {
            'name': 'New Test Employee',
            'employee_id_str': 'EMP-TEST',
            'contact_details': 'newtest@example.com',
            'pay_rate': 24.50,
            'payment_method_preference': 'CHECK',
            'is_active': True,
            'hire_date': '2025-01-01'
        }
        response = client.post('/employee/add', data=employee_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Employee New Test Employee added successfully!' in response.data
        assert b'New Test Employee' in response.data

def test_add_project_route(app, client):
    """Test adding a new project."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        # Get the form page
        response = client.get('/project/add', follow_redirects=True)
        assert response.status_code == 200
        assert b'Add Project' in response.data
        
        # Submit the form with valid data
        project_data = {
            'name': 'New Test Project',
            'project_id_str': 'PRJ-TEST',
            'client_name': 'Test Client',
            'location': 'Test Location',
            'start_date': '2025-04-01',
            'end_date': '2025-04-30',
            'contract_value': 7500.0,
            'description': 'This is a test project',
            'status': 'PENDING'
        }
        response = client.post('/project/add', data=project_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Project New Test Project added successfully!' in response.data
        assert b'New Test Project' in response.data

def test_future_enhancements_route(app, client):
    """Test the future enhancements page.
    The route may still exist but the link has been removed from the UI."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        # The route may still exist, so we'll accept any valid HTTP response
        response = client.get('/future-enhancements')
        # We expect either success (200), redirect (302), or not found (404)
        assert response.status_code in [200, 302, 404]
        
        # With follow_redirects, we should end up somewhere valid
        response = client.get('/future-enhancements', follow_redirects=True)
        assert response.status_code == 200

def test_suggest_enhancement_route(app, client):
    """Test submitting an enhancement suggestion."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        suggestion_data = {
            'title': 'Integration with QuickBooks',
            'description': 'Add integration with QuickBooks for seamless accounting workflows.',
            'priority': 'Medium'
        }
        response = client.post('/suggest-enhancement', data=suggestion_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Thank you for your enhancement suggestion' in response.data
        assert b'Integration with QuickBooks' in response.data

def test_project_detail_route(app, client):
    """Test the project detail page."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        # Create a test project
        from models import Project, ProjectStatus
        from datetime import date, timedelta
        
        test_project = Project(
            name="Test Detail Project",
            project_id_str="TEST-DETAIL-001",
            client_name="Test Client",
            location="Test Location",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            contract_value=10000.0,
            description="Project for detail view test",
            status=ProjectStatus.IN_PROGRESS
        )
        db.session.add(test_project)
        db.session.commit()
        
        # Get the project ID
        project_id = test_project.id
        
        # Test the project detail page
        response = client.get(f'/project/view/{project_id}', follow_redirects=True)
        assert response.status_code == 200
        assert bytes(test_project.name, 'utf-8') in response.data
        assert b'Project Details' in response.data
        assert b'Contract Value' in response.data

def test_nonexistent_route(app, client):
    """Test accessing a non-existent route."""
    with app.app_context():
        # First login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        login(client, "testuser", "testpassword")
        
        response = client.get('/nonexistent-page', follow_redirects=True)
        assert response.status_code == 404
