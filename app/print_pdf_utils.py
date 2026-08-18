# app/pdf_utils.py
"""
ساخت فاکتور PDF دقیقاً هم‌اندازهٔ نمونه‌ای که فرستادی (A5: 148×210mm)،
با فضای بالای صفحه برای سربرگ از‌پیش‌چاپ‌شده.

نیاز به این پکیج‌ها داره (نصب با pip، همه pure-Python هستن، نیازی به کامپایلر ندارن):
    pip install fpdf2 arabic-reshaper python-bidi

از فونت فارسی خود ویندوز (Tahoma) استفاده می‌کنه — نیازی به دانلود فونت نیست.
"""
import os
import tempfile
import time

try:
    from fpdf import FPDF
    import arabic_reshaper
    from bidi.algorithm import get_display
    PDF_LIBS_OK = True
except ImportError:
    PDF_LIBS_OK = False

PDF_JOBS_DIR = os.path.join(tempfile.gettempdir(), "gamekaren_print_jobs")

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]

# ==== اندازه‌ها (میلی‌متر) — بر اساس نمونهٔ PDF ارسالی (A5 = 148×210mm) ====
PAGE_W = 148
PAGE_H = 210
MARGIN_L = 8
MARGIN_R = 8
TOP_MARGIN = 26     # فضای خالی بالای صفحه برای سربرگ از‌پیش‌چاپ‌شده
BOTTOM_MARGIN = 12  # فضای خالی پایین صفحه برای فوتر از‌پیش‌چاپ‌شده

COL_ROW = 10     # عرض ستون «ردیف»
COL_DESC = 52    # عرض ستون «شرح» — در صورت نیاز تا ۲ خط می‌شکنه
COL_SERIAL = 42  # عرض ستون «سریال» — بزرگ‌تر شده چون سریال‌ها معمولاً طولانی‌ان
ROW_H = 8


def _find_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def rtl(text):
    """متن فارسی رو برای نمایش درست (چسبیدن حروف + راست‌به‌چپ) آماده می‌کنه."""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


def _wrap_plain_lines(pdf, text, width, max_lines=2):
    """متن ساده (هنوز rtl نشده) رو در صورت لزوم به حداکثر max_lines خط می‌شکنه تا تو
    عرض ستون جا بشه؛ اگه حتی با شکستن هم جا نشد، خط آخر با سه‌نقطه کوتاه می‌شه."""
    pdf.set_font('Fa', '', 9)  # اندازه‌ی پایه، برای اندازه‌گیری درست عرض متن
    text = (text or '—').strip() or '—'
    words = text.split(' ')
    lines = []
    current = ''
    for w in words:
        trial = f"{current} {w}".strip()
        if pdf.get_string_width(trial) <= width - 3 or not current:
            current = trial
        else:
            lines.append(current)
            current = w
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if not lines:
        lines = [text]
    lines = lines[:max_lines]
    last = lines[-1]
    if pdf.get_string_width(last) > width - 3:
        while pdf.get_string_width(last + '…') > width - 3 and len(last) > 1:
            last = last[:-1]
        lines[-1] = last + '…'
    return lines


def _fit_font_size(pdf, text, width, base_size=9, min_size=6.5):
    """اگه متن (مثل سریال یا مبلغ) از عرض ستون بیشتر باشه، فونت رو کمی کوچیک می‌کنه
    تا جا بشه، بدون اینکه سرریز کنه یا رو ستون بعدی بیفته."""
    size = base_size
    pdf.set_font('Fa', '', size)
    while pdf.get_string_width(text) > width - 3 and size > min_size:
        size -= 0.5
        pdf.set_font('Fa', '', size)
    return size


def _draw_checkbox(pdf, x, y, size=3.2):
    """یک چک‌باکس تیک‌خورده (کادر مربعی + علامت تیک داخلش) رسم می‌کنه."""
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.25)
    pdf.rect(x, y, size, size)
    pdf.line(x + size * 0.18, y + size * 0.55, x + size * 0.42, y + size * 0.82)
    pdf.line(x + size * 0.42, y + size * 0.82, x + size * 0.85, y + size * 0.18)
    pdf.set_line_width(0.2)


