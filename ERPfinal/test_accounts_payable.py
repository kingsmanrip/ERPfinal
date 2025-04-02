import os
import unittest
import datetime
from flask import url_for
from app import app, db
from models import AccountsPayable, PaymentMethod, PaymentStatus, ExpenseCategory, Project

class AccountsPayableTests(unittest.TestCase):
    """Test suite for the Accounts Payable module"""
    
    def setUp(self):
        """Set up test environment"""
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create all tables in the in-memory database
        db.create_all()
        
        # Create a test project
        test_project = Project(
            name='Test Project',
            project_id_str='TEST001',
            client_name='Test Client',
            description='Test project for accounts payable',
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            status='IN_PROGRESS'
        )
        db.session.add(test_project)
        db.session.commit()
        self.test_project_id = test_project.id
        
        # Add test data
        self.create_test_data()
        
        # Mock the login
        with self.app as c:
            with c.session_transaction() as sess:
                sess['logged_in'] = True
                sess['username'] = 'test_user'
    
    def create_test_data(self):
        """Create test accounts payable records"""
        # Create a pending record
        pending_ap = AccountsPayable(
            vendor_name='ABC Supplier',
            description='Office supplies',
            amount=150.75,
            issue_date=datetime.date.today() - datetime.timedelta(days=10),
            due_date=datetime.date.today() + datetime.timedelta(days=20),
            payment_method=PaymentMethod.BANK_TRANSFER,
            category=ExpenseCategory.SUPPLIES,
            status=PaymentStatus.PENDING
        )
        
        # Create an overdue record
        overdue_ap = AccountsPayable(
            vendor_name='XYZ Utilities',
            description='Electricity bill',
            amount=285.30,
            issue_date=datetime.date.today() - datetime.timedelta(days=45),
            due_date=datetime.date.today() - datetime.timedelta(days=15),
            payment_method=PaymentMethod.OTHER,
            category=ExpenseCategory.UTILITIES,
            status=PaymentStatus.OVERDUE
        )
        
        # Create a paid record
        paid_ap = AccountsPayable(
            vendor_name='123 Insurance',
            description='Insurance premium',
            amount=750.00,
            issue_date=datetime.date.today() - datetime.timedelta(days=30),
            due_date=datetime.date.today() - datetime.timedelta(days=5),
            payment_method=PaymentMethod.CHECK,
            category=ExpenseCategory.INSURANCE,
            status=PaymentStatus.PAID,
            payment_date=datetime.date.today() - datetime.timedelta(days=3),
            check_number='1234',
            bank_name='Test Bank',
            project_id=self.test_project_id
        )
        
        db.session.add_all([pending_ap, overdue_ap, paid_ap])
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_accounts_payable_list(self):
        """Test the accounts payable listing page"""
        response = self.app.get('/accounts_payable')
        self.assertEqual(response.status_code, 200)
        
        # Check that all three test records are shown
        self.assertIn(b'ABC Supplier', response.data)
        self.assertIn(b'XYZ Utilities', response.data)
        self.assertIn(b'123 Insurance', response.data)
        
        # Check for dashboard stats
        self.assertIn(b'Total Pending', response.data)
        self.assertIn(b'Overdue Payments', response.data)
        self.assertIn(b'Due This Week', response.data)
    
    def test_filtering(self):
        """Test filtering of accounts payable records"""
        # Test status filter
        response = self.app.get('/accounts_payable?status=PENDING')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ABC Supplier', response.data)
        self.assertNotIn(b'XYZ Utilities', response.data)
        
        # Test vendor filter
        response = self.app.get('/accounts_payable?vendor=XYZ')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'XYZ Utilities', response.data)
        self.assertNotIn(b'ABC Supplier', response.data)
        
        # Test category filter
        response = self.app.get('/accounts_payable?category=INSURANCE')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'123 Insurance', response.data)
        self.assertNotIn(b'ABC Supplier', response.data)
        
        # Test due date filter
        response = self.app.get('/accounts_payable?due_date=overdue')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'XYZ Utilities', response.data)
    
    def test_add_accounts_payable(self):
        """Test adding a new accounts payable record"""
        response = self.app.get('/accounts_payable/add')
        self.assertEqual(response.status_code, 200)
        
        # Submit a new record
        data = {
            'vendor_name': 'New Vendor',
            'description': 'Test description',
            'amount': 100.00,
            'issue_date': datetime.date.today().strftime('%Y-%m-%d'),
            'due_date': (datetime.date.today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
            'payment_method': 'CASH',
            'category': 'RENT',
            'status': 'PENDING',
            'project_id': 0,
            'notes': 'Test notes'
        }
        
        response = self.app.post('/accounts_payable/add', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that the new record appears in the list
        self.assertIn(b'New Vendor', response.data)
        self.assertIn(b'Test description', response.data)
        
        # Verify in database
        record = AccountsPayable.query.filter_by(vendor_name='New Vendor').first()
        self.assertIsNotNone(record)
        self.assertEqual(record.amount, 100.00)
        self.assertEqual(record.status, PaymentStatus.PENDING)
    
    def test_edit_accounts_payable(self):
        """Test editing an accounts payable record"""
        # Get an existing record
        record = AccountsPayable.query.filter_by(vendor_name='ABC Supplier').first()
        
        response = self.app.get(f'/accounts_payable/edit/{record.id}')
        self.assertEqual(response.status_code, 200)
        
        # Update the record
        data = {
            'vendor_name': 'ABC Supplier Updated',
            'description': 'Updated description',
            'amount': 200.50,
            'issue_date': record.issue_date.strftime('%Y-%m-%d'),
            'due_date': record.due_date.strftime('%Y-%m-%d'),
            'payment_method': 'CASH',
            'category': 'SUPPLIES',
            'status': 'PENDING',
            'project_id': 0,
            'notes': 'Updated notes'
        }
        
        response = self.app.post(f'/accounts_payable/edit/{record.id}', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that the record was updated
        updated_record = AccountsPayable.query.get(record.id)
        self.assertEqual(updated_record.vendor_name, 'ABC Supplier Updated')
        self.assertEqual(updated_record.amount, 200.50)
        self.assertEqual(updated_record.description, 'Updated description')
    
    def test_mark_paid(self):
        """Test marking an accounts payable record as paid"""
        # Get a pending record
        record = AccountsPayable.query.filter_by(vendor_name='ABC Supplier').first()
        
        # Mark as paid
        data = {
            'payment_date': datetime.date.today().strftime('%Y-%m-%d'),
            'payment_method': 'CHECK',
            'check_number': '5678',
            'bank_name': 'Test Bank'
        }
        
        response = self.app.post(f'/accounts_payable/mark_paid/{record.id}', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that the record was updated
        updated_record = AccountsPayable.query.get(record.id)
        self.assertEqual(updated_record.status, PaymentStatus.PAID)
        self.assertEqual(updated_record.check_number, '5678')
        self.assertEqual(updated_record.bank_name, 'Test Bank')
    
    def test_delete_accounts_payable(self):
        """Test deleting an accounts payable record"""
        # Get a record
        record = AccountsPayable.query.filter_by(vendor_name='ABC Supplier').first()
        
        # Delete the record
        response = self.app.post(f'/accounts_payable/delete/{record.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify the record was deleted
        deleted_record = AccountsPayable.query.get(record.id)
        self.assertIsNone(deleted_record)
    
    def test_export_accounts_payable(self):
        """Test exporting accounts payable data"""
        # Test CSV export
        response = self.app.get('/export/accounts_payable/csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.headers['Content-Type'])
        
        # Test Excel export
        response = self.app.get('/export/accounts_payable/excel')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.ms-excel', response.headers['Content-Type'])
        
        # Test PDF export
        response = self.app.get('/export/accounts_payable/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/pdf', response.headers['Content-Type'])

if __name__ == '__main__':
    unittest.main()
