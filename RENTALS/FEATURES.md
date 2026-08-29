# Tenant Ledger & Arrears Management Features

## Overview
This implementation adds two key features to the PROPATIA property management system:

1. **Tenant Ledger View** - A comprehensive running balance statement for each tenant
2. **Overdue Invoice Management** - Automatic detection and marking of overdue invoices as arrears

---

## Feature 1: Tenant Ledger View

### Description
The Tenant Ledger provides a detailed, chronological view of all financial transactions (invoices and payments) for a specific tenant, with a running balance calculation.

### Access
- Navigate to **Tenants** > Select a tenant > Click **Ledger** button
- Or directly visit: `tenants/ledger/<tenant_id>/`

### What It Shows
- **Tenant Information**: Name, phone, unit, property, status
- **Summary Statistics**:
  - Total Invoiced
  - Total Paid
  - Current Balance (Due)
  - Overdue Invoice Count
  
- **Ledger Entries Table**:
  - Date (sorted chronologically)
  - Description (Invoice or Payment type)
  - Debit (Invoices - in KES)
  - Credit (Payments - in KES)
  - Running Balance
  - Status (Paid, Partially Paid, Unpaid, Claimed, Unclaimed)
  - Overdue Indicator (for past-due unpaid invoices)

### Features
- Color-coded status badges
- Highlights overdue invoices in red
- Print-friendly design (Print button included)
- Responsive table layout
- Distinguishes between invoice and payment types

### Model/View Details
**View File**: `tenants/views.py::tenant_ledger()`
**Template**: `tenants/templates/tenants/tenant_ledger.html`
**URL**: `tenants/urls.py` (route: `ledger/<int:pk>/`)

---

## Feature 2: Overdue Invoice Management

### Description
A Django management command that identifies invoices with due dates in the past and marks them as arrears in the system. This can be run manually or scheduled as a daily task.

### Management Command
```bash
python manage.py mark_overdue_invoices [options]
```

### Options
- `--days N`: Number of days in the past to consider as overdue (default: 0, meaning today)
- `--dry-run`: Preview changes without making updates to the database
- `--user ID`: Mark overdue invoices only for a specific user ID

### Examples
```bash
# Check all invoices due today or earlier
python manage.py mark_overdue_invoices

# Check invoices overdue by 7+ days
python manage.py mark_overdue_invoices --days 7

# Preview changes first
python manage.py mark_overdue_invoices --dry-run

# Only mark for user with ID 5
python manage.py mark_overdue_invoices --user 5
```

### Database Model: Arrears

**Fields**:
- `invoice` (FK) - Link to the Invoice
- `tenant` (FK) - Link to the Tenant
- `unit` (FK) - Link to the Unit
- `user` (FK) - User who owns the property
- `amount_due` (Decimal) - Amount remaining on the invoice
- `days_overdue` (Integer) - Days since due date
- `status` (CharField) - Choices: `pending`, `resolved`, `written_off`
- `date_marked` (DateTime) - When this record was created
- `date_resolved` (DateTime) - When marked as resolved (null initially)
- `notes` (TextField) - Optional notes about the arrears

**Key Features**:
- Unique constraint on `(invoice, tenant)` - prevents duplicate arrears records
- Ordered by most recent first
- `mark_resolved()` method to manually mark as resolved
- Admin interface with filtering and bulk actions

### Model/Command Details
**Model File**: `arrears/models.py::Arrears`
**Admin File**: `arrears/admin.py`
**Command File**: `invoices/management/commands/mark_overdue_invoices.py`
**Migration**: `arrears/migrations/0001_initial.py`

---

## Integration Points

### 1. Arrears Report View
The existing arrears report has been updated to use the new Arrears model instead of computing arrears on the fly.

**URL**: `/arrears/`
**Features**:
- Filter by property, unit, tenant, or status
- Display all arrears with days overdue and amount due
- Link directly to tenant ledger from each arrears record
- Summary of total arrears amount
- Print-friendly interface

### 2. Admin Interface
The Arrears model is registered in Django admin with:
- List display of key information
- Filtering by status, date, and user
- Search by tenant name or invoice number
- Bulk action to mark records as resolved
- Readonly fields for timestamps

### 3. Tenants List Update
An additional "Ledger" button has been added to each tenant's action column in the tenant list view.

---

## Usage Scenarios

### Scenario 1: Daily Arrears Check
Run the management command daily via cron or Celery:
```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/RENTALS && python manage.py mark_overdue_invoices
```

### Scenario 2: Manual Audit
A landlord can manually run the command to catch up on any missed arrears:
```bash
python manage.py mark_overdue_invoices --dry-run  # Preview
python manage.py mark_overdue_invoices            # Execute
```

### Scenario 3: Tenant Financial Review
A landlord reviews a tenant's complete payment history:
1. Navigate to Tenants list
2. Click "Ledger" for the desired tenant
3. Review all invoices and payments chronologically
4. See running balance to understand what's currently due

