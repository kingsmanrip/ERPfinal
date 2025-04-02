import pytest
from datetime import date, time, timedelta
from models import db, Employee, Project, Timesheet, Material, Expense, Invoice, ProjectStatus, PaymentMethod, PaymentStatus, User

def login(client, username, password):
    """Helper function to log in a user."""
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_project_workflow(app, client):
    """Test the entire project workflow from creation to completion."""
    with app.app_context():
        # Create and login as the test user
        user = User(username="testuser")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        
        login_response = login(client, "testuser", "testpassword")
        assert login_response.status_code == 200
        # 1. Create a new employee
        employee_data = {
            'name': 'Integration Tester',
            'employee_id_str': 'INT001',
            'contact_details': 'integration@test.com',
            'pay_rate': 30.0,
            'payment_method_preference': 'CHECK',
            'is_active': True,
            'hire_date': '2025-01-15'
        }
        response = client.post('/employee/add', data=employee_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Integration Tester' in response.data
        
        # Get the employee ID
        employee = Employee.query.filter_by(name='Integration Tester').first()
        assert employee is not None
        
        # 2. Create a new project
        project_data = {
            'name': 'Integration Test Project',
            'project_id_str': 'INT-PRJ-001',
            'client_name': 'Integration Client',
            'location': 'Test Site',
            'start_date': date.today().strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'contract_value': 8000.0,
            'description': 'Project for integration testing',
            'status': 'IN_PROGRESS'
        }
        response = client.post('/project/add', data=project_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Integration Test Project' in response.data
        
        # Get the project ID
        project = Project.query.filter_by(name='Integration Test Project').first()
        assert project is not None
        
        # 3. Add timesheet entries
        timesheet_data = {
            'employee_id': employee.id,
            'project_id': project.id,
            'date': date.today().strftime('%Y-%m-%d'),
            'entry_time': '08:00',
            'exit_time': '17:00',
            'lunch_duration_minutes': 60
        }
        response = client.post('/timesheet/add', data=timesheet_data, follow_redirects=True)
        assert response.status_code == 200
        # Check for the actual flash message format used in the app
        assert b'Timesheet for Integration Tester on project Integration Test Project added successfully!' in response.data
        
        # 4. Add materials
        material_data = {
            'project_id': project.id,
            'description': 'Integration Test Material',
            'supplier': 'Test Supplier',
            'cost': 500.0,
            'purchase_date': date.today().strftime('%Y-%m-%d'),
            'category': 'Testing Materials'
        }
        response = client.post('/material/add', data=material_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Material added successfully' in response.data
        
        # 5. Add expense
        expense_data = {
            'description': 'Integration Test Expense',
            'category': 'Testing',
            'amount': 250.0,
            'date': date.today().strftime('%Y-%m-%d'),
            'supplier_vendor': 'Test Vendor',
            'payment_method': 'CHECK',
            'payment_status': 'PENDING',
            'project_id': project.id
        }
        response = client.post('/expense/add', data=expense_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Expense added successfully' in response.data
        
        # Update project status to COMPLETED before creating an invoice
        # This is necessary because invoices can only be created for COMPLETED or INVOICED projects
        project.status = ProjectStatus.COMPLETED
        db.session.commit()
        
        # 6. Create invoice
        invoice_data = {
            'project_id': project.id,
            'invoice_number': 'INV-INT-001',
            'invoice_date': date.today().strftime('%Y-%m-%d'),
            'due_date': (date.today() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'amount': 8000.0,
            'status': 'PENDING'
        }
        response = client.post('/invoice/add', data=invoice_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invoice added successfully!' in response.data
        
        # 7. Verify project details
        response = client.get(f'/project/view/{project.id}')
        assert response.status_code == 200
        
        # Check that project shows correct financial data
        # This is a simple check that the page loads correctly with all components
        assert b'Integration Test Project' in response.data
        assert b'Labor Cost' in response.data
        assert b'Material Cost' in response.data
        assert b'Other Expenses' in response.data
        assert b'Total Cost' in response.data
        assert b'Profit' in response.data
        
        # Timesheet should show in project details
        assert b'Integration Tester' in response.data
        # Material should show in project details
        assert b'Integration Test Material' in response.data
        # Expense should show in project details
        assert b'Integration Test Expense' in response.data
        # Invoice should show in project details
        assert b'INV-INT-001' in response.data

def test_payroll_workflow(app, client, sample_data):
    """Test the full payroll workflow from timesheet entry to payment."""
    with app.app_context():
        # Create and login as the test user
        if not User.query.filter_by(username="testuser").first():
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        
        login_response = login(client, "testuser", "testpassword")
        assert login_response.status_code == 200
        # 1. Get an employee from sample data
        employee_id = sample_data['employee_ids'][0]
        employee = db.session.get(Employee, employee_id)  # Use session.get instead of query.get
        
        # 2. Get a project from sample data
        project_id = sample_data['project_ids'][0]
        project = db.session.get(Project, project_id)  # Use session.get instead of query.get
        
        # 3. Add a timesheet for this employee on this project
        timesheet_data = {
            'employee_id': employee.id,
            'project_id': project.id,
            'date': date.today().strftime('%Y-%m-%d'),
            'entry_time': '08:00',
            'exit_time': '17:00',
            'lunch_duration_minutes': 30
        }
        
        with client:
            response = client.post('/timesheet/add', data=timesheet_data, follow_redirects=True)
            assert response.status_code == 200
        
        # 4. Check the payroll report - use the correct route from app.py
        response = client.get('/payroll/report')
        assert response.status_code == 200
        
        # 5. Record a payroll payment
        payment_data = {
            'employee_id': employee.id,
            'pay_period_start': (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'pay_period_end': date.today().strftime('%Y-%m-%d'),
            'gross_amount': 1000.0,  # Changed from 'amount' to 'gross_amount' to match the updated form
            'payment_date': date.today().strftime('%Y-%m-%d'),
            'payment_method': 'CASH',
            'notes': 'Integration test payment'
        }
        
        # Use the correct route for recording payments
        response = client.post('/payroll/record-payment', data=payment_data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Payment recorded successfully' in response.data
