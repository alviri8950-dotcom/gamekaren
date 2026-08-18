# gamekaren_project/app/migrations/0003_align_gametitle_schema.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_remove_transaction_device_gametitle_delete_device_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="gametitle",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="gametitle",
            name="source_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="gametitle",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=None),
            preserve_default=False,
        ),
    ]
