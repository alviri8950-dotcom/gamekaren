from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_party_phone_sms_notifications'),
    ]

    operations = [
        migrations.CreateModel(
            name='SerialCounter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefix', models.CharField(max_length=20, unique=True, verbose_name='پیشوند')),
                ('last_value', models.PositiveIntegerField(default=0, verbose_name='آخرین شماره صادرشده')),
            ],
            options={
                'verbose_name': 'شمارنده سریال',
                'verbose_name_plural': 'شمارنده‌های سریال',
            },
        ),
        migrations.CreateModel(
            name='GeneratedSerialBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefix', models.CharField(default='KAREN', max_length=20, verbose_name='پیشوند')),
                ('quantity', models.PositiveIntegerField(verbose_name='تعداد')),
                ('note', models.CharField(blank=True, default='', max_length=255, verbose_name='یادداشت (مثلاً نام کالا)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تولید')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='serial_batches', to='app.personnel', verbose_name='تولیدکننده')),
            ],
            options={
                'verbose_name': 'دسته سریال تولیدی',
                'verbose_name_plural': 'دسته‌های سریال تولیدی',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GeneratedSerial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(db_index=True, max_length=50, unique=True, verbose_name='سریال')),
                ('sequence_number', models.PositiveIntegerField(unique=True, verbose_name='شماره ترتیبی')),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='serials', to='app.generatedserialbatch', verbose_name='دسته')),
            ],
            options={
                'verbose_name': 'سریال تولیدی',
                'verbose_name_plural': 'سریال‌های تولیدی',
                'ordering': ['sequence_number'],
            },
        ),
    ]
