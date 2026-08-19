from django.db import migrations, models


class Migration(migrations.Migration):
    """اصلاح نوع فیلد id در ۳ مدل تولید سریال از AutoField به BigAutoField —
    فقط یک تصحیح متادیتای Django است (هماهنگ با DEFAULT_AUTO_FIELD پروژه)،
    در SQLite هیچ تغییری در دادهٔ واقعی ستون ایجاد نمی‌کند."""

    dependencies = [
        ('app', '0025_serial_generator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serialcounter',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='generatedserialbatch',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='generatedserial',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
