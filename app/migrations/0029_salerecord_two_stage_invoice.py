# Generated manually for two-stage sale invoice flow

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0028_alter_expense_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='salerecord',
            name='is_finalized',
            field=models.BooleanField(default=False, verbose_name='نهایی‌شده (پرداخت ثبت و رسید فروشگاه چاپ شده)'),
        ),
        migrations.AddField(
            model_name='salerecord',
            name='finalized_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='تاریخ نهایی‌شدن'),
        ),
    ]
