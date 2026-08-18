import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def backfill_fifo_remaining(apps, schema_editor):
    """برای خریدهای فله‌ی قبلی (بدون سریال)، مانده‌ی FIFO رو بر اساس موجودی فعلی انبار حدس منطقی می‌زنه:
    فرض می‌کنیم قدیمی‌ترین خریدها اول فروخته شده‌اند (دقیقاً همون قانون FIFO رو به‌عقب اعمال می‌کنیم)."""
    PurchaseRecord = apps.get_model('app', 'PurchaseRecord')
    StockLevel = apps.get_model('app', 'StockLevel')

    groups = PurchaseRecord.objects.filter(
        serial_number='', is_voided=False
    ).values_list('device_name_id', 'device_type_id', 'accessory_id').distinct()

    for device_name_id, device_type_id, accessory_id in groups:
        lots = list(PurchaseRecord.objects.filter(
            device_name_id=device_name_id, device_type_id=device_type_id, accessory_id=accessory_id,
            serial_number='', is_voided=False
        ).order_by('created_at'))
        if not lots:
            continue
        stock = StockLevel.objects.filter(
            device_name_id=device_name_id, device_type_id=device_type_id, accessory_id=accessory_id
        ).first()
        current_stock = stock.quantity if stock else 0
        total_purchased = sum(l.quantity for l in lots)
        already_sold = max(0, total_purchased - current_stock)

        for lot in lots:
            consume = min(lot.quantity, already_sold)
            lot.remaining_quantity = lot.quantity - consume
            already_sold -= consume
            lot.save(update_fields=['remaining_quantity'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_gameinstallorder_customer_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaserecord',
            name='remaining_quantity',
            field=models.PositiveIntegerField(default=0, verbose_name='مانده برای FIFO (فقط کالای فله)'),
        ),
        migrations.AddField(
            model_name='salelineitem',
            name='cost_amount',
            field=models.BigIntegerField(default=0, verbose_name='هزینه تمام‌شده (سریال‌محور یا FIFO)'),
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=100, verbose_name='عنوان هزینه')),
                ('subcategory', models.CharField(blank=True, default='', max_length=100, verbose_name='زیرعنوان (مثلاً نوع قبض)')),
                ('salary_month', models.CharField(blank=True, default='', max_length=50, verbose_name='ماه حقوق (شمسی)')),
                ('amount', models.BigIntegerField(verbose_name='مبلغ (تومان)')),
                ('note', models.CharField(blank=True, default='', max_length=255, verbose_name='توضیحات')),
                ('payment_method', models.CharField(choices=[('bank', 'بانک'), ('party', 'حساب اشخاص (بستانکار)')], max_length=10, verbose_name='محل پرداخت')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='تاریخ و ساعت ثبت')),
                ('is_voided', models.BooleanField(default=False, verbose_name='ابطال\u200cشده')),
                ('voided_at', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ ابطال')),
                ('bank_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expenses', to='app.bankaccount', verbose_name='حساب بانکی')),
                ('party', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expenses', to='app.party', verbose_name='شخص (بستانکار)')),
                ('personnel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salary_expenses', to='app.personnel', verbose_name='پرسنل (برای حقوق)')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expenses_created', to='app.personnel', verbose_name='ثبت\u200cکننده')),
            ],
            options={
                'verbose_name': 'هزینه',
                'verbose_name_plural': 'هزینه\u200cها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(backfill_fifo_remaining, noop),
    ]
