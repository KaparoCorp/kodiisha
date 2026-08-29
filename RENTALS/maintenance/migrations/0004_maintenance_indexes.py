from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0003_maintenance_created_at_maintenance_updated_at'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='maintenance',
            index=models.Index(fields=['property', 'date'], name='maintenance_property_date'),
        ),
        migrations.AddIndex(
            model_name='maintenance',
            index=models.Index(fields=['property', 'status'], name='maintenance_property_status'),
        ),
    ]
