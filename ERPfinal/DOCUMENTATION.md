# Mauricio PDQ ERP System Documentation

## Overview

The Mauricio PDQ ERP System is a comprehensive Enterprise Resource Planning solution designed specifically for Mauricio PDQ Paint & Drywall. This web-based application helps streamline business operations by managing employees, projects, timesheets, materials, expenses, invoices, and payroll in a single integrated platform.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation and Setup](#installation-and-setup)
3. [Data Models](#data-models)
4. [Features and Modules](#features-and-modules)
5. [Application Workflows](#application-workflows)
6. [User Interface](#user-interface)
7. [Testing](#testing)
8. [Security Considerations](#security-considerations)
9. [System Administration](#system-administration)
10. [Troubleshooting](#troubleshooting)
11. [Future Enhancements](#future-enhancements)
12. [Technical Implementation Notes](#technical-implementation-notes)
13. [Recent Enhancements](#recent-enhancements)

## System Architecture

### Technology Stack

- **Backend**: Python 3.7+ with Flask Framework
- **Database**: SQLite via SQLAlchemy ORM
- **Frontend**: HTML/CSS with Bootstrap 5 for responsive design
- **Form Handling**: WTForms for form creation and validation
- **Testing**: pytest with flask-pytest extension
- **Additional Libraries**:
  - Flask-SQLAlchemy: Database ORM integration
  - Flask-WTF: Form handling with CSRF protection
  - Flask-Bootstrap: UI components and styling

### Directory Structure

```
mauricioERP/
│
├── app.py                 # Main application with routes and configuration
├── models.py              # Database models and relationships
├── forms.py               # Form definitions using WTForms
├── requirements.txt       # Python dependencies
├── README.md              # Basic project information
├── STRUCTURE.md           # Detailed structure documentation
├── DOCUMENTATION.md       # This comprehensive documentation file
│
├── instance/              # Database storage (created at runtime)
│   └── erp.db             # SQLite database file
│
├── templates/             # HTML templates
│   ├── layout.html        # Base template with navigation
│   ├── index.html         # Dashboard
│   ├── employees.html     # Employee listing
│   ├── employee_form.html # Add/edit employee
│   └── ... (other templates)
│
├── tests/                 # Test directory
│   ├── test_models.py     # Tests for data models
│   ├── test_forms.py      # Tests for form validation
│   ├── test_routes.py     # Tests for route functionality
│   ├── test_integration.py # Integration tests
│   ├── test_complex_scenarios.py # Tests for complex business flows
│   ├── test_edge_cases.py # Tests for boundary conditions
│   └── test_security_and_validation.py # Security and validation tests
```

## Installation and Setup

### Prerequisites

- Python 3.7 or higher
- Git (for cloning the repository)
- Windows, macOS, or Linux operating system

### Installation Steps

1. **Clone the repository**:
   ```
   git clone https://github.com/kingsmanrip/mauricioERP.git
   cd mauricioERP
   ```

2. **Create and activate a virtual environment**:
   ```
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   ```
   # Option 1 - Using the built-in command
   flask init-db

   # Option 2 - Using Python directly
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Run the application**:
   ```
   python app.py
   ```

6. **Run tests**:
   ```
   python -m pytest
   ```

## Data Models

### Model Relationships and Cascade Behavior

The database schema uses SQLAlchemy relationships with proper cascade behavior to ensure data integrity. Key relationship features include:

- **Foreign keys with ondelete='CASCADE'**: Ensures that when a parent record is deleted, all related child records are automatically deleted
- **Backref configuration**: Properly configured to avoid conflicts and circular references
- **Relationship indexes**: Added for performance optimization on common queries

### Core Models

#### Employee

- **Key fields**:
  - `id` (Primary Key)
  - `name`
  - `employee_id_str` (Unique identifier string)
  - `pay_rate`
  - `contact_details`
  - `hire_date`
  - `is_active` (Status flag)

- **Relationships**: 
  - One-to-many with Timesheet
  - One-to-many with PayrollPayment

- **Business logic**:
  - Validates employee status changes
  - Ensures active employees for timesheet entry

#### Project

- **Key fields**:
  - `id` (Primary Key)
  - `name`
  - `project_id_str` (Unique identifier string)
  - `client_name`
  - `location`
  - `start_date` and `end_date`
  - `contract_value`
  - `status` (Using ProjectStatus enum)

- **Relationships**:
  - One-to-many with Timesheet
  - One-to-many with Material
  - One-to-many with Expense
  - One-to-many with Invoice

- **Properties**:
  - `total_material_cost`: Calculated sum of all material costs
  - `total_labor_cost`: Calculated sum of timesheet hours multiplied by employee pay rates
  - `total_other_expenses`: Calculated sum of all expenses
  - `total_cost`: Sum of materials, labor, and expenses
  - `profit`: Contract value minus total cost (estimated profit)
  - `actual_revenue`: Calculated sum of all paid invoices
  - `actual_net_profit`: Actual revenue minus total cost (actual money made)

#### Timesheet

- **Key fields**:
  - `id` (Primary Key)
  - `employee_id` (Foreign Key with CASCADE)
  - `project_id` (Foreign Key with CASCADE)
  - `date`
  - `entry_time` and `exit_time`
  - `lunch_duration_minutes`: Lunch break duration

- **Properties**:
  - `raw_hours`: Calculated raw hours between entry and exit times
  - `calculated_hours`: Working hours after lunch break adjustments, with special handling for different lunch durations

- **Validation**:
  - Prevents timesheets for inactive employees
  - Ensures valid time entries

#### Material

- **Key fields**:
  - `id` (Primary Key)
  - `project_id` (Foreign Key with CASCADE)
  - `description`
  - `supplier`
  - `cost`
  - `purchase_date`
  - `category`

#### Expense

- **Key fields**:
  - `id` (Primary Key)
  - `description`
  - `category`
  - `amount`
  - `date`
  - `supplier_vendor`
  - `project_id` (Foreign Key with CASCADE, nullable)
  - `payment_method` (Using PaymentMethod enum)
  - `payment_status` (Using PaymentStatus enum)

#### PayrollPayment

- **Key fields**:
  - `id` (Primary Key)
  - `employee_id` (Foreign Key with CASCADE)
  - `payment_date`
  - `pay_period_start` and `pay_period_end`
  - `gross_amount` (Total amount before deductions)
  - `amount` (Net amount after deductions)
  - `payment_method` (Using PaymentMethod enum)
  - `notes`
  - `check_number` (For check payments)
  - `bank_name` (For check payments)

- **Properties**:
  - `total_deductions`: Calculated sum of all associated deduction amounts
  - `net_amount`: Calculated as gross_amount minus total_deductions

- **Relationships**:
  - One-to-many with PayrollDeduction

#### Invoice

- **Key fields**:
  - `id` (Primary Key)
  - `project_id` (Foreign Key with CASCADE)
  - `invoice_number` (Unique)
  - `date`
  - `due_date`
  - `amount`
  - `status` (Using PaymentStatus enum)
  - `paid_date`
  - `payment_method` (Using PaymentMethod enum)

## Features and Modules

### Dashboard

- Interactive visual analytics dashboard with key business metrics
- Financial summary cards including:
  - Total and active projects counter
  - Total invoiced amounts
  - Unpaid invoices tracking
  - Weekly hours logged by employees
- Project status distribution chart (doughnut chart with color-coded status visualization)
- Monthly expense trend visualization (line chart showing past 5 months of expense data)
- Top performing projects with color-coded profit margin indicators and visual progress bars
- Quick action buttons for common tasks
- Recent expenses overview with categorization

### Data Export Functionality

- Excel and PDF export options for key data types:
  - Invoices export with project details, amounts, and status
  - Projects export with detailed status, dates, and financial metrics
  - Timesheets export with employee hours, projects, and calculated totals
  - Expenses export with categorization, payment status, and project association
- Export buttons integrated into each list view for easy access
- Excel exports using pandas DataFrames for rich formatting and data handling
- PDF exports using FPDF with temporary file handling for reliable generation
- Proper attachment handling with appropriate MIME types for browser compatibility
- Automatic file naming for downloaded reports

### Employee Management

- Comprehensive employee information tracking
- Status management (active/inactive)
- Payroll rate tracking

### Project Management

- Full project lifecycle handling
- Status tracking (Pending → In Progress → Completed → Invoiced → Paid)
- Financial analysis with real-time cost and profit calculations

### Time Tracking

- Daily timesheet entry by employee and project
- Automatic calculation of hours with lunch break handling
- Special handling for overnight shifts

### Materials Management

- Record materials used in projects
- Track suppliers and costs
- Categorize materials for reporting

### Expense Tracking

- Record business expenses with or without project association
- Track payment methods and status
- Categorization for financial reporting

### Accounts Payable (Tested & Verified)

- Comprehensive management of vendor payments and bills
- Track payment due dates with automatic overdue status update
- Dashboard with overview of total pending amounts, overdue payments, and payments due this week
- Advanced filtering by payment status, category, vendor name, and due date periods
- Support for linking accounts payable records to specific projects
- Quick-action system for marking payments as paid with payment details capture
- Full payment history with date, method, check details (if applicable), and notes
- Export capabilities to Excel, PDF, and CSV formats
- Data validation to ensure business rules (e.g., due dates cannot be earlier than issue dates)
- Thoroughly tested with all CRUD operations verified
- Validation rules confirmed for dates and payment information
- Database schema properly updated and verified for production use

### Invoicing

- Generate invoices for completed projects
- Track payment status
- Record payment information

### Payroll Management

- Calculate payroll based on recorded timesheets
- Generate payroll reports with detailed breakdowns
- Record payments to employees with comprehensive deduction tracking
- Support for multiple deduction types (taxes, insurance, retirement, advances, etc.)
- Dynamic UI for adding/removing deductions with real-time calculations
- Detailed reporting showing both gross and net amounts
- Tooltips in reports to show deduction breakdowns
- Check payment tracking with check numbers and bank information

## Testing

### Test Framework

The application includes a comprehensive test suite using pytest with the following main components. As of April 2, 2025, all 51 automated tests are passing successfully with only some non-critical SQLAlchemy deprecation warnings:

1. **Unit Tests**:
   - Model validation tests
   - Form validation tests
   - Route functionality tests

2. **Integration Tests**:
   - Project workflow tests (from creation to completion)
   - Payroll workflow tests (from timesheet entry to payment with deductions)
   - Authentication tests to ensure proper access control

3. **Edge Case Tests**:
   - Time boundary tests
   - Date boundary tests
   - Data validation tests
   - Error handling tests

4. **Complex Scenario Tests**:
   - Complete project lifecycle
   - Multiple project resource allocation
   - Employee status change impacts
   - Project status changes
   - Payroll deduction calculations

5. **Security and Validation Tests**:
   - Input sanitization
   - Numeric input validation
   - Data consistency
   - Performance with large queries
   - Transaction integrity
   - Authentication validation

6. **Payroll Deductions and Cash Flow Tests**:
   - Payroll deduction calculation tests
   - Project labor cost with payroll tests
   - Comprehensive cash flow tests
   - Payroll net amount consistency tests

7. **Net Profit Tests**:
   - Actual revenue calculation tests
   - Actual net profit calculation tests

### Running Tests

To run the complete test suite:
```
python -m pytest
```

To run specific test categories:
```
python -m pytest tests/test_models.py  # Run only model tests
python -m pytest -v  # Run with verbose output
```

## Security Considerations

Current security features:
- User authentication with secure password hashing
- Session management for login state
- Route protection with login_required decorator
- CSRF protection via Flask-WTF
- Input validation and sanitization
- Business rule enforcement

Recommended additions for production:
- Role-based access control
- Multi-factor authentication
- Password reset functionality
- User account management
- HTTPS configuration
- Environment variables for sensitive information (especially SECRET_KEY)
- Regular database backups
- Session timeout settings
- Login attempt limiting

## Troubleshooting

### Common Issues

#### Authentication Issues
- If you forget the default password, you can change it by running a Python script in the application context
- Default credentials are username: `patricia` and password: `Patri2025`

#### Database Issues
- If database errors occur, check file permissions on the instance directory
- For a fresh start, delete the instance/erp.db file and reinitialize

#### Application Errors
- Check the Flask debug output for error messages
- Ensure all dependencies are installed correctly
- Verify that the database migrations are up to date

#### Form Submission Problems
- Ensure all required fields are properly filled
- Check validation rules in forms.py
- Enable debug mode for detailed error messages

## Future Enhancements

The following enhancements have been identified as priority items for future development:

### 1. Email Notifications System (HIGH PRIORITY)
- **Description**: Implement automated email notifications for critical business events
- **Key Features**:
  - Invoice due date reminders to clients and staff
  - Project deadline alerts and milestone notifications
  - Weekly summary reports of timesheet entries
  - Material inventory warnings when stock is low
  - Monthly financial summaries for management
- **Technical Approach**: Integrate Flask-Mail with scheduled tasks (using Celery or APScheduler)
- **Expected Benefits**: Proactive business management, improved cash flow, reduced missed deadlines

### 2. Dashboard Filters and Date Ranges (HIGH PRIORITY)
- **Description**: Enhance the analytics dashboard with filtering and date comparison capabilities
- **Key Features**:
  - Date range selection for all dashboard metrics and charts
  - Comparison views (year-over-year, month-over-month)
  - Filter by project, client, employee, or department
  - Save filter presets for commonly used views
- **Technical Approach**: Add JavaScript-based filtering with AJAX dashboard updates
- **Expected Benefits**: More granular business insights, better trend analysis, customized views for different roles

### 3. Client Portal (HIGH PRIORITY)
- **Description**: Create a limited-access portal for clients to view their project information
- **Key Features**:
  - Project status tracking and timeline visibility
  - Invoice viewing and online payment capabilities
  - Document sharing for project deliverables
  - Messaging system for client-team communication
- **Technical Approach**: Create separate client-focused Flask routes with client authentication
- **Expected Benefits**: Increased client satisfaction, reduced administrative overhead for status updates, faster payments

### 4. Data Import Functionality (HIGH PRIORITY)
- **Description**: Add bulk data import capabilities to complement existing export functionality
- **Key Features**:
  - CSV/Excel import for all major data types (projects, clients, expenses, etc.)
  - Data validation during import with error reporting
  - Template downloads for proper formatting
  - Scheduled imports for integration with other systems
- **Technical Approach**: Use pandas for data processing with format validation
- **Expected Benefits**: Faster data entry, reduced manual errors, easier integration with external systems

### Additional Future Enhancements

- Role-based access control
- Mobile optimization for field workers
- Integration with accounting software
- Advanced reporting and analytics
- Multi-factor authentication
- Quick search functionality across all data

## Technical Implementation Notes

### Dashboard Implementation
- Uses Chart.js for interactive data visualizations
- Implements responsive design with Bootstrap 5
- Calculates key metrics in Python code rather than in templates for better reliability
- Pre-processes data for visualizations on the server-side to optimize performance
- Uses appropriate text sizing classes (display-6) to ensure large numbers are displayed properly
- Ensures all financial figures fit within their containers without overflow issues

### UI Design Considerations

- **Numeric Display**: Large numbers (financial amounts, project counts, hours) use `display-6` class in dashboard and `h3` elements in reports to maintain proper layout regardless of value size
- **Responsive Breakpoints**: Layout adapts to different screen sizes with Bootstrap's grid system
- **Color Scheme**: Uses consistent Bootstrap color utilities (primary, success, warning, info) for information hierarchy
- **Card Components**: Cards are used as the primary UI component for displaying grouped information
- **Accessibility**: Maintains proper color contrast and text sizing for readability

### Export Functionality Implementation
- Uses pandas DataFrames for Excel file generation
  - Better handling of data formatting and column headers
  - Improved compatibility with various Excel versions
  - Support for custom column styling and formatting
- Implements PDF generation via FPDF
  - Uses temporary files for reliable PDF output
  - Handles different page orientations based on report complexity
  - Implements proper encoding for special characters
  - Ensures consistent formatting across different report types
- File serving uses appropriate MIME types for browser compatibility
- All export functionality is protected by the same authentication system

### Database Design
- The database schema is designed with normalization principles to minimize data redundancy and improve data integrity.
- Indexes are used on columns used in WHERE and JOIN clauses to improve query performance.
- Relationships between tables are established using foreign keys to maintain data consistency.
- The database is designed to support the application's functionality, including user authentication, project management, time tracking, and invoicing.

## Recent Enhancements

### Test Suite Improvements (April 2, 2025)

The test suite has been significantly improved to ensure system reliability:

- Fixed all failing tests in the Accounts Payable module
- Resolved authentication-related test issues across the entire test suite
- Fixed enum reference mismatches in test files (notably `PaymentMethod.BANK_TRANSFER` to `PaymentMethod.TRANSFER`)
- Improved test data handling for more reliable test execution
- Enhanced form testing to properly match application validation requirements
- Updated MIME type assertions for export functionality tests
- Improved test session handling to prevent transaction rollback errors
- Achieved 100% pass rate across all 51 automated tests

### SQLAlchemy 2.0 Compatibility Updates

All database access patterns have been modernized to align with SQLAlchemy 2.0 best practices:

```python
# Old approach (deprecated)
employee = Employee.query.get(id)
project = Project.query.get_or_404(id)

# New approach
employee = db.session.get(Employee, id)

# With proper error handling for not found items
project = db.session.get(Project, id)
if not project:
    flash('Project not found.', 'danger')
    return redirect(url_for('projects')), 404
```

This update:
- Eliminates deprecation warnings
- Prepares the codebase for future SQLAlchemy 2.0 migration
- Improves error handling patterns
- Provides more explicit database access code

### Comprehensive Payroll Deductions System

A complete payroll deductions system has been implemented with the following features:

1. **PayrollDeduction Model**:
   - Linked to PayrollPayment via foreign key relationship
   - Supports multiple deduction types (taxes, insurance, retirement, advances, etc.)
   - Tracks description, amount, and deduction type
   - Includes notes field for additional context

2. **Enhanced PayrollPayment Model**:
   - Added gross_amount field to track pre-deduction amount
   - Implemented property methods to calculate net amount after deductions
   - Added relationship to PayrollDeduction for easy access to deductions
   - Includes check_number and bank_name fields for check payments
   - Properly initializes amount field to prevent NOT NULL constraint errors
   - Implements read-only properties for total_deductions and net_amount

3. **Dynamic UI for Deduction Management**:
   - JavaScript-powered interface for adding/removing deductions
   - Real-time calculation of net amount as deductions are added
   - User-friendly form with validation
   - Supports multiple deduction types with dropdown selection

4. **Enhanced Payroll Reports**:
   - Display both gross and net amounts
   - Detailed breakdown of deductions
   - Tooltips to show deduction details
   - Safe handling of edge cases where no deductions exist
   - Proper handling of payment method totals

5. **Form Validation Improvements**:
   - Enhanced validate_end_after_start function to work with both start_date and pay_period_start field names
   - Improved error handling for date validation
   - Added validation for check payment details

6. **Bug Fixes**:
   - Fixed NOT NULL constraint errors in PayrollPayment model
   - Fixed issue with total_deductions property being treated as writable
   - Resolved UndefinedError in payroll reports when no payments exist for certain methods
   - Improved error handling throughout the payroll workflow

### UI Improvements

1. **Streamlined Dashboard**:
   - Removed the Quick Actions section for a cleaner interface
   - Improved layout to emphasize financial metrics and project performance

2. **Navigation Enhancements**:
   - Removed Future Enhancements link from navigation menu
   - Focused navigation on implemented functionality

3. **Improved Error Handling**:
   - Fixed BuildError related to non-existent routes
   - Added proper error handling for missing data
   - Improved user feedback for non-implemented features

4. **Invoice Page Improvements**:
   - Removed non-functional buttons and export options
   - Added clear indicators for features coming soon
   - Improved layout consistency

### Enhanced Export Capabilities

New comprehensive export functionality has been implemented, supporting three formats:

1. **Excel (.xlsx)**:
   - Formatted spreadsheets with all data
   - Uses pandas and openpyxl for generation
   - Preserves data types and formatting

2. **PDF**:
   - Printable reports with consistent layout
   - Includes title and proper column headers
   - Formatted for readability

3. **CSV**:
   - Simple, universal format for data exchange
   - Compatible with most data analysis tools
   - Useful for importing into other systems

The export system is built on reusable helper functions:

```python
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
```

Each data type (Projects, Timesheets, Expenses, etc.) has its own dedicated export route:

```python
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
    
    # Handle different format types
    if format == 'excel':
        return export_to_excel(timesheets_data, 'timesheets')
    elif format == 'pdf':
        return export_to_pdf(timesheets_data, 'Timesheets', 'timesheets.pdf')
    elif format == 'csv':
        return export_to_csv(timesheets_data, 'timesheets')
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('timesheets'))
```

The UI has been updated with dropdown menus for all export options:

```html
<div class="dropdown me-2">
    <button class="btn btn-outline-primary dropdown-toggle" type="button" id="exportDropdown" data-bs-toggle="dropdown" aria-expanded="false">
        Export
    </button>
    <ul class="dropdown-menu" aria-labelledby="exportDropdown">
        <li><a class="dropdown-item" href="{{ url_for('export_projects', format='excel') }}">Excel (.xlsx)</a></li>
        <li><a class="dropdown-item" href="{{ url_for('export_projects', format='pdf') }}">PDF</a></li>
        <li><a class="dropdown-item" href="{{ url_for('export_projects', format='csv') }}">CSV</a></li>
    </ul>
</div>
```

### Enhanced Timesheet Calculations

The Timesheet model has been updated to implement precise lunch break rules:

```python
@property
def calculated_hours(self):
    """Calculate the actual working hours after deducting lunch break.
    Rules:
    - Lunch breaks ≥ 60 minutes: Only deduct 30 minutes
    - Lunch breaks < 30 minutes: No deduction
    - Lunch breaks 30-59 minutes: Deduct actual time
    """
    if self.lunch_duration_minutes is None:
        return self.raw_hours
    
    # Apply lunch deduction rules
    if self.lunch_duration_minutes >= 60:
        # For lunch breaks 1 hour or longer, deduct only 30 minutes
        return self.raw_hours - 0.5
    elif self.lunch_duration_minutes < 30:
        # For lunch breaks less than 30 minutes, no deduction
        return self.raw_hours
    else:
        # For lunch breaks between 30-59 minutes, deduct the actual time
        return self.raw_hours - (self.lunch_duration_minutes / 60.0)
```

This enhancement ensures fair and accurate calculation of employee working hours.

### Improved Payment Method Tracking

The PayrollPayment model has been enhanced to track detailed payment information:

```python
# New fields in PayrollPayment model
check_number = db.Column(db.String(50))  # Track check numbers for CHECK payments
bank_name = db.Column(db.String(100))    # Track bank information for CHECK payments

def validate_check_details(self):
    """Validate that check payments have a check number."""
    if self.payment_method == PaymentMethod.CHECK:
        return self.check_number is not None and self.check_number.strip() != ''
    return True
```

These additions allow tracking:
- Check numbers for check payments
- Bank names for better financial record-keeping
- Validation to ensure check payments have associated check numbers

### Enhanced Payroll Reporting

The payroll report functionality has been improved to:

1. **Display Payment Method Breakdowns**:
   - Separate sections for Cash and Check payments
   - Summary cards showing total amounts per payment method

2. **Improved Visualization**:
   - Color-coded indicators (green for Cash, blue for Check)
   - Check numbers displayed for Check payments
   - Comprehensive payment status tracking

3. **UI Optimizations**:
   - Properly sized numeric displays for large dollar amounts
   - Consistent spacing and alignment for financial data
   - Mobile-responsive design for field technicians

### Mock Data Generation

A dedicated script (`generate_mock_data.py`) has been implemented to generate realistic test data, including:

- 15 employees with various pay rates and skills
- 25 projects with different statuses and contract values
- 344 timesheets with various lunch break durations
- 96 materials with costs and categories
- 72 expenses with different payment methods
- 24 payroll payments (both Cash and Check methods)
- 3 invoices in various states

This data is crucial for stress testing and validating the system's performance with realistic volumes.

### Database Schema Updates

Added script (`update_schema.py`) to upgrade existing databases with the new payment tracking fields:

```python
# Adding new columns to payroll_payment table
conn.execute(sa.text('ALTER TABLE payroll_payment ADD COLUMN check_number VARCHAR(50)'))
conn.execute(sa.text('ALTER TABLE payroll_payment ADD COLUMN bank_name VARCHAR(100)'))
```

### UI Improvements

Enhanced the display of large financial values throughout the application:

- Changed from `display-4` to `display-6` class for dashboard cards
- Replaced `h2` with `h3` elements for payment summary cards
- Added consistent margin and padding for financial data
