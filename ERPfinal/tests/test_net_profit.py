import pytest
from datetime import date, time, timedelta
from models import Employee, Project, Timesheet, Material, Expense, Invoice, ProjectStatus, PaymentMethod, PaymentStatus

def test_actual_net_profit_calculation(app):
    """Test that actual net profit is calculated correctly."""
    with app.app_context():
        from models import db
        
        # Create a test project
        project = Project(
            name="Net Profit Test Project",
            project_id_str="NPTP001",
            client_name="Test Client",
            contract_value=10000.0,
            status=ProjectStatus.PAID
        )
        db.session.add(project)
        db.session.flush()  # Get the project ID
        
        # Add some materials
        material = Material(
            project_id=project.id,
            description="Test Material",
            supplier="Test Supplier",
            cost=1000.0,
            purchase_date=date.today() - timedelta(days=30),
            category="Test Category"
        )
        db.session.add(material)
        
        # Add some expenses
        expense = Expense(
            project_id=project.id,
            description="Test Expense",
            category="Test Category",
            amount=500.0,
            date=date.today() - timedelta(days=20),
            supplier_vendor="Test Vendor",
            payment_method=PaymentMethod.CHECK,
            payment_status=PaymentStatus.PAID
        )
        db.session.add(expense)
        
        # Add an employee
        employee = Employee(
            name="Test Employee",
            employee_id_str="TE001",
            contact_details="test@example.com",
            pay_rate=25.0,
            is_active=True
        )
        db.session.add(employee)
        db.session.flush()  # Get the employee ID
        
        # Add a timesheet (8 hours at $25/hour = $200)
        timesheet = Timesheet(
            employee_id=employee.id,
            project_id=project.id,
            date=date.today() - timedelta(days=15),
            entry_time=time(8, 0),
            exit_time=time(16, 0),
            lunch_duration_minutes=30
        )
        db.session.add(timesheet)
        
        # Add a paid invoice
        invoice = Invoice(
            project_id=project.id,
            invoice_number="INV-TEST-001",
            invoice_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=5),
            amount=9000.0,  # Less than contract value
            status=PaymentStatus.PAID,
            payment_received_date=date.today() - timedelta(days=3)
        )
        db.session.add(invoice)
        
        db.session.commit()
        
        # Refresh the project
        project = db.session.get(Project, project.id)
        
        # Total cost should be $1000 (material) + $500 (expense) + $200 (labor) = $1700
        assert project.total_material_cost == 1000.0
        assert project.total_other_expenses == 500.0
        assert project.total_labor_cost == 200.0
        assert project.total_cost == 1700.0
        
        # Actual revenue should be $9000 (paid invoice)
        assert project.actual_revenue == 9000.0
        
        # Actual net profit should be $9000 - $1700 = $7300
        assert project.actual_net_profit == 7300.0
        
        # Clean up
        db.session.delete(invoice)
        db.session.delete(timesheet)
        db.session.delete(employee)
        db.session.delete(expense)
        db.session.delete(material)
        db.session.delete(project)
        db.session.commit()

def test_multiple_invoices_net_profit(app):
    """Test net profit calculation with multiple invoices in different states."""
    with app.app_context():
        from models import db
        
        # Create a test project
        project = Project(
            name="Multiple Invoices Test",
            project_id_str="MIT001",
            client_name="Test Client",
            contract_value=20000.0,
            status=ProjectStatus.INVOICED
        )
        db.session.add(project)
        db.session.flush()
        
        # Add a fixed cost
        expense = Expense(
            project_id=project.id,
            description="Project Expenses",
            category="Materials",
            amount=5000.0,
            date=date.today() - timedelta(days=30),
            supplier_vendor="Supplier",
            payment_method=PaymentMethod.CHECK,
            payment_status=PaymentStatus.PAID
        )
        db.session.add(expense)
        
        # Add multiple invoices in different states
        # Paid invoice
        invoice1 = Invoice(
            project_id=project.id,
            invoice_number="INV-MULTI-001",
            invoice_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=10),
            amount=8000.0,
            status=PaymentStatus.PAID,
            payment_received_date=date.today() - timedelta(days=5)
        )
        db.session.add(invoice1)
        
        # Pending invoice
        invoice2 = Invoice(
            project_id=project.id,
            invoice_number="INV-MULTI-002",
            invoice_date=date.today() - timedelta(days=10),
            due_date=date.today() + timedelta(days=10),
            amount=7000.0,
            status=PaymentStatus.PENDING
        )
        db.session.add(invoice2)
        
        # Overdue invoice
        invoice3 = Invoice(
            project_id=project.id,
            invoice_number="INV-MULTI-003",
            invoice_date=date.today() - timedelta(days=30),
            due_date=date.today() - timedelta(days=15),
            amount=5000.0,
            status=PaymentStatus.OVERDUE
        )
        db.session.add(invoice3)
        
        db.session.commit()
        
        # Refresh the project
        project = db.session.get(Project, project.id)
        
        # Total cost is $5000
        assert project.total_cost == 5000.0
        
        # Only the paid invoice should count toward actual revenue ($8000)
        assert project.actual_revenue == 8000.0
        
        # Actual net profit should be $8000 - $5000 = $3000
        assert project.actual_net_profit == 3000.0
        
        # Clean up
        db.session.delete(invoice1)
        db.session.delete(invoice2)
        db.session.delete(invoice3)
        db.session.delete(expense)
        db.session.delete(project)
        db.session.commit()
