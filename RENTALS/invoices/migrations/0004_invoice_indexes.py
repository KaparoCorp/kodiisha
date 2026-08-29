from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0003_invoice_created_at_invoice_updated_at'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['user', 'status', 'due_date'], name='invoice_user_status_due'),
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['unit', 'due_date'], name='invoice_unit_due'),
        ),
    ]
