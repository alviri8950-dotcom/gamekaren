# Generated manually for SMS integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_merge_20260814_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='party',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='شماره تماس'),
        ),
        migrations.AddField(
            model_name='party',
            name='sms_notifications_enabled',
            field=models.BooleanField(default=False, verbose_name='ارسال پیامک برای تراکنش‌های این شخص'),
        ),
    ]
