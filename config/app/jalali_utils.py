# app/jalali_utils.py
"""
تبدیل تاریخ/ساعت بین میلادی و شمسی.
از کتابخانه jdatetime استفاده می‌کند (باید در requirements نصب شود: pip install jdatetime)
"""
import jdatetime
from django.utils import timezone

J_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


def to_jalali_string(dt):
    """یک datetime میلادی را به رشته شمسی خوانا تبدیل می‌کند.
    خروجی نمونه: «۲۷ تیر ۱۴۰۳ - ۱۴:۳۲»
    """
    if dt is None:
        return ""
    jd = jdatetime.datetime.fromgregorian(datetime=dt)
    return f"{jd.day} {J_MONTHS[jd.month - 1]} {jd.year} - {jd.hour:02d}:{jd.minute:02d}"


def now_jalali_parts():
    """تاریخ/ساعت فعلی سیستم را به‌صورت اجزای شمسی برمی‌گرداند — برای پرکردن پیش‌فرض فیلدهای ادمین."""
    now = timezone.now()
    jd = jdatetime.datetime.fromgregorian(datetime=now)
    return {"year": jd.year, "month": jd.month, "day": jd.day, "hour": jd.hour, "minute": jd.minute}


def jalali_to_gregorian_datetime(jy, jm, jd, hour=0, minute=0):
    """اجزای تاریخ/ساعت شمسی را به یک datetime میلادی (timezone-aware) تبدیل می‌کند."""
    jdt = jdatetime.datetime(int(jy), int(jm), int(jd), int(hour), int(minute))
    gdt = jdt.togregorian()
    if timezone.is_naive(gdt):
        gdt = timezone.make_aware(gdt)
    return gdt


def jalali_month_start():
    """ساعت ۰۰:۰۰ روز اول ماه شمسی جاری را برمی‌گرداند (میلادی، timezone-aware)."""
    now = timezone.now()
    jd = jdatetime.datetime.fromgregorian(datetime=now)
    return jalali_to_gregorian_datetime(jd.year, jd.month, 1, 0, 0)