def _render_terms_flow(pdf, term_texts, x_right, y, width, line_h=6, checkbox_size=3.2, gap=2.2, term_gap=5, max_y=None):
    """شرایط انتخاب‌شده رو پشت هم، با یک چک‌باکس تیک‌خورده جلوی (سمت راست) هرکدوم، توی یک
    ردیف می‌چینه و هروقت عرض ردیف پر بشه به خط بعد می‌شکنه. اگه max_y داده بشه و محتوا بهش
    برسه (یعنی به فوتر از‌پیش‌چاپ‌شده نزدیک بشه)، از چاپ باقی‌ی موارد صرف‌نظر می‌کنه.
    ارتفاع نهایی مصرف‌شده (y جدید) رو برمی‌گردونه."""
    if not term_texts:
        return y
    pdf.set_font('Fa', '', 8.5)
    left_bound = x_right - width
    cur_x = x_right
    for raw_text in term_texts:
        text = rtl(raw_text)
        text_w = pdf.get_string_width(text)
        max_item_w = width - checkbox_size - gap
        if text_w > max_item_w:
            plain = raw_text
            while pdf.get_string_width(rtl(plain + '…')) > max_item_w and len(plain) > 1:
                plain = plain[:-1]
            text = rtl(plain + '…')
            text_w = pdf.get_string_width(text)
        item_w = checkbox_size + gap + text_w
        if cur_x - item_w < left_bound and cur_x != x_right:
            y += line_h
            cur_x = x_right
            if max_y and y + line_h > max_y:
                return y  # دیگه جا نیست، از چاپ باقی موارد صرف‌نظر می‌کنیم تا به فوتر نرسه
        item_x = cur_x - item_w
        pdf.set_xy(item_x, y)
        pdf.cell(text_w, line_h, text, align='R')
        _draw_checkbox(pdf, item_x + text_w + gap, y + (line_h - checkbox_size) / 2, checkbox_size)
        cur_x = item_x - term_gap
    return y + line_h


def _line_item_description(item):
    if item.accessory:
        parts = [item.accessory.name]
        if item.accessory.brand:
            parts.append(item.accessory.brand.name)
        if item.accessory.model:
            parts.append(item.accessory.model)
        if item.accessory.color:
            parts.append(item.accessory.color.name)
        return " - ".join(parts)
    parts = [item.device_name.name] if item.device_name else []
    if item.device_type:
        parts.append(item.device_type.name)
    if item.device_variant:
        parts.append(f"سری {item.device_variant.code}")
    if item.device_region:
        parts.append(f"ریژن {item.device_region.code}")
    return " - ".join(parts)


