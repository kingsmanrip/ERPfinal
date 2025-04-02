from app import app, db
from sqlalchemy import Column, String
import sqlalchemy as sa

def add_columns_to_payroll_payment():
    """Add check_number and bank_name columns to payroll_payment table"""
    with app.app_context():
        # Using SQLAlchemy core to execute raw SQL
        conn = db.engine.connect()
        
        try:
            print("Adding check_number column to payroll_payment table...")
            conn.execute(sa.text('ALTER TABLE payroll_payment ADD COLUMN check_number VARCHAR(50)'))
            
            print("Adding bank_name column to payroll_payment table...")
            conn.execute(sa.text('ALTER TABLE payroll_payment ADD COLUMN bank_name VARCHAR(100)'))
            
            conn.commit()
            print("Database schema updated successfully!")
        except Exception as e:
            print(f"Error updating schema: {e}")
            # The column might already exist, which is fine
            conn.commit()

if __name__ == '__main__':
    add_columns_to_payroll_payment()
