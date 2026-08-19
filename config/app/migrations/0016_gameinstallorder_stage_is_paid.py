from django.db import migrations, models


def backfill_stage(apps, schema_editor):
    """سفارش‌های قبلی (که قبل از این تغییر ثبت شدن) رو بر اساس فیلدهای موجودشون به مرحله‌ی درست منتقل می‌کنه."""
    GameInstallOrder = apps.get_model('app', 'GameInstallOrder')
    GameInstallOrder.objects.filter(delivered=True).update(stage='delivered')
    GameInstallOrder.objects.filter(delivered=False, return_at__isnull=False).update(stage='returned')
    GameInstallOrder.objects.filter(delivered=False, return_at__isnull=True, installer__isnull=False).update(stage='sent_to_installer')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_alter_inventoryitem_serial_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameinstallorder',
            name='stage',
            field=models.CharField(
                choices=[
                    ('ordered', '۱. سفارش مشتری'),
                    ('sent_to_installer', '۲. ارسال برای نصاب'),
                    ('returned', '۳. بازگشت از نصب'),
                    ('delivered', '۴. تحویل مشتری'),
                ],
                default='ordered', max_length=20, verbose_name='مرحله',
            ),
        ),
        migrations.AddField(
            model_name='gameinstallorder',
            name='is_paid',
            field=models.BooleanField(default=False, verbose_name='پرداخت شده'),
        ),
        migrations.RunPython(backfill_stage, noop),
    ]
