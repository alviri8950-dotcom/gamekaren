import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_gameinstallorder_stage_is_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='balance',
            field=models.BigIntegerField(default=0, verbose_name='موجودی (تومان)'),
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='نام')),
                ('kind', models.CharField(choices=[
                    ('supplier', 'تأمین‌کننده'), ('installer', 'نصاب'),
                    ('customer', 'مشتری'), ('other', 'سایر'),
                ], default='other', max_length=20, verbose_name='نوع')),
                ('balance', models.BigIntegerField(default=0, verbose_name='مانده حساب (تومان)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'شخص (حساب اشخاص)',
                'verbose_name_plural': 'اشخاص (حساب اشخاص)',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PartyLedgerEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.BigIntegerField(verbose_name='مبلغ (تومان)')),
                ('balance_after', models.BigIntegerField(default=0, verbose_name='مانده پس از این رویداد')),
                ('description', models.CharField(blank=True, default='', max_length=255, verbose_name='شرح')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='تاریخ و ساعت')),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='app.party', verbose_name='شخص')),
            ],
            options={
                'verbose_name': 'تراکنش حساب شخص',
                'verbose_name_plural': 'تراکنش‌های حساب اشخاص',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='payment',
            name='party',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='sale_payments', to='app.party', verbose_name='شخص (حساب اشخاص)',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_type',
            field=models.CharField(choices=[
                ('pos', 'پوز (کارتخوان)'), ('transfer', 'انتقال بانکی'), ('party_account', 'حساب اشخاص (نسیه)'),
            ], max_length=20, verbose_name='نوع پرداخت'),
        ),
    ]
