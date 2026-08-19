# app/admin.py
from django import forms
from django.contrib import admin
from .models import (
    GameTitle, GamePlatformAvailability, Personnel, Product, PurchaseRecord,
    ProductGroup, DeviceName, DeviceType, DeviceVariant, DeviceRegion, Supplier,
    SaleTerm, BankAccount, SaleRecord, SaleLineItem, Payment,
    Installer, GameInstallOrder, StockLevel, InventoryItem,
    AccessoryBrand, AccessoryColor, Accessory,
    Party, PartyLedgerEntry, Expense,
    SerialCounter, GeneratedSerialBatch, GeneratedSerial,
)


class GamePlatformAvailabilityInline(admin.TabularInline):
    model = GamePlatformAvailability
    extra = 1


@admin.register(GameTitle)
class GameTitleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "source", "updated_at")
    list_filter = ("is_active", "source")
    search_fields = ("name", "source")
    list_editable = ("is_active",)
    inlines = [GamePlatformAvailabilityInline]


class PersonnelAdminForm(forms.ModelForm):
    new_password = forms.CharField(
        label="تنظیم/تغییر رمز عبور", required=False, widget=forms.PasswordInput,
        help_text="فقط وقتی می‌خوای رمز رو تنظیم کنی یا عوض کنی این رو پر کن — خالی بذاری رمز فعلی دست‌نخورده می‌مونه."
    )

    class Meta:
        model = Personnel
        fields = "__all__"
        exclude = ("password_hash",)

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            instance.set_password(new_password)
        if commit:
            instance.save()
        return instance


@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    form = PersonnelAdminForm
    list_display = ("name", "is_admin", "is_active", "has_password", "created_at")
    list_editable = ("is_admin", "is_active")
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "new_password", "is_admin", "is_active")}),
        ("دسترسی‌ها (وقتی مدیر نباشه، همین‌ها تعیین‌کننده‌ن)", {
            "fields": ("can_purchase", "can_sale", "can_install", "can_view_reports", "can_manage_parties", "can_manage_expenses", "can_void_or_edit")
        }),
    )

    def has_password(self, obj):
        return bool(obj.password_hash)
    has_password.boolean = True
    has_password.short_description = "رمز تنظیم شده"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "created_at")
    list_filter = ("category", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name",)


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)


class DeviceTypeInline(admin.TabularInline):
    model = DeviceType
    extra = 1
    fields = ("name", "brand", "color", "condition", "is_active", "order")


@admin.register(DeviceName)
class DeviceNameAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "is_active", "order")
    list_filter = ("group",)
    list_editable = ("is_active", "order")
    search_fields = ("name",)
    inlines = [DeviceTypeInline]


class DeviceVariantInline(admin.TabularInline):
    model = DeviceVariant
    extra = 1


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ("device_name", "name", "brand", "color", "condition", "is_active", "order")
    list_filter = ("device_name", "brand", "color", "condition", "is_active")
    list_editable = ("is_active", "order")
    search_fields = ("name", "device_name__name")
    inlines = [DeviceVariantInline]


@admin.register(DeviceRegion)
class DeviceRegionAdmin(admin.ModelAdmin):
    list_display = ("code", "is_active", "order")
    list_editable = ("is_active", "order")


@admin.register(AccessoryBrand)
class AccessoryBrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(AccessoryColor)
class AccessoryColorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "model", "color", "is_active")
    list_filter = ("brand", "color", "is_active")
    search_fields = ("name", "model", "brand__name")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = (
        "device_name", "device_type", "serial_number", "quantity",
        "unit_price", "supplier", "receiver", "created_at",
    )
    list_filter = ("device_name", "receiver")
    search_fields = ("serial_number", "supplier__name", "device_name__name")


@admin.register(SaleTerm)
class SaleTermAdmin(admin.ModelAdmin):
    list_display = ("text", "is_active", "order")
    list_editable = ("is_active", "order")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("label", "balance", "is_active", "order")
    list_editable = ("balance", "is_active", "order")


