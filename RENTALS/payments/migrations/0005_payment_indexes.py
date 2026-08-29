from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_payment_updated_at'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', 'date'], name='payment_user_date'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['property', 'date'], name='payment_property_date'),
        ),
    ]