### Scenario 4: Arrears Collection
After marking overdue invoices:
1. Visit Arrears Report
2. Filter by status = "pending" or by high days overdue
3. See which tenants owe the most
4. Click "Ledger" to review their full history before collection

---

## Technical Architecture

### Data Flow for Arrears
1. **Invoice Created** → `due_date` set
2. **Due Date Passes** → Invoice status remains `Unpaid` or `Partially Paid`
3. **Management Command Runs** → Creates `Arrears` record with calculated `days_overdue`
4. **Arrears Marked** → Record stored in database (searchable, filterable)
5. **Collection Action** → Arrears status updated to `resolved` or `written_off`

### Data Flow for Tenant Ledger
1. **Query All Invoices** → For the tenant, sorted by `due_date`
2. **Query All Payments** → For the tenant, sorted by `date`
3. **Merge & Sort** → Combine both, sort by date chronologically
4. **Calculate Running Balance** → Loop through sorted entries:
   - Add invoice amounts (debit)
   - Subtract payment amounts (credit)
   - Running balance = cumulative total
5. **Render Template** → Display formatted ledger with color coding

---

## Database Schema

### Arrears Table
```
arrears_arrears
├── id (PK)
├── user_id (FK → auth_user)
├── invoice_id (FK → invoices_invoice)
├── tenant_id (FK → tenants_tenant)
├── unit_id (FK → units_unit)
├── amount_due (Decimal(12,2))
├── days_overdue (Integer)
├── status (CharField: pending/resolved/written_off)
├── date_marked (DateTime)
├── date_resolved (DateTime, nullable)
├── notes (TextField, nullable)
└── UNIQUE(invoice_id, tenant_id)
```

---

## Files Modified/Created

### New Files
- `arrears/models.py` - Arrears model definition
- `arrears/migrations/0001_initial.py` - Database migration
- `arrears/templates/arrears/arrears_report.html` - Arrears report template
- `tenants/templates/tenants/tenant_ledger.html` - Ledger template
- `invoices/management/commands/mark_overdue_invoices.py` - Management command
- `invoices/management/__init__.py` - Package initialization
- `invoices/management/commands/__init__.py` - Package initialization

### Modified Files
- `arrears/views.py` - Updated to use Arrears model
- `arrears/admin.py` - Registered Arrears in admin
- `arrears/urls.py` - Already had the route
- `tenants/views.py` - Added tenant_ledger view
- `tenants/urls.py` - Added ledger URL route
- `tenants/templates/tenants/tenants_view.html` - Added ledger button to actions

---

## Testing & Verification

### Run Django Checks
```bash
python manage.py check
# Output: System check identified no issues (0 silenced).
```

### Test Management Command
```bash
# Dry run to see what would be marked
python manage.py mark_overdue_invoices --dry-run

# Execute the command
python manage.py mark_overdue_invoices

# Verify records created
python manage.py shell
>>> from arrears.models import Arrears
>>> Arrears.objects.count()
# Should show the number of arrears records created
```

### Test Tenant Ledger
1. Visit: `/tenants/ledger/1/`
2. Verify tenant information displays
3. Check ledger entries are chronologically sorted
4. Verify running balance calculations
5. Test print functionality

### Test Arrears Report
1. Visit: `/arrears/`
2. Verify all arrears records display
3. Test filters (property, unit, tenant, status)
4. Click "Ledger" links to tenant ledger
5. Verify total arrears amount calculation

---

## Future Enhancements

1. **Email Notifications**: Send arrears notifications to landlords/tenants
2. **Batch Payments**: Improved interface to attach multiple payments at once
3. **Payment Plans**: Track structured payment arrangements for overdue amounts
4. **Automated Reminders**: Send SMS/email reminders to tenants with overdue invoices
5. **Compliance Reports**: Generate reports for accounting/audit purposes
6. **Partial Payment Tracking**: Better visualization of partial payment allocation
7. **Late Fees**: Automatic calculation of late fees on overdue amounts

---

## Support & Troubleshooting

### Command doesn't run
- Ensure you're in the project directory
- Use the full path to Python in the virtual environment
- Check that `invoices` app is in `INSTALLED_APPS`

### Arrears not appearing
- Run: `python manage.py mark_overdue_invoices` to create records
- Check that invoices have `due_date` ≤ today and `status` in ['Unpaid', 'Partially Paid']

### Ledger shows incorrect balance
- Verify all invoices and payments are in the database
- Check that invoice amounts and payment amounts are correctly entered
- Ensure payments are not duplicated in database

### Admin interface errors
- Run: `python manage.py migrate` to ensure all migrations are applied
- Clear browser cache if old UI appears

---

**Created**: May 13, 2026
**Status**: Implemented and Tested
**Database**: SQLite (db.sqlite3)
**Django Version**: 6.0.2
