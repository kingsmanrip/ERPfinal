import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5
from functools import wraps
import flask_excel as excel
from fpdf import FPDF
import tempfile
import io
import pandas as pd

from models import db, Employee, Project, Timesheet, Material, Expense, PayrollPayment, PayrollDeduction, Invoice, ProjectStatus, PaymentMethod, PaymentStatus, User, DeductionType, ExpenseCategory, AccountsPayable
from forms import EmployeeForm, ProjectForm, TimesheetForm, MaterialForm, ExpenseForm, PayrollPaymentForm, PayrollDeductionForm, InvoiceForm, LoginForm, AccountsPayableForm

load_dotenv()  # Load environment variables if needed

app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-default-hardcoded-secret-key')  # CHANGE THIS in production
# Use instance folder for the database
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "erp.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db.init_app(app)
csrf = CSRFProtect(app)
bootstrap = Bootstrap5(app)  # Initialize Bootstrap5
excel.init_excel(app)  # Initialize Excel export

# --- Authentication utilities ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def get_week_start_end(dt=None):
    """Gets the start (Monday) and end (Sunday) dates of the week for a given date."""
    dt = dt or date.today()
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    return start, end

# --- Export Helpers ---
def export_to_excel(data, prefix):
    """Helper function to export data to Excel"""
    df = pd.DataFrame(data)
    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)
    
    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f'{prefix}_report.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def export_to_pdf(data, title, filename):
    """Helper function to export data to PDF"""
    pdf = FPDF()
    pdf.add_page('L')  # Landscape orientation for more columns
    
    # Add title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'{title} Report', 0, 1, 'C')
    pdf.ln(5)
    
    # Add header
    if data:
        pdf.set_font('Arial', 'B', 8)
        col_width = 270 / len(data[0].keys())
        for key in data[0].keys():
            pdf.cell(col_width, 10, str(key), 1)
        pdf.ln()
        
        # Add data
        pdf.set_font('Arial', '', 8)
        for item in data:
            for key, value in item.items():
                pdf.cell(col_width, 10, str(value)[:20], 1)
            pdf.ln()
    
    # Create temp file and write PDF to it
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf_path = tmp.name
        pdf.output(pdf_path)
        
    # Return the created PDF file
    return send_file(
        pdf_path,
        as_attachment=True, 
        download_name=filename,
        mimetype='application/pdf'
    )

def export_to_csv(data, prefix):
    """Helper function to export data to CSV"""
    df = pd.DataFrame(data)
    csv_file = io.StringIO()
    df.to_csv(csv_file, index=False)
    csv_file.seek(0)
    
    return Response(
        csv_file.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={prefix}_report.csv'
        }
    )

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# --- Routes ---

@app.route('/')
@login_required
def index():
    """Dashboard"""
    # Total projects counter (instead of just active projects)
    total_projects = Project.query.count()
    active_projects = Project.query.filter(Project.status == ProjectStatus.IN_PROGRESS).count()
    
    # Project financial metrics - include all projects
    all_projects = Project.query.all()
    
    # Sort by profit margin (descending)
    sorted_projects = sorted(
        all_projects, 
        key=lambda p: p.profit_margin if p.profit_margin is not None else -999, 
        reverse=True
    )
    
    # Calculate progress bar widths for the top projects
    top_projects = sorted_projects[:5]
    for project in top_projects:
        # Calculate a width between 0-100% for the progress bar
        # Add 40% to profit margin to make small profit margins visible
        # but cap at 100%
        profit_margin = project.profit_margin or 0
        project.progress_width = max(0, min(100, profit_margin + 40))
    
    # Financial summary
    total_invoiced = db.session.query(db.func.sum(Invoice.amount)).scalar() or 0
    unpaid_invoices = db.session.query(db.func.sum(Invoice.amount)).filter(
        Invoice.status != PaymentStatus.PAID
    ).scalar() or 0
    
    # Calculate total net profit across all projects
    total_net_profit = sum(project.actual_net_profit for project in all_projects)
    
    # Timesheet summary for current week
    start_of_week, end_of_week = get_week_start_end()
    # Get timesheets directly instead of using the property in SQL
    weekly_timesheets = Timesheet.query.filter(
        Timesheet.date >= start_of_week,
        Timesheet.date <= end_of_week
    ).all()
    
    # Calculate hours in Python logic instead of SQL
    weekly_hours = sum(ts.calculated_hours for ts in weekly_timesheets)
    
    # Project status distribution
    project_status_counts = {}
    for status in ProjectStatus:
        project_status_counts[status.name] = Project.query.filter(Project.status == status).count()
    
    # Recent expenses
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    expenses_total = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    
    # Monthly expense trend (last 5 months)
    today = date.today()
    monthly_expenses = []
    monthly_labels = []
    for i in range(4, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)  # Approximate
        month_name = month_date.strftime('%b')
        monthly_labels.append(month_name)
        
        next_month = month_date.replace(day=28) + timedelta(days=4)  # Move to next month
        next_month = next_month.replace(day=1)  # First day of next month
        
        month_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.date >= month_date,
            Expense.date < next_month
        ).scalar() or 0
        
        monthly_expenses.append(round(month_expenses, 2))
    
    return render_template('index.html',
                          active_projects=active_projects,
                          total_projects=total_projects,
                          top_projects=top_projects,
                          recent_expenses=recent_expenses,
                          total_invoiced=total_invoiced,
                          unpaid_invoices=unpaid_invoices,
                          weekly_hours=weekly_hours,
                          project_status_counts=project_status_counts,
                          expenses_total=expenses_total,
                          monthly_expenses=monthly_expenses,
                          monthly_labels=monthly_labels,
                          total_net_profit=total_net_profit)

