# Generated by Django 5.2.4 on 2025-07-23 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_company_deleted_company_deleted_by_cascade_and_more'),
        ('inventory', '0004_rename_historicalinventory_historicalstockrecord_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalstockrecord',
            name='deleted',
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='historicalstockrecord',
            name='deleted_by_cascade',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='inventorylocation',
            name='deleted',
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='inventorylocation',
            name='deleted_by_cascade',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='inventorylocation',
            name='height',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, verbose_name='Yüksekliği (cm)'),
        ),
        migrations.AddField(
            model_name='stockrecord',
            name='deleted',
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='stockrecord',
            name='deleted_by_cascade',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name='inventorylocation',
            name='width',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True, verbose_name='Genişliği (cm)'),
        ),
        migrations.AlterUniqueTogether(
            name='stockrecord',
            unique_together={('material', 'uom', 'location')},
        ),
    ]
