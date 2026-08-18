# -*- coding: utf-8 -*-
"""
سرویس ارسال پیامک از طریق کاوه‌نگار (Kavenegar).

طراحی عمدی: هیچ تابعی در این فایل استثنا (exception) بالا نمی‌ندازه.
دلیلش اینه که ارسال پیامک نباید هیچ‌وقت باعث خراب شدن ثبت فاکتور،
تحویل سفارش نصب یا تراکنش حساب اشخاص بشه. اگه پیامک نرسید، فقط
لاگ می‌شه و کار اصلی ادامه پیدا می‌کنه.

تنظیمات لازم در settings.py:
    SMS_ENABLED = True/False
    KAVENEGAR_API_KEY = '...'
    KAVENEGAR_SENDER = '...'   (اختیاری - اگه خالی باشه، خط پیش‌فرض حساب کاوه‌نگار استفاده می‌شه)
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

KAVENEGAR_SEND_URL = "https://api.kavenegar.com/v1/{api_key}/sms/send.json"


def send_sms(phone, message):
    """
    ارسال یک پیامک ساده به یک شماره.
    خروجی: (ok: bool, detail: str) — هیچ‌وقت استثنا بالا نمی‌ره.
    """
    phone = (phone or "").strip()
    if not phone:
        return False, "شماره تماس خالی است"

    if not getattr(settings, "SMS_ENABLED", False):
        logger.info("SMS غیرفعال است - پیام برای %s ارسال نشد: %s", phone, message)
        return False, "سرویس پیامک غیرفعال است"

    api_key = getattr(settings, "KAVENEGAR_API_KEY", "")
    if not api_key:
        logger.warning("KAVENEGAR_API_KEY تنظیم نشده است")
        return False, "کلید API کاوه‌نگار تنظیم نشده"

    payload = {"receptor": phone, "message": message}
    sender = getattr(settings, "KAVENEGAR_SENDER", "")
    if sender:
        payload["sender"] = sender

    url = KAVENEGAR_SEND_URL.format(api_key=api_key)
    try:
        resp = requests.post(url, data=payload, timeout=8)
        data = resp.json()
        status = (data.get("return") or {}).get("status")
        if status == 200:
            logger.info("پیامک با موفقیت به %s ارسال شد", phone)
            return True, "ارسال شد"
        detail = (data.get("return") or {}).get("message", "خطای نامشخص از کاوه‌نگار")
        logger.error("خطای کاوه‌نگار برای %s: %s (status=%s)", phone, detail, status)
        return False, detail
    except requests.RequestException as exc:
        logger.exception("ارسال پیامک به %s با خطا مواجه شد", phone)
        return False, str(exc)
    except ValueError:
        # پاسخ JSON نامعتبر بود
        logger.exception("پاسخ نامعتبر از کاوه‌نگار برای %s", phone)
        return False, "پاسخ نامعتبر از سرویس پیامک"


def send_sale_invoice_sms(sale):
    """پیامک تأییدیه فاکتور فروش، بعد از ثبت فاکتور."""
    if not sale.customer_phone:
        return
    total = f"{sale.total_price:,}"
    balance = sale.balance
    if balance > 0:
        text = (
            f"گیم‌کارن\n"
            f"فاکتور #{sale.id} به مبلغ {total} تومان ثبت شد.\n"
            f"مانده قابل پرداخت: {balance:,} تومان"
        )
    else:
        text = (
            f"گیم‌کارن\n"
            f"فاکتور #{sale.id} به مبلغ {total} تومان ثبت و تسویه شد."
        )
    send_sms(sale.customer_phone, text)


def send_install_delivered_sms(order):
    """پیامک تحویل سفارش نصب بازی، بعد از رسیدن به مرحله «تحویل مشتری»."""
    if not order.customer_phone:
        return
    text = (
        f"گیم‌کارن\n"
        f"سفارش نصب #{order.id} ({order.device_name}) تحویل داده شد.\n"
        f"از خرید شما متشکریم."
    )
    send_sms(order.customer_phone, text)


def send_party_ledger_sms(party, amount, description):
    """
    پیامک تغییر مانده حساب، فقط برای اشخاصی که sms_notifications_enabled
    براشون فعال باشه (نه همه‌ی اشخاص حساب).
    """
    if not getattr(party, "sms_notifications_enabled", False):
        return
    if not getattr(party, "phone", ""):
        return

    direction = "بدهکار شدید" if amount > 0 else "بستانکار شدید"
    text = (
        f"گیم‌کارن\n"
        f"{description}\n"
        f"مبلغ: {abs(amount):,} تومان ({direction})\n"
        f"مانده جدید: {party.balance:,} تومان"
    )
    send_sms(party.phone, text)
