# app/context_processors.py
from .models import Personnel


def active_user_context(request):
    """کاربر فعال فعلی و لیست پرسنل فعال را در تمام قالب‌ها در دسترس می‌گذارد
    تا نوار بالای صفحه بتواند انتخابگر «کاربر فعال» را نمایش دهد."""
    active_personnel = None
    active_id = request.session.get('active_personnel_id') if hasattr(request, 'session') else None
    if active_id:
        active_personnel = Personnel.objects.filter(id=active_id, is_active=True).first()
    return {
        'active_personnel': active_personnel,
        'all_personnel': Personnel.objects.filter(is_active=True).order_by('name'),
    }
