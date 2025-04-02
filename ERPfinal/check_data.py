from app import app
from models import db, Project, Employee, Timesheet, Material, Expense, PayrollPayment, Invoice

def check_data():
    with app.app_context():
        print(f"Projects: {Project.query.count()}")
        print(f"Employees: {Employee.query.count()}")
        print(f"Timesheets: {Timesheet.query.count()}")
        print(f"Materials: {Material.query.count()}")
        print(f"Expenses: {Expense.query.count()}")
        print(f"Payroll Payments: {PayrollPayment.query.count()}")
        print(f"Invoices: {Invoice.query.count()}")

if __name__ == "__main__":
    check_data()
