from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arrears', '0004_remove_arrears_arrears_user_status_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='arrears',
            index=models.Index(fields=['user', 'status'], name='arrears_user_status'),
        ),
        migrations.AddIndex(
            model_name='arrears',
            index=models.Index(fields=['date_marked'], name='arrears_date_marked'),
        ),
    ]