def build_invoice_pdf(sale, copy_type):
    """یک PDF فاکتور می‌سازه (copy_type: 'customer' یا 'store') و مسیر فایل رو برمی‌گردونه.
    خروجی: (filepath, None) موفق، یا (None, پیام خطا) در صورت شکست."""
    if not PDF_LIBS_OK:
        return None, "کتابخانه‌های PDF نصب نشده — روی سرور بزن: pip install fpdf2 arabic-reshaper python-bidi"
    font_path = _find_font()
    if not font_path:
        return None, "فونت فارسی (Tahoma) روی سرور پیدا نشد."

    os.makedirs(PDF_JOBS_DIR, exist_ok=True)

    usable_w = PAGE_W - MARGIN_L - MARGIN_R
    col_amount_w = usable_w - COL_ROW - COL_DESC - COL_SERIAL

    pdf = FPDF(orientation='P', unit='mm', format=(PAGE_W, PAGE_H))
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.add_font('Fa', '', font_path)
    pdf.set_font('Fa', '', 9)

    y = TOP_MARGIN + (10 if copy_type == 'customer' else 0)  # نسخهٔ مشتری ۱ سانتی‌متر پایین‌تر شروع می‌شه (۲ سانتی‌متر بالاتر از قبل)

    # شماره فاکتور یونیک — وسط‌چین، بالای ردیف اطلاعات خریدار
    invoice_no = f"INV-{sale.id}"
    pdf.set_font('Fa', '', 11)
    pdf.set_xy(MARGIN_L, y)
    pdf.cell(usable_w, 7, rtl(f"شماره فاکتور: {invoice_no}"), align='C')
    y += 8

    # تاریخ و ساعت — خط جدای خودش (راست‌چین)، تا هیچ‌وقت با اطلاعات خریدار قاطی نشه
    pdf.set_font('Fa', '', 8.5)
    pdf.set_xy(MARGIN_L, y)
    pdf.cell(usable_w, 5.5, rtl(f"تاریخ و ساعت ثبت: {sale.jalali_datetime}"), align='R')
    y += 6

    # ردیف اطلاعات خریدار — سه سلول مجزا با عرض ثابت (نه یک رشته‌ی بلند)، تا هیچ‌کدوم
    # روی هم یا روی ردیف تاریخ سرریز نکنه؛ اگه هم متن بلند بود، فونتش خودکار کوچیک می‌شه.
    buyer_col_w = usable_w / 3
    buyer_fields = [
        f"نام خریدار: {sale.customer_name or '—'}",
        f"کد ملی: {sale.customer_national_id or '—'}",
        f"تلفن: {sale.customer_phone or '—'}",
    ]
    x = MARGIN_L + usable_w
    for field_text in buyer_fields:
        x -= buyer_col_w
        _fit_font_size(pdf, rtl(field_text), buyer_col_w, base_size=8.5, min_size=6)
        pdf.set_xy(x, y)
        pdf.cell(buyer_col_w, 6, rtl(field_text), align='C')
    pdf.set_font('Fa', '', 9)
    y += 10

    # هدر جدول (راست‌به‌چپ: ردیف سمت راست‌ترین)
    headers = [('ردیف', COL_ROW), ('شرح', COL_DESC), ('سریال', COL_SERIAL), ('مبلغ', col_amount_w)]
    x = MARGIN_L + usable_w
    pdf.set_font('Fa', '', 9)
    for name, wcol in headers:
        x -= wcol
        pdf.set_xy(x, y)
        pdf.cell(wcol, ROW_H, rtl(name), border=1, align='C')
    y += ROW_H

    for idx, item in enumerate(sale.items.all(), start=1):
        desc_plain = _line_item_description(item)
        desc_lines = _wrap_plain_lines(pdf, desc_plain, COL_DESC, max_lines=2)
        row_h = ROW_H if len(desc_lines) <= 1 else ROW_H * 1.7

        amount_text = f"{item.total_price:,}"
        serial_text = item.serial_number or '—'

        x = MARGIN_L + usable_w

        # ردیف
        x -= COL_ROW
        pdf.set_font('Fa', '', 9)
        pdf.set_xy(x, y)
        pdf.cell(COL_ROW, row_h, str(idx), border=1, align='C')

        # شرح — کادر رو دستی می‌کشیم چون ممکنه چند خط باشه
        x -= COL_DESC
        pdf.rect(x, y, COL_DESC, row_h)
        line_h = row_h / len(desc_lines)
        pdf.set_font('Fa', '', 9)
        for li, line in enumerate(desc_lines):
            pdf.set_xy(x, y + li * line_h)
            pdf.cell(COL_DESC, line_h, rtl(line), align='C')

        # سریال — در صورت نیاز فونت کمی کوچیک می‌شه تا جا بشه
        x -= COL_SERIAL
        _fit_font_size(pdf, serial_text, COL_SERIAL)
        pdf.set_xy(x, y)
        pdf.cell(COL_SERIAL, row_h, serial_text, border=1, align='C')

        # مبلغ
        x -= col_amount_w
        _fit_font_size(pdf, amount_text, col_amount_w)
        pdf.set_xy(x, y)
        pdf.cell(col_amount_w, row_h, amount_text, border=1, align='C')

        pdf.set_font('Fa', '', 9)
        y += row_h

    # جمع کل
    total_text = f"{sale.total_price:,}"
    _fit_font_size(pdf, total_text, col_amount_w)
    pdf.set_xy(MARGIN_L, y)
    pdf.cell(col_amount_w, ROW_H, total_text, border=1, align='C')
    pdf.set_font('Fa', '', 9)
    pdf.set_xy(MARGIN_L + col_amount_w, y)
    pdf.cell(COL_ROW + COL_DESC + COL_SERIAL, ROW_H, rtl('جمع کل'), border=1, align='C')
    y += ROW_H + 4

    # بارکد شماره فاکتور — خارج از جدول، برای اسکن و دسترسی سریع توی صفحه‌ی گزارش فروش
    barcode_w = 60
    pdf.code39(f"*{invoice_no}*", x=MARGIN_L + (usable_w - barcode_w) / 2, y=y, w=1.1, h=10)
    y += 12
    pdf.set_font('Fa', '', 7.5)
    pdf.set_xy(MARGIN_L, y)
    pdf.cell(usable_w, 4, invoice_no, align='C')
    y += 8

    pdf.set_font('Fa', '', 9)
    if copy_type == 'customer':
        term_texts = [t.text for t in sale.terms.all()]
        y = _render_terms_flow(
            pdf, term_texts,
            x_right=MARGIN_L + usable_w, y=y, width=usable_w,
            max_y=PAGE_H - BOTTOM_MARGIN,
        )
    else:
        pdf.set_xy(MARGIN_L, y)
        pdf.cell(usable_w, 6, rtl('شرایط پرداخت‌ها:'), align='R')
        y += 6
        payments = list(sale.payments.all())
        if payments:
            for p in payments:
                acc = f" - {p.bank_account.label}" if p.bank_account else ""
                tracking = f" (پیگیری: {p.tracking_number})" if p.tracking_number else ""
                line = f"{p.get_payment_type_display()}{acc}: {p.amount:,} تومان{tracking}"
                pdf.set_xy(MARGIN_L, y)
                pdf.cell(usable_w, 6, rtl(line), align='R')
                y += 6
        else:
            pdf.set_xy(MARGIN_L, y)
            pdf.cell(usable_w, 6, rtl('ثبت نشده'), align='R')
            y += 6
        if sale.change:
            pdf.set_xy(MARGIN_L, y)
            pdf.cell(usable_w, 6, rtl('تعویض: بله'), align='R')
            y += 6
        y += 2
        pdf.set_xy(MARGIN_L, y)
        pdf.cell(usable_w, 6, rtl(f"ثبت‌کننده: {sale.seller.name}"), align='R')
        y += 6

    filename = f"invoice_{sale.id}_{copy_type}_{int(time.time())}.pdf"
    filepath = os.path.join(PDF_JOBS_DIR, filename)
    pdf.output(filepath)
    return filepath, None