class PartyAdminForm(forms.ModelForm):
    BALANCE_TYPE_CHOICES = [
        ("settled", "تسویه (بدون مانده)"),
        ("debtor", "بدهکار (شخص به فروشگاه مدیونه)"),
        ("creditor", "بستانکار (فروشگاه به شخص مدیونه)"),
    ]
    balance_type = forms.ChoiceField(
        label="نوع مانده حساب", choices=BALANCE_TYPE_CHOICES, required=True,
    )
    balance_amount = forms.IntegerField(
        label="مبلغ مانده حساب (تومان)", required=False, min_value=0, initial=0,
        help_text="همیشه عدد مثبت وارد کن؛ نوع بدهکار/بستانکار بودن رو از گزینه‌ی بالا مشخص کن.",
    )

    class Meta:
        model = Party
        fields = ("name", "kind", "phone", "sms_notifications_enabled")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance and instance.pk:
            if instance.balance > 0:
                self.fields["balance_type"].initial = "debtor"
                self.fields["balance_amount"].initial = instance.balance
            elif instance.balance < 0:
                self.fields["balance_type"].initial = "creditor"
                self.fields["balance_amount"].initial = -instance.balance
            else:
                self.fields["balance_type"].initial = "settled"
                self.fields["balance_amount"].initial = 0
        else:
            self.fields["balance_type"].initial = "settled"
            self.fields["balance_amount"].initial = 0

    def clean(self):
        cleaned = super().clean()
        balance_type = cleaned.get("balance_type")
        amount = cleaned.get("balance_amount") or 0
        if balance_type in ("debtor", "creditor") and amount <= 0:
            self.add_error("balance_amount", "برای بدهکار/بستانکار، مبلغ باید بزرگ‌تر از صفر باشه.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        balance_type = self.cleaned_data.get("balance_type")
        amount = self.cleaned_data.get("balance_amount") or 0
        if balance_type == "debtor":
            instance.balance = amount
        elif balance_type == "creditor":
            instance.balance = -amount
        else:
            instance.balance = 0
        if commit:
            instance.save()
        return instance


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    form = PartyAdminForm
    list_display = ("name", "kind", "balance_status_display", "phone", "sms_notifications_enabled", "created_at")
    list_filter = ("kind", "sms_notifications_enabled")
    list_editable = ("phone", "sms_notifications_enabled")
    search_fields = ("name", "phone")
    fields = ("name", "kind", "balance_type", "balance_amount", "phone", "sms_notifications_enabled")

    def balance_status_display(self, obj):
        if obj.balance > 0:
            return f"بدهکار: {obj.balance} تومان"
        if obj.balance < 0:
            return f"بستانکار: {-obj.balance} تومان"
        return "تسویه"
    balance_status_display.short_description = "مانده حساب"


@admin.register(PartyLedgerEntry)
class PartyLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("party", "amount", "balance_after", "description", "created_at")
    list_filter = ("party",)
    search_fields = ("party__name", "description")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("category", "subcategory", "amount", "payment_method", "created_by", "created_at", "is_voided")
    list_filter = ("category", "payment_method", "is_voided")
    search_fields = ("category", "subcategory", "note")


class SaleLineItemInline(admin.TabularInline):
    model = SaleLineItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "customer_phone", "seller", "created_at")
    search_fields = ("customer_name", "customer_phone", "customer_national_id")
    list_filter = ("seller",)
    inlines = [SaleLineItemInline, PaymentInline]


@admin.register(Installer)
class InstallerAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_editable = ("is_active",)
    search_fields = ("name",)


@admin.register(GameInstallOrder)
class GameInstallOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer_name", "device_name", "installer",
        "delivered", "receiver", "order_datetime",
    )
    list_filter = ("device_name", "installer", "delivered")
    search_fields = ("customer_name", "serial_number")


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ("device_name", "device_type", "quantity")
    list_filter = ("device_name",)
    list_editable = ("quantity",)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "device_name", "device_type", "status", "unit_cost", "created_at", "sold_at")
    list_filter = ("status", "device_name")
    search_fields = ("serial_number",)


@admin.register(GeneratedSerialBatch)
class GeneratedSerialBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "prefix", "quantity", "created_at")
    list_filter = ("prefix",)


@admin.register(GeneratedSerial)
class GeneratedSerialAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "sequence_number", "batch")
    search_fields = ("serial_number",)


@admin.register(SerialCounter)
class SerialCounterAdmin(admin.ModelAdmin):
    list_display = ("prefix", "last_value")