# --- Employee Routes ---
@app.route('/employees')
@login_required
def employees():
    all_employees = Employee.query.order_by(Employee.name).all()
    return render_template('employees.html', employees=all_employees)

@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        # Handle empty employee_id_str by setting it to None instead of empty string
        employee_id_str = form.employee_id_str.data if form.employee_id_str.data else None
        
        new_employee = Employee(
            name=form.name.data,
            employee_id_str=employee_id_str,
            contact_details=form.contact_details.data,
            pay_rate=form.pay_rate.data,
            payment_method_preference=PaymentMethod[form.payment_method_preference.data] if form.payment_method_preference.data else None,
            is_active=form.is_active.data,
            hire_date=form.hire_date.data
        )
        db.session.add(new_employee)
        db.session.commit()
        flash(f'Employee {new_employee.name} added successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', form=form, title="Add Employee")

@app.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = db.session.get(Employee, id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees')), 404
        
    form = EmployeeForm(obj=employee)
    # Ensure correct enum loading for SelectField
    if request.method == 'GET' and employee.payment_method_preference:
        form.payment_method_preference.data = employee.payment_method_preference.name

    if form.validate_on_submit():
        employee.name = form.name.data
        # Handle empty employee_id_str by setting it to None instead of empty string
        employee.employee_id_str = form.employee_id_str.data if form.employee_id_str.data else None
        employee.contact_details = form.contact_details.data
        employee.pay_rate = form.pay_rate.data
        employee.payment_method_preference = PaymentMethod[form.payment_method_preference.data] if form.payment_method_preference.data else None
        employee.is_active = form.is_active.data
        employee.hire_date = form.hire_date.data
        db.session.commit()
        flash(f'Employee {employee.name} updated successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', form=form, title="Edit Employee", employee=employee)

@app.route('/employee/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = db.session.get(Employee, id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('employees')), 404
        
    try:
        db.session.delete(employee)
        db.session.commit()
        flash(f'Employee {employee.name} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {e}. They might have associated records.', 'danger')
    return redirect(url_for('employees'))

# --- Project Routes ---
@app.route('/projects')
@login_required
def projects():
    all_projects = Project.query.order_by(Project.start_date.desc()).all()
    return render_template('projects.html', projects=all_projects)

@app.route('/project/add', methods=['GET', 'POST'])
@login_required
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        # Handle empty project_id_str by setting it to None instead of empty string
        project_id_str = form.project_id_str.data if form.project_id_str.data else None
        
        new_project = Project(
            name=form.name.data,
            project_id_str=project_id_str,
            client_name=form.client_name.data,
            location=form.location.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            contract_value=form.contract_value.data,
            description=form.description.data,
            status=ProjectStatus[form.status.data]
        )
        
        # Validate that end date is after start date if both are provided
        if not new_project.validate_dates() and form.start_date.data and form.end_date.data:
            flash('Error: End date must be on or after start date.', 'danger')
            return render_template('project_form.html', form=form, title="Add Project")
            
        db.session.add(new_project)
        db.session.commit()
        flash(f'Project {new_project.name} added successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Add Project")

@app.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    project = db.session.get(Project, id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects')), 404
    
    form = ProjectForm(obj=project)
    # Handle enum loading for SelectField
    if request.method == 'GET':
        form.status.data = project.status.name

    if form.validate_on_submit():
        project.name = form.name.data
        # Handle empty project_id_str by setting it to None instead of empty string
        project.project_id_str = form.project_id_str.data if form.project_id_str.data else None
        project.client_name = form.client_name.data
        project.location = form.location.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.contract_value = form.contract_value.data
        project.description = form.description.data
        project.status = ProjectStatus[form.status.data]  # Update status from form
        
        # Validate that end date is after start date if both are provided
        if not project.validate_dates() and form.start_date.data and form.end_date.data:
            flash('Error: End date must be on or after start date.', 'danger')
            return render_template('project_form.html', form=form, title="Edit Project", project=project)
            
        db.session.commit()
        flash(f'Project {project.name} updated successfully!', 'success')
        return redirect(url_for('projects'))
    return render_template('project_form.html', form=form, title="Edit Project", project=project)

@app.route('/project/view/<int:id>')
@login_required
def project_detail(id):
    project = db.session.get(Project, id)
    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects')), 404
        
    # Calculate costs (using properties defined in model)
    labor_cost = project.total_labor_cost
    material_cost = project.total_material_cost
    other_expenses = project.total_other_expenses
    total_cost = project.total_cost
    profit = project.profit

    # Fetch related items
    timesheets = Timesheet.query.filter_by(project_id=id).order_by(Timesheet.date.desc()).all()
    materials = Material.query.filter_by(project_id=id).order_by(Material.purchase_date.desc()).all()
    expenses = Expense.query.filter_by(project_id=id).order_by(Expense.date.desc()).all()
    invoices = Invoice.query.filter_by(project_id=id).order_by(Invoice.invoice_date.desc()).all()

    return render_template('project_detail.html',
                           project=project,
                           labor_cost=labor_cost,
                           material_cost=material_cost,
                           other_expenses=other_expenses,
                           total_cost=total_cost,
                           profit=profit,
                           timesheets=timesheets,
                           materials=materials,
                           expenses=expenses,
                           invoices=invoices)

# --- Timesheet Routes ---
@app.route('/timesheets')
@login_required
def timesheets():
    # Basic view - show all timesheets, maybe filter by week later
    page = request.args.get('page', 1, type=int)
    timesheet_list = Timesheet.query.join(Employee).join(Project)\
                        .order_by(Timesheet.date.desc(), Employee.name)\
                        .paginate(page=page, per_page=20)  # Add pagination
    return render_template('timesheets.html', timesheets=timesheet_list)

@app.route('/timesheet/add', methods=['GET', 'POST'])
@login_required
def add_timesheet():
    form = TimesheetForm()
    
    # Populate the employee and project choices
    form.employee_id.choices = [(emp.id, f"{emp.name} ({emp.employee_id_str or 'No ID'})") 
                               for emp in Employee.query.filter_by(is_active=True).order_by(Employee.name).all()]
    form.project_id.choices = [(proj.id, f"{proj.name} ({proj.project_id_str or 'No ID'})") 
                              for proj in Project.query.filter(Project.status.in_([ProjectStatus.PENDING, ProjectStatus.IN_PROGRESS]))
                              .order_by(Project.name).all()]
    
    if form.validate_on_submit():
        # Create new timesheet
        timesheet = Timesheet(
            employee_id=form.employee_id.data,
            project_id=form.project_id.data,
            date=form.date.data,
            entry_time=form.entry_time.data,
            exit_time=form.exit_time.data,
            lunch_duration_minutes=form.lunch_duration_minutes.data
        )
        
        # Validate the timesheet
        is_valid, message = timesheet.is_valid()
        if is_valid:
            db.session.add(timesheet)
            db.session.commit()
            
            # Get the names for the flash message
            employee = db.session.get(Employee, form.employee_id.data)
            project = db.session.get(Project, form.project_id.data)
            
            flash(f'Timesheet for {employee.name} on project {project.name} added successfully!', 'success')
            return redirect(url_for('timesheets'))
        else:
            flash(f'Error adding timesheet: {message}', 'danger')
    
    return render_template('timesheet_form.html', form=form, title="Add Timesheet Entry")

# --- Material Routes ---
@app.route('/materials')
@login_required
def materials():
    all_materials = Material.query.join(Project).order_by(Material.purchase_date.desc()).all()
    return render_template('materials.html', materials=all_materials)

@app.route('/material/add', methods=['GET', 'POST'])
@login_required
def add_material():
    form = MaterialForm()
    form.project_id.choices = [(p.id, p.name) for p in Project.query.order_by('name')]

    if form.validate_on_submit():
        new_material = Material(
            project_id=form.project_id.data,
            description=form.description.data,
            supplier=form.supplier.data,
            cost=form.cost.data,
            purchase_date=form.purchase_date.data,
            category=form.category.data
        )
        db.session.add(new_material)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('materials'))

    if not form.is_submitted():
        form.purchase_date.data = date.today()

    return render_template('material_form.html', form=form, title="Add Material")

# --- Expense Routes ---
@app.route('/expenses')
@login_required
def expenses():
    all_expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=all_expenses)

@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    # Add empty choice + projects
    form.project_id.choices = [('', '-- None --')] + [(p.id, p.name) for p in Project.query.order_by('name')]

    if form.validate_on_submit():
        new_expense = Expense(
            description=form.description.data,
            category=form.category.data,
            amount=form.amount.data,
            date=form.date.data,
            supplier_vendor=form.supplier_vendor.data,
            payment_method=PaymentMethod[form.payment_method.data] if form.payment_method.data else None,
            payment_status=PaymentStatus[form.payment_status.data],
            due_date=form.due_date.data,
            # Handle optional project link
            project_id=form.project_id.data if form.project_id.data else None
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))

    if not form.is_submitted():
        form.date.data = date.today()
        form.payment_status.data = PaymentStatus.PENDING.name  # Default status

    return render_template('expense_form.html', form=form, title="Add Expense")

# --- Payroll Routes ---
@app.route('/payroll/record-payment', methods=['GET', 'POST'])
@login_required
def record_payroll_payment():
    form = PayrollPaymentForm()
    # Populate employee choices
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    
    # Get deduction types for the template
    deduction_types = list(DeductionType)
    
    if form.validate_on_submit():
        # Create the payment with gross amount and initially set amount equal to gross_amount
        new_payment = PayrollPayment(
            employee_id=form.employee_id.data,
            pay_period_start=form.pay_period_start.data,
            pay_period_end=form.pay_period_end.data,
            gross_amount=form.gross_amount.data,
            amount=form.gross_amount.data,  # Initially set to gross amount, will be updated after deductions
            payment_date=form.payment_date.data,
            payment_method=PaymentMethod[form.payment_method.data],
            notes=form.notes.data,
            # Add check details
            check_number=form.check_number.data if form.payment_method.data == 'CHECK' else None,
            bank_name=form.bank_name.data if form.payment_method.data == 'CHECK' else None
        )
        
        # Validate that end date is after start date
        if not new_payment.validate_dates():
            flash('Error: Pay period end date must be on or after start date.', 'danger')
            return render_template('payroll_payment_form.html', form=form, deduction_types=deduction_types, title="Record Payroll Payment")
            
        # Validate check details if payment method is Check
        if form.payment_method.data == 'CHECK' and not new_payment.validate_check_details():
            flash('Error: Check number is required for check payments.', 'danger')
            return render_template('payroll_payment_form.html', form=form, deduction_types=deduction_types, title="Record Payroll Payment")
        
        # Add the payment first to get an ID
        db.session.add(new_payment)
        db.session.flush()
        
        # Process deductions if any
        if 'deduction_description[]' in request.form:
            descriptions = request.form.getlist('deduction_description[]')
            amounts = request.form.getlist('deduction_amount[]')
            types = request.form.getlist('deduction_type[]')
            notes = request.form.getlist('deduction_notes[]')
            
            for i in range(len(descriptions)):
                if descriptions[i] and amounts[i] and float(amounts[i]) > 0:
                    deduction = PayrollDeduction(
                        payroll_payment_id=new_payment.id,
                        description=descriptions[i],
                        amount=float(amounts[i]),
                        deduction_type=DeductionType[types[i]],
                        notes=notes[i] if i < len(notes) else None
                    )
                    db.session.add(deduction)
            
            # Update the net amount after all deductions are processed
            total_deductions = sum(float(amount) for amount in amounts if amount and float(amount) > 0)
            new_payment.amount = new_payment.gross_amount - total_deductions
        
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
        return redirect(url_for('payroll_report'))
    
    return render_template('payroll_payment_form.html', form=form, deduction_types=deduction_types, title="Record Payment")

@app.route('/payroll/report')
@login_required
def payroll_report():
    """Comprehensive report showing weekly hours and recorded payments with payment method breakdown"""
    target_date_str = request.args.get('date')
    target_date = date.today()
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Using today's date.", 'warning')

    start_of_week, end_of_week = get_week_start_end(target_date)

    # 1. Calculate hours worked per employee for the selected week
    employees = Employee.query.filter_by(is_active=True).all()
    weekly_hours_data = {}
    for emp in employees:
        timesheets_this_week = Timesheet.query.filter(
            Timesheet.employee_id == emp.id,
            Timesheet.date >= start_of_week,
            Timesheet.date <= end_of_week
        ).all()
        total_hours = sum(ts.calculated_hours for ts in timesheets_this_week)
        potential_pay = total_hours * emp.pay_rate
        weekly_hours_data[emp.id] = {
            'employee': emp,
            'total_hours': total_hours,
            'potential_pay': potential_pay,
            'timesheets': timesheets_this_week
        }

    # 2. Get recorded payments for that period (or overlapping)
    recorded_payments = PayrollPayment.query.filter(
        # Simple overlap check, might need refinement
        PayrollPayment.pay_period_end >= start_of_week,
        PayrollPayment.pay_period_start <= end_of_week
    ).order_by(PayrollPayment.payment_date.desc()).all()
    
    # Fetch deductions for each payment
    for payment in recorded_payments:
        # Load deductions for the payment
        payment.deductions = PayrollDeduction.query.filter_by(payroll_payment_id=payment.id).all()
        
        # We don't need to calculate total_deductions here as it's a property in the model
        # that will be calculated automatically when accessed

    # Add payment info to the weekly data
    for payment in recorded_payments:
        if payment.employee_id in weekly_hours_data:
             if 'payments' not in weekly_hours_data[payment.employee_id]:
                 weekly_hours_data[payment.employee_id]['payments'] = []
             weekly_hours_data[payment.employee_id]['payments'].append(payment)
    
    # 3. Calculate payment method totals for the report
    payment_method_totals = {
        'CASH': {
            'count': 0,
            'total': 0.0,
            'payments': []
        },
        'CHECK': {
            'count': 0,
            'total': 0.0,
            'payments': []
        }
    }
    
    # Add other payment methods as needed
    for payment in recorded_payments:
        if payment.payment_method == PaymentMethod.CASH:
            method = 'CASH'
        elif payment.payment_method == PaymentMethod.CHECK:
            method = 'CHECK'
        else:
            # Skip other payment methods for this specific report
            continue
            
        payment_method_totals[method]['count'] += 1
        payment_method_totals[method]['total'] += payment.gross_amount
        # Use the net_amount property from the model
        # Add net amount to the totals if not already there
        if 'total_after_deductions' not in payment_method_totals[method]:
            payment_method_totals[method]['total_after_deductions'] = 0
        payment_method_totals[method]['total_after_deductions'] += payment.net_amount
        payment_method_totals[method]['payments'].append(payment)
    
    # 4. Calculate total hours across all employees
    total_weekly_hours = sum(data['total_hours'] for data in weekly_hours_data.values())
    
    # Find previous and next week for navigation
    prev_week = target_date - timedelta(days=7)
    next_week = target_date + timedelta(days=7)
    
    return render_template('payroll_report.html', 
                          weekly_data=weekly_hours_data,
                          recorded_payments=recorded_payments,
                          payment_method_totals=payment_method_totals,
                          current_week_start=start_of_week,
                          current_week_end=end_of_week,
                          prev_week=prev_week,
                          next_week=next_week,
                          total_weekly_hours=total_weekly_hours)

# --- Invoice Routes (Basic CRUD) ---
@app.route('/invoices')
@login_required
def invoices():
    all_invoices = Invoice.query.join(Project).order_by(Invoice.invoice_date.desc()).all()
    return render_template('invoices.html', invoices=all_invoices)

@app.route('/invoice/add', methods=['GET', 'POST'])
@login_required
def add_invoice():
    form = InvoiceForm()
    # Populate project choices
    form.project_id.choices = [(p.id, p.name) for p in Project.query.filter(
        Project.status.in_([ProjectStatus.COMPLETED, ProjectStatus.INVOICED])
    ).order_by(Project.name).all()]
    
    if form.validate_on_submit():
        new_invoice = Invoice(
            project_id=form.project_id.data,
            invoice_number=form.invoice_number.data,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            amount=form.amount.data,
            status=PaymentStatus[form.status.data],
            payment_received_date=form.payment_received_date.data if form.status.data == PaymentStatus.PAID.name else None
        )
        
        # Validate that due date is after invoice date if provided
        if not new_invoice.validate_dates() and form.invoice_date.data and form.due_date.data:
            flash('Error: Due date must be on or after invoice date.', 'danger')
            return render_template('invoice_form.html', form=form, title="Add Invoice")
            
        # If status is PAID, need payment date
        if form.status.data == PaymentStatus.PAID.name and not form.payment_received_date.data:
            flash('Error: Payment received date is required when status is PAID.', 'danger')
            return render_template('invoice_form.html', form=form, title="Add Invoice")
        
        db.session.add(new_invoice)
        
        # Update project status if invoice is being created
        project = Project.query.get(form.project_id.data)
        if project.status == ProjectStatus.COMPLETED:
            project.status = ProjectStatus.INVOICED
        
        # Update project status if invoice is marked as paid
        if form.status.data == PaymentStatus.PAID.name:
            project.status = ProjectStatus.PAID
            
        db.session.commit()
        flash('Invoice added successfully!', 'success')
        return redirect(url_for('invoices'))
    
    return render_template('invoice_form.html', form=form, title="Add Invoice")

@app.route('/invoice/delete/<int:id>', methods=['POST'])
@login_required
def delete_invoice(id):
    invoice = db.session.get(Invoice, id)
    if not invoice:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('invoices')), 404
    
    try:
        db.session.delete(invoice)
        db.session.commit()
        flash(f'Invoice {invoice.invoice_number} deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {e}', 'danger')
    return redirect(url_for('invoices'))

