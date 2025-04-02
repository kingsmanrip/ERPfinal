from app import app, db
from models import (Employee, Project, Timesheet, Material, Expense, PayrollPayment, 
                   Invoice, ProjectStatus, PaymentMethod, PaymentStatus, User)
from datetime import date, timedelta, datetime, time
import random
from werkzeug.security import generate_password_hash
import string

def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def random_time(start_hour=7, end_hour=17):
    """Generate a random time between start_hour and end_hour"""
    hour = random.randint(start_hour, end_hour)
    minute = random.choice([0, 15, 30, 45])
    return time(hour, minute)

def random_string(length=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def generate_mock_data():
    """Generate mock data for the ERP system"""
    with app.app_context():
        # --- Create default user if not exists ---
        if not User.query.filter_by(username='patricia').first():
            user = User(username='patricia')
            user.set_password('Patri2025')
            db.session.add(user)
            db.session.commit()
            print("Default user created (username: patricia, password: Patri2025)")
        
        # --- Create Employees ---
        employee_names = [
            'John Smith', 'Maria Garcia', 'Robert Johnson', 'David Lee', 
            'Michael Williams', 'Sarah Brown', 'James Wilson', 'Jessica Martinez',
            'Carlos Rodriguez', 'Daniel Harris', 'Mark Davis', 'Lisa Anderson',
            'Kevin Thomas', 'Laura Taylor', 'Christopher Jackson'
        ]
        
        # Pay rates for different roles
        painter_rate = random.uniform(20.0, 25.0)  # Painters
        drywall_rate = random.uniform(22.0, 28.0)  # Drywallers
        lead_rate = random.uniform(30.0, 35.0)     # Lead workers
        apprentice_rate = random.uniform(15.0, 18.0)  # Apprentices
        
        # Clear existing data
        print("Clearing existing data...")
        PayrollPayment.query.delete()
        Timesheet.query.delete()
        Material.query.delete()
        Expense.query.delete()
        Invoice.query.delete()
        Employee.query.delete()
        Project.query.delete()
        db.session.commit()
        
        print("Adding employees...")
        employees = []
        for idx, name in enumerate(employee_names, 1):
            # Assign rates based on role pattern
            if idx <= 5:  # Painters
                pay_rate = round(painter_rate, 2)
                role = "Painter"
            elif idx <= 10:  # Drywallers
                pay_rate = round(drywall_rate, 2)
                role = "Drywaller"
            elif idx <= 12:  # Lead workers
                pay_rate = round(lead_rate, 2)
                role = "Lead"
            else:  # Apprentices
                pay_rate = round(apprentice_rate, 2)
                role = "Apprentice"
                
            # Create employee with role in contact details
            employee = Employee(
                name=name,
                employee_id_str=f'EMP{idx:03}',
                contact_details=f"Role: {role}\nPhone: (555) 123-{random.randint(1000, 9999)}\nEmail: {name.lower().replace(' ', '.')}@example.com",
                pay_rate=pay_rate,
                payment_method_preference=random.choice([PaymentMethod.CASH, PaymentMethod.CHECK]),
                is_active=random.random() > 0.1,  # 90% are active
                hire_date=random_date(date.today() - timedelta(days=730), date.today() - timedelta(days=30))
            )
            db.session.add(employee)
            employees.append(employee)
        
        db.session.commit()
        print(f"Added {len(employees)} employees")
        
        # --- Create Projects ---
        project_types = ['Interior Painting', 'Exterior Painting', 'Drywall Installation', 
                         'Drywall Repair', 'Texture Application', 'Full Renovation']
        client_names = ['Smith Family', 'Johnson Residence', 'Garcia Home', 'Williams Office', 
                         'Taylor Construction', 'Harris Properties', 'Martinez Building',
                         'ABC Company', 'XYZ Corporation', 'Main Street Apartments',
                         'Parkview Condos', 'Sunnyvale HOA', 'Greenfield Developments']
        locations = ['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm Blvd', 
                      '654 Cedar Ln', '987 Maple Dr', '147 Birch Path',
                      '258 Spruce Way', '369 Willow Circle', '741 Redwood Court']
        
        print("Adding projects...")
        projects = []
        # Create a mix of projects with different statuses
        for i in range(25):
            # Determine project type
            project_type = random.choice(project_types)
            
            # Set contract value based on project type
            if 'Interior Painting' in project_type:
                base_value = random.uniform(1500, 4000)
            elif 'Exterior Painting' in project_type:
                base_value = random.uniform(3000, 8000)
            elif 'Drywall Installation' in project_type:
                base_value = random.uniform(2500, 6000)
            elif 'Drywall Repair' in project_type:
                base_value = random.uniform(800, 2000)
            elif 'Texture Application' in project_type:
                base_value = random.uniform(1200, 3000)
            elif 'Full Renovation' in project_type:
                base_value = random.uniform(10000, 25000)
            else:
                base_value = random.uniform(1000, 5000)
                
            # Adjust by size factor (random multiplier)
            size_factor = random.uniform(0.8, 1.5)
            contract_value = round(base_value * size_factor, 2)
            
            # Determine status with weighted distribution
            status_weights = [
                (ProjectStatus.PENDING, 15),
                (ProjectStatus.IN_PROGRESS, 40),
                (ProjectStatus.COMPLETED, 20),
                (ProjectStatus.INVOICED, 15),
                (ProjectStatus.PAID, 8),
                (ProjectStatus.CANCELLED, 2)
            ]
            status = random.choices(
                [s[0] for s in status_weights],
                weights=[s[1] for s in status_weights]
            )[0]
            
            # Determine dates based on status
            today = date.today()
            if status == ProjectStatus.PENDING:
                # Future project
                start_date = random_date(today, today + timedelta(days=60))
                end_date = start_date + timedelta(days=random.randint(5, 30))
            elif status == ProjectStatus.IN_PROGRESS:
                # Ongoing project
                start_date = random_date(today - timedelta(days=30), today - timedelta(days=1))
                end_date = random_date(today + timedelta(days=1), today + timedelta(days=30))
            elif status in [ProjectStatus.COMPLETED, ProjectStatus.INVOICED, ProjectStatus.PAID]:
                # Past project
                end_date = random_date(today - timedelta(days=60), today - timedelta(days=1))
                start_date = end_date - timedelta(days=random.randint(5, 30))
            else:  # CANCELLED
                # Could be anytime
                start_date = random_date(today - timedelta(days=180), today - timedelta(days=30))
                end_date = start_date + timedelta(days=random.randint(5, 30))
            
            project = Project(
                name=f"{random.choice(client_names)} - {project_type}",
                project_id_str=f'PRJ{i+1:03}',
                client_name=random.choice(client_names),
                location=random.choice(locations),
                start_date=start_date,
                end_date=end_date,
                contract_value=contract_value,
                description=f"Scope: {project_type} project at {random.choice(locations)}. " + 
                             f"Approximately {random.randint(1, 5)} rooms or {random.randint(800, 3000)} square feet.",
                status=status
            )
            db.session.add(project)
            projects.append(project)
        
        db.session.commit()
        print(f"Added {len(projects)} projects")
        
        # --- Create Timesheets ---
        print("Adding timesheets...")
        timesheet_count = 0
        active_employees = [e for e in employees if e.is_active]
        
        # Generate timesheets for past 30 days
        for day_offset in range(30, 0, -1):
            entry_date = date.today() - timedelta(days=day_offset)
            
            # Skip weekends
            if entry_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
                
            # For each day, assign some employees to projects
            for project in [p for p in projects if p.status != ProjectStatus.CANCELLED]:
                # Only create timesheets for projects that were active on that date
                if (project.start_date and project.start_date > entry_date) or \
                   (project.end_date and project.end_date < entry_date):
                    continue
                    
                # Assign 2-4 employees to this project on this day
                project_employees = random.sample(active_employees, random.randint(2, min(4, len(active_employees))))
                
                for employee in project_employees:
                    # Standard 8-hour workday with variations
                    entry_time = random_time(7, 9)  # Start between 7am and 9am
                    
                    # Handle lunch variations to test the lunch break rules
                    lunch_options = [0, 20, 30, 45, 60, 75]
                    lunch_duration_minutes = random.choice(lunch_options)
                    
                    # Calculate exit time (around 8 hours plus lunch)
                    work_hours = random.uniform(7.5, 8.5)  # Slight variations in workday length
                    exit_hour = entry_time.hour + int(work_hours) + (lunch_duration_minutes // 60)
                    exit_minute = entry_time.minute + ((lunch_duration_minutes % 60) + int((work_hours % 1) * 60)) % 60
                    if exit_minute >= 60:
                        exit_hour += 1
                        exit_minute -= 60
                    exit_time = time(exit_hour % 24, exit_minute)
                    
                    timesheet = Timesheet(
                        employee_id=employee.id,
                        project_id=project.id,
                        date=entry_date,
                        entry_time=entry_time,
                        exit_time=exit_time,
                        lunch_duration_minutes=lunch_duration_minutes
                    )
                    db.session.add(timesheet)
                    timesheet_count += 1
        
        db.session.commit()
        print(f"Added {timesheet_count} timesheets")
        
        # --- Create Materials ---
        print("Adding materials...")
        material_count = 0
        material_categories = {
            'Paint': ['Interior Paint', 'Exterior Paint', 'Primer', 'Ceiling Paint', 'Trim Paint'],
            'Drywall': ['Drywall Sheets', 'Joint Compound', 'Tape', 'Corner Bead', 'Screws'],
            'Tools': ['Brushes', 'Rollers', 'Scrapers', 'Sanders', 'Sprayers'],
            'Supplies': ['Drop Cloths', 'Masking Tape', 'Plastic Sheeting', 'Sandpaper', 'Patching Compound']
        }
        
        suppliers = ['Home Depot', 'Lowe\'s', 'Sherwin Williams', 'Benjamin Moore', 
                     'True Value', 'Ace Hardware', 'PPG Paints', 'Kelly-Moore', 
                     'Dunn-Edwards', 'Construction Supply Co.']
        
        # Add materials to active and recently completed projects
        for project in projects:
            # Skip pending or cancelled projects
            if project.status in [ProjectStatus.PENDING, ProjectStatus.CANCELLED]:
                continue
                
            # Number of material entries varies by project size
            num_entries = int((project.contract_value / 1000) * random.uniform(0.8, 1.5))
            num_entries = max(3, min(20, num_entries))  # Between 3 and 20 entries
            
            for _ in range(num_entries):
                category = random.choice(list(material_categories.keys()))
                description = random.choice(material_categories[category])
                
                # Cost depends on category and random variation
                if category == 'Paint':
                    base_cost = random.uniform(30, 80)  # Paint per gallon
                elif category == 'Drywall':
                    base_cost = random.uniform(15, 40)  # Drywall materials
                elif category == 'Tools':
                    base_cost = random.uniform(20, 100)  # Tools
                else:  # Supplies
                    base_cost = random.uniform(10, 50)  # Misc supplies
                
                # Add quantity variation
                quantity = random.randint(1, 5)
                cost = round(base_cost * quantity, 2)
                
                # Purchase date is between project start and today (or project end if completed)
                purchase_end_date = project.end_date if project.status != ProjectStatus.IN_PROGRESS else date.today()
                purchase_date = random_date(project.start_date, purchase_end_date)
                
                material = Material(
                    project_id=project.id,
                    description=f"{description} ({quantity} units)",
                    supplier=random.choice(suppliers),
                    cost=cost,
                    purchase_date=purchase_date,
                    category=category
                )
                db.session.add(material)
                material_count += 1
        
        db.session.commit()
        print(f"Added {material_count} materials")
        
        # --- Create Expenses ---
        print("Adding expenses...")
        expense_count = 0
        expense_categories = ['Office Supplies', 'Vehicle Expenses', 'Tools and Equipment', 
                              'Insurance', 'Utilities', 'Rent', 'Marketing', 'Licenses/Permits',
                              'Training', 'Miscellaneous']
        expense_descriptions = {
            'Office Supplies': ['Printer Paper', 'Ink Cartridges', 'Pens and Markers', 'Folders', 'Business Cards'],
            'Vehicle Expenses': ['Fuel', 'Maintenance', 'Repairs', 'Insurance', 'Registration'],
            'Tools and Equipment': ['Equipment Rental', 'Tool Purchase', 'Equipment Repair', 'Power Tools', 'Ladders'],
            'Insurance': ['Liability Insurance', 'Workers Comp', 'Vehicle Insurance', 'Property Insurance'],
            'Utilities': ['Electricity', 'Water', 'Gas', 'Internet', 'Phone Service'],
            'Rent': ['Office Rent', 'Storage Rent', 'Workshop Rent'],
            'Marketing': ['Print Advertising', 'Online Ads', 'Signage', 'Website Costs', 'Business Cards'],
            'Licenses/Permits': ['Business License', 'Contractor License', 'Permit Fees', 'Certification Costs'],
            'Training': ['Workshop Fees', 'Online Courses', 'Safety Training', 'Certification Classes'],
            'Miscellaneous': ['Cleaning Supplies', 'Safety Equipment', 'Staff Meals', 'Bank Fees']
        }
        
        suppliers = ['Office Depot', 'Staples', 'Amazon', 'Shell', 'Chevron', 
                     'AT&T', 'Verizon', 'City of Cleveland', 'State of Ohio',
                     'Ryder Truck Rental', 'Enterprise', 'United Insurance']
        
        # Generate regular business expenses for past 90 days
        for day_offset in range(90, 0, -1):
            expense_date = date.today() - timedelta(days=day_offset)
            
            # Some days have expenses, some don't
            if random.random() < 0.4:  # 40% chance of expenses on any given day
                # 1-3 expenses per day with expenses
                for _ in range(random.randint(1, 3)):
                    category = random.choice(expense_categories)
                    description = random.choice(expense_descriptions[category])
                    
                    # Amount depends on category
                    if category in ['Rent', 'Insurance']:
                        amount = random.uniform(500, 2000)
                    elif category in ['Vehicle Expenses', 'Utilities']:
                        amount = random.uniform(100, 500)
                    elif category in ['Licenses/Permits', 'Marketing']:
                        amount = random.uniform(200, 800)
                    else:
                        amount = random.uniform(20, 200)
                    
                    # Always assign a project (since project_id appears to be non-nullable)
                    project_id = random.choice(projects).id
                    
                    # Setup payment info
                    payment_method = random.choice(list(PaymentMethod))
                    payment_status = random.choice(list(PaymentStatus))
                    
                    # Due date logic
                    if payment_status == PaymentStatus.PENDING:
                        due_date = expense_date + timedelta(days=random.randint(7, 30))
                    else:
                        due_date = None
                    
                    expense = Expense(
                        description=description,
                        category=category,
                        amount=round(amount, 2),
                        date=expense_date,
                        supplier_vendor=random.choice(suppliers),
                        project_id=project_id,
                        payment_method=payment_method,
                        payment_status=payment_status,
                        due_date=due_date
                    )
                    db.session.add(expense)
                    expense_count += 1
        
        db.session.commit()
        print(f"Added {expense_count} expenses")
        
        # --- Create PayrollPayments ---
        print("Adding payroll payments...")
        payment_count = 0
        
        # Generate bi-weekly payroll for past 90 days
        for period_end in range(90, 0, -14):  # Bi-weekly periods
            period_end_date = date.today() - timedelta(days=period_end)
            period_start_date = period_end_date - timedelta(days=13)  # 2-week period
            payment_date = period_end_date + timedelta(days=3)  # Pay 3 days after period ends
            
            # Make payments to employees
            for employee in active_employees:
                # Calculate timesheets for this employee in this period
                period_timesheets = Timesheet.query.filter(
                    Timesheet.employee_id == employee.id,
                    Timesheet.date >= period_start_date,
                    Timesheet.date <= period_end_date
                ).all()
                
                if not period_timesheets:
                    continue  # Skip if no hours worked
                    
                # Calculate total hours and amount
                total_hours = sum(ts.calculated_hours for ts in period_timesheets)
                amount = round(total_hours * employee.pay_rate, 2)
                
                # Some payments are cash, some are check
                if random.random() < 0.4:  # 40% cash, 60% check
                    payment_method = PaymentMethod.CASH
                    check_number = None
                    bank_name = None
                else:
                    payment_method = PaymentMethod.CHECK
                    check_number = f"{random.randint(1000, 9999)}"
                    bank_name = random.choice(["Chase", "Bank of America", "Wells Fargo", "Citi", "Local Credit Union"])
                
                payment = PayrollPayment(
                    employee_id=employee.id,
                    pay_period_start=period_start_date,
                    pay_period_end=period_end_date,
                    amount=amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    check_number=check_number,
                    bank_name=bank_name,
                    notes=f"Payment for period {period_start_date} to {period_end_date}. {total_hours:.2f} hours @ ${employee.pay_rate:.2f}/hr"
                )
                db.session.add(payment)
                payment_count += 1
        
        db.session.commit()
        print(f"Added {payment_count} payroll payments")
        
        # --- Create Invoices ---
        print("Adding invoices...")
        invoice_count = 0
        
        # Create invoices for completed, invoiced and paid projects
        for project in projects:
            if project.status in [ProjectStatus.COMPLETED, ProjectStatus.INVOICED, ProjectStatus.PAID]:
                # Invoice is created after project completion
                invoice_date = project.end_date + timedelta(days=random.randint(1, 7))
                due_date = invoice_date + timedelta(days=30)  # Net 30 terms
                
                # For paid invoices, add payment date
                if project.status == ProjectStatus.PAID:
                    payment_received_date = due_date - timedelta(days=random.randint(0, 25))  # Paid before due date
                    status = PaymentStatus.PAID
                elif project.status == ProjectStatus.INVOICED:
                    payment_received_date = None
                    # Some invoices are overdue
                    if due_date < date.today():
                        status = PaymentStatus.OVERDUE
                    else:
                        status = PaymentStatus.PENDING
                else:  # Completed but not officially invoiced
                    payment_received_date = None
                    status = None  # Will skip this invoice creation
                
                if status:  # Only create invoice if we have a status
                    # Sometimes invoice amount differs slightly from contract (change orders, etc)
                    amount = project.contract_value * random.uniform(0.95, 1.1)
                    
                    invoice = Invoice(
                        project_id=project.id,
                        invoice_number=f"INV-{random_string(6)}",
                        invoice_date=invoice_date,
                        due_date=due_date,
                        amount=round(amount, 2),
                        status=status,
                        payment_received_date=payment_received_date
                    )
                    db.session.add(invoice)
                    invoice_count += 1
        
        db.session.commit()
        print(f"Added {invoice_count} invoices")
        
        print("Mock data generation complete!")

if __name__ == '__main__':
    generate_mock_data()
