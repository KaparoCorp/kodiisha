from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('water_bills', '0004_waterbill_created_at_waterbill_updated_at_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='waterbill',
            index=models.Index(fields=['unit', 'due_date', 'status'], name='waterbill_unit_due_status'),
        ),
    ]
