from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_tenant_id_card_tenant_kra_pin'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tenant',
            old_name='id_card',
            new_name='id_card_front',
        ),
        migrations.AlterField(
            model_name='tenant',
            name='id_card_front',
            field=models.FileField(blank=True, null=True, upload_to='tenant_documents/id_cards/front/'),
        ),
        migrations.AddField(
            model_name='tenant',
            name='id_card_back',
            field=models.FileField(blank=True, null=True, upload_to='tenant_documents/id_cards/back/'),
        ),
        migrations.AlterField(
            model_name='tenant',
            name='kra_pin',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