def send_pdf_to_default_printer(filepath):
    if os.name != 'nt':
        return False, "این قابلیت فقط روی ویندوز کار می‌کنه."
    try:
        os.startfile(filepath, "print")
        return True, "به پرینتر پیش‌فرض سرور فرستاده شد."
    except Exception as e:
        return False, f"خطا در ارسال به پرینتر: {e}"


# ==== رسید نصب بازی: یک برگه A5 (148×210) شامل دو نیمهٔ A6 (رسید مشتری + برگهٔ نصاب) ====
INSTALL_PAGE_W = 148
INSTALL_PAGE_H = 210
INSTALL_HALF_H = 105
INSTALL_MARGIN = 6

SHOP_NAME = "گیم‌کارن"
SHOP_ADDRESS = "تهران، میدان امام خمینی، پاساژ لباف، طبقه همکف، پلاک 1/20"
SHOP_PHONE = "02133974370"


def _find_logo():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'app-icon.jpeg')
    return path if os.path.exists(path) else None


def _install_half_header(pdf, y0, title=None):
    """هدر هر نیمه: لوگو + نام فروشگاه (و در صورت وجود title، وسط‌چین زیر نام فروشگاه). بدون آدرس/تلفن."""
    logo = _find_logo()
    usable_w = INSTALL_PAGE_W - 2 * INSTALL_MARGIN
    if logo:
        pdf.image(logo, x=INSTALL_MARGIN, y=y0 + 2, w=12, h=12)
    center_x = INSTALL_MARGIN + 16
    center_w = usable_w - 32
    pdf.set_font('Fa', '', 12)
    pdf.set_xy(center_x, y0 + 2)
    pdf.cell(center_w, 6, rtl(SHOP_NAME), align='C')
    if title:
        pdf.set_font('Fa', '', 9.5)
        pdf.set_xy(center_x, y0 + 8)
        pdf.cell(center_w, 5, rtl(title), align='C')
    pdf.set_draw_color(150, 150, 150)
    pdf.line(INSTALL_MARGIN, y0 + 15, INSTALL_PAGE_W - INSTALL_MARGIN, y0 + 15)


