from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from .jalali_utils import to_jalali_string


class GameTitle(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=100, blank=True, default="")
    source_url = models.URLField(blank=True, default="")
    platforms = models.ManyToManyField(
        'DeviceName', through='GamePlatformAvailability', verbose_name="پلتفرم‌های سازگار",
        blank=True, related_name="game_titles"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Game Title"
        verbose_name_plural = "Game Titles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class GamePlatformAvailability(models.Model):
    """در دسترس بودن یک بازی روی یک دستگاه، به‌صورت لایسنس یا کپی (یا هر دو، با دو ردیف جدا)."""
    LICENSE_CHOICES = [
        ("license", "لایسنس"),
        ("copy", "کپی"),
    ]
    game = models.ForeignKey(GameTitle, verbose_name="بازی", on_delete=models.CASCADE, related_name="availabilities")
    device_name = models.ForeignKey('DeviceName', verbose_name="دستگاه", on_delete=models.CASCADE, related_name="game_availabilities")
    license_type = models.CharField("نوع", max_length=10, choices=LICENSE_CHOICES)

    class Meta:
        verbose_name = "دسترسی بازی"
        verbose_name_plural = "دسترسی‌های بازی"
        unique_together = [("game", "device_name", "license_type")]

    def __str__(self):
        return f"{self.game} - {self.device_name} - {self.get_license_type_display()}"


class Personnel(models.Model):
    """پرسنل فروشگاه — برای ورود به سیستم و ثبت فروشنده/دریافت‌کننده در فرم‌ها. سطح دسترسی هرکس جداگانه قابل‌تنظیمه."""
    name = models.CharField("نام", max_length=150, unique=True)
    password_hash = models.CharField("رمز عبور (هش‌شده)", max_length=255, blank=True, default="")
    is_admin = models.BooleanField("دسترسی مدیر (همه‌چیز)", default=False)
    is_active = models.BooleanField("فعال", default=True)

    can_purchase = models.BooleanField("دسترسی به ثبت خرید", default=True)
    can_sale = models.BooleanField("دسترسی به ثبت فروش", default=True)
    can_install = models.BooleanField("دسترسی به نصب بازی", default=True)
    can_view_reports = models.BooleanField("دسترسی به گزارش‌ها", default=False)
    can_manage_parties = models.BooleanField("دسترسی به حساب اشخاص", default=False)
    can_manage_expenses = models.BooleanField("دسترسی به ثبت هزینه", default=False)
    can_void_or_edit = models.BooleanField("دسترسی به ویرایش/ابطال رکوردها", default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پرسنل"
        verbose_name_plural = "پرسنل"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        if not self.password_hash:
            return False
        return check_password(raw_password, self.password_hash)

    def has_perm(self, perm_name):
        """is_admin همه‌چیز رو می‌بینه؛ در غیر این صورت فلگ مشخص همون شخص چک می‌شه."""
        if self.is_admin:
            return True
        return getattr(self, perm_name, False)


class Product(models.Model):
    """کالا یا دستگاهی که در فرم فروش فعلاً استفاده می‌شود (خرید اکنون از DeviceName/DeviceType استفاده می‌کند)."""
    CATEGORY_CHOICES = [
        ("console", "کنسول"),
        ("controller", "کنترلر"),
        ("accessory", "لوازم جانبی"),
        ("game", "بازی"),
        ("digital_account", "اکانت دیجیتال"),
        ("other", "سایر"),
    ]
    name = models.CharField("نام کالا", max_length=200)
    category = models.CharField("دسته‌بندی", max_length=30, choices=CATEGORY_CHOICES, default="console")
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کالا"
        verbose_name_plural = "کالاها"
        ordering = ["category", "name"]
        unique_together = [("name", "category")]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ProductGroup(models.Model):
    """گروه اصلی محصول — مثل کنسول، دسته بازی، جانبی، بازی، اکانت دیجیتال."""
    name = models.CharField("نام گروه", max_length=100, unique=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "گروه محصول"
        verbose_name_plural = "گروه‌های محصول"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class DeviceName(models.Model):
    """نام دستگاه (زیرگروه)، مثل PS5، PS4، Xbox Series، PSP و ..."""
    group = models.ForeignKey(
        ProductGroup, verbose_name="گروه", on_delete=models.SET_NULL, null=True, blank=True, related_name="device_names"
    )
    name = models.CharField("نام دستگاه", max_length=100, unique=True)
    has_region = models.BooleanField("دارای ریژن", default=False)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نام دستگاه"
        verbose_name_plural = "نام‌های دستگاه"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class DeviceType(models.Model):
    """نوع دستگاه، وابسته به نام دستگاه — مثل درایو، دیجیتال، پرو و ..."""
    CONDITION_CHOICES = [
        ("new", "نو"),
        ("used", "استوک"),
    ]
    device_name = models.ForeignKey(
        DeviceName, verbose_name="نام دستگاه", on_delete=models.CASCADE, related_name="types"
    )
    name = models.CharField("نوع دستگاه", max_length=100)
    brand = models.ForeignKey(
        'AccessoryBrand', verbose_name="برند", on_delete=models.SET_NULL, null=True, blank=True, related_name="device_types"
    )
    color = models.ForeignKey(
        'AccessoryColor', verbose_name="رنگ", on_delete=models.SET_NULL, null=True, blank=True, related_name="device_types"
    )
    condition = models.CharField("وضعیت", max_length=10, choices=CONDITION_CHOICES, default="new")
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "نوع دستگاه"
        verbose_name_plural = "نوع‌های دستگاه"
        ordering = ["device_name__order", "order", "name"]
        unique_together = [("device_name", "name")]

    def __str__(self):
        return f"{self.device_name} - {self.name}"


class Supplier(models.Model):
    """فروشنده/تأمین‌کننده — لیست به‌مرور با تایپ نام‌های جدید کامل می‌شود."""
    name = models.CharField("نام تأمین‌کننده", max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تأمین‌کننده"
        verbose_name_plural = "تأمین‌کنندگان"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseRecord(models.Model):
    """رکورد خرید کالا از تأمین‌کننده / ورود کالا به انبار. یا دستگاه (device_name) یا کالای جانبی (accessory) پر می‌شود."""
    serial_number = models.CharField("شماره سریال", max_length=150, blank=True, default="")
    device_name = models.ForeignKey(
        DeviceName, verbose_name="نام دستگاه", on_delete=models.PROTECT,
        related_name="purchases", null=True, blank=True
    )
    device_type = models.ForeignKey(
        DeviceType, verbose_name="نوع دستگاه", on_delete=models.PROTECT,
        related_name="purchases", null=True, blank=True
    )
    device_variant = models.ForeignKey(
        'DeviceVariant', verbose_name="شماره سری", on_delete=models.SET_NULL,
        related_name="purchases", null=True, blank=True
    )
    device_region = models.ForeignKey(
        'DeviceRegion', verbose_name="ریژن", on_delete=models.SET_NULL,
        related_name="purchases", null=True, blank=True
    )
    accessory = models.ForeignKey(
        'Accessory', verbose_name="کالای جانبی", on_delete=models.PROTECT,
        related_name="purchases", null=True, blank=True
    )
    quantity = models.PositiveIntegerField("تعداد", default=1)
    unit_price = models.PositiveBigIntegerField("قیمت واحد (تومان)", default=0)
    remaining_quantity = models.PositiveIntegerField("مانده برای FIFO (فقط کالای فله)", default=0)
    supplier = models.ForeignKey(
        Supplier, verbose_name="تأمین‌کننده", on_delete=models.SET_NULL,
        related_name="purchases", null=True, blank=True
    )
    receiver = models.ForeignKey(
        Personnel, verbose_name="دریافت‌کننده", on_delete=models.PROTECT, related_name="purchases_received"
    )
    created_at = models.DateTimeField("تاریخ و ساعت ثبت", default=timezone.now)
    is_voided = models.BooleanField("ابطال‌شده", default=False)
    voided_at = models.DateTimeField("تاریخ ابطال", null=True, blank=True)

    class Meta:
        verbose_name = "رکورد خرید"
        verbose_name_plural = "رکوردهای خرید"
        ordering = ["-created_at"]

    def __str__(self):
        if self.accessory:
            return f"{self.accessory} × {self.quantity}"
        type_part = f" {self.device_type.name}" if self.device_type else ""
        return f"{self.device_name}{type_part} × {self.quantity} - {self.serial_number or 'بدون سریال'}"

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    @property
    def jalali_datetime(self):
        return to_jalali_string(self.created_at)



class SaleTerm(models.Model):
    """شرایط فروش قابل‌انتخاب روی فاکتور — مثل «۱۰ روز مهلت تست»."""
    text = models.CharField("متن شرط", max_length=200, unique=True)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "شرط فروش"
        verbose_name_plural = "شرایط فروش"
        ordering = ["order", "text"]

    def __str__(self):
        return self.text


class BankAccount(models.Model):
    """حساب‌های بانکی/کارتخوان فروشگاه، برای انتخاب در پرداخت‌های انتقالی."""
    label = models.CharField("عنوان حساب", max_length=150, unique=True)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)
    balance = models.BigIntegerField("موجودی (تومان)", default=0)

    class Meta:
        verbose_name = "حساب بانکی"
        verbose_name_plural = "حساب‌های بانکی"
        ordering = ["order", "label"]

    def __str__(self):
        return self.label


class Party(models.Model):
    """حساب اشخاص — تأمین‌کننده، نصاب، مشتری نسیه یا هر شخص دیگری که با فروشگاه حساب دارد.
    balance: مثبت یعنی این شخص به فروشگاه بدهکاره، منفی یعنی فروشگاه به این شخص بدهکاره (بستانکار)."""
    KIND_CHOICES = [
        ("supplier", "تأمین‌کننده"),
        ("installer", "نصاب"),
        ("customer", "مشتری"),
        ("other", "سایر"),
    ]
    name = models.CharField("نام", max_length=200, unique=True)
    kind = models.CharField("نوع", max_length=20, choices=KIND_CHOICES, default="other")
    balance = models.BigIntegerField("مانده حساب (تومان)", default=0)
    phone = models.CharField("شماره تماس", max_length=20, blank=True, default="")
    sms_notifications_enabled = models.BooleanField("ارسال پیامک برای تراکنش‌های این شخص", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "شخص (حساب اشخاص)"
        verbose_name_plural = "اشخاص (حساب اشخاص)"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def status_label(self):
        if self.balance > 0:
            return "بدهکار"
        if self.balance < 0:
            return "بستانکار"
        return "تسویه"


class PartyLedgerEntry(models.Model):
    """یک ردیف از تراکنش‌های حساب یک شخص. amount مثبت=بدهکارتر شدن شخص، منفی=بستانکارتر شدن شخص."""
    party = models.ForeignKey(Party, verbose_name="شخص", on_delete=models.CASCADE, related_name="entries")
    amount = models.BigIntegerField("مبلغ (تومان)")
    balance_after = models.BigIntegerField("مانده پس از این رویداد", default=0)
    description = models.CharField("شرح", max_length=255, blank=True, default="")
    created_at = models.DateTimeField("تاریخ و ساعت", default=timezone.now)

    class Meta:
        verbose_name = "تراکنش حساب شخص"
        verbose_name_plural = "تراکنش‌های حساب اشخاص"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.party.name} - {self.amount}"

    @property
    def jalali_datetime(self):
        return to_jalali_string(self.created_at)


class Expense(models.Model):
    """هزینه‌های جاری فروشگاه: حقوق، اجاره، قبض، هزینه عمومی، هزینه تعمیر و... . عنوان و زیرعنوان آزادانه قابل افزایش‌اند."""
    PAYMENT_METHOD_CHOICES = [
        ("bank", "بانک"),
        ("party", "حساب اشخاص (بستانکار)"),
    ]
    category = models.CharField("عنوان هزینه", max_length=100)
    subcategory = models.CharField("زیرعنوان (مثلاً نوع قبض)", max_length=100, blank=True, default="")
    personnel = models.ForeignKey(
        Personnel, verbose_name="پرسنل (برای حقوق)", on_delete=models.SET_NULL,
        related_name="salary_expenses", null=True, blank=True
    )
    salary_month = models.CharField("ماه حقوق (شمسی)", max_length=50, blank=True, default="")
    amount = models.BigIntegerField("مبلغ (تومان)")
    note = models.CharField("توضیحات", max_length=255, blank=True, default="")
    payment_method = models.CharField("محل پرداخت", max_length=10, choices=PAYMENT_METHOD_CHOICES)
    bank_account = models.ForeignKey(
        BankAccount, verbose_name="حساب بانکی", on_delete=models.SET_NULL,
        related_name="expenses", null=True, blank=True
    )
    party = models.ForeignKey(
        Party, verbose_name="شخص (بستانکار)", on_delete=models.SET_NULL,
        related_name="expenses", null=True, blank=True
    )
    created_by = models.ForeignKey(
        Personnel, verbose_name="ثبت‌کننده", on_delete=models.PROTECT, related_name="expenses_created"
    )
    created_at = models.DateTimeField("تاریخ و ساعت ثبت", default=timezone.now)
    is_voided = models.BooleanField("ابطال‌شده", default=False)
    voided_at = models.DateTimeField("تاریخ ابطال", null=True, blank=True)

    class Meta:
        verbose_name = "هزینه"
        verbose_name_plural = "هزینه‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.category} - {self.amount}"

    @property
    def jalali_datetime(self):
        return to_jalali_string(self.created_at)


class SaleRecord(models.Model):
    """سربرگ فاکتور فروش — اطلاعات مشتری، شرایط، فروشنده و تاریخ. اقلام و پرداخت‌ها جدا و مرتبط‌اند."""
    customer_name = models.CharField("نام مشتری", max_length=200, blank=True, default="")
    customer_national_id = models.CharField("کد ملی مشتری", max_length=20, blank=True, default="")
    customer_phone = models.CharField("شماره تماس مشتری", max_length=20, blank=True, default="")

    terms = models.ManyToManyField(SaleTerm, verbose_name="شرایط فروش", blank=True, related_name="sales")
    change = models.BooleanField("تعویض (Change)", default=False)

    seller = models.ForeignKey(
        Personnel, verbose_name="فروشنده", on_delete=models.PROTECT, related_name="sales_made"
    )
    created_at = models.DateTimeField("تاریخ و ساعت ثبت", default=timezone.now)
    is_voided = models.BooleanField("ابطال‌شده", default=False)
    voided_at = models.DateTimeField("تاریخ ابطال", null=True, blank=True)

    class Meta:
        verbose_name = "فاکتور فروش"
        verbose_name_plural = "فاکتورهای فروش"
        ordering = ["-created_at"]

    def __str__(self):
        return f"فاکتور #{self.id} - {self.customer_name or 'بدون نام'}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def balance(self):
        return self.total_price - self.total_paid

    @property
    def jalali_datetime(self):
        return to_jalali_string(self.created_at)


class SaleLineItem(models.Model):
    """یک ردیف از اقلام فاکتور فروش. یا دستگاه (device_name) یا کالای جانبی (accessory) پر می‌شود."""
    sale = models.ForeignKey(SaleRecord, verbose_name="فاکتور", on_delete=models.CASCADE, related_name="items")
    device_name = models.ForeignKey(
        DeviceName, verbose_name="نام دستگاه", on_delete=models.PROTECT,
        related_name="sale_items", null=True, blank=True
    )
    device_type = models.ForeignKey(
        DeviceType, verbose_name="نوع دستگاه", on_delete=models.PROTECT,
        related_name="sale_items", null=True, blank=True
    )
    device_variant = models.ForeignKey(
        'DeviceVariant', verbose_name="شماره سری", on_delete=models.SET_NULL,
        related_name="sale_items", null=True, blank=True
    )
    device_region = models.ForeignKey(
        'DeviceRegion', verbose_name="ریژن", on_delete=models.SET_NULL,
        related_name="sale_items", null=True, blank=True
    )
    accessory = models.ForeignKey(
        'Accessory', verbose_name="کالای جانبی", on_delete=models.PROTECT,
        related_name="sale_items", null=True, blank=True
    )
    serial_number = models.CharField("شماره سریال", max_length=150, blank=True, default="")
    quantity = models.PositiveIntegerField("تعداد", default=1)
    unit_price = models.PositiveBigIntegerField("قیمت واحد (تومان)", default=0)
    cost_amount = models.BigIntegerField("هزینه تمام‌شده (سریال‌محور یا FIFO)", default=0)

    class Meta:
        verbose_name = "ردیف فاکتور فروش"
        verbose_name_plural = "ردیف‌های فاکتور فروش"

    def __str__(self):
        if self.accessory:
            return f"{self.accessory} × {self.quantity}"
        type_part = f" {self.device_type.name}" if self.device_type else ""
        return f"{self.device_name}{type_part} × {self.quantity}"

    @property
    def variant_region_code(self):
        """کد ترکیبی سری+ریژن، مثلاً «۲۱» + «۱۶» = «۲۱۱۶»."""
        parts = []
        if self.device_variant:
            parts.append(self.device_variant.code)
        if self.device_region:
            parts.append(self.device_region.code)
        return "".join(parts)

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    @property
    def profit(self):
        return self.total_price - self.cost_amount

class Payment(models.Model):
    """یک روش پرداخت برای یک فاکتور فروش (هر فاکتور می‌تواند چند روش پرداخت داشته باشد)."""
    PAYMENT_TYPE_CHOICES = [
        ("pos", "پوز (کارتخوان)"),
        ("transfer", "انتقال بانکی"),
        ("party_account", "حساب اشخاص (نسیه)"),
    ]
    sale = models.ForeignKey(SaleRecord, verbose_name="فاکتور", on_delete=models.CASCADE, related_name="payments")
    payment_type = models.CharField("نوع پرداخت", max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.PositiveBigIntegerField("مبلغ (تومان)", default=0)
    tracking_number = models.CharField("شماره پیگیری", max_length=100, blank=True, default="")
    bank_account = models.ForeignKey(
        BankAccount, verbose_name="حساب مقصد", on_delete=models.SET_NULL,
        related_name="payments", null=True, blank=True
    )
    party = models.ForeignKey(
        'Party', verbose_name="شخص (حساب اشخاص)", on_delete=models.SET_NULL,
        related_name="sale_payments", null=True, blank=True
    )

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount}"


class Installer(models.Model):
    """نصاب — کسی که کار نصب بازی را انجام می‌دهد. لیست از تنظیمات قابل‌مدیریت است."""
    name = models.CharField("نام نصاب", max_length=150, unique=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نصاب"
        verbose_name_plural = "نصاب‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class GameInstallOrder(models.Model):
    """سفارش نصب بازی — یک روند ۴مرحله‌ای: سفارش مشتری → ارسال برای نصاب → بازگشت از نصب → تحویل مشتری."""
    STAGE_ORDERED = "ordered"
    STAGE_SENT = "sent_to_installer"
    STAGE_RETURNED = "returned"
    STAGE_DELIVERED = "delivered"
    STAGE_CHOICES = [
        (STAGE_ORDERED, "۱. سفارش مشتری"),
        (STAGE_SENT, "۲. ارسال برای نصاب"),
        (STAGE_RETURNED, "۳. بازگشت از نصب"),
        (STAGE_DELIVERED, "۴. تحویل مشتری"),
    ]
    stage = models.CharField("مرحله", max_length=20, choices=STAGE_CHOICES, default=STAGE_ORDERED)
    is_paid = models.BooleanField("پرداخت شده", default=False)

    # کادر مشتری
    customer_name = models.CharField("نام مشتری", max_length=200, blank=True, default="")
    customer_phone = models.CharField("شماره تماس مشتری", max_length=30, blank=True, default="")
    serial_number = models.CharField("شماره سریال دستگاه", max_length=150, blank=True, default="")
    device_name = models.ForeignKey(
        DeviceName, verbose_name="نام دستگاه", on_delete=models.PROTECT, related_name="install_orders"
    )
    LICENSE_CHOICES = [
        ("license", "لایسنس"),
        ("copy", "کپی"),
    ]
    license_type = models.CharField("لایسنس / کپی", max_length=10, choices=LICENSE_CHOICES, default="copy")
    receiver = models.ForeignKey(
        Personnel, verbose_name="کاربر", on_delete=models.PROTECT, related_name="install_orders_received"
    )
    order_datetime = models.DateTimeField("تاریخ و ساعت سفارش", default=timezone.now)

    game_slot_1 = models.ForeignKey(GameTitle, verbose_name="بازی ۱", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_2 = models.ForeignKey(GameTitle, verbose_name="بازی ۲", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_3 = models.ForeignKey(GameTitle, verbose_name="بازی ۳", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_4 = models.ForeignKey(GameTitle, verbose_name="بازی ۴", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_5 = models.ForeignKey(GameTitle, verbose_name="بازی ۵", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_6 = models.ForeignKey(GameTitle, verbose_name="بازی ۶", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_7 = models.ForeignKey(GameTitle, verbose_name="بازی ۷", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_8 = models.ForeignKey(GameTitle, verbose_name="بازی ۸", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_9 = models.ForeignKey(GameTitle, verbose_name="بازی ۹", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    game_slot_10 = models.ForeignKey(GameTitle, verbose_name="بازی ۱۰", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    # کادر روند نصب
    referred_at = models.DateTimeField("تاریخ و ساعت ارجاع به نصاب", default=timezone.now)
    installer = models.ForeignKey(
        Installer, verbose_name="نصاب", on_delete=models.SET_NULL, null=True, blank=True, related_name="install_orders"
    )
    return_at = models.DateTimeField("تاریخ و ساعت بازگشت", null=True, blank=True)
    install_cost = models.PositiveBigIntegerField("هزینه نصب (تومان)", default=0)
    delivered = models.BooleanField("تحویل داده شد", default=False)
    delivered_at = models.DateTimeField("تاریخ و ساعت تحویل", null=True, blank=True)
    installer_fee = models.BigIntegerField("دستمزد نصاب (تومان)", null=True, blank=True)
    is_voided = models.BooleanField("ابطال‌شده", default=False)
    voided_at = models.DateTimeField("تاریخ ابطال", null=True, blank=True)

    class Meta:
        verbose_name = "سفارش نصب بازی"
        verbose_name_plural = "سفارش‌های نصب بازی"
        ordering = ["-order_datetime"]

    def __str__(self):
        return f"نصب #{self.id} - {self.customer_name or 'بدون نام'} ({self.device_name})"

    @property
    def games(self):
        return [g for g in [
            self.game_slot_1, self.game_slot_2, self.game_slot_3, self.game_slot_4, self.game_slot_5,
            self.game_slot_6, self.game_slot_7, self.game_slot_8, self.game_slot_9, self.game_slot_10,
        ] if g]

    @property
    def stage_number(self):
        return {self.STAGE_ORDERED: 1, self.STAGE_SENT: 2, self.STAGE_RETURNED: 3, self.STAGE_DELIVERED: 4}.get(self.stage, 1)

    @property
    def order_jalali(self):
        return to_jalali_string(self.order_datetime)

    @property
    def referred_jalali(self):
        return to_jalali_string(self.referred_at)

    @property
    def return_jalali(self):
        return to_jalali_string(self.return_at)

    @property
    def delivered_jalali(self):
        return to_jalali_string(self.delivered_at)


class StockLevel(models.Model):
    """موجودی تجمیعی برای کالاهای بدون سریال (فله‌ای) — بر اساس نام/نوع دستگاه یا کالای جانبی."""
    device_name = models.ForeignKey(DeviceName, verbose_name="نام دستگاه", on_delete=models.CASCADE, related_name="stock_levels", null=True, blank=True)
    device_type = models.ForeignKey(DeviceType, verbose_name="نوع دستگاه", on_delete=models.CASCADE, related_name="stock_levels", null=True, blank=True)
    accessory = models.ForeignKey('Accessory', verbose_name="کالای جانبی", on_delete=models.CASCADE, related_name="stock_levels", null=True, blank=True)
    quantity = models.IntegerField("موجودی", default=0)

    class Meta:
        verbose_name = "موجودی (فله‌ای)"
        verbose_name_plural = "موجودی‌های فله‌ای"
        unique_together = [("device_name", "device_type", "accessory")]

    def __str__(self):
        if self.accessory:
            return f"{self.accessory}: {self.quantity}"
        type_part = f" {self.device_type.name}" if self.device_type else ""
        return f"{self.device_name}{type_part}: {self.quantity}"


class InventoryItem(models.Model):
    """یک واحد فیزیکی موجودی با سریال مشخص — از خرید وارد می‌شود، با اسکن سریال در فروش خارج می‌شود."""
    STATUS_CHOICES = [
        ("in_stock", "در انبار"),
        ("sold", "فروخته‌شده"),
    ]
    device_name = models.ForeignKey(DeviceName, verbose_name="نام دستگاه", on_delete=models.PROTECT, related_name="inventory_items", null=True, blank=True)
    device_type = models.ForeignKey(DeviceType, verbose_name="نوع دستگاه", on_delete=models.PROTECT, related_name="inventory_items", null=True, blank=True)
    accessory = models.ForeignKey('Accessory', verbose_name="کالای جانبی", on_delete=models.PROTECT, related_name="inventory_items", null=True, blank=True)
    serial_number = models.CharField("شماره سریال / بارکد", max_length=150, blank=True, default="", db_index=True)
    purchase = models.ForeignKey(
        PurchaseRecord, verbose_name="از خرید", on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_items"
    )
    unit_cost = models.PositiveBigIntegerField("قیمت خرید (تومان)", default=0)
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default="in_stock")
    sale_line_item = models.OneToOneField(
        SaleLineItem, verbose_name="ردیف فروش", on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_item"
    )
    created_at = models.DateTimeField("تاریخ ورود به انبار", auto_now_add=True)
    sold_at = models.DateTimeField("تاریخ فروش", null=True, blank=True)

    class Meta:
        verbose_name = "واحد موجودی"
        verbose_name_plural = "واحدهای موجودی"
        ordering = ["-created_at"]

    def __str__(self):
        if self.accessory:
            return f"{self.accessory} - {self.serial_number}"
        type_part = f" {self.device_type.name}" if self.device_type else ""
        return f"{self.device_name}{type_part} - {self.serial_number}"


class DeviceVariant(models.Model):
    """جزئیات بیشتر نوع دستگاه — مثل شماره سری برد (فقط برای بعضی نوع‌ها کاربرد دارد)."""
    device_type = models.ForeignKey(DeviceType, verbose_name="نوع دستگاه", on_delete=models.CASCADE, related_name="variants")
    code = models.CharField("کد/شماره سری", max_length=50)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "جزئیات نوع دستگاه"
        verbose_name_plural = "جزئیات نوع دستگاه"
        unique_together = [("device_type", "code")]
        ordering = ["order", "code"]

    def __str__(self):
        return f"{self.device_type} - {self.code}"


class DeviceRegion(models.Model):
    """ریژن دستگاه (۰۰/۰۸/۱۵/۱۶) — فقط برای دستگاه‌هایی که ریژن دارند (مثل PS4/PS5) نشان داده می‌شود."""
    code = models.CharField("کد ریژن", max_length=20, unique=True)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        verbose_name = "ریژن"
        verbose_name_plural = "ریژن‌ها"
        ordering = ["order", "code"]

    def __str__(self):
        return self.code


class AccessoryBrand(models.Model):
    """برند لوازم جانبی — لیست به‌مرور با تایپ نام‌های جدید هنگام خرید کامل می‌شود."""
    name = models.CharField("نام برند", max_length=150, unique=True)

    class Meta:
        verbose_name = "برند لوازم جانبی"
        verbose_name_plural = "برندهای لوازم جانبی"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AccessoryColor(models.Model):
    """رنگ لوازم جانبی — لیست به‌مرور با تایپ رنگ‌های جدید هنگام خرید کامل می‌شود."""
    name = models.CharField("رنگ", max_length=100, unique=True)

    class Meta:
        verbose_name = "رنگ لوازم جانبی"
        verbose_name_plural = "رنگ‌های لوازم جانبی"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Accessory(models.Model):
    """یک قلم کالای جانبی (نام + برند + مدل + رنگ) — کاملاً پویا، هنگام خرید تعریف/انتخاب می‌شود."""
    name = models.CharField("نام کالا", max_length=200)
    brand = models.ForeignKey(
        AccessoryBrand, verbose_name="برند", on_delete=models.SET_NULL, null=True, blank=True, related_name="accessories"
    )
    model = models.CharField("مدل", max_length=200, blank=True, default="")
    color = models.ForeignKey(
        AccessoryColor, verbose_name="رنگ", on_delete=models.SET_NULL, null=True, blank=True, related_name="accessories"
    )
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کالای جانبی"
        verbose_name_plural = "کالاهای جانبی"
        unique_together = [("name", "brand", "model", "color")]
        ordering = ["name"]

    def __str__(self):
        parts = [self.name]
        if self.brand: parts.append(self.brand.name)
        if self.model: parts.append(self.model)
        if self.color: parts.append(self.color.name)
        return " - ".join(parts)
