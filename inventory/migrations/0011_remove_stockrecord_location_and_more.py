# Generated by Django 5.2.4 on 2025-07-31 12:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_alter_stockrecord_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockrecord',
            name='location',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='material',
        ),
        migrations.DeleteModel(
            name='HistoricalStockRecord',
        ),
        migrations.DeleteModel(
            name='StockRecord',
        ),
    ]