def _install_half_footer(pdf, y0, show_address):
    usable_w = INSTALL_PAGE_W - 2 * INSTALL_MARGIN
    footer_y = y0 + INSTALL_HALF_H - 8
    pdf.set_draw_color(150, 150, 150)
    pdf.line(INSTALL_MARGIN, footer_y - 2, INSTALL_PAGE_W - INSTALL_MARGIN, footer_y - 2)
    pdf.set_font('Fa', '', 7)
    text = f"{SHOP_NAME}  |  آدرس: {SHOP_ADDRESS}  |  تلفن: {SHOP_PHONE}" if show_address else SHOP_NAME
    pdf.set_xy(INSTALL_MARGIN, footer_y)
    pdf.cell(usable_w, 5, rtl(text), align='C')


def _install_sign_box(pdf, x, y, w, h, label):
    pdf.set_draw_color(180, 180, 180)
    pdf.rect(x, y, w, h)
    pdf.set_font('Fa', '', 7.5)
    pdf.set_text_color(140, 140, 140)
    pdf.set_xy(x, y + h - 5)
    pdf.cell(w, 5, rtl(label), align='C')
    pdf.set_text_color(0, 0, 0)


def build_install_receipt_pdf(order):
    """رسید نصب بازی رو به‌صورت یک PDF با اندازهٔ A5 (شامل دو نیمهٔ A6: رسید مشتری + برگهٔ نصاب) می‌سازه."""
    if not PDF_LIBS_OK:
        return None, "کتابخانه‌های PDF نصب نشده — روی سرور بزن: pip install fpdf2 arabic-reshaper python-bidi"
    font_path = _find_font()
    if not font_path:
        return None, "فونت فارسی (Tahoma) روی سرور پیدا نشد."

    os.makedirs(PDF_JOBS_DIR, exist_ok=True)
    usable_w = INSTALL_PAGE_W - 2 * INSTALL_MARGIN

    pdf = FPDF(orientation='P', unit='mm', format=(INSTALL_PAGE_W, INSTALL_PAGE_H))
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.add_font('Fa', '', font_path)

    games = order.games

    # ---- نیمهٔ بالا: رسید مشتری (بدون آدرس در هدر؛ عنوان وسط هدر چاپ می‌شود) ----
    y0 = 0
    _install_half_header(pdf, y0, title='رسید مشتری')
    y = y0 + 19

    pdf.set_font('Fa', '', 8.5)
    rows = [
        (f"نام مشتری: {order.customer_name or '—'}", f"شماره سفارش: #{order.id}"),
        (f"دستگاه: {order.device_name.name} ({order.get_license_type_display()})", f"سریال: {order.serial_number or '—'}"),
    ]
    for right, left in rows:
        pdf.set_xy(INSTALL_MARGIN, y)
        pdf.cell(usable_w / 2, 5.5, rtl(left), align='L')
        pdf.set_xy(INSTALL_MARGIN + usable_w / 2, y)
        pdf.cell(usable_w / 2, 5.5, rtl(right), align='R')
        y += 5.5
    pdf.set_xy(INSTALL_MARGIN, y)
    pdf.cell(usable_w, 5.5, rtl(f"تاریخ و ساعت ثبت: {order.order_jalali}"), align='R')
    y += 8

    pdf.set_font('Fa', '', 9)
    pdf.set_xy(INSTALL_MARGIN, y)
    pdf.cell(usable_w, 5, rtl('لیست بازی‌ها:'), align='R')
    y += 5.5
    pdf.set_font('Fa', '', 8.5)
    if games:
        for g in games:
            pdf.set_xy(INSTALL_MARGIN, y)
            pdf.cell(usable_w, 5, rtl(f"- {g.name}"), align='R')
            y += 5
    else:
        pdf.set_xy(INSTALL_MARGIN, y)
        pdf.cell(usable_w, 5, rtl('—'), align='R')
        y += 5
    y += 3

    paid_label = 'پرداخت شده' if order.is_paid else 'پرداخت نشده'
    pdf.set_font('Fa', '', 9)
    pdf.set_xy(INSTALL_MARGIN, y)
    pdf.cell(usable_w / 2, 6, rtl(paid_label), align='L')
    pdf.set_xy(INSTALL_MARGIN + usable_w / 2, y)
    pdf.cell(usable_w / 2, 6, rtl(f"هزینه نصب: {order.install_cost:,} تومان"), align='R')

    # امضای مشتری + محل مهر
    box_y = y0 + INSTALL_HALF_H - 24
    box_w = (usable_w - 4) / 2
    box_h = 12
    _install_sign_box(pdf, INSTALL_MARGIN, box_y, box_w, box_h, 'امضای مشتری')
    _install_sign_box(pdf, INSTALL_MARGIN + box_w + 4, box_y, box_w, box_h, 'محل مهر')

    _install_half_footer(pdf, y0, show_address=True)

    # ---- خط برش ----
    pdf.set_draw_color(120, 120, 120)
    pdf.dashed_line(0, INSTALL_HALF_H, INSTALL_PAGE_W, INSTALL_HALF_H, dash_length=2, space_length=1.5)

    # ---- نیمهٔ پایین: برگهٔ نصاب (بدون آدرس، نه در هدر نه در فوتر) ----
    y0 = INSTALL_HALF_H
    _install_half_header(pdf, y0, title='برگهٔ نصاب')
    y = y0 + 19

    pdf.set_font('Fa', '', 9)
    pdf.set_xy(INSTALL_MARGIN, y)
    pdf.cell(usable_w, 5.5, rtl(f"نام مشتری: {order.customer_name or '—'}"), align='R')
    y += 8

    pdf.set_xy(INSTALL_MARGIN, y)
    pdf.cell(usable_w, 5, rtl('لیست بازی‌ها:'), align='R')
    y += 5.5
    pdf.set_font('Fa', '', 8.5)
    if games:
        for g in games:
            pdf.set_xy(INSTALL_MARGIN, y)
            pdf.cell(usable_w, 5, rtl(f"- {g.name}"), align='R')
            y += 5
    else:
        pdf.set_xy(INSTALL_MARGIN, y)
        pdf.cell(usable_w, 5, rtl('—'), align='R')
        y += 5

    # امضای مشتری
    box_y = y0 + INSTALL_HALF_H - 24
    _install_sign_box(pdf, INSTALL_MARGIN, box_y, usable_w, 12, 'امضای مشتری')

    _install_half_footer(pdf, y0, show_address=False)

    filename = f"install_{order.id}_{int(time.time())}.pdf"
    filepath = os.path.join(PDF_JOBS_DIR, filename)
    pdf.output(filepath)
    return filepath, None


