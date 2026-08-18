import re
import json
import time
from functools import wraps
from datetime import timedelta
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .print_utils import send_text_to_default_printer
from .print_pdf_utils import build_invoice_pdf, send_pdf_to_default_printer, build_install_receipt_pdf
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction


def require_permission(perm_name):
    """دکوریتور: فقط کاربری که لاگین کرده و مجوز perm_name رو داره (یا مدیره) می‌تونه وارد این ویو بشه."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            personnel_id = request.session.get('active_personnel_id')
            personnel = Personnel.objects.filter(id=personnel_id, is_active=True).first() if personnel_id else None
            if not personnel:
                return redirect(f"{reverse('login')}?next={request.path}")
            if not personnel.has_perm(perm_name):
                messages.error(request, 'دسترسی لازم برای این بخش رو نداری — با مدیر هماهنگ کن.')
                return redirect('game_index')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def party_ledger_add(party_name, amount, description, kind='other'):
    """مبلغ رو به حساب یک شخص اضافه/کم می‌کنه و یک ردیف تراکنش ثبت می‌کنه.
    amount مثبت یعنی شخص بدهکارتر می‌شه (به ما مدیون‌تر)، منفی یعنی بستانکارتر می‌شه (ما بهش مدیون‌تریم)."""
    name = (party_name or '').strip()
    if not name:
        return None
    party, _ = Party.objects.get_or_create(name=name, defaults={'kind': kind})
    party.balance += amount
    party.save(update_fields=['balance'])
    PartyLedgerEntry.objects.create(party=party, amount=amount, balance_after=party.balance, description=description)
    return party


CAPITAL_SUPPLIER_NAME = "موجودی اولیه"


def _normalize_fa(text):
    """یکسان‌سازی کاراکترهای عربی/فارسی مشابه (ی/ي، ک/ك) و فاصله‌های اضافه، برای مقایسه‌ی دقیق‌تر."""
    return (text or '').strip().replace('ي', 'ی').replace('ك', 'ک')


def is_capital_supplier_name(name):
    """تشخیص می‌ده که نام تأمین‌کننده همون عنوان ویژه‌ی «موجودی اولیه»ست یا نه —
    این مورد باید به‌عنوان سرمایه ثبت بشه، نه بدهی به یک شخص واقعی."""
    return _normalize_fa(name) == CAPITAL_SUPPLIER_NAME


def capital_ledger_add(amount, description):
    """مبلغ رو به «حساب سرمایه» اضافه/کم می‌کنه (نه به حساب یک شخص) — برای مواردی مثل
    «موجودی اولیه» که بدهی به یک تأمین‌کننده‌ی واقعی نیست. این حساب یک BankAccount غیرفعال
    (is_active=False) هست، پس هیچ‌وقت توی لیست بستانکاران/اشخاص یا فهرست حساب‌های بانکی
    قابل‌انتخاب برای پرداخت نشون داده نمی‌شه."""
    account, _ = BankAccount.objects.get_or_create(
        label='سرمایه', defaults={'is_active': False, 'order': 9999}
    )
    account.balance += amount
    account.save(update_fields=['balance'])
    return account


def consume_fifo_cost(device_name, device_type, accessory, quantity_needed):
    """برای کالای فله‌ای (بدون سریال): از قدیمی‌ترین خرید باقیمانده مصرف می‌کنه و هزینه‌ی کل رو برمی‌گردونه (FIFO)."""
    lots = PurchaseRecord.objects.filter(
        device_name=device_name, device_type=device_type, accessory=accessory,
        serial_number='', is_voided=False, remaining_quantity__gt=0
    ).order_by('created_at')
    total_cost = 0
    remaining_needed = quantity_needed
    for lot in lots:
        if remaining_needed <= 0:
            break
        take = min(lot.remaining_quantity, remaining_needed)
        total_cost += take * lot.unit_price
        lot.remaining_quantity -= take
        lot.save(update_fields=['remaining_quantity'])
        remaining_needed -= take
    if remaining_needed > 0:
        # داده‌ی ناقص (مثلاً از قبل از این فیچر) — با آخرین قیمت خرید شناخته‌شده تخمین می‌زنیم
        last_purchase = PurchaseRecord.objects.filter(
            device_name=device_name, device_type=device_type, accessory=accessory,
            serial_number='', is_voided=False
        ).order_by('-created_at').first()
        fallback_price = last_purchase.unit_price if last_purchase else 0
        total_cost += remaining_needed * fallback_price
    return total_cost


def restore_fifo_cost(device_name, device_type, accessory, quantity_to_restore):
    """معکوس consume_fifo_cost — وقتی فروشی ابطال می‌شه، مقدار مصرف‌شده رو به همون ترتیب FIFO برمی‌گردونه."""
    lots = PurchaseRecord.objects.filter(
        device_name=device_name, device_type=device_type, accessory=accessory,
        serial_number='', is_voided=False
    ).order_by('created_at')
    remaining = quantity_to_restore
    for lot in lots:
        if remaining <= 0:
            break
        capacity = lot.quantity - lot.remaining_quantity
        give_back = min(capacity, remaining)
        if give_back > 0:
            lot.remaining_quantity += give_back
            lot.save(update_fields=['remaining_quantity'])
            remaining -= give_back

from .models import (
    GameTitle, GamePlatformAvailability, Personnel, Product, PurchaseRecord, DeviceName, DeviceType, DeviceVariant, DeviceRegion, Supplier,
    SaleTerm, BankAccount, SaleRecord, SaleLineItem, Payment,
    Installer, GameInstallOrder, StockLevel, InventoryItem,
    AccessoryBrand, AccessoryColor, Accessory,
    Party, PartyLedgerEntry, Expense,
    SerialCounter, GeneratedSerialBatch, GeneratedSerial,
)
from django.db.models import Sum, Count
from .jalali_utils import jalali_to_gregorian_datetime, now_jalali_parts, jalali_month_start, to_jalali_string
from .seed import ensure_seed_devices, ensure_seed_sale_extras
from .seed_games import ensure_seed_games

def index(request):
    return render(request, 'index.html')

def game_catalog(request):
    games = GameTitle.objects.all()
    return render(request, 'game_catalog.html', {'game_catalog': games})

def goods_entry_type(request):
    return render(request, 'goods_entry_type.html')

def goods_entry(request, entry_type):
    context = {'entry_type': entry_type}
    # اگر نوع ورود 'game_install' بود، لیست نام بازی‌ها را برای انتخابگر می‌فرستیم
    if entry_type == 'game_install':
        context['game_names'] = list(GameTitle.objects.all().values_list('name', flat=True))
    
    return render(request, 'goods_entry.html', context)

def game_install_tracking(request):
    return render(request, 'game_install_tracking.html')

def game_install_delivery(request):
    return render(request, 'game_install_delivery.html')

def game_install_report(request):
    return render(request, 'game_install_report.html')

def game_delivery_registration(request):
    # پردازش‌های لازم برای ثبت و سپس هدایت به صفحه اصلی
    return redirect('game_index')


@require_permission('can_install')
def game_install_placeholder(request):
    ensure_seed_devices()
    ensure_seed_games()
    active_id = request.session.get('active_personnel_id')
    active_personnel = Personnel.objects.filter(id=active_id, is_active=True).first() if active_id else None

    device_names = DeviceName.objects.filter(is_active=True)
    # نقشه: device_id -> {'license': [...], 'copy': [...]}
    device_games_map = {}
    for dn in device_names:
        avail = GamePlatformAvailability.objects.filter(device_name=dn, game__is_active=True).select_related('game')
        by_license = {'license': [], 'copy': []}
        for a in avail:
            by_license[a.license_type].append({"id": a.game.id, "name": a.game.name})
        device_games_map[dn.id] = by_license
    installers = Installer.objects.filter(is_active=True)

    if request.method == 'POST':
        if not active_personnel:
            messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
            return redirect('game_install')

        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        serial_number = request.POST.get('serial_number', '').strip()
        device_name = DeviceName.objects.filter(id=request.POST.get('device_name_id')).first()
        if not device_name:
            messages.error(request, 'نام دستگاه را انتخاب کن.')
            return redirect('game_install')
        license_type = request.POST.get('license_type') or 'copy'
        if license_type not in ('license', 'copy'):
            license_type = 'copy'

        game_slots = {}
        for i in range(1, 11):
            gid = request.POST.get(f'game_slot_{i}')
            game_slots[f'game_slot_{i}'] = GameTitle.objects.filter(id=gid).first() if gid else None

        cost_raw = request.POST.get('install_cost') or '0'
        install_cost = re.sub(r'[^\d]', '', cost_raw) or '0'
        is_paid = request.POST.get('is_paid') == 'on'

        order = GameInstallOrder.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            serial_number=serial_number,
            device_name=device_name,
            license_type=license_type,
            receiver=active_personnel,
            install_cost=int(install_cost),
            is_paid=is_paid,
            stage=GameInstallOrder.STAGE_ORDERED,
            **game_slots,
        )
        messages.success(request, 'سفارش نصب بازی ثبت شد — حالا رسیدش رو چاپ کن.')
        return redirect('install_print', order_id=order.id)

    active_orders = GameInstallOrder.objects.select_related('device_name', 'installer', 'receiver').filter(
        is_voided=False
    ).exclude(stage=GameInstallOrder.STAGE_DELIVERED)[:60]
    recent_delivered = GameInstallOrder.objects.select_related('device_name', 'installer', 'receiver').filter(
        is_voided=False, stage=GameInstallOrder.STAGE_DELIVERED
    )[:15]
    return render(request, 'game_install.html', {
        'device_names': device_names,
        'device_games_json': json.dumps(device_games_map, ensure_ascii=False),
        'installers': installers,
        'now_jalali': now_jalali_parts(),
        'active_personnel': active_personnel,
        'active_orders': active_orders,
        'recent_delivered': recent_delivered,
    })


@require_POST
@require_permission('can_install')
def install_stage2_send(request, order_id):
    """مرحله ۲: ارسال سفارش برای نصاب."""
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return redirect('game_install')

    order = GameInstallOrder.objects.filter(id=order_id, is_voided=False).first()
    if not order:
        messages.error(request, 'این سفارش پیدا نشد.')
        return redirect('game_install')
    if order.stage != GameInstallOrder.STAGE_ORDERED:
        messages.info(request, 'این سفارش قبلاً به مرحله‌ی بعد رفته.')
        return redirect('game_install')

    installer_name = request.POST.get('installer_name', '').strip()
    if not installer_name:
        messages.error(request, 'نام نصاب را وارد کن.')
        return redirect('game_install')
    installer, _ = Installer.objects.get_or_create(name=installer_name)

    order.installer = installer
    order.referred_at = timezone.now()
    order.stage = GameInstallOrder.STAGE_SENT
    order.save(update_fields=['installer', 'referred_at', 'stage'])
    messages.success(request, f'سفارش برای «{installer.name}» ارسال شد.')
    return redirect('game_install')


@require_POST
@require_permission('can_install')
def install_stage3_return(request, order_id):
    """مرحله ۳: ثبت بازگشت از نصب."""
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return redirect('game_install')

    order = GameInstallOrder.objects.filter(id=order_id, is_voided=False).first()
    if not order:
        messages.error(request, 'این سفارش پیدا نشد.')
        return redirect('game_install')
    if order.stage != GameInstallOrder.STAGE_SENT:
        messages.info(request, 'این سفارش توی مرحله‌ی «ارسال برای نصاب» نیست.')
        return redirect('game_install')

    fee_raw = request.POST.get('installer_fee') or '0'
    installer_fee = int(re.sub(r'[^\d]', '', fee_raw) or '0')

    order.return_at = timezone.now()
    order.stage = GameInstallOrder.STAGE_RETURNED
    order.installer_fee = installer_fee
    order.save(update_fields=['return_at', 'stage', 'installer_fee'])
    if order.installer and installer_fee > 0:
        party_ledger_add(order.installer.name, -installer_fee, f"دستمزد نصب بازی #{order.id}", kind='installer')
    messages.success(request, 'بازگشت از نصب ثبت شد.')
    return redirect('game_install')


@require_POST
@require_permission('can_install')
def install_stage4_deliver(request, order_id):
    """مرحله ۴: تحویل به مشتری."""
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return redirect('game_install')

    order = GameInstallOrder.objects.filter(id=order_id, is_voided=False).first()
    if not order:
        messages.error(request, 'این سفارش پیدا نشد.')
        return redirect('game_install')
    if order.stage != GameInstallOrder.STAGE_RETURNED:
        messages.info(request, 'این سفارش هنوز از نصب برنگشته.')
        return redirect('game_install')

    order.delivered = True
    order.delivered_at = timezone.now()
    order.stage = GameInstallOrder.STAGE_DELIVERED
    order.save(update_fields=['delivered', 'delivered_at', 'stage'])
    messages.success(request, 'سفارش تحویل مشتری داده شد.')
    return redirect('game_install')


@require_permission('can_install')
def install_print(request, order_id):
    """پرینت دوتایی A6+A6 روی یک برگه A5: رسید مشتری + برگه‌ی نصاب."""
    order = GameInstallOrder.objects.select_related('device_name', 'installer', 'receiver').filter(id=order_id).first()
    if not order:
        messages.error(request, 'این سفارش پیدا نشد.')
        return redirect('game_install')
    return render(request, 'install_print.html', {'order': order})


@require_permission('can_install')
def install_print_to_printer(request, order_id):
    """رسید نصب رو مستقیم به پرینتر پیش‌فرض سرور می‌فرسته (بدون دیالوگ پرینت مرورگر)."""
    order = GameInstallOrder.objects.select_related('device_name', 'installer', 'receiver').filter(id=order_id).first()
    if not order:
        messages.error(request, 'این سفارش پیدا نشد.')
        return redirect('game_install')

    filepath, err = build_install_receipt_pdf(order)
    if err:
        messages.error(request, f"ساخت PDF شکست خورد: {err}")
        return redirect('install_print', order_id=order.id)

    ok, msg = send_pdf_to_default_printer(filepath)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('install_print', order_id=order.id)


# ---------- حساب اشخاص (تأمین‌کننده، نصاب، مشتری نسیه، ...) ----------

@require_permission('can_manage_parties')
def parties_list(request):
    q = request.GET.get('q', '').strip()
    parties = Party.objects.all()
    if q:
        parties = parties.filter(name__icontains=q)
    debtor_total = sum(p.balance for p in parties if p.balance > 0)
    creditor_total = sum(-p.balance for p in parties if p.balance < 0)
    all_parties = Party.objects.values('id', 'name')
    return render(request, 'parties_list.html', {
        'parties': parties,
        'q': q,
        'debtor_total': debtor_total,
        'creditor_total': creditor_total,
        'banks': BankAccount.objects.filter(is_active=True),
        'all_parties_json': json.dumps(list(all_parties), ensure_ascii=False),
    })


@require_permission('can_manage_parties')
def party_detail(request, party_id):
    party = Party.objects.filter(id=party_id).first()
    if not party:
        messages.error(request, 'این حساب پیدا نشد.')
        return redirect('parties_list')
    entries = party.entries.all()[:200]
    banks = BankAccount.objects.filter(is_active=True)
    return render(request, 'party_detail.html', {'party': party, 'entries': entries, 'banks': banks})


@require_POST
@require_permission('can_manage_parties')
def party_pay(request, party_id):
    """ثبت پرداخت به یک شخص (مثلاً تسویه با تأمین‌کننده یا نصاب) — از طریق بانک یا حواله از حساب شخص دیگر."""
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return redirect('party_detail', party_id=party_id)

    party = Party.objects.filter(id=party_id).first()
    if not party:
        messages.error(request, 'این حساب پیدا نشد.')
        return redirect('parties_list')

    amount_raw = request.POST.get('amount') or '0'
    amount = int(re.sub(r'[^\d]', '', amount_raw) or '0')
    if amount <= 0:
        messages.error(request, 'مبلغ را درست وارد کن.')
        return redirect('party_detail', party_id=party_id)

    method = request.POST.get('method')  # 'bank' یا 'transfer'

    with transaction.atomic():
        if method == 'bank':
            bank = BankAccount.objects.filter(id=request.POST.get('bank_id')).first()
            if not bank:
                messages.error(request, 'یک حساب بانکی انتخاب کن.')
                return redirect('party_detail', party_id=party_id)
            bank.balance -= amount
            bank.save(update_fields=['balance'])
            party_ledger_add(party.name, amount, f"پرداخت از {bank.label}", kind=party.kind)
        elif method == 'transfer':
            source_name = request.POST.get('source_party_name', '').strip()
            if not source_name:
                messages.error(request, 'نام شخص واریزکننده (حواله) را وارد کن.')
                return redirect('party_detail', party_id=party_id)
            party_ledger_add(source_name, -amount, f"حواله به {party.name}", kind='other')
            party_ledger_add(party.name, amount, f"دریافت حواله از {source_name}", kind=party.kind)
        else:
            messages.error(request, 'محل پرداخت را انتخاب کن.')
            return redirect('party_detail', party_id=party_id)

    messages.success(request, 'پرداخت ثبت شد.')
    return redirect('party_detail', party_id=party_id)


# ---------- هزینه‌های جاری فروشگاه ----------

DEFAULT_EXPENSE_CATEGORIES = ['حقوق', 'اجاره', 'قبض', 'هزینه عمومی', 'هزینه تعمیر']
DEFAULT_BILL_SUBCATEGORIES = ['برق', 'آب', 'گاز', 'بیمه', 'اینترنت']


@require_permission('can_manage_expenses')
def expense_entry(request):
    active_personnel = _active_personnel(request)
    banks = BankAccount.objects.filter(is_active=True)
    personnel_list = Personnel.objects.filter(is_active=True)

    existing_categories = list(Expense.objects.values_list('category', flat=True).distinct())
    categories = DEFAULT_EXPENSE_CATEGORIES + [c for c in existing_categories if c not in DEFAULT_EXPENSE_CATEGORIES]
    existing_subcats = list(Expense.objects.exclude(subcategory='').values_list('subcategory', flat=True).distinct())
    subcategories = DEFAULT_BILL_SUBCATEGORIES + [c for c in existing_subcats if c not in DEFAULT_BILL_SUBCATEGORIES]

    if request.method == 'POST':
        if not active_personnel:
            messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
            return redirect('expense_entry')

        category = request.POST.get('category', '').strip()
        if not category:
            messages.error(request, 'عنوان هزینه را وارد کن.')
            return redirect('expense_entry')

        subcategory = request.POST.get('subcategory', '').strip() if category == 'قبض' else ''
        personnel_id = request.POST.get('personnel_id', '') if category == 'حقوق' else ''
        salary_month = request.POST.get('salary_month', '').strip() if category == 'حقوق' else ''
        note = request.POST.get('note', '').strip()

        amount_raw = request.POST.get('amount') or '0'
        amount = int(re.sub(r'[^\d]', '', amount_raw) or '0')
        if amount <= 0:
            messages.error(request, 'مبلغ را درست وارد کن.')
            return redirect('expense_entry')

        method = request.POST.get('payment_method')
        if method not in ('bank', 'party'):
            messages.error(request, 'محل پرداخت را انتخاب کن.')
            return redirect('expense_entry')

        with transaction.atomic():
            bank = None
            party = None
            if method == 'bank':
                bank = BankAccount.objects.filter(id=request.POST.get('bank_id')).first()
                if not bank:
                    messages.error(request, 'یک حساب بانکی انتخاب کن.')
                    return redirect('expense_entry')
                bank.balance -= amount
                bank.save(update_fields=['balance'])
            else:
                party_name = request.POST.get('party_name', '').strip()
                if not party_name:
                    messages.error(request, 'نام شخص (بستانکار) را وارد کن.')
                    return redirect('expense_entry')
                party = party_ledger_add(party_name, -amount, f"هزینه: {category}" + (f" ({subcategory})" if subcategory else ""), kind='other')

            expense = Expense.objects.create(
                category=category,
                subcategory=subcategory,
                personnel_id=personnel_id or None,
                salary_month=salary_month,
                amount=amount,
                note=note,
                payment_method=method,
                bank_account=bank,
                party=party,
                created_by=active_personnel,
            )

        messages.success(request, 'هزینه ثبت شد.')
        return redirect('expense_entry')

    recent_expenses = Expense.objects.select_related('personnel', 'bank_account', 'party', 'created_by').all()[:60]
    return render(request, 'expense_entry.html', {
        'active_personnel': active_personnel,
        'banks': banks,
        'personnel_list': personnel_list,
        'categories_json': json.dumps(categories, ensure_ascii=False),
        'subcategories_json': json.dumps(subcategories, ensure_ascii=False),
        'recent_expenses': recent_expenses,
        'now_jalali': now_jalali_parts(),
    })


@require_POST
@require_permission('can_manage_expenses')
def expense_void(request, expense_id):
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return redirect('expense_entry')

    expense = Expense.objects.filter(id=expense_id).first()
    if not expense:
        messages.error(request, 'این هزینه پیدا نشد.')
        return redirect('expense_entry')
    if expense.is_voided:
        messages.info(request, 'این هزینه قبلاً ابطال شده بود.')
        return redirect('expense_entry')

    with transaction.atomic():
        if expense.payment_method == 'bank' and expense.bank_account:
            expense.bank_account.balance += expense.amount
            expense.bank_account.save(update_fields=['balance'])
        elif expense.payment_method == 'party' and expense.party:
            party_ledger_add(expense.party.name, expense.amount, f"ابطال هزینه #{expense.id}", kind=expense.party.kind)
        expense.is_voided = True
        expense.voided_at = timezone.now()
        expense.save(update_fields=['is_voided', 'voided_at'])

    messages.success(request, 'هزینه ابطال شد.')
    return redirect('expense_entry')


def serial_lookup(request):
    serial = request.GET.get('serial', '').strip()
    if not serial:
        return JsonResponse({'found': False})

    # ممکنه چند واحد فیزیکی سریال مشترک داشته باشن (مثلاً همه دسته‌های سفید) —
    # پس اول دنبال یه واحد «در انبار» با این سریال می‌گردیم؛ فقط وقتی هیچ‌کدوم موجود نبود، سریال رو «فروخته‌شده» اعلام می‌کنیم.
    item = InventoryItem.objects.select_related(
        'device_name', 'device_type', 'accessory', 'accessory__brand', 'accessory__color',
        'purchase', 'purchase__device_variant', 'purchase__device_region'
    ).filter(serial_number=serial, status='in_stock').first()

    if not item:
        any_item = InventoryItem.objects.filter(serial_number=serial).exists()
        if any_item:
            return JsonResponse({'found': True, 'already_sold': True, 'message': 'همه‌ی واحدهای این سریال قبلاً فروخته شده — دیگه موجودی نداره.'})
        return JsonResponse({'found': False})

    if item.accessory:
        acc = item.accessory
        return JsonResponse({
            'found': True,
            'already_sold': False,
            'is_accessory': True,
            'accessory_id': acc.id,
            'accessory_name': acc.name,
            'accessory_brand': acc.brand.name if acc.brand else '',
            'accessory_model': acc.model or '',
            'accessory_color': acc.color.name if acc.color else '',
        })

    variant_id = ''
    region_id = ''
    if item.purchase:
        if item.purchase.device_variant_id:
            variant_id = item.purchase.device_variant_id
        if item.purchase.device_region_id:
            region_id = item.purchase.device_region_id

    return JsonResponse({
        'found': True,
        'already_sold': False,
        'is_accessory': False,
        'device_name_id': item.device_name_id,
        'device_name': item.device_name.name if item.device_name else '',
        'device_type_id': item.device_type_id,
        'device_type': item.device_type.name if item.device_type else '',
        'device_variant_id': variant_id,
        'device_region_id': region_id,
    })


@require_permission('can_sale')
def sale_entry(request):
    ensure_seed_devices()
    ensure_seed_sale_extras()

    active_id = request.session.get('active_personnel_id')
    active_personnel = Personnel.objects.filter(id=active_id, is_active=True).first() if active_id else None

    device_names = DeviceName.objects.filter(is_active=True).prefetch_related('types')
    device_types_map = {}
    device_variants_map = {}
    for dn in device_names:
        types = dn.types.filter(is_active=True)
        device_types_map[dn.id] = [{"id": t.id, "name": t.name} for t in types]
        for t in types:
            variants = t.variants.filter(is_active=True)
            if variants:
                device_variants_map[t.id] = [{"id": v.id, "code": v.code} for v in variants]
    device_regions = DeviceRegion.objects.filter(is_active=True)
    devices_with_region = list(device_names.filter(has_region=True).values_list('id', flat=True))
    sale_terms = SaleTerm.objects.filter(is_active=True)
    bank_accounts = BankAccount.objects.filter(is_active=True)

    accessories = Accessory.objects.filter(is_active=True).select_related('brand', 'color')
    accessory_names = sorted(set(a.name for a in accessories))
    accessory_options_map = {}
    for a in accessories:
        label_parts = [p for p in [a.brand.name if a.brand else '', a.model, a.color.name if a.color else ''] if p]
        label = " - ".join(label_parts) if label_parts else "استاندارد"
        accessory_options_map.setdefault(a.name, []).append({"id": a.id, "label": label})

    if request.method == 'POST':
        if not active_personnel:
            messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
            return redirect('game_sales_invoice')

        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_national_id = request.POST.get('customer_national_id', '').strip()
        term_ids = request.POST.getlist('terms[]')

        item_device_name_ids = request.POST.getlist('item_device_name_id[]')
        item_device_type_ids = request.POST.getlist('item_device_type_id[]')
        item_device_variant_ids = request.POST.getlist('item_device_variant_id[]')
        item_device_region_ids = request.POST.getlist('item_device_region_id[]')
        item_accessory_ids = request.POST.getlist('item_accessory_id[]')
        item_serials = request.POST.getlist('item_serial[]')
        item_qtys = request.POST.getlist('item_qty[]')
        item_prices = request.POST.getlist('item_price[]')

        pay_types = request.POST.getlist('payment_type[]')
        pay_amounts = request.POST.getlist('payment_amount[]')
        pay_trackings = request.POST.getlist('payment_tracking[]')
        pay_accounts = request.POST.getlist('payment_account_id[]')
        pay_party_names = request.POST.getlist('payment_party_name[]')

        # حداقل یک ردیف کالای معتبر لازم است (دستگاه یا کالای جانبی)
        valid_rows = [
            i for i in range(len(item_device_name_ids))
            if item_device_name_ids[i] or (i < len(item_accessory_ids) and item_accessory_ids[i])
        ]
        if not valid_rows:
            messages.error(request, 'حداقل یک ردیف کالا لازم است.')
            return redirect('game_sales_invoice')

        sale = SaleRecord.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_national_id=customer_national_id,
            change=request.POST.get('change') == 'on',
            seller=active_personnel,
        )
        if term_ids:
            sale.terms.set(SaleTerm.objects.filter(id__in=term_ids))

        for i in valid_rows:
            accessory_id = item_accessory_ids[i] if i < len(item_accessory_ids) else ''
            accessory = Accessory.objects.filter(id=accessory_id).first() if accessory_id else None

            device_name = None
            device_type = None
            device_variant = None
            device_region = None
            if not accessory:
                device_name = DeviceName.objects.filter(id=item_device_name_ids[i]).first()
                if not device_name:
                    continue
                device_type_id = item_device_type_ids[i] if i < len(item_device_type_ids) else ''
                device_type = DeviceType.objects.filter(id=device_type_id).first() if device_type_id else None
                variant_id = item_device_variant_ids[i] if i < len(item_device_variant_ids) else ''
                device_variant = DeviceVariant.objects.filter(id=variant_id).first() if variant_id else None
                region_id = item_device_region_ids[i] if i < len(item_device_region_ids) else ''
                device_region = DeviceRegion.objects.filter(id=region_id).first() if region_id else None

            serial = item_serials[i].strip() if i < len(item_serials) else ''
            try:
                qty = max(1, int(item_qtys[i]))
            except (ValueError, IndexError):
                qty = 1
            price_raw = item_prices[i] if i < len(item_prices) else '0'
            price = re.sub(r'[^\d]', '', price_raw) or '0'

            line_item = SaleLineItem.objects.create(
                sale=sale, device_name=device_name, device_type=device_type,
                device_variant=device_variant, device_region=device_region, accessory=accessory,
                serial_number=serial, quantity=qty, unit_price=int(price),
            )

            if serial:
                # اگه این سریال دقیقاً یک واحد موجود در انبار باشه، همون رو فروخته‌شده علامت بزن
                inv_item = InventoryItem.objects.filter(serial_number=serial, status='in_stock').first()
                if inv_item:
                    inv_item.status = 'sold'
                    inv_item.sale_line_item = line_item
                    inv_item.sold_at = timezone.now()
                    inv_item.save(update_fields=['status', 'sale_line_item', 'sold_at'])
                    line_item.cost_amount = inv_item.unit_cost
                    line_item.save(update_fields=['cost_amount'])
            else:
                # کالای بدون سریال — از موجودی فله‌ای کسر کن و هزینه‌ی FIFO رو محاسبه کن
                stock = StockLevel.objects.filter(device_name=device_name, device_type=device_type, accessory=accessory).first()
                if stock:
                    stock.quantity -= qty
                    stock.save(update_fields=['quantity'])
                line_item.cost_amount = consume_fifo_cost(device_name, device_type, accessory, qty)
                line_item.save(update_fields=['cost_amount'])

        for i, ptype in enumerate(pay_types):
            amount_raw = pay_amounts[i] if i < len(pay_amounts) else '0'
            amount = int(re.sub(r'[^\d]', '', amount_raw) or '0')
            if amount <= 0:
                continue
            account_id = pay_accounts[i] if i < len(pay_accounts) else ''
            party_name = pay_party_names[i].strip() if i < len(pay_party_names) else ''
            ptype = ptype if ptype in ('pos', 'transfer', 'party_account') else 'pos'

            bank = None
            party = None
            if ptype == 'transfer' and account_id:
                bank = BankAccount.objects.filter(id=account_id).first()
                if bank:
                    bank.balance += amount
                    bank.save(update_fields=['balance'])
            elif ptype == 'party_account' and party_name:
                party = party_ledger_add(party_name, amount, f"فروش نسیه - فاکتور #{sale.id}", kind='customer')

            Payment.objects.create(
                sale=sale,
                payment_type=ptype,
                amount=amount,
                tracking_number=pay_trackings[i].strip() if i < len(pay_trackings) else '',
                bank_account=bank,
                party=party,
            )

        action = request.POST.get('action', 'save')
        if action == 'save_print':
            ok, msg = _print_both_invoice_copies(sale)
            if ok:
                messages.success(request, f'فاکتور ثبت شد. {msg}')
            else:
                messages.error(request, f'فاکتور ثبت شد. {msg}')
        else:
            messages.success(request, 'فاکتور فروش با موفقیت ثبت شد.')
        return redirect('sale_print', sale_id=sale.id)

    recent_sales = SaleRecord.objects.select_related('seller').prefetch_related('items', 'payments').all()[:30]
    return render(request, 'sale_entry.html', {
        'device_names_json': json.dumps([{"id": dn.id, "name": dn.name} for dn in device_names], ensure_ascii=False),
        'device_types_json': json.dumps(device_types_map, ensure_ascii=False),
        'device_variants_json': json.dumps(device_variants_map, ensure_ascii=False),
        'devices_with_region_json': json.dumps(devices_with_region),
        'device_regions_json': json.dumps([{"id": r.id, "code": r.code} for r in device_regions], ensure_ascii=False),
        'accessory_names_json': json.dumps(accessory_names, ensure_ascii=False),
        'accessory_options_json': json.dumps(accessory_options_map, ensure_ascii=False),
        'sale_terms': sale_terms,
        'bank_accounts_json': json.dumps([{"id": a.id, "label": a.label} for a in bank_accounts], ensure_ascii=False),
        'party_names_json': json.dumps(list(Party.objects.values_list('name', flat=True)), ensure_ascii=False),
        'recent_sales': recent_sales,
    })


def sale_print(request, sale_id):
    sale = SaleRecord.objects.select_related('seller').prefetch_related('items', 'payments', 'terms').filter(id=sale_id).first()
    if not sale:
        messages.error(request, 'این فاکتور پیدا نشد.')
        return redirect('game_sales_invoice')
    return render(request, 'sale_print.html', {'sale': sale})


def _print_both_invoice_copies(sale):
    """هر دو نسخه (مشتری و فروشگاه) رو به‌صورت PDF (اندازه A5) به پرینتر می‌فرسته. خروجی: (ok, پیام).
    نسخهٔ مشتری همیشه اول فرستاده می‌شه؛ چون os.startfile ناهمزمانه (فقط برنامه رو باز می‌کنه
    و منتظر چاپ واقعی نمی‌مونه)، چند ثانیه صبر می‌کنیم تا نسخهٔ مشتری واقعاً وارد صف پرینتر بشه،
    بعد نسخهٔ فروشگاه رو می‌فرستیم — تا نوبت چاپ‌شون هیچ‌وقت جابه‌جا نشه."""
    path1, err1 = build_invoice_pdf(sale, 'customer')
    if err1:
        return False, f"ساخت PDF نسخهٔ مشتری شکست خورد: {err1}"
    path2, err2 = build_invoice_pdf(sale, 'store')
    if err2:
        return False, f"ساخت PDF نسخهٔ فروشگاه شکست خورد: {err2}"

    ok1, msg1 = send_pdf_to_default_printer(path1)
    time.sleep(4)  # فرصت کافی برای باز شدن PDF و رسیدن واقعی به صف پرینتر، قبل از ارسال نسخهٔ بعدی
    ok2, msg2 = send_pdf_to_default_printer(path2)
    if ok1 and ok2:
        return True, "هر دو نسخهٔ فاکتور (مشتری و فروشگاه) به پرینتر فرستاده شد."
    if ok1 and not ok2:
        return False, f"نسخهٔ مشتری چاپ شد، ولی نسخهٔ فروشگاه چاپ نشد: {msg2}"
    if ok2 and not ok1:
        return False, f"نسخهٔ فروشگاه چاپ شد، ولی نسخهٔ مشتری چاپ نشد: {msg1}"
    return False, f"چاپ هیچ‌کدوم از دو نسخه انجام نشد: {msg1}"


def sale_print_to_printer(request, sale_id):
    sale = SaleRecord.objects.select_related('seller').prefetch_related('items', 'payments', 'terms').filter(id=sale_id).first()
    if not sale:
        messages.error(request, 'این فاکتور پیدا نشد.')
        return redirect('game_sales_invoice')

    ok, msg = _print_both_invoice_copies(sale)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect('sale_print', sale_id=sale.id)


def consignment_placeholder(request):
    # صفحه «امانی» — فیلدها در مرحله بعد طبق توضیح مهدی مشخص و کامل می‌شود.
    return render(request, 'consignment.html')


def repair_placeholder(request):
    # صفحه «تعمیرات» — فیلدها در مرحله بعد طبق توضیح مهدی مشخص و کامل می‌شود.
    return render(request, 'repair.html')


def games_manage(request):
    ensure_seed_devices()
    ensure_seed_games()
    device_names = DeviceName.objects.filter(is_active=True)
    edit_id = request.GET.get('edit')
    editing_game = GameTitle.objects.filter(id=edit_id).first() if edit_id else None
    editing_availability = set()
    if editing_game:
        editing_availability = set(
            (a.device_name_id, a.license_type) for a in editing_game.availabilities.all()
        )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete':
            GameTitle.objects.filter(id=request.POST.get('game_id')).delete()
            messages.success(request, 'بازی حذف شد.')
            return redirect('games_manage')

        if action == 'toggle_active':
            game = GameTitle.objects.filter(id=request.POST.get('game_id')).first()
            if game:
                game.is_active = not game.is_active
                game.save(update_fields=['is_active'])
            return redirect('games_manage')

        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'نام بازی را وارد کن.')
            return redirect('games_manage')

        game_id = request.POST.get('game_id')
        if game_id:
            game = GameTitle.objects.filter(id=game_id).first()
            if not game:
                messages.error(request, 'بازی پیدا نشد.')
                return redirect('games_manage')
            game.name = name
            game.save()
            GamePlatformAvailability.objects.filter(game=game).delete()
        else:
            game, _ = GameTitle.objects.get_or_create(name=name)

        for combo in request.POST.getlist('availability[]'):
            try:
                device_id_str, license_type = combo.split(':')
            except ValueError:
                continue
            device_name = DeviceName.objects.filter(id=device_id_str).first()
            if device_name and license_type in ('license', 'copy'):
                GamePlatformAvailability.objects.get_or_create(game=game, device_name=device_name, license_type=license_type)

        messages.success(request, 'بازی ذخیره شد.')
        return redirect('games_manage')

    games = GameTitle.objects.all().prefetch_related('availabilities__device_name')
    return render(request, 'games_manage.html', {
        'device_names': device_names,
        'games': games,
        'editing_game': editing_game,
        'editing_availability': editing_availability,
    })


def inventory_view(request):
    stock_levels = StockLevel.objects.select_related('device_name', 'device_type').filter(quantity__gt=0)
    in_stock_items = InventoryItem.objects.select_related('device_name', 'device_type').filter(status='in_stock')
    return render(request, 'inventory.html', {
        'stock_levels': stock_levels,
        'in_stock_items': in_stock_items,
    })


SERIAL_PREFIX = "KAREN"
SERIAL_DIGITS = 6  # KAREN + ۶ رقم => مثلاً KAREN000123


def _reserve_serial_range(prefix, quantity):
    """به‌صورت اتمیک یک بازه از شماره‌های ترتیبی رو برای این پیشوند رزرو می‌کنه — حتی زیر بار
    چند کاربر همزمان، هیچ‌وقت دو نفر یک بازه رو نمی‌گیرن (select_for_update صف می‌بندد)."""
    with transaction.atomic():
        counter, _ = SerialCounter.objects.select_for_update().get_or_create(prefix=prefix)
        start = counter.last_value + 1
        end = counter.last_value + quantity
        counter.last_value = end
        counter.save(update_fields=['last_value'])
    return start, end


def serial_generator(request):
    """تولید سریال برای کالاهایی که سریال کارخانه‌ای ندارن — هر بار تولید، یک بازه‌ی یکتا
    و تضمین‌شده از سریال‌های KARENxxxxxx رزرو می‌کنه و آماده‌ی چاپ روی برچسب A4 می‌کنه."""
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', '0'))
        except ValueError:
            quantity = 0

        if quantity < 1 or quantity > 500:
            messages.error(request, 'تعداد باید بین ۱ تا ۵۰۰ باشه.')
            return redirect('serial_generator')

        start, end = _reserve_serial_range(SERIAL_PREFIX, quantity)

        batch = GeneratedSerialBatch.objects.create(prefix=SERIAL_PREFIX, quantity=quantity)
        GeneratedSerial.objects.bulk_create([
            GeneratedSerial(
                batch=batch,
                serial_number=f"{SERIAL_PREFIX}{n:0{SERIAL_DIGITS}d}",
                sequence_number=n,
            )
            for n in range(start, end + 1)
        ])
        messages.success(request, f'{quantity} سریال جدید تولید شد.')
        return redirect('serial_labels_print', batch_id=batch.id)

    recent_batches = GeneratedSerialBatch.objects.all()[:30]
    return render(request, 'serial_generator.html', {
        'recent_batches': recent_batches,
        'prefix': SERIAL_PREFIX,
    })


def serial_labels_print(request, batch_id):
    batch = GeneratedSerialBatch.objects.prefetch_related('serials').filter(id=batch_id).first()
    if not batch:
        messages.error(request, 'این دسته سریال پیدا نشد.')
        return redirect('serial_generator')
    return render(request, 'serial_labels_print.html', {
        'batch': batch,
        'serials': batch.serials.all(),
    })

REPORT_TYPES = {
    'sales': 'فاکتورهای فروش',
    'purchases': 'خریدها',
    'banks': 'بانک‌ها',
    'inventory': 'موجودی کالا',
    'installs': 'نصب بازی',
    'profit': 'سود و زیان',
}


def _get_date_range(request):
    now = timezone.now()
    preset = request.GET.get('preset', 'month')
    custom_from = request.GET.get('from_y') and request.GET.get('from_m') and request.GET.get('from_d')
    custom_to = request.GET.get('to_y') and request.GET.get('to_m') and request.GET.get('to_d')

    if custom_from and custom_to:
        try:
            date_from = jalali_to_gregorian_datetime(request.GET['from_y'], request.GET['from_m'], request.GET['from_d'], 0, 0)
            date_to = jalali_to_gregorian_datetime(request.GET['to_y'], request.GET['to_m'], request.GET['to_d'], 23, 59)
            preset = 'custom'
        except (TypeError, ValueError):
            date_from = jalali_month_start()
            date_to = now
    elif preset == 'today':
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = now
    elif preset == 'week':
        date_from = now - timedelta(days=7)
        date_to = now
    else:
        preset = 'month'
        date_from = jalali_month_start()
        date_to = now
    return preset, date_from, date_to


@require_permission('can_view_reports')
def reports_home(request):
    return render(request, 'reports.html', {'report_types': REPORT_TYPES})


def _build_report_context(request, report_type):
    preset, date_from, date_to = _get_date_range(request)
    device_name_id = request.GET.get('device_name_id', '')

    context = {
        'report_type': report_type,
        'report_title': REPORT_TYPES.get(report_type, ''),
        'preset': preset,
        'now_jalali': now_jalali_parts(),
        'date_from_jalali': to_jalali_string(date_from),
        'date_to_jalali': to_jalali_string(date_to),
        'device_names': DeviceName.objects.filter(is_active=True),
        'selected_device_name_id': device_name_id,
    }

    if report_type == 'sales':
        items_qs = SaleLineItem.objects.filter(
            sale__created_at__gte=date_from, sale__created_at__lte=date_to
        ).select_related('sale', 'sale__seller', 'device_name', 'device_type', 'accessory')
        if device_name_id:
            items_qs = items_qs.filter(device_name_id=device_name_id)
        items_qs = items_qs.order_by('-sale__created_at')
        non_voided_qs = items_qs.exclude(sale__is_voided=True)
        context['sale_items'] = items_qs[:200]
        context['sales_total'] = sum(i.total_price for i in non_voided_qs)
        context['sales_count'] = non_voided_qs.values('sale').distinct().count()

    elif report_type == 'purchases':
        qs = PurchaseRecord.objects.filter(
            created_at__gte=date_from, created_at__lte=date_to
        ).select_related('device_name', 'device_type', 'accessory', 'supplier', 'receiver')
        if device_name_id:
            qs = qs.filter(device_name_id=device_name_id)
        qs = qs.order_by('-created_at')
        non_voided_qs = qs.exclude(is_voided=True)
        context['purchases'] = qs[:200]
        context['purchases_total'] = sum(p.total_price for p in non_voided_qs)
        context['purchases_count'] = non_voided_qs.count()

    elif report_type == 'banks':
        payments_qs = Payment.objects.filter(
            sale__created_at__gte=date_from, sale__created_at__lte=date_to
        ).select_related('bank_account')
        by_account = {}
        pos_total = 0
        pos_count = 0
        for p in payments_qs:
            if p.payment_type == 'pos':
                pos_total += p.amount
                pos_count += 1
            else:
                key = p.bank_account.label if p.bank_account else 'نامشخص'
                by_account.setdefault(key, {'count': 0, 'total': 0})
                by_account[key]['count'] += 1
                by_account[key]['total'] += p.amount
        context['bank_breakdown'] = sorted(by_account.items(), key=lambda kv: -kv[1]['total'])
        context['pos_total'] = pos_total
        context['pos_count'] = pos_count

    elif report_type == 'inventory':
        stock_qs = StockLevel.objects.select_related('device_name', 'device_type', 'accessory').filter(quantity__gt=0)
        items_qs = InventoryItem.objects.select_related('device_name', 'device_type', 'accessory').filter(status='in_stock')
        bulk_lots_qs = PurchaseRecord.objects.select_related('device_name', 'device_type', 'accessory').filter(
            serial_number='', is_voided=False, remaining_quantity__gt=0
        )
        if device_name_id:
            stock_qs = stock_qs.filter(device_name_id=device_name_id)
            items_qs = items_qs.filter(device_name_id=device_name_id)
            bulk_lots_qs = bulk_lots_qs.filter(device_name_id=device_name_id)
        context['stock_levels'] = stock_qs
        context['in_stock_items'] = items_qs

        serial_value = items_qs.aggregate(v=Sum('unit_cost'))['v'] or 0
        bulk_value = sum(lot.remaining_quantity * lot.unit_price for lot in bulk_lots_qs)
        context['in_stock_value'] = serial_value
        context['bulk_stock_value'] = bulk_value
        context['inventory_total_value'] = serial_value + bulk_value

        # جمع‌بندی به تفکیک هر گروه کالا (مثلاً PS5) — سریال‌دار + فله با هم، برای دیدن ارزش هر گروه
        def _group_key(dn, dt, acc):
            if acc:
                return ('accessory', acc.id), acc.name
            label = (dn.name if dn else 'نامشخص') + (f' {dt.name}' if dt else '')
            return ('device', dn.id if dn else None), label

        groups = {}
        for it in items_qs:
            key, label = _group_key(it.device_name, it.device_type, it.accessory)
            g = groups.setdefault(key, {'label': label, 'serial_count': 0, 'serial_value': 0, 'bulk_qty': 0, 'bulk_value': 0})
            g['serial_count'] += 1
            g['serial_value'] += it.unit_cost
        for lot in bulk_lots_qs:
            key, label = _group_key(lot.device_name, lot.device_type, lot.accessory)
            g = groups.setdefault(key, {'label': label, 'serial_count': 0, 'serial_value': 0, 'bulk_qty': 0, 'bulk_value': 0})
            g['bulk_qty'] += lot.remaining_quantity
            g['bulk_value'] += lot.remaining_quantity * lot.unit_price

        group_rows = list(groups.values())
        for g in group_rows:
            g['total_value'] = g['serial_value'] + g['bulk_value']
        group_rows.sort(key=lambda g: -g['total_value'])
        context['inventory_groups'] = group_rows

    elif report_type == 'installs':
        qs = GameInstallOrder.objects.filter(
            order_datetime__gte=date_from, order_datetime__lte=date_to
        ).select_related('device_name', 'installer', 'receiver')
        installer_id = request.GET.get('installer_id', '')
        if installer_id:
            qs = qs.filter(installer_id=installer_id)
        if device_name_id:
            qs = qs.filter(device_name_id=device_name_id)
        qs = qs.order_by('-order_datetime')
        non_voided_qs = qs.exclude(is_voided=True)
        context['installers'] = Installer.objects.filter(is_active=True)
        context['selected_installer_id'] = installer_id
        context['install_orders'] = qs[:200]
        context['installs_count'] = non_voided_qs.count()
        context['installs_revenue'] = sum(o.install_cost for o in non_voided_qs)
        context['installs_delivered'] = non_voided_qs.filter(delivered=True).count()
        context['installs_pending'] = context['installs_count'] - context['installs_delivered']

    elif report_type == 'profit':
        sale_items_qs = SaleLineItem.objects.filter(
            sale__created_at__gte=date_from, sale__created_at__lte=date_to, sale__is_voided=False
        )
        sales_revenue = sum(i.total_price for i in sale_items_qs)
        sales_cogs = sum(i.cost_amount for i in sale_items_qs)
        sales_profit = sales_revenue - sales_cogs

        install_qs = GameInstallOrder.objects.filter(
            is_voided=False, return_at__gte=date_from, return_at__lte=date_to
        )
        install_revenue = sum(o.install_cost for o in install_qs)
        install_fees = sum((o.installer_fee or 0) for o in install_qs)
        install_profit = install_revenue - install_fees

        expense_qs = Expense.objects.filter(is_voided=False, created_at__gte=date_from, created_at__lte=date_to)
        expenses_total = sum(e.amount for e in expense_qs)

        purchases_qs = PurchaseRecord.objects.filter(created_at__gte=date_from, created_at__lte=date_to, is_voided=False)
        purchases_total = sum(p.total_price for p in purchases_qs)

        context['sales_revenue'] = sales_revenue
        context['sales_cogs'] = sales_cogs
        context['sales_profit'] = sales_profit
        context['install_revenue'] = install_revenue
        context['install_fees'] = install_fees
        context['install_profit'] = install_profit
        context['expenses_total'] = expenses_total
        context['purchases_total_period'] = purchases_total
        context['profit_estimate'] = sales_profit + install_profit - expenses_total

    return context


@require_permission('can_view_reports')
def report_detail(request, report_type):
    if report_type not in REPORT_TYPES:
        messages.error(request, 'گزارش نامعتبر است.')
        return redirect('reports_home')
    context = _build_report_context(request, report_type)
    return render(request, 'report_detail.html', context)


def _build_report_print_text(context):
    report_type = context['report_type']
    lines = []
    lines.append("=" * 40)
    lines.append(f"گیم‌کارن - {context['report_title']}")
    lines.append(f"بازه: {context['date_from_jalali']} تا {context['date_to_jalali']}")
    lines.append("=" * 40)

    if report_type == 'sales':
        lines.append(f"تعداد فاکتور: {context['sales_count']}")
        lines.append(f"جمع فروش: {context['sales_total']} تومان")
        lines.append("-" * 40)
        for i in context['sale_items']:
            name = i.accessory.name if i.accessory else (i.device_name.name if i.device_name else '—')
            lines.append(f"فاکتور #{i.sale_id} | {name} x{i.quantity} | {i.total_price} تومان | {i.sale.seller.name}")

    elif report_type == 'purchases':
        lines.append(f"تعداد خرید: {context['purchases_count']}")
        lines.append(f"جمع خرید: {context['purchases_total']} تومان")
        lines.append("-" * 40)
        for p in context['purchases']:
            name = p.accessory.name if p.accessory else (p.device_name.name if p.device_name else '—')
            lines.append(f"{name} x{p.quantity} | {p.total_price} تومان | تأمین‌کننده: {p.supplier.name if p.supplier else '—'}")

    elif report_type == 'banks':
        lines.append(f"پوز (کارتخوان): {context['pos_count']} تراکنش، {context['pos_total']} تومان")
        lines.append("-" * 40)
        for name, data in context['bank_breakdown']:
            lines.append(f"{name}: {data['count']} تراکنش، {data['total']} تومان")

    elif report_type == 'inventory':
        lines.append(f"ارزش خرید موجودی سریال‌دار: {context['in_stock_value']} تومان")
        lines.append("-" * 40)
        lines.append("واحدهای سریال‌دار:")
        for item in context['in_stock_items']:
            name = item.accessory.name if item.accessory else (item.device_name.name if item.device_name else '—')
            lines.append(f"  {item.serial_number} | {name}")
        lines.append("-" * 40)
        lines.append("موجودی فله‌ای:")
        for s in context['stock_levels']:
            name = s.accessory.name if s.accessory else (s.device_name.name if s.device_name else '—')
            lines.append(f"  {name}: {s.quantity} عدد")

    elif report_type == 'installs':
        lines.append(f"تعداد سفارش: {context['installs_count']} (تحویل‌شده: {context['installs_delivered']}, در جریان: {context['installs_pending']})")
        lines.append(f"درآمد نصب: {context['installs_revenue']} تومان")
        lines.append("-" * 40)
        for o in context['install_orders']:
            lines.append(f"  {o.order_jalali} | {o.customer_name or '—'} | {o.device_name.name} | نصاب: {o.installer.name if o.installer else '—'} | {o.install_cost} تومان")

    elif report_type == 'profit':
        lines.append(f"سود فروش (فروش − بهای تمام‌شده): {context['sales_profit']} تومان")
        lines.append(f"  (فروش: {context['sales_revenue']} | بهای تمام‌شده: {context['sales_cogs']})")
        lines.append(f"سود نصب بازی (هزینه نصب − دستمزد نصاب): {context['install_profit']} تومان")
        lines.append(f"جمع هزینه‌های جاری: {context['expenses_total']} تومان")
        lines.append("-" * 40)
        lines.append(f"سود/زیان خالص: {context['profit_estimate']} تومان")

    lines.append("=" * 40)
    return "\n".join(lines)


@require_permission('can_view_reports')
def report_print(request, report_type):
    if report_type not in REPORT_TYPES:
        messages.error(request, 'گزارش نامعتبر است.')
        return redirect('reports_home')
    context = _build_report_context(request, report_type)
    text = _build_report_print_text(context)
    ok, msg = send_text_to_default_printer(text, job_name=f"report_{report_type}")
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect(f"{reverse('report_detail', args=[report_type])}?{request.GET.urlencode()}")



def login_view(request):
    if request.session.get('active_personnel_id'):
        personnel = Personnel.objects.filter(id=request.session['active_personnel_id'], is_active=True).first()
        if personnel:
            return redirect(request.GET.get('next') or 'game_index')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        password = request.POST.get('password', '')
        personnel = Personnel.objects.filter(name=name, is_active=True).first()
        if personnel and personnel.password_hash and personnel.check_password(password):
            request.session['active_personnel_id'] = personnel.id
            messages.success(request, f'خوش اومدی {personnel.name}!')
            return redirect(request.POST.get('next') or 'game_index')
        messages.error(request, 'نام یا رمز عبور اشتباهه.')

    return render(request, 'login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    request.session.flush()
    return redirect('login')


# ---------- خرید ----------

@require_permission('can_purchase')
def purchase_entry(request):
    ensure_seed_devices()

    active_id = request.session.get('active_personnel_id')
    active_personnel = Personnel.objects.filter(id=active_id, is_active=True).first() if active_id else None
    is_admin = bool(active_personnel and active_personnel.is_admin)

    device_names = DeviceName.objects.filter(is_active=True).prefetch_related('types')
    device_types_map = {}
    device_variants_map = {}
    for dn in device_names:
        types = dn.types.filter(is_active=True)
        device_types_map[dn.id] = [{"id": t.id, "name": t.name} for t in types]
        for t in types:
            variants = t.variants.filter(is_active=True)
            if variants:
                device_variants_map[t.id] = [{"id": v.id, "code": v.code} for v in variants]
    device_regions = DeviceRegion.objects.filter(is_active=True)
    devices_with_region = list(device_names.filter(has_region=True).values_list('id', flat=True))

    suppliers = Supplier.objects.all()
    accessory_brands = AccessoryBrand.objects.all()
    accessory_colors = AccessoryColor.objects.all()
    accessory_names = Accessory.objects.filter(is_active=True).values_list('name', flat=True).distinct()
    all_personnel_active = Personnel.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        if not active_personnel:
            messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
            return redirect('purchase_entry')

        item_type = request.POST.get('item_type') or 'device'
        serial_number = request.POST.get('serial_number', '').strip()
        quantity = request.POST.get('quantity') or '1'
        unit_price_raw = request.POST.get('unit_price') or '0'
        unit_price = re.sub(r'[^\d]', '', unit_price_raw) or '0'
        supplier_name = request.POST.get('supplier_name', '').strip()

        try:
            quantity = max(1, int(quantity))
        except ValueError:
            quantity = 1
        try:
            unit_price = max(0, int(unit_price))
        except ValueError:
            unit_price = 0

        device_name = device_type = device_variant = device_region = None
        accessory = None

        if item_type == 'accessory':
            acc_name = request.POST.get('accessory_name', '').strip()
            acc_brand_name = request.POST.get('accessory_brand', '').strip()
            acc_model = request.POST.get('accessory_model', '').strip()
            acc_color_name = request.POST.get('accessory_color', '').strip()

            if not acc_name:
                messages.error(request, 'نام کالای جانبی را وارد کن.')
                return redirect('purchase_entry')

            acc_brand = None
            if acc_brand_name:
                acc_brand, _ = AccessoryBrand.objects.get_or_create(name=acc_brand_name)
            acc_color = None
            if acc_color_name:
                acc_color, _ = AccessoryColor.objects.get_or_create(name=acc_color_name)

            accessory, _ = Accessory.objects.get_or_create(
                name=acc_name, brand=acc_brand, model=acc_model, color=acc_color
            )
        else:
            device_name = DeviceName.objects.filter(id=request.POST.get('device_name_id')).first()
            if not device_name:
                messages.error(request, 'نام دستگاه را انتخاب کن.')
                return redirect('purchase_entry')
            device_type_id = request.POST.get('device_type_id') or None
            device_type = DeviceType.objects.filter(id=device_type_id).first() if device_type_id else None
            variant_id = request.POST.get('device_variant_id') or None
            device_variant = DeviceVariant.objects.filter(id=variant_id).first() if variant_id else None
            region_id = request.POST.get('device_region_id') or None
            device_region = DeviceRegion.objects.filter(id=region_id).first() if region_id else None

        # کالای دارای سریال — سریال می‌تونه بین چند واحد مشترک باشه (مثلاً یک کد برای همه دسته‌های سفید)،
        # پس تعداد به همون چیزی که واردشده می‌مونه و برای هر واحد یک ردیف InventoryItem جدا ساخته می‌شه.

        supplier = None
        if supplier_name:
            supplier, _ = Supplier.objects.get_or_create(name=supplier_name)

        # دریافت‌کننده: فقط ادمین می‌تواند شخص دیگری غیر از خودش انتخاب کند
        if is_admin:
            receiver_id = request.POST.get('receiver_id') or active_personnel.id
            receiver = Personnel.objects.filter(id=receiver_id).first() or active_personnel
        else:
            receiver = active_personnel

        # تاریخ/ساعت: پیش‌فرض سیستم، فقط ادمین می‌تواند تغییرش بدهد
        record_datetime = timezone.now()
        if is_admin and request.POST.get('override_datetime') == 'on':
            try:
                record_datetime = jalali_to_gregorian_datetime(
                    request.POST.get('j_year'),
                    request.POST.get('j_month'),
                    request.POST.get('j_day'),
                    request.POST.get('j_hour') or 0,
                    request.POST.get('j_minute') or 0,
                )
            except (TypeError, ValueError):
                messages.error(request, 'تاریخ واردشده معتبر نبود، تاریخ سیستم به‌جاش استفاده شد.')
                record_datetime = timezone.now()

        purchase = PurchaseRecord.objects.create(
            serial_number=serial_number,
            device_name=device_name,
            device_type=device_type,
            device_variant=device_variant,
            device_region=device_region,
            accessory=accessory,
            quantity=quantity,
            unit_price=unit_price,
            remaining_quantity=0 if serial_number else quantity,
            supplier=supplier,
            receiver=receiver,
            created_at=record_datetime,
        )

        if serial_number:
            for _ in range(quantity):
                InventoryItem.objects.create(
                    device_name=device_name,
                    device_type=device_type,
                    accessory=accessory,
                    serial_number=serial_number,
                    purchase=purchase,
                    unit_cost=unit_price,
                    status='in_stock',
                )
        else:
            stock, _ = StockLevel.objects.get_or_create(
                device_name=device_name, device_type=device_type, accessory=accessory, defaults={'quantity': 0}
            )
            stock.quantity += quantity
            stock.save()

        if supplier:
            if is_capital_supplier_name(supplier.name):
                capital_ledger_add(purchase.total_price, f"خرید #{purchase.id} - {supplier.name}")
            else:
                party_ledger_add(supplier.name, -purchase.total_price, f"خرید #{purchase.id}", kind='supplier')

        messages.success(request, 'خرید با موفقیت ثبت شد و به انبار اضافه شد.')
        return redirect('purchase_entry')

    recent_purchases = PurchaseRecord.objects.select_related(
        'device_name', 'device_type', 'device_variant', 'device_region', 'accessory', 'receiver', 'supplier'
    ).all()[:50]

    return render(request, 'purchase_entry.html', {
        'device_names': device_names,
        'device_types_json': json.dumps(device_types_map, ensure_ascii=False),
        'device_variants_json': json.dumps(device_variants_map, ensure_ascii=False),
        'devices_with_region_json': json.dumps(devices_with_region),
        'device_regions': device_regions,
        'suppliers': suppliers,
        'accessory_brands': accessory_brands,
        'accessory_colors': accessory_colors,
        'accessory_names': accessory_names,
        'is_admin': is_admin,
        'all_personnel_active': all_personnel_active,
        'now_jalali': now_jalali_parts(),
        'recent_purchases': recent_purchases,
    })


# ---------- ابطال و ویرایش رکوردها (از قسمت گزارش) ----------

def _active_personnel(request):
    active_id = request.session.get('active_personnel_id')
    return Personnel.objects.filter(id=active_id, is_active=True).first() if active_id else None


def _redirect_with_qs(report_type, request):
    qs = request.POST.get('return_qs') or request.GET.urlencode()
    url = reverse('report_detail', args=[report_type])
    return redirect(f"{url}?{qs}" if qs else url)


@require_POST
@require_permission('can_void_or_edit')
def purchase_void(request, purchase_id):
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return _redirect_with_qs('purchases', request)

    purchase = PurchaseRecord.objects.filter(id=purchase_id).first()
    if not purchase:
        messages.error(request, 'این خرید پیدا نشد.')
        return _redirect_with_qs('purchases', request)
    if purchase.is_voided:
        messages.info(request, 'این خرید قبلاً ابطال شده بود.')
        return _redirect_with_qs('purchases', request)

    with transaction.atomic():
        if purchase.serial_number:
            items_qs = InventoryItem.objects.filter(purchase=purchase)
            if items_qs.filter(status='sold').exists():
                messages.error(request, 'بخشی از واحدهای این خرید قبلاً فروخته شده — اول باید فروش‌های مرتبط را ابطال کنی.')
                return _redirect_with_qs('purchases', request)
            items_qs.delete()
        else:
            if purchase.remaining_quantity < purchase.quantity:
                messages.error(request, 'بخشی از این خرید قبلاً طبق FIFO مصرف (فروخته) شده — اول فروش‌های مرتبط را ابطال کن.')
                return _redirect_with_qs('purchases', request)
            stock = StockLevel.objects.filter(
                device_name=purchase.device_name, device_type=purchase.device_type, accessory=purchase.accessory
            ).first()
            if stock:
                stock.quantity = max(0, stock.quantity - purchase.quantity)
                stock.save(update_fields=['quantity'])
            purchase.remaining_quantity = 0
        purchase.is_voided = True
        purchase.voided_at = timezone.now()
        purchase.save(update_fields=['is_voided', 'voided_at', 'remaining_quantity'])
        if purchase.supplier:
            if is_capital_supplier_name(purchase.supplier.name):
                capital_ledger_add(-purchase.total_price, f"ابطال خرید #{purchase.id} - {purchase.supplier.name}")
            else:
                party_ledger_add(purchase.supplier.name, purchase.total_price, f"ابطال خرید #{purchase.id}", kind='supplier')

    messages.success(request, 'خرید ابطال شد و موجودی اصلاح شد.')
    return _redirect_with_qs('purchases', request)


@require_permission('can_void_or_edit')
def purchase_edit(request, purchase_id):
    purchase = PurchaseRecord.objects.select_related('device_name', 'device_type', 'accessory', 'supplier').filter(id=purchase_id).first()
    if not purchase:
        messages.error(request, 'این خرید پیدا نشد.')
        return redirect('reports_home')
    if purchase.is_voided:
        messages.error(request, 'خرید ابطال‌شده قابل ویرایش نیست.')
        return redirect(reverse('report_detail', args=['purchases']))

    return_qs = request.GET.get('return_qs', '') or request.POST.get('return_qs', '')

    if request.method == 'POST':
        if not _active_personnel(request):
            messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
            return redirect(request.get_full_path())

        unit_price_raw = request.POST.get('unit_price') or '0'
        unit_price = int(re.sub(r'[^\d]', '', unit_price_raw) or '0')
        supplier_name = request.POST.get('supplier_name', '').strip()
        old_total = purchase.total_price
        old_supplier = purchase.supplier

        with transaction.atomic():
            try:
                new_quantity = max(1, int(request.POST.get('quantity') or purchase.quantity))
            except ValueError:
                new_quantity = purchase.quantity

            if purchase.serial_number:
                items_qs = InventoryItem.objects.filter(purchase=purchase)
                current_count = items_qs.count()
                delta = new_quantity - current_count
                if delta > 0:
                    for _ in range(delta):
                        InventoryItem.objects.create(
                            device_name=purchase.device_name, device_type=purchase.device_type,
                            accessory=purchase.accessory, serial_number=purchase.serial_number,
                            purchase=purchase, unit_cost=unit_price, status='in_stock',
                        )
                elif delta < 0:
                    removable = list(items_qs.filter(status='in_stock')[:(-delta)])
                    if len(removable) < -delta:
                        messages.error(request, 'به‌اندازه‌ی کافی واحد «در انبار» از این خرید نیست تا تعداد کم بشه — بعضی از واحدها قبلاً فروخته شده.')
                        return redirect(request.get_full_path())
                    for it in removable:
                        it.delete()
                InventoryItem.objects.filter(purchase=purchase).update(unit_cost=unit_price)
                purchase.quantity = new_quantity
            else:
                delta = new_quantity - purchase.quantity
                if delta < 0 and purchase.remaining_quantity + delta < 0:
                    messages.error(request, 'نمی‌شه تعداد رو کمتر از مقداری که طبق FIFO فروخته شده کاهش داد.')
                    return redirect(request.get_full_path())
                if delta != 0:
                    stock = StockLevel.objects.filter(
                        device_name=purchase.device_name, device_type=purchase.device_type, accessory=purchase.accessory
                    ).first()
                    if stock:
                        stock.quantity = max(0, stock.quantity + delta)
                        stock.save(update_fields=['quantity'])
                purchase.remaining_quantity = purchase.remaining_quantity + delta
                purchase.quantity = new_quantity

            purchase.unit_price = unit_price
            if supplier_name:
                supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
                purchase.supplier = supplier
            else:
                purchase.supplier = None
            purchase.save()

            # حساب تأمین‌کننده رو با تغییرات هماهنگ می‌کنیم: اول اثر قبلی رو برمی‌گردونیم، بعد اثر جدید رو ثبت می‌کنیم
            new_total = purchase.total_price
            if old_supplier:
                if is_capital_supplier_name(old_supplier.name):
                    capital_ledger_add(-old_total, f"ویرایش خرید #{purchase.id} (برگشت مبلغ قبلی) - {old_supplier.name}")
                else:
                    party_ledger_add(old_supplier.name, old_total, f"ویرایش خرید #{purchase.id} (برگشت مبلغ قبلی)", kind='supplier')
            if purchase.supplier:
                if is_capital_supplier_name(purchase.supplier.name):
                    capital_ledger_add(new_total, f"ویرایش خرید #{purchase.id} - {purchase.supplier.name}")
                else:
                    party_ledger_add(purchase.supplier.name, -new_total, f"ویرایش خرید #{purchase.id}", kind='supplier')

        messages.success(request, 'خرید ویرایش شد.')
        url = reverse('report_detail', args=['purchases'])
        return redirect(f"{url}?{return_qs}" if return_qs else url)

    return render(request, 'purchase_edit.html', {'purchase': purchase, 'return_qs': return_qs})


@require_POST
@require_permission('can_void_or_edit')
def sale_void(request, sale_id):
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return _redirect_with_qs('sales', request)

    sale = SaleRecord.objects.prefetch_related('items').filter(id=sale_id).first()
    if not sale:
        messages.error(request, 'این فاکتور پیدا نشد.')
        return _redirect_with_qs('sales', request)
    if sale.is_voided:
        messages.info(request, 'این فاکتور قبلاً ابطال شده بود.')
        return _redirect_with_qs('sales', request)

    with transaction.atomic():
        for item in sale.items.all():
            if item.serial_number:
                inv = InventoryItem.objects.filter(sale_line_item=item).first()
                if inv:
                    inv.status = 'in_stock'
                    inv.sale_line_item = None
                    inv.sold_at = None
                    inv.save(update_fields=['status', 'sale_line_item', 'sold_at'])
            else:
                stock, _ = StockLevel.objects.get_or_create(
                    device_name=item.device_name, device_type=item.device_type, accessory=item.accessory,
                    defaults={'quantity': 0}
                )
                stock.quantity += item.quantity
                stock.save(update_fields=['quantity'])
                restore_fifo_cost(item.device_name, item.device_type, item.accessory, item.quantity)
        sale.is_voided = True
        sale.voided_at = timezone.now()
        sale.save(update_fields=['is_voided', 'voided_at'])

        for payment in sale.payments.select_related('bank_account', 'party').all():
            if payment.payment_type == 'transfer' and payment.bank_account:
                payment.bank_account.balance -= payment.amount
                payment.bank_account.save(update_fields=['balance'])
            elif payment.payment_type == 'party_account' and payment.party:
                party_ledger_add(payment.party.name, -payment.amount, f"ابطال فاکتور #{sale.id}", kind=payment.party.kind)

    messages.success(request, 'فاکتور فروش ابطال شد و موجودی برگشت داده شد.')
    return _redirect_with_qs('sales', request)


@require_permission('can_void_or_edit')
def sale_edit(request, sale_id):
    sale = SaleRecord.objects.prefetch_related('items').filter(id=sale_id).first()
    if not sale:
        messages.error(request, 'این فاکتور پیدا نشد.')
        return redirect('reports_home')
    if sale.is_voided:
        messages.error(request, 'فاکتور ابطال‌شده قابل ویرایش نیست.')
        return redirect(reverse('report_detail', args=['sales']))

    return_qs = request.GET.get('return_qs', '') or request.POST.get('return_qs', '')

    if request.method == 'POST':
        if not _active_personnel(request):
            messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
            return redirect(request.get_full_path())

        sale.customer_name = request.POST.get('customer_name', '').strip()
        sale.customer_phone = request.POST.get('customer_phone', '').strip()
        sale.customer_national_id = request.POST.get('customer_national_id', '').strip()
        sale.save(update_fields=['customer_name', 'customer_phone', 'customer_national_id'])

        with transaction.atomic():
            for item in sale.items.all():
                price_raw = request.POST.get(f'item_price_{item.id}') or str(item.unit_price)
                item.unit_price = int(re.sub(r'[^\d]', '', price_raw) or item.unit_price)

                if not item.serial_number:
                    qty_raw = request.POST.get(f'item_qty_{item.id}') or str(item.quantity)
                    try:
                        new_qty = max(1, int(qty_raw))
                    except ValueError:
                        new_qty = item.quantity
                    delta = new_qty - item.quantity
                    if delta != 0:
                        stock, _ = StockLevel.objects.get_or_create(
                            device_name=item.device_name, device_type=item.device_type, accessory=item.accessory,
                            defaults={'quantity': 0}
                        )
                        # فروش بیشتر یعنی موجودی بیشتر کسر میشه؛ فروش کمتر یعنی برگشت به موجودی
                        stock.quantity = max(0, stock.quantity - delta)
                        stock.save(update_fields=['quantity'])
                        if delta > 0:
                            item.cost_amount += consume_fifo_cost(item.device_name, item.device_type, item.accessory, delta)
                        else:
                            restore_fifo_cost(item.device_name, item.device_type, item.accessory, -delta)
                            # هزینه‌ی واحد رو تناسبی کم می‌کنیم (چون دقیقاً معلوم نیست کدوم واحد برگشت خورده)
                            per_unit_cost = (item.cost_amount / item.quantity) if item.quantity else 0
                            item.cost_amount = max(0, round(item.cost_amount - per_unit_cost * (-delta)))
                    item.quantity = new_qty
                item.save(update_fields=['unit_price', 'quantity', 'cost_amount'])

        messages.success(request, 'فاکتور ویرایش شد.')
        url = reverse('report_detail', args=['sales'])
        return redirect(f"{url}?{return_qs}" if return_qs else url)

    return render(request, 'sale_edit.html', {'sale': sale, 'return_qs': return_qs})


@require_POST
@require_permission('can_void_or_edit')
def install_void(request, order_id):
    if not _active_personnel(request):
        messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
        return _redirect_with_qs('installs', request)

    order = GameInstallOrder.objects.filter(id=order_id).first()
    if not order:
        messages.error(request, 'این سفارش پیدا نشد.')
        return _redirect_with_qs('installs', request)
    if order.is_voided:
        messages.info(request, 'این سفارش قبلاً ابطال شده بود.')
        return _redirect_with_qs('installs', request)

    order.is_voided = True
    order.voided_at = timezone.now()
    order.save(update_fields=['is_voided', 'voided_at'])
    if order.installer and order.installer_fee:
        party_ledger_add(order.installer.name, order.installer_fee, f"ابطال سفارش نصب #{order.id}", kind='installer')
    messages.success(request, 'سفارش نصب ابطال شد.')
    return _redirect_with_qs('installs', request)


@require_permission('can_void_or_edit')
def install_edit(request, order_id):
    order = GameInstallOrder.objects.select_related('device_name', 'installer').filter(id=order_id).first()
    if not order:
        messages.error(request, 'این سفارش پیدا نشد.')
        return redirect('reports_home')
    if order.is_voided:
        messages.error(request, 'سفارش ابطال‌شده قابل ویرایش نیست.')
        return redirect(reverse('report_detail', args=['installs']))

    installers = Installer.objects.filter(is_active=True)
    return_qs = request.GET.get('return_qs', '') or request.POST.get('return_qs', '')

    if request.method == 'POST':
        if not _active_personnel(request):
            messages.error(request, 'اول باید «کاربر فعال» را از بالای صفحه انتخاب کنی.')
            return redirect(request.get_full_path())

        order.customer_name = request.POST.get('customer_name', '').strip()
        cost_raw = request.POST.get('install_cost') or '0'
        order.install_cost = int(re.sub(r'[^\d]', '', cost_raw) or '0')
        installer_id = request.POST.get('installer_id') or ''
        order.installer = Installer.objects.filter(id=installer_id).first() if installer_id else None
        order.delivered = request.POST.get('delivered') == 'on'
        if order.delivered and not order.delivered_at:
            order.delivered_at = timezone.now()
        if not order.delivered:
            order.delivered_at = None
        # مرحله رو هم با تیک «تحویل» هماهنگ نگه می‌داریم
        if order.delivered:
            order.stage = GameInstallOrder.STAGE_DELIVERED
        elif order.stage == GameInstallOrder.STAGE_DELIVERED:
            order.stage = GameInstallOrder.STAGE_RETURNED if order.return_at else (
                GameInstallOrder.STAGE_SENT if order.installer else GameInstallOrder.STAGE_ORDERED
            )
        order.save()

        messages.success(request, 'سفارش نصب ویرایش شد.')
        url = reverse('report_detail', args=['installs'])
        return redirect(f"{url}?{return_qs}" if return_qs else url)

    return render(request, 'install_edit.html', {'order': order, 'installers': installers, 'return_qs': return_qs})
