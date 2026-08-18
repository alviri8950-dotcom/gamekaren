from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_unify_prices_to_toman'),
    ]

    operations = [
        migrations.AddField(
            model_name='personnel',
            name='password_hash',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='رمز عبور (هش\u200cشده)'),
        ),
        migrations.AddField(
            model_name='personnel',
            name='can_purchase',
            field=models.BooleanField(default=True, verbose_name='دسترسی به ثبت خرید'),
        ),
        migrations.AddField(
            model_name='personnel',
            name='can_sale',
            field=models.BooleanField(default=True, verbose_name='دسترسی به ثبت فروش'),
        ),
        migrations.AddField(
            model_name='personnel',
            name='can_install',
            field=models.BooleanField(default=True, verbose_name='دسترسی به نصب بازی'),
        ),
        migrations.AddField(
            model_name='personnel',
            name='can_view_reports',
            field=models.BooleanField(default=False, verbose_name='دسترسی به گزارش\u200cها'),
        ),
        migrations.AddField(
            model_name='personnel',
            name='can_manage_parties',
            field=models.BooleanField(default=False, verbose_name='دسترسی به حساب اشخاص'),
        ),
        migrations.AddField(
            model_name='personnel',
            name='can_manage_expenses',
            field=models.BooleanField(default=False, verbose_name='دسترسی به ثبت هزینه'),
        ),
        migrations.AddField(
            model_name='personnel',
            name='can_void_or_edit',
            field=models.BooleanField(default=False, verbose_name='دسترسی به ویرایش/ابطال رکوردها'),
        ),
        migrations.AlterField(
            model_name='personnel',
            name='is_admin',
            field=models.BooleanField(default=False, verbose_name='دسترسی مدیر (همه\u200cچیز)'),
        ),
    ]