# ==== برچسب سریال (A4، چند ستونه، با بارکد Code39) ====
LABEL_PAGE_W = 210
LABEL_PAGE_H = 297
LABEL_PAGE_MARGIN = 8   # حاشیه‌ی بیرونی خود صفحه A4
LABEL_W = 40            # عرض هر برچسب (میلی‌متر) = ۴ سانتی‌متر
LABEL_H = 10            # ارتفاع هر برچسب (میلی‌متر) = ۱ سانتی‌متر
LABEL_GAP = 2           # فاصله بین برچسب‌ها (میلی‌متر)


def build_serial_labels_pdf(batch_id, serial_numbers):
    """یک PDF شامل برچسب A4 (چند صفحه در صورت نیاز) برای لیست سریال‌های دادهشده می‌سازه.
    هر برچسب ۴×۱ سانتی‌متر، فقط بارکد Code39 (قابل اسکن) + خود سریال به‌صورت متن — بدون نام فروشگاه.
    خروجی: (filepath, None) موفق، یا (None, پیام خطا)."""
    if not PDF_LIBS_OK:
        return None, "کتابخانه‌های PDF نصب نشده — روی سرور بزن: pip install fpdf2 arabic-reshaper python-bidi"
    font_path = _find_font()
    if not font_path:
        return None, "فونت فارسی (Tahoma) روی سرور پیدا نشد."

    os.makedirs(PDF_JOBS_DIR, exist_ok=True)

    usable_w = LABEL_PAGE_W - 2 * LABEL_PAGE_MARGIN
    usable_h = LABEL_PAGE_H - 2 * LABEL_PAGE_MARGIN
    pitch_w = LABEL_W + LABEL_GAP
    pitch_h = LABEL_H + LABEL_GAP
    cols = int((usable_w + LABEL_GAP) // pitch_w)
    rows = int((usable_h + LABEL_GAP) // pitch_h)
    per_page = cols * rows
    # شبکه رو وسط صفحه قرار می‌دیم (فضای اضافی مساوی از دو طرف)
    grid_w = cols * LABEL_W + (cols - 1) * LABEL_GAP
    grid_h = rows * LABEL_H + (rows - 1) * LABEL_GAP
    start_x = (LABEL_PAGE_W - grid_w) / 2
    start_y = (LABEL_PAGE_H - grid_h) / 2

    pdf = FPDF(orientation='P', unit='mm', format=(LABEL_PAGE_W, LABEL_PAGE_H))
    pdf.set_auto_page_break(False)
    pdf.add_font('Fa', '', font_path)

    barcode_h = 6.5
    for page_start in range(0, len(serial_numbers), per_page):
        pdf.add_page()
        page_serials = serial_numbers[page_start:page_start + per_page]
        for idx, serial in enumerate(page_serials):
            row, col = divmod(idx, cols)
            x = start_x + col * pitch_w
            y = start_y + row * pitch_h

            # کادر دور برچسب (خط برش)
            pdf.set_draw_color(190, 190, 190)
            pdf.set_line_width(0.15)
            pdf.rect(x, y, LABEL_W, LABEL_H)

            barcode_text = f"*{serial}*"
            # فرمول عرض Code39 در fpdf2: هر کاراکتر ≈ 16/3 برابر پارامتر w
            target_w = LABEL_W - 3
            bar_w = target_w / (len(barcode_text) * 16 / 3)
            actual_w = bar_w * len(barcode_text) * 16 / 3
            pdf.code39(barcode_text, x=x + (LABEL_W - actual_w) / 2, y=y + 0.6, w=bar_w, h=barcode_h)

            pdf.set_font('Fa', '', 6.5)
            pdf.set_xy(x, y + barcode_h + 0.9)
            pdf.cell(LABEL_W, 3, serial, align='C')

    filename = f"serials_{batch_id}_{int(time.time())}.pdf"
    filepath = os.path.join(PDF_JOBS_DIR, filename)
    pdf.output(filepath)
    return filepath, None