# --- Accounts Payable Routes ---
@app.route('/accounts_payable')
@login_required
def accounts_payable():
    """List all accounts payable with filtering options."""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    vendor_filter = request.args.get('vendor', '')
    due_date_filter = request.args.get('due_date', 'all')  # all, overdue, thisweek, thismonth
    
    # Base query
    query = AccountsPayable.query
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter(AccountsPayable.status == status_filter)
    
    if category_filter != 'all':
        query = query.filter(AccountsPayable.category == category_filter)
    
    if vendor_filter:
        query = query.filter(AccountsPayable.vendor_name.ilike(f'%{vendor_filter}%'))
    
    if due_date_filter == 'overdue':
        query = query.filter(AccountsPayable.due_date < date.today(), 
                            AccountsPayable.status != PaymentStatus.PAID)
    elif due_date_filter == 'thisweek':
        today = date.today()
        end_of_week = today + timedelta(days=6-today.weekday())
        query = query.filter(AccountsPayable.due_date <= end_of_week, 
                            AccountsPayable.due_date >= today,
                            AccountsPayable.status != PaymentStatus.PAID)
    elif due_date_filter == 'thismonth':
        today = date.today()
        next_month = date(today.year + (today.month == 12), 
                          (today.month % 12) + 1, 
                          1)
        end_of_month = next_month - timedelta(days=1)
        query = query.filter(AccountsPayable.due_date <= end_of_month,
                            AccountsPayable.due_date >= today,
                            AccountsPayable.status != PaymentStatus.PAID)
    
    # Order by due date by default, with pending and overdue first
    payables = query.order_by(
        db.case({
            PaymentStatus.OVERDUE.name: 1,
            PaymentStatus.PENDING.name: 2,
            PaymentStatus.PARTIAL.name: 3,
            PaymentStatus.PAID.name: 4
        }, value=AccountsPayable.status),
        AccountsPayable.due_date
    ).all()
    
    # Get today's date
    today = date.today()
    
    # Get statistics for dashboard
    total_pending = sum(ap.amount for ap in payables if ap.status != PaymentStatus.PAID)
    overdue_count = sum(1 for ap in payables if ap.due_date < today and ap.status != PaymentStatus.PAID)
    due_this_week = sum(1 for ap in payables 
                       if ap.due_date <= today + timedelta(days=7) 
                       and ap.due_date >= today 
                       and ap.status != PaymentStatus.PAID)
    
    return render_template('accounts_payable.html', 
                          payables=payables,
                          status_filter=status_filter,
                          category_filter=category_filter,
                          vendor_filter=vendor_filter,
                          due_date_filter=due_date_filter,
                          statuses=PaymentStatus,
                          categories=ExpenseCategory,
                          total_pending=total_pending,
                          overdue_count=overdue_count,
                          due_this_week=due_this_week,
                          today=today,
                          timedelta=timedelta)

