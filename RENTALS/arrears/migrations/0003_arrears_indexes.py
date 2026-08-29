from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrears', '0002_arrears_updated_at'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='arrears',
            index=models.Index(fields=['user', 'status'], name='arrears_user_status'),
        ),
        migrations.AddIndex(
            model_name='arrears',
            index=models.Index(fields=['invoice', 'tenant'], name='arrears_invoice_tenant'),
        ),
    ]
