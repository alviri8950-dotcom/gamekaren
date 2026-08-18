from django.db import migrations, models


def convert_rial_to_toman(apps, schema_editor):
    """داده‌های قدیمی که به ریال ذخیره شده بودن (قیمت خرید و هزینه‌ی تمام‌شده) رو به تومان تبدیل می‌کنه،
    چون از این به بعد همه‌جای سیستم قیمت‌ها یکدست تومان هستن."""
    PurchaseRecord = apps.get_model('app', 'PurchaseRecord')
    InventoryItem = apps.get_model('app', 'InventoryItem')
    SaleLineItem = apps.get_model('app', 'SaleLineItem')

    for p in PurchaseRecord.objects.all():
        p.unit_price = round(p.unit_price / 10)
        p.save(update_fields=['unit_price'])

    for item in InventoryItem.objects.all():
        item.unit_cost = round(item.unit_cost / 10)
        item.save(update_fields=['unit_cost'])

    for line in SaleLineItem.objects.all():
        if line.cost_amount:
            line.cost_amount = round(line.cost_amount / 10)
            line.save(update_fields=['cost_amount'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_expense_fifo_cost_tracking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaserecord',
            name='unit_price',
            field=models.PositiveBigIntegerField(default=0, verbose_name='قیمت واحد (تومان)'),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='unit_cost',
            field=models.PositiveBigIntegerField(default=0, verbose_name='قیمت خرید (تومان)'),
        ),
        migrations.RunPython(convert_rial_to_toman, noop),
    ]