@app.route('/accounts_payable/add', methods=['GET', 'POST'])
@login_required
def add_accounts_payable():
    """Add a new accounts payable record."""
    form = AccountsPayableForm()
    
    # Populate project choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, f"{p.name} ({p.project_id_str})") for p in projects]
    
    if form.validate_on_submit():
        # Create new accounts payable object
        payable = AccountsPayable(
            vendor_name=form.vendor_name.data,
            description=form.description.data,
            amount=form.amount.data,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            payment_method=PaymentMethod[form.payment_method.data],
            category=ExpenseCategory[form.category.data],
            status=PaymentStatus[form.status.data],
            payment_date=form.payment_date.data,
            check_number=form.check_number.data,
            bank_name=form.bank_name.data,
            notes=form.notes.data,
            project_id=form.project_id.data if form.project_id.data and form.project_id.data != 0 else None
        )
        
        try:
            # Validate business rules
            payable.validate_dates()
            if payable.status == PaymentStatus.PAID:
                payable.validate_payment_details()
                
            # Save to database
            db.session.add(payable)
            db.session.commit()
            flash('Accounts payable record added successfully!', 'success')
            return redirect(url_for('accounts_payable'))
        except ValueError as e:
            flash(f'Error: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('accounts_payable_form.html', form=form, title="Add Accounts Payable")

@app.route('/accounts_payable/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_accounts_payable(id):
    """Edit an existing accounts payable record."""
    payable = AccountsPayable.query.get_or_404(id)
    form = AccountsPayableForm(obj=payable)
    
    # Populate project choices
    projects = Project.query.order_by(Project.name).all()
    form.project_id.choices = [(0, '-- No Project --')] + [(p.id, f"{p.name} ({p.project_id_str})") for p in projects]
    
    if request.method == 'GET':
        form.payment_method.data = payable.payment_method.name
        form.category.data = payable.category.name
        form.status.data = payable.status.name
        form.project_id.data = payable.project_id if payable.project_id else 0
    
    if form.validate_on_submit():
        # Update payable object
        payable.vendor_name = form.vendor_name.data
        payable.description = form.description.data
        payable.amount = form.amount.data
        payable.issue_date = form.issue_date.data
        payable.due_date = form.due_date.data
        payable.payment_method = PaymentMethod[form.payment_method.data]
        payable.category = ExpenseCategory[form.category.data]
        payable.status = PaymentStatus[form.status.data]
        payable.payment_date = form.payment_date.data
        payable.check_number = form.check_number.data
        payable.bank_name = form.bank_name.data
        payable.notes = form.notes.data
        payable.project_id = form.project_id.data if form.project_id.data and form.project_id.data != 0 else None
        
        try:
            # Validate business rules
            payable.validate_dates()
            if payable.status == PaymentStatus.PAID:
                payable.validate_payment_details()
                
            # Save to database
            db.session.commit()
            flash('Accounts payable record updated successfully!', 'success')
            return redirect(url_for('accounts_payable'))
        except ValueError as e:
            flash(f'Error: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('accounts_payable_form.html', form=form, payable=payable, title="Edit Accounts Payable")

@app.route('/accounts_payable/delete/<int:id>', methods=['POST'])
@login_required
def delete_accounts_payable(id):
    """Delete an accounts payable record."""
    payable = AccountsPayable.query.get_or_404(id)
    
    try:
        db.session.delete(payable)
        db.session.commit()
        flash('Accounts payable record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('accounts_payable'))

@app.route('/accounts_payable/mark_paid/<int:id>', methods=['POST'])
@login_required
def mark_accounts_payable_paid(id):
    """Quick action to mark an accounts payable record as paid."""
    payable = AccountsPayable.query.get_or_404(id)
    
    # Get form data
    payment_date = request.form.get('payment_date', date.today())
    payment_method = request.form.get('payment_method', PaymentMethod.CASH.name)
    check_number = request.form.get('check_number')
    bank_name = request.form.get('bank_name')
    
    # Convert payment_date if it's a string
    if isinstance(payment_date, str):
        try:
            payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        except ValueError:
            payment_date = date.today()
    
    # Update record
    payable.status = PaymentStatus.PAID
    payable.payment_date = payment_date
    payable.payment_method = PaymentMethod[payment_method]
    
    if payment_method == PaymentMethod.CHECK.name:
        payable.check_number = check_number
        payable.bank_name = bank_name
    
    try:
        # Validate payment details
        payable.validate_payment_details()
        
        # Save changes
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('accounts_payable'))

@app.route('/export/accounts_payable/<format>', methods=['GET'])
@login_required
def export_accounts_payable(format):
    """Export accounts payable data in various formats."""
    # Query all accounts payable records
    payables = AccountsPayable.query.order_by(AccountsPayable.due_date).all()
    
    # Prepare data for export
    data = [[
        'Vendor', 'Description', 'Amount', 'Issue Date', 'Due Date', 
        'Status', 'Category', 'Payment Method', 'Payment Date', 
        'Check Number', 'Bank Name', 'Project', 'Notes'
    ]]
    
    for p in payables:
        project_name = p.project.name if p.project else 'N/A'
        payment_date = p.payment_date.strftime('%Y-%m-%d') if p.payment_date else 'N/A'
        data.append([
            p.vendor_name,
            p.description,
            f"${p.amount:.2f}",
            p.issue_date.strftime('%Y-%m-%d'),
            p.due_date.strftime('%Y-%m-%d'),
            p.status.value,
            p.category.value,
            p.payment_method.value,
            payment_date,
            p.check_number or 'N/A',
            p.bank_name or 'N/A',
            project_name,
            p.notes or ''
        ])
    
    # Export to requested format
    if format == 'excel':
        return export_to_excel(data, 'accounts_payable')
    elif format == 'pdf':
        return export_to_pdf(data, 'Accounts Payable Report', 'accounts_payable_report')
    elif format == 'csv':
        return export_to_csv(data, 'accounts_payable')
    else:
        flash('Unsupported export format', 'danger')
        return redirect(url_for('accounts_payable'))

# --- Export Routes ---
@app.route('/export/projects/<format>')
@login_required
def export_projects(format):
    """Export projects to Excel, PDF, or CSV"""
    projects = Project.query.order_by(Project.start_date.desc()).all()
    
    projects_data = []
    for project in projects:
        projects_data.append({
            'Project ID': project.project_id_str or '',
            'Name': project.name,
            'Client': project.client_name or '',
            'Location': project.location or '',
            'Start Date': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
            'End Date': project.end_date.strftime('%Y-%m-%d') if project.end_date else '',
            'Status': project.status.value if project.status else '',
            'Contract Value': f"${project.contract_value:.2f}" if project.contract_value else '$0.00',
            'Labor Cost': f"${project.total_labor_cost:.2f}",
            'Material Cost': f"${project.total_material_cost:.2f}",
            'Other Expenses': f"${project.total_other_expenses:.2f}",
            'Total Cost': f"${project.total_cost:.2f}",
            'Profit': f"${project.profit:.2f}",
            'Profit Margin': f"{project.profit_margin:.2f}%"
        })
    
    if format == 'excel':
        return export_to_excel(projects_data, 'projects')
    elif format == 'pdf':
        return export_to_pdf(projects_data, 'Projects', 'projects.pdf')
    elif format == 'csv':
        return export_to_csv(projects_data, 'projects')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('projects'))

@app.route('/export/timesheets/<format>')
@login_required
def export_timesheets(format):
    """Export timesheets to Excel, PDF, or CSV"""
    timesheets = Timesheet.query.order_by(Timesheet.date.desc()).all()
    
    timesheets_data = []
    for timesheet in timesheets:
        employee = db.session.get(Employee, timesheet.employee_id)
        project = db.session.get(Project, timesheet.project_id)
        
        timesheets_data.append({
            'Date': timesheet.date.strftime('%Y-%m-%d'),
            'Employee': employee.name if employee else 'Unknown',
            'Project': project.name if project else 'Unknown',
            'Entry Time': timesheet.entry_time.strftime('%H:%M'),
            'Exit Time': timesheet.exit_time.strftime('%H:%M'),
            'Lunch (mins)': timesheet.lunch_duration_minutes or 0,
            'Raw Hours': f"{timesheet.raw_hours:.2f}",
            'Calculated Hours': f"{timesheet.calculated_hours:.2f}",
            'Labor Cost': f"${timesheet.calculated_hours * (employee.pay_rate if employee else 0):.2f}"
        })
    
    if format == 'excel':
        return export_to_excel(timesheets_data, 'timesheets')
    elif format == 'pdf':
        return export_to_pdf(timesheets_data, 'Timesheets', 'timesheets.pdf')
    elif format == 'csv':
        return export_to_csv(timesheets_data, 'timesheets')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('timesheets'))

@app.route('/export/expenses/<format>')
@login_required
def export_expenses(format):
    """Export expenses to Excel, PDF, or CSV"""
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    expenses_data = []
    for expense in expenses:
        project = db.session.get(Project, expense.project_id) if expense.project_id else None
        
        expenses_data.append({
            'Date': expense.date.strftime('%Y-%m-%d'),
            'Description': expense.description,
            'Category': expense.category or '',
            'Amount': f"${expense.amount:.2f}",
            'Supplier/Vendor': expense.supplier_vendor or '',
            'Project': project.name if project else 'N/A',
            'Payment Method': expense.payment_method.value if expense.payment_method else '',
            'Payment Status': expense.payment_status.value if expense.payment_status else ''
        })
    
    if format == 'excel':
        return export_to_excel(expenses_data, 'expenses')
    elif format == 'pdf':
        return export_to_pdf(expenses_data, 'Expenses', 'expenses.pdf')
    elif format == 'csv':
        return export_to_csv(expenses_data, 'expenses')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('expenses'))

