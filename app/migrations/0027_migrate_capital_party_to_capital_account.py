from django.db import migrations


CAPITAL_SUPPLIER_NAME = "موجودی اولیه"


def _normalize_fa(text):
    return (text or '').strip().replace('ي', 'ی').replace('ك', 'ک')


def migrate_forward(apps, schema_editor):
    """مانده‌ی حساب شخص/تأمین‌کننده‌ی «موجودی اولیه» (اگر وجود داشته باشه) رو به حساب مخفی
    «سرمایه» منتقل می‌کنه. هیچ رکوردی حذف نمی‌شه؛ فقط مانده‌ی Party صفر می‌شه و یک
    PartyLedgerEntry برای شفافیت تاریخچه ثبت می‌شه، و همون مبلغ به BankAccount سرمایه اضافه می‌شه."""
    Party = apps.get_model('app', 'Party')
    PartyLedgerEntry = apps.get_model('app', 'PartyLedgerEntry')
    BankAccount = apps.get_model('app', 'BankAccount')

    parties = Party.objects.all()
    target = None
    for p in parties:
        if _normalize_fa(p.name) == CAPITAL_SUPPLIER_NAME:
            target = p
            break

    if not target or target.balance == 0:
        return

    capital_account, _ = BankAccount.objects.get_or_create(
        label='سرمایه', defaults={'is_active': False, 'order': 9999, 'balance': 0}
    )

    # موجودی اولیه به‌صورت تأمین‌کننده معمولاً بستانکار (balance منفی) ثبت می‌شه —
    # یعنی همون مبلغی که باید به سرمایه اضافه بشه، مقدار مثبتِ قدرمطلق مانده است.
    amount_to_move = abs(target.balance)

    capital_account.balance += amount_to_move
    capital_account.save()

    PartyLedgerEntry.objects.create(
        party=target,
        amount=-target.balance,
        balance_after=0,
        description='انتقال مانده به حساب سرمایه (اصلاح دسته‌بندی گزارش‌ها)',
    )
    target.balance = 0
    target.save()


def migrate_backward(apps, schema_editor):
    """برگردوندن مبلغ از حساب سرمایه به همون Party — فقط برای امکان reverse کردن migration."""
    Party = apps.get_model('app', 'Party')
    PartyLedgerEntry = apps.get_model('app', 'PartyLedgerEntry')
    BankAccount = apps.get_model('app', 'BankAccount')

    capital_account = BankAccount.objects.filter(label='سرمایه').first()
    if not capital_account or capital_account.balance == 0:
        return

    target = None
    for p in Party.objects.all():
        if _normalize_fa(p.name) == CAPITAL_SUPPLIER_NAME:
            target = p
            break
    if not target:
        return

    amount = capital_account.balance
    capital_account.balance = 0
    capital_account.save()

    target.balance -= amount
    target.save()
    PartyLedgerEntry.objects.create(
        party=target,
        amount=-amount,
        balance_after=target.balance,
        description='بازگردانی مانده از حساب سرمایه (reverse migration)',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0026_fix_serial_generator_id_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
