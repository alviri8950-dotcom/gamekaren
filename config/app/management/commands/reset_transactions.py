from django.core.management.base import BaseCommand
from django.db import transaction, connection

from app.models import (
    PurchaseRecord, InventoryItem, SaleRecord, SaleLineItem, Payment,
    GameInstallOrder, Expense, Party, PartyLedgerEntry, StockLevel, BankAccount,
)

# جدول‌هایی که پاک می‌شن (فقط اطلاعات معاملاتی) — کاتالوگ/تنظیمات (بازی‌ها، دستگاه‌ها، پرسنل، تأمین‌کننده، نصاب، خود حساب‌های بانکی) دست نمی‌خوره
WIPED_TABLES = [
    'app_payment', 'app_salelineitem', 'app_salerecord',
    'app_inventoryitem', 'app_purchaserecord', 'app_stocklevel',
    'app_gameinstallorder', 'app_expense',
    'app_partyledgerentry', 'app_party',
]


class Command(BaseCommand):
    help = "کل اطلاعات معاملاتی (خرید، فروش، نصب بازی، هزینه، حساب اشخاص، موجودی) رو پاک می‌کنه. کاتالوگ/تنظیمات دست نمی‌خوره."

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='بدون تأیید دستی اجرا کن')

    def handle(self, *args, **options):
        counts = {
            'خریدها': PurchaseRecord.objects.count(),
            'واحدهای انبار (سریال‌دار)': InventoryItem.objects.count(),
            'موجودی فله‌ای': StockLevel.objects.count(),
            'فاکتورهای فروش': SaleRecord.objects.count(),
            'سفارش‌های نصب بازی': GameInstallOrder.objects.count(),
            'هزینه‌ها': Expense.objects.count(),
            'اشخاص (حساب)': Party.objects.count(),
        }
        self.stdout.write(self.style.WARNING("این موارد برای همیشه پاک می‌شن:"))
        for label, count in counts.items():
            self.stdout.write(f"  - {label}: {count}")
        self.stdout.write(self.style.WARNING("کاتالوگ/تنظیمات (بازی‌ها، دستگاه‌ها، پرسنل، تأمین‌کننده، نصاب، لیست بانک‌ها) دست نمی‌خوره — فقط موجودی بانک‌ها صفر می‌شه."))

        if not options['yes']:
            answer = input("\nمطمئنی؟ این کار غیرقابل‌برگشته. برای ادامه بنویس «بله»: ")
            if answer.strip() != 'بله':
                self.stdout.write(self.style.ERROR("لغو شد — چیزی پاک نشد."))
                return

        with transaction.atomic():
            Payment.objects.all().delete()
            SaleLineItem.objects.all().delete()
            SaleRecord.objects.all().delete()
            InventoryItem.objects.all().delete()
            PurchaseRecord.objects.all().delete()
            StockLevel.objects.all().delete()
            GameInstallOrder.objects.all().delete()
            Expense.objects.all().delete()
            PartyLedgerEntry.objects.all().delete()
            Party.objects.all().delete()
            BankAccount.objects.update(balance=0)

            # شماره‌ی سفارش‌ها/فاکتورها از ۱ دوباره شروع بشه (فقط روی SQLite)
            if connection.vendor == 'sqlite':
                with connection.cursor() as cursor:
                    for table in WIPED_TABLES:
                        cursor.execute("DELETE FROM sqlite_sequence WHERE name = %s", [table])

        self.stdout.write(self.style.SUCCESS("\nتمام اطلاعات معاملاتی پاک شد. برنامه آماده‌ی شروع از صفره."))