@app.route('/export/payroll/<format>')
@login_required
def export_payroll(format):
    """Export payroll data to Excel, PDF, or CSV"""
    payroll_payments = PayrollPayment.query.order_by(PayrollPayment.payment_date.desc()).all()
    
    payroll_data = []
    for payment in payroll_payments:
        employee = db.session.get(Employee, payment.employee_id)
        
        check_info = ""
        if payment.payment_method == PaymentMethod.CHECK:
            check_info = f"Check #{payment.check_number}" if payment.check_number else "No check number"
            if payment.bank_name:
                check_info += f", {payment.bank_name}"
        
        payroll_data.append({
            'Employee': employee.name if employee else 'Unknown',
            'Pay Period Start': payment.pay_period_start.strftime('%Y-%m-%d'),
            'Pay Period End': payment.pay_period_end.strftime('%Y-%m-%d'),
            'Payment Date': payment.payment_date.strftime('%Y-%m-%d'),
            'Amount': f"${payment.amount:.2f}",
            'Payment Method': payment.payment_method.value,
            'Check Details': check_info,
            'Notes': payment.notes or ''
        })
    
    if format == 'excel':
        return export_to_excel(payroll_data, 'payroll')
    elif format == 'pdf':
        return export_to_pdf(payroll_data, 'Payroll', 'payroll.pdf')
    elif format == 'csv':
        return export_to_csv(payroll_data, 'payroll')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('payroll_report'))

