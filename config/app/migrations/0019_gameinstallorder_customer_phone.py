from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_gameinstallorder_installer_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameinstallorder',
            name='customer_phone',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='شماره تماس مشتری'),
        ),
    ]
