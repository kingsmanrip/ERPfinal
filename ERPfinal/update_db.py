import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, Float, String
from app import app

def update_database():
    # Get the database URI from the app config
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    
    # Create an engine connected to the database
    engine = create_engine(db_uri)
    
    # Create a metadata object
    metadata = MetaData()
    
    # Reflect the existing table
    payroll_payment = Table('payroll_payment', metadata, autoload_with=engine)
    
    columns_to_add = {
        'gross_amount': 'FLOAT',
        'check_number': 'TEXT',
        'bank_name': 'TEXT'
    }
    
    # Add each missing column
    with engine.begin() as conn:
        for column_name, column_type in columns_to_add.items():
            # Check if the column already exists
            if column_name not in payroll_payment.columns:
                print(f"Adding '{column_name}' column to payroll_payment table...")
                # Add the new column
                conn.execute(f"ALTER TABLE payroll_payment ADD COLUMN {column_name} {column_type}")
                print(f"Column '{column_name}' added successfully!")
            else:
                print(f"Column '{column_name}' already exists in payroll_payment table.")
    
    print("Database update completed!")

if __name__ == "__main__":
    # Stop the app before updating the database
    print("Updating database schema...")
    update_database()