# --- Future Enhancements Routes ---
@app.route('/future-enhancements')
@login_required
def future_enhancements():
    """Display future enhancement plans and suggestion form"""
    # Predefined enhancements based on documentation
    enhancements = [
        {
            'title': 'Role-Based Authentication',
            'description': 'Expand the existing authentication system to include role-based permissions for administrators, managers, and staff, allowing different access levels to various features.',
            'priority': 'High'
        },
        {
            'title': 'Multi-Factor Authentication',
            'description': 'Enhance security by implementing multi-factor authentication options such as email verification codes or authenticator apps.',
            'priority': 'Medium'
        },
        {
            'title': 'Enhanced Analytics Dashboard',
            'description': 'Expand the current dashboard with more interactive drill-down capabilities, data filtering options, and custom date range selections.',
            'priority': 'Medium'
        },
        {
            'title': 'Document Management',
            'description': 'Upload and store project-related documents such as contracts, designs, and client communications directly in the system.',
            'priority': 'Medium'
        },
        {
            'title': 'Client Portal',
            'description': 'Allow clients to view project status, approve work, and access invoices through a secure client portal.',
            'priority': 'Medium'
        },
        {
            'title': 'PDF Export',
            'description': 'Generate downloadable PDF reports, invoices, and timesheets for offline sharing and record-keeping.',
            'priority': 'Medium'
        },
        {
            'title': 'Email Notifications',
            'description': 'Send automatic updates for key events such as invoice due dates, project milestones, and payment confirmations.',
            'priority': 'Low'
        },
        {
            'title': 'Mobile Application',
            'description': 'Develop a companion app for field use, allowing employees to log time and materials directly from job sites.',
            'priority': 'High'
        },
        {
            'title': 'Inventory Management',
            'description': 'Track inventory levels and automate reordering to ensure materials are always available when needed.',
            'priority': 'Medium'
        },
        {
            'title': 'Integration with Accounting Software',
            'description': 'Connect with accounting and tax software to streamline financial reporting and tax preparation.',
            'priority': 'Medium'
        },
        {
            'title': 'Electronic Signatures',
            'description': 'Enable digital signing of documents for contracts, approvals, and other paperwork.',
            'priority': 'Low'
        },
        {
            'title': 'Password Reset Functionality',
            'description': 'Implement a self-service password reset feature that allows users to reset their passwords via email verification.',
            'priority': 'Medium'
        },
        {
            'title': 'User Profile Management',
            'description': 'Allow users to update their profile information and preferences, including password changes and notification settings.',
            'priority': 'Low'
        }
    ]
    
    # Form for suggesting new enhancements
    from forms import EnhancementSuggestionForm
    form = EnhancementSuggestionForm()
    
    return render_template('future_enhancements.html', enhancements=enhancements, form=form)

@app.route('/suggest-enhancement', methods=['POST'])
@login_required
def suggest_enhancement():
    """Handle enhancement suggestions"""
    from forms import EnhancementSuggestionForm
    form = EnhancementSuggestionForm()
    
    if form.validate_on_submit():
        # In a real implementation, you would save this to a database
        # For now, just show a success message
        flash(f'Thank you for your enhancement suggestion: "{form.title.data}". Our team will review it!', 'success')
        return redirect(url_for('future_enhancements'))
    
    # If form validation fails, return to the page with errors
    enhancements = []  # You would need to repopulate this
    flash('Please correct the errors in your submission.', 'danger')
    return render_template('future_enhancements.html', enhancements=enhancements, form=form)

# --- Create DB tables ---
@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    with app.app_context():
        db.create_all()
    print('Initialized the database.')

# --- Main execution ---
if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        
        # Create default user if it doesn't exist
        if not User.query.filter_by(username='patricia').first():
            default_user = User(username='patricia')
            default_user.set_password('Patri2025')
            db.session.add(default_user)
            db.session.commit()
            print('Created default user: patricia')
            
    app.run(debug=True, host='0.0.0.0', port=5004)  # Runs on localhost and network IP