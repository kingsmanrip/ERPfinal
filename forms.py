from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, DateField, SelectField, TextAreaField, SubmitField, TimeField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Optional, NumberRange, Email, ValidationError
from models import ProjectStatus, PaymentMethod, PaymentStatus
from datetime import date

# Custom validators
def validate_end_after_start(form, field):
    """Validate that end date is on or after start date."""
    if form.start_date.data and field.data and field.data < form.start_date.data:
        raise ValidationError('End date must be on or after start date.')

def validate_future_date(form, field):
    """Validate that a date is in the future (for due dates)."""
    if field.data and field.data < date.today():
        raise ValidationError('Date must be today or in the future.')

def validate_not_negative(form, field):
    """Validate that a numeric field is not negative."""
    if field.data is not None and field.data < 0:
        raise ValidationError('Value cannot be negative.')

# --- Form Definitions ---

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class EmployeeForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    employee_id_str = StringField('Employee ID (Optional)')
    contact_details = TextAreaField('Contact Details')
    pay_rate = FloatField('Pay Rate (per hour)', validators=[DataRequired(), NumberRange(min=0, message="Pay rate cannot be negative")])
    payment_method_preference = SelectField('Preferred Payment Method', choices=[(pm.name, pm.value) for pm in PaymentMethod if pm != PaymentMethod.OTHER], coerce=str, validators=[Optional()])
    is_active = BooleanField('Active Employee', default=True)
    hire_date = DateField('Hire Date', validators=[Optional()])
    submit = SubmitField('Save Employee')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    project_id_str = StringField('Project ID (Optional)')
    client_name = StringField('Client Name')
    location = StringField('Location')
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional(), validate_end_after_start])
    contract_value = FloatField('Contract Value ($)', validators=[Optional(), NumberRange(min=0, message="Contract value cannot be negative")])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[(ps.name, ps.value) for ps in ProjectStatus], default=ProjectStatus.PENDING.name, validators=[DataRequired()])
    submit = SubmitField('Save Project')

class TimesheetForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    entry_time = TimeField('Entry Time', validators=[DataRequired()], format='%H:%M')
    exit_time = TimeField('Exit Time', validators=[DataRequired()], format='%H:%M')
    lunch_duration_minutes = IntegerField('Lunch Break (minutes)', default=0, validators=[DataRequired(), NumberRange(min=0, message="Lunch duration cannot be negative")])
    submit = SubmitField('Save Timesheet Entry')
    
    def validate_exit_time(form, field):
        """Validate that exit time is after entry time."""
        if form.entry_time.data and field.data and field.data <= form.entry_time.data:
            # Allow overnight shifts (next day implied)
            # Just provide a warning that will be handled in the route
            pass

class MaterialForm(FlaskForm):
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    description = StringField('Material Description', validators=[DataRequired()])
    supplier = StringField('Supplier')
    cost = FloatField('Cost ($)', validators=[DataRequired(), NumberRange(min=0, message="Cost cannot be negative")])
    purchase_date = DateField('Purchase Date', validators=[DataRequired()], format='%Y-%m-%d')
    category = StringField('Category (e.g., Paint, Drywall)')
    submit = SubmitField('Save Material')

class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    category = StringField('Category (e.g., Rent, Fuel)', validators=[DataRequired()])
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0, message="Amount cannot be negative")])
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    supplier_vendor = StringField('Supplier/Vendor')
    payment_method = SelectField('Payment Method', choices=[('', '-- Select --')] + [(pm.name, pm.value) for pm in PaymentMethod], validators=[Optional()])
    payment_status = SelectField('Payment Status', choices=[(ps.name, ps.value) for ps in PaymentStatus], default=PaymentStatus.PENDING.name, validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[Optional()])
    project_id = SelectField('Link to Project (Optional)', coerce=lambda x: int(x) if x else None, validators=[Optional()])
    submit = SubmitField('Save Expense')
    
    def validate_due_date(form, field):
        """Validate that due date is not earlier than expense date."""
        if form.date.data and field.data and field.data < form.date.data:
            raise ValidationError('Due date should not be earlier than expense date.')

# Basic form for recording a payroll payment manually
class PayrollPaymentForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    pay_period_start = DateField('Pay Period Start', validators=[DataRequired()], format='%Y-%m-%d')
    pay_period_end = DateField('Pay Period End', validators=[DataRequired(), validate_end_after_start], format='%Y-%m-%d')
    amount = FloatField('Amount Paid ($)', validators=[DataRequired(), NumberRange(min=0, message="Amount cannot be negative")])
    payment_date = DateField('Payment Date', validators=[DataRequired()], format='%Y-%m-%d')
    payment_method = SelectField('Payment Method', choices=[(pm.name, pm.value) for pm in PaymentMethod if pm != PaymentMethod.OTHER], coerce=str, validators=[DataRequired()])
    notes = TextAreaField('Notes (e.g., adjustments)')
    submit = SubmitField('Record Payment')

# Basic form for creating/editing invoices
class InvoiceForm(FlaskForm):
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    invoice_number = StringField('Invoice Number')
    invoice_date = DateField('Invoice Date', validators=[DataRequired()], format='%Y-%m-%d')
    due_date = DateField('Due Date', validators=[Optional()], format='%Y-%m-%d')
    amount = FloatField('Invoice Amount ($)', validators=[DataRequired(), NumberRange(min=0, message="Amount cannot be negative")])
    status = SelectField('Status', choices=[(ps.name, ps.value) for ps in PaymentStatus], default=PaymentStatus.PENDING.name, validators=[DataRequired()])
    payment_received_date = DateField('Payment Received Date', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Save Invoice')
    
    def validate_due_date(form, field):
        """Validate that due date is not earlier than invoice date."""
        if form.invoice_date.data and field.data and field.data < form.invoice_date.data:
            raise ValidationError('Due date should not be earlier than invoice date.')
            
    def validate_payment_received_date(form, field):
        """Validate that payment received date is provided when status is PAID."""
        if form.status.data == PaymentStatus.PAID.name and not field.data:
            raise ValidationError('Payment received date is required when status is PAID.')

# Form for suggesting new enhancements
class EnhancementSuggestionForm(FlaskForm):
    title = StringField('Enhancement Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('Low', 'Low - Nice to have'),
        ('Medium', 'Medium - Important but not urgent'),
        ('High', 'High - Critical functionality')
    ], default='Medium', validators=[DataRequired()])
    submit = SubmitField('Submit Suggestion')