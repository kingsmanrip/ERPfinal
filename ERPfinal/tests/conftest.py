import os
import sys
import pytest
from datetime import date, timedelta

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from models import db, Employee, Project, Timesheet, Material, Expense, PayrollPayment, Invoice, ProjectStatus, PaymentMethod, PaymentStatus

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Set testing configuration
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })

    # Create the database and tables
    with flask_app.app_context():
        db.create_all()

    yield flask_app

    # Clean up / reset resources
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def sample_data(app):
    """Insert sample data for testing."""
    with app.app_context():
        # Create test employees
        employee1 = Employee(
            name="John Doe",
            employee_id_str="EMP001",
            contact_details="john@example.com",
            pay_rate=25.0,
            payment_method_preference=PaymentMethod.CHECK,
            is_active=True,
            hire_date=date.today() - timedelta(days=90)
        )
        employee2 = Employee(
            name="Jane Smith",
            employee_id_str="EMP002",
            contact_details="jane@example.com",
            pay_rate=28.0,
            payment_method_preference=PaymentMethod.CASH,
            is_active=True,
            hire_date=date.today() - timedelta(days=30)
        )
        db.session.add_all([employee1, employee2])
        db.session.commit()

        # Create test projects
        project1 = Project(
            name="Office Renovation",
            project_id_str="PRJ001",
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
            project_id_str="PRJ002",
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

        # Store IDs instead of objects to prevent DetachedInstanceError
        data = {
            'employee_ids': [employee1.id, employee2.id],
            'project_ids': [project1.id, project2.id]
        }
        
        return data
