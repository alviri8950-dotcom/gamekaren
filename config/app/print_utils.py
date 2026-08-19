# app/print_utils.py
"""
ارسال مستقیم به پرینتر پیش‌فرض همون کامپیوتری که سرور جنگو روش اجرا می‌شه —
نه پرینتر گوشی/مرورگر کاربر. از os.startfile(path, "print") استفاده می‌کنه که
یه قابلیت داخلی خود ویندوزه (نیاز به نصب هیچ پکیج اضافه‌ای مثل pywin32 نداره).

این فقط روی ویندوز کار می‌کنه (os.startfile فقط توی ویندوز وجود داره).
فایل متنی موقت رو با Notepad باز می‌کنه و بی‌صدا دستور چاپ رو می‌فرسته؛
هیچ پنجره‌ای دیده نمی‌شه.
"""
import os
import tempfile
import time

PRINT_JOBS_DIR = os.path.join(tempfile.gettempdir(), "gamekaren_print_jobs")


def send_text_to_default_printer(text, job_name="print_job"):
    """متن ساده رو به پرینتر پیش‌فرض سرور می‌فرسته. خروجی: (True, پیام) یا (False, پیام خطا)."""
    if os.name != 'nt':
        return False, "این قابلیت فقط روی ویندوز کار می‌کنه."

    os.makedirs(PRINT_JOBS_DIR, exist_ok=True)
    safe_name = "".join(c for c in job_name if c.isalnum() or c in ("-", "_")) or "job"
    filename = f"{safe_name}_{int(time.time())}.txt"
    filepath = os.path.join(PRINT_JOBS_DIR, filename)

    try:
        # utf-8-sig تا نوت‌پد فارسی رو درست نشون بده
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(text)
        os.startfile(filepath, "print")
        return True, "به پرینتر پیش‌فرض سرور فرستاده شد."
    except Exception as e:
        return False, f"خطا در ارسال به پرینتر: {e}"
