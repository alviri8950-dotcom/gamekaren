from django.urls import path
from . import views

urlpatterns = [
    # صفحه اصلی
    path('', views.index, name='game_index'),
    
    # کاتالوگ بازی‌ها
    path('catalog/', views.game_catalog, name='game_catalog'),
    
    # منوی انتخاب نوع ورود کالا (کنسول، لوازم جانبی و غیره)
    path('goods-entry-type/', views.goods_entry_type, name='game_goods_entry_type'),
    
    # صفحه ورود کالا (با پارامتر نوع ورودی)
    path('goods-entry/<str:entry_type>/', views.goods_entry, name='game_goods_entry'),
    
    # بخش‌های مربوط به نصب بازی
    path('install-tracking/', views.game_install_tracking, name='game_install_tracking'),
    path('install-delivery/', views.game_install_delivery, name='game_install_delivery'),
    path('install-report/', views.game_install_report, name='game_install_report'),
    
    # ثبت نهایی (اکشن‌ها)
    path('delivery-registration/', views.game_delivery_registration, name='game_delivery_registration'),

    # پیش‌نمایش صفحاتی که هنوز کامل نشدن (فقط تا NoReverseMatch رخ نده)
    path('game-install/', views.game_install_placeholder, name='game_install'),
    path('game-install/<int:order_id>/send/', views.install_stage2_send, name='install_stage2_send'),
    path('game-install/<int:order_id>/return/', views.install_stage3_return, name='install_stage3_return'),
    path('game-install/<int:order_id>/deliver/', views.install_stage4_deliver, name='install_stage4_deliver'),
    path('game-install/<int:order_id>/print/', views.install_print, name='install_print'),
    path('game-install/<int:order_id>/print/printer/', views.install_print_to_printer, name='install_print_to_printer'),

    path('parties/', views.parties_list, name='parties_list'),
    path('parties/<int:party_id>/', views.party_detail, name='party_detail'),
    path('parties/<int:party_id>/pay/', views.party_pay, name='party_pay'),

    path('expenses/', views.expense_entry, name='expense_entry'),
    path('expenses/<int:expense_id>/void/', views.expense_void, name='expense_void'),

    # فروش — فاکتور فروش کامل و فعال
    path('sale/', views.sale_entry, name='game_sales_invoice'),
    path('sale/<int:sale_id>/print/', views.sale_print, name='sale_print'),
    path('sale/<int:sale_id>/print-to-printer/', views.sale_print_to_printer, name='sale_print_to_printer'),
    path('api/serial-lookup/', views.serial_lookup, name='serial_lookup'),

    # کاربر فعال
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # خرید — ماژول کامل و فعال
    path('purchase/', views.purchase_entry, name='purchase_entry'),

    # امانی، تعمیرات، گزارش — فعلاً پیش‌نمایش، فیلدهاشون در مراحل بعد مشخص و کامل می‌شه
    path('consignment/', views.consignment_placeholder, name='consignment'),
    path('repair/', views.repair_placeholder, name='repair'),
    path('reports/', views.reports_home, name='reports_home'),
    path('reports/<str:report_type>/', views.report_detail, name='report_detail'),
    path('reports/<str:report_type>/print/', views.report_print, name='report_print'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('games/', views.games_manage, name='games_manage'),

    # تولید سریال برای کالاهای بدون سریال کارخانه‌ای + چاپ برچسب A4
    path('serial-generator/', views.serial_generator, name='serial_generator'),
    path('serial-generator/<int:batch_id>/print/', views.serial_labels_print, name='serial_labels_print'),

    # ابطال و ویرایش (از قسمت گزارش)
    path('purchase/<int:purchase_id>/void/', views.purchase_void, name='purchase_void'),
    path('purchase/<int:purchase_id>/edit/', views.purchase_edit, name='purchase_edit'),
    path('sale/<int:sale_id>/void/', views.sale_void, name='sale_void'),
    path('sale/<int:sale_id>/edit/', views.sale_edit, name='sale_edit'),
    path('install-order/<int:order_id>/void/', views.install_void, name='install_void'),
    path('install-order/<int:order_id>/edit/', views.install_edit, name='install_edit'),
]
