"""
Manual test script for Accounts Payable module.
This script will test basic CRUD operations on the accounts payable table.
"""

import os
import sys
from datetime import date, timedelta
from app import app, db
from models import AccountsPayable, PaymentMethod, PaymentStatus, ExpenseCategory

def run_tests():
    """Run a series of tests against the Accounts Payable functionality"""
    print("Starting Accounts Payable tests...")
    
    # Test 1: Create a new accounts payable record
    print("\nTEST 1: Create a new accounts payable record")
    try:
        new_ap = AccountsPayable(
            vendor_name="Test Vendor",
            description="Test supplies",
            amount=250.50,
            issue_date=date.today() - timedelta(days=10),
            due_date=date.today() + timedelta(days=15),
            payment_method=PaymentMethod.CASH,
            category=ExpenseCategory.OFFICE,
            status=PaymentStatus.PENDING
        )
        db.session.add(new_ap)
        db.session.commit()
        
        # Verify it was created
        record = AccountsPayable.query.filter_by(vendor_name="Test Vendor").first()
        if record and record.amount == 250.50 and record.status == PaymentStatus.PENDING:
            print("✓ Successfully created accounts payable record")
        else:
            print("✗ Failed to create accounts payable record correctly")
            
        # Save record ID for later tests
        record_id = record.id
    except Exception as e:
        print(f"✗ Error creating accounts payable record: {e}")
        return
    
    # Test 2: Read/Query accounts payable records
    print("\nTEST 2: Query accounts payable records")
    try:
        # Get all records
        all_records = AccountsPayable.query.all()
        print(f"✓ Found {len(all_records)} total records")
        
        # Filter by status
        pending = AccountsPayable.query.filter(AccountsPayable.status == PaymentStatus.PENDING).all()
        print(f"✓ Found {len(pending)} pending records")
        
        # Filter by due date
        today = date.today()
        upcoming = AccountsPayable.query.filter(
            AccountsPayable.due_date >= today,
            AccountsPayable.due_date <= today + timedelta(days=30),
            AccountsPayable.status != PaymentStatus.PAID
        ).all()
        print(f"✓ Found {len(upcoming)} records due in the next 30 days")
    except Exception as e:
        print(f"✗ Error querying accounts payable records: {e}")
    
    # Test 3: Update an accounts payable record
    print("\nTEST 3: Update an accounts payable record")
    try:
        record = AccountsPayable.query.get(record_id)
        if not record:
            print("✗ Could not find record to update")
            return
            
        # Update the record
        record.amount = 300.75
        record.description = "Updated description"
        db.session.commit()
        
        # Verify the update
        updated = AccountsPayable.query.get(record_id)
        if updated.amount == 300.75 and updated.description == "Updated description":
            print("✓ Successfully updated accounts payable record")
        else:
            print("✗ Failed to update accounts payable record")
    except Exception as e:
        print(f"✗ Error updating accounts payable record: {e}")
    
    # Test 4: Mark a record as paid
    print("\nTEST 4: Mark record as paid")
    try:
        record = AccountsPayable.query.get(record_id)
        if not record:
            print("✗ Could not find record to mark as paid")
            return
            
        # Mark as paid
        record.status = PaymentStatus.PAID
        record.payment_date = date.today()
        record.payment_method = PaymentMethod.CHECK
        record.check_number = "12345"
        record.bank_name = "Test Bank"
        db.session.commit()
        
        # Verify the payment
        paid = AccountsPayable.query.get(record_id)
        if (paid.status == PaymentStatus.PAID and 
            paid.payment_date == date.today() and
            paid.check_number == "12345"):
            print("✓ Successfully marked record as paid")
        else:
            print("✗ Failed to mark record as paid")
    except Exception as e:
        print(f"✗ Error marking record as paid: {e}")
    
    # Test 5: Delete a record
    print("\nTEST 5: Delete a record")
    try:
        # Create a temporary record to delete
        temp_ap = AccountsPayable(
            vendor_name="Temp Vendor",
            description="To be deleted",
            amount=100.00,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            payment_method=PaymentMethod.CASH,
            category=ExpenseCategory.OTHER,
            status=PaymentStatus.PENDING
        )
        db.session.add(temp_ap)
        db.session.commit()
        
        # Get the temp record ID
        temp_id = temp_ap.id
        
        # Delete the record
        db.session.delete(temp_ap)
        db.session.commit()
        
        # Verify deletion
        deleted = AccountsPayable.query.get(temp_id)
        if deleted is None:
            print("✓ Successfully deleted accounts payable record")
        else:
            print("✗ Failed to delete accounts payable record")
    except Exception as e:
        print(f"✗ Error deleting accounts payable record: {e}")
    
    # Test 6: Validate business rules
    print("\nTEST 6: Validate business rules")
    try:
        # Rule 1: Due date cannot be earlier than issue date
        invalid_ap = AccountsPayable(
            vendor_name="Invalid Vendor",
            description="Invalid dates",
            amount=100.00,
            issue_date=date.today(),
            due_date=date.today() - timedelta(days=1),  # Due date before issue date
            payment_method=PaymentMethod.CASH,
            category=ExpenseCategory.OTHER,
            status=PaymentStatus.PENDING
        )
        
        error_caught = False
        try:
            invalid_ap.validate_dates()
        except ValueError:
            error_caught = True
        
        if error_caught:
            print("✓ Successfully caught invalid due date")
        else:
            print("✗ Failed to catch invalid due date")
            
        # Rule 2: Paid record must have payment details
        invalid_paid = AccountsPayable(
            vendor_name="Invalid Paid",
            description="Missing payment details",
            amount=100.00,
            issue_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=5),
            payment_method=PaymentMethod.CHECK,
            category=ExpenseCategory.OTHER,
            status=PaymentStatus.PAID,
            # Missing check_number and bank_name
        )
        
        error_caught = False
        try:
            invalid_paid.validate_payment_details()
        except ValueError:
            error_caught = True
        
        if error_caught:
            print("✓ Successfully caught missing payment details")
        else:
            print("✗ Failed to catch missing payment details")
    except Exception as e:
        print(f"✗ Error testing validation rules: {e}")
    
    print("\nAccounts Payable tests completed.")

if __name__ == "__main__":
    with app.app_context():
        run_tests()
