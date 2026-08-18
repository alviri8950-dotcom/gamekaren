from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_party_ledger_bank_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameinstallorder',
            name='installer_fee',
            field=models.BigIntegerField(blank=True, null=True, verbose_name='دستمزد نصاب (تومان)'),
        ),
    ]
