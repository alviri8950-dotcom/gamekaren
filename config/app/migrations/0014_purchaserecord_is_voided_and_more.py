from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_productgroup_devicetype_brand_devicetype_color_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaserecord',
            name='is_voided',
            field=models.BooleanField(default=False, verbose_name='ابطال\u200cشده'),
        ),
        migrations.AddField(
            model_name='purchaserecord',
            name='voided_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='تاریخ ابطال'),
        ),
        migrations.AddField(
            model_name='salerecord',
            name='is_voided',
            field=models.BooleanField(default=False, verbose_name='ابطال\u200cشده'),
        ),
        migrations.AddField(
            model_name='salerecord',
            name='voided_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='تاریخ ابطال'),
        ),
        migrations.AddField(
            model_name='gameinstallorder',
            name='is_voided',
            field=models.BooleanField(default=False, verbose_name='ابطال\u200cشده'),
        ),
        migrations.AddField(
            model_name='gameinstallorder',
            name='voided_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='تاریخ ابطال'),
        ),
    ]
