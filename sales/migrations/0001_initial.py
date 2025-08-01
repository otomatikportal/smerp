# Generated by Django 5.2.4 on 2025-07-25 05:29

import core.fields
import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0005_company_deleted_company_deleted_by_cascade_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalVariableCost',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('cost', models.DecimalField(decimal_places=3, max_digits=30, verbose_name='Birim maliyeti')),
                ('uom', core.fields.UOMField(choices=[('ADT', 'Adet'), ('KG', 'Kilogram'), ('G', 'Gram'), ('L', 'Litre'), ('ML', 'Mililitre'), ('M', 'Metre'), ('BOX', 'Koli'), ('PLT', 'Palet')], default='ADT', max_length=4, verbose_name='Birim')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('material', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='core.material', verbose_name='Malzeme')),
            ],
            options={
                'verbose_name': 'historical variable cost',
                'verbose_name_plural': 'historical variable costs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='VariableCost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('cost', models.DecimalField(decimal_places=3, max_digits=30, verbose_name='Birim maliyeti')),
                ('uom', core.fields.UOMField(choices=[('ADT', 'Adet'), ('KG', 'Kilogram'), ('G', 'Gram'), ('L', 'Litre'), ('ML', 'Mililitre'), ('M', 'Metre'), ('BOX', 'Koli'), ('PLT', 'Palet')], default='ADT', max_length=4, verbose_name='Birim')),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.material', verbose_name='Malzeme')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
