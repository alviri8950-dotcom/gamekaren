from django.shortcuts import redirect
from django.urls import reverse


class RequireLoginMiddleware:
    """اگه کاربر لاگین نکرده باشه، به‌جز صفحه‌ی ورود و پنل ادمین جنگو (که خودش لاگین جدا داره)،
    هر صفحه‌ی دیگه‌ای رو به صفحه‌ی ورود هدایت می‌کنه."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        exempt = (
            path.startswith('/admin/')
            or path.startswith('/static/')
            or path.startswith('/media/')
            or path == reverse('login')
        )
        if not exempt:
            personnel_id = request.session.get('active_personnel_id')
            if not personnel_id:
                login_url = reverse('login')
                return redirect(f"{login_url}?next={path}")
        return self.get_response(request)
