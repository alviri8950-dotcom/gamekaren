from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_purchaserecord_is_voided_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='serial_number',
            field=models.CharField(
                blank=True, db_index=True, default='', max_length=150,
                verbose_name='شماره سریال / بارکد',
            ),
        ),
    ]
