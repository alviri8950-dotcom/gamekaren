# app/seed.py
"""
این ماژول کاتالوگ دستگاه‌ها/کنترلرها/ریژن‌ها را همگام نگه می‌دارد.
sync_device_catalog() هر بار صفحه خرید یا نصب بازی باز می‌شود اجرا می‌شود:
- اگر یک نام دستگاه یا نوع از قبل با همین اسم وجود داشته باشد، دست‌نخورده می‌ماند.
- نام‌های قدیمی که باید تغییر کنند (مثل تغییرات PS5) صراحتاً rename می‌شوند.
- موارد جدید (PS1/PS2، مدل‌های کنترلر، شماره سری، ریژن) اضافه می‌شوند.
این یعنی روی دیتابیسی که از قبل داده دارد هم امن اجرا می‌شود، نه فقط دیتابیس خالی.
"""
from .models import (
    ProductGroup, DeviceName, DeviceType, DeviceVariant, DeviceRegion,
    SaleTerm, BankAccount,
)

# ترتیب و نام گروه‌های اصلی
SEED_GROUPS = ["کنسول", "دسته بازی", "لوازم جانبی", "بازی", "اکانت دیجیتال"]

# هر نام دستگاه زیر کدوم گروه قرار می‌گیره
DEVICE_GROUP_MAP = {
    "PS5": "کنسول", "PS4": "کنسول", "PS3": "کنسول", "PS2": "کنسول", "PS1": "کنسول",
    "Xbox Series": "کنسول", "Xbox One": "کنسول", "PSP": "کنسول", "Nintendo Switch": "کنسول",
    "کنترلر PlayStation": "دسته بازی", "کنترلر Xbox": "دسته بازی",
    "لوازم جانبی": "لوازم جانبی",
    "بازی": "بازی",
    "اکانت دیجیتال": "اکانت دیجیتال",
}

# (نام دستگاه, دارای ریژن, [نوع‌ها])
SEED_CATALOG = [
    ("PS5", True, ["فت درایو", "فت دیجیتال", "اسلیم درایو", "اسلیم دیجیتال", "پرو"]),
    ("PS4", True, ["فت", "اسلیم", "پرو"]),
    ("PS3", False, ["فت", "اسلیم", "سوپر اسلیم",
                     "۲۰ گیگ", "۴۰ گیگ", "۶۰ گیگ", "۸۰ گیگ", "۱۲۰ گیگ", "۱۶۰ گیگ", "۲۵۰ گیگ", "۳۲۰ گیگ", "۵۰۰ گیگ"]),
    ("PS2", False, ["فت", "اسلیم"]),
    ("PS1", False, ["فت", "اسلیم"]),
    ("Xbox Series", False, ["Series X", "Series S"]),
    ("Xbox One", False, ["استاندارد", "S", "X"]),
    ("PSP", False, ["1000", "2000", "3000", "Go", "Street", "Vita Slim", "Vita Fat"]),
    ("Nintendo Switch", False, ["استاندارد", "OLED", "Lite", "Switch 2"]),
    ("کنترلر PlayStation", False, [
        "DualSense", "DualSense Edge", "DualShock 4",
        "PS1 - اورجینال", "PS2 - اورجینال", "PS3 - DualShock 3",
        "PS4 - برد اصلی", "PS4 - اورجینال", "PS4 - فیک", "PS5 - DualSense", "PS5 - DualSense Edge",
    ]),
    ("کنترلر Xbox", False, ["Wireless Controller", "Elite Series 2", "دسته 360", "One S", "Series"]),
    ("لوازم جانبی", False, ["هدست", "شارژر", "کابل HDMI", "پایه شارژ", "کاور و برچسب"]),
    ("بازی", False, ["نسخه دیسک", "نسخه دیجیتال"]),
    ("اکانت دیجیتال", False, ["PSN Plus", "Xbox Game Pass"]),
]

# تغییر نام نوع‌های قدیمی به نام جدید (فقط برای PS5)
RENAMES = {
    "PS5": {
        "استاندارد (درایو)": "فت درایو",
        "دیجیتال": "فت دیجیتال",
    },
}

# شماره سری برد، بر اساس دسته فت/اسلیم/پرو — برای PS4 و PS5
SERIES_BY_CATEGORY = {
    "فت": ["10", "11", "12"],
    "اسلیم": ["20", "21", "22"],
    "پرو": ["70", "71", "72"],
}

SEED_REGIONS = ["00", "08", "15", "16"]

SEED_SALE_TERMS = [
    "به شرط قیمت",
    "به شرط اصالت کالا",
    "به شرط آکبند",
    "یک سال خدمات پس از فروش",
    "۱۰ روز مهلت تست",
]

SEED_BANK_ACCOUNTS = [
    "کارتخوان فروشگاه",
    "بانک ملت",
    "بانک ملی",
    "بانک تجارت",
]


def sync_device_catalog():
    groups = {}
    for order, name in enumerate(SEED_GROUPS):
        g, _ = ProductGroup.objects.get_or_create(name=name, defaults={"order": order})
        groups[name] = g

    for order, (device_name, has_region, types) in enumerate(SEED_CATALOG):
        group_name = DEVICE_GROUP_MAP.get(device_name)
        dn, _ = DeviceName.objects.get_or_create(
            name=device_name, defaults={"order": order, "has_region": has_region, "group": groups.get(group_name)}
        )
        if dn.has_region != has_region:
            dn.has_region = has_region
            dn.save(update_fields=["has_region"])
        if dn.group_id is None and group_name:
            dn.group = groups[group_name]
            dn.save(update_fields=["group"])

        # اعمال تغییر نام‌های قدیمی
        for old_name, new_name in RENAMES.get(device_name, {}).items():
            DeviceType.objects.filter(device_name=dn, name=old_name).update(name=new_name)

        for t_order, type_name in enumerate(types):
            dt, _ = DeviceType.objects.get_or_create(device_name=dn, name=type_name, defaults={"order": t_order})
            if device_name in ("PS4", "PS5"):
                for category, codes in SERIES_BY_CATEGORY.items():
                    if type_name.startswith(category):
                        for v_order, code in enumerate(codes):
                            DeviceVariant.objects.get_or_create(device_type=dt, code=code, defaults={"order": v_order})
                        break

    for order, code in enumerate(SEED_REGIONS):
        DeviceRegion.objects.get_or_create(code=code, defaults={"order": order})


# نگه‌داشته شده برای سازگاری با کدهای قبلی که این اسم را صدا می‌زنند
def ensure_seed_devices():
    sync_device_catalog()


def ensure_seed_sale_extras():
    for order, text in enumerate(SEED_SALE_TERMS):
        SaleTerm.objects.get_or_create(text=text, defaults={"order": order})
    for order, label in enumerate(SEED_BANK_ACCOUNTS):
        BankAccount.objects.get_or_create(label=label, defaults={"order": order})
