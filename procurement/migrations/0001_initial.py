# Generated by Django 5.2.4 on 2025-07-21 14:03

import core.fields
import django.core.validators
import django.db.models.deletion
import simple_history.models
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0003_historicalmaterial_deleted_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalMaterialDemand',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('demand_no', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('uom', core.fields.UOMField(choices=[('ADT', 'Adet'), ('KG', 'Kilogram'), ('G', 'Gram'), ('L', 'Litre'), ('ML', 'Mililitre'), ('M', 'Metre'), ('BOX', 'Koli'), ('PLT', 'Palet')], default='ADT', max_length=4, verbose_name='Birim')),
                ('deadline', models.DateField()),
                ('description', models.TextField(max_length=500)),
                ('status', models.CharField(choices=[('submitted', 'Gönderildi'), ('approved', 'Onaylandı'), ('rejected', 'Reddedildi'), ('cancelled', 'İptal Edildi'), ('ordered', 'Sipariş Verildi'), ('received', 'Teslim Alındı'), ('closed', 'Kapandı')], default='draft', max_length=20)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('material', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='core.material')),
            ],
            options={
                'verbose_name': 'historical material demand',
                'verbose_name_plural': 'historical material demands',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalProcurementOrder',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('payment_term', models.CharField(choices=[('NET_T', 'Net T'), ('DUE_ON_RECEIPT', 'Due on Receipt'), ('CIA', 'Cash in Advance'), ('CWO', 'Cash with Order'), ('COD', 'Cash on Delivery'), ('CAD', 'Cash Against Documents'), ('EOM', 'End of Month'), ('T_EOM', 'T Days End of Month'), ('PROX', 'Proximo'), ('PARTIAL_ADVANCE', 'Partial Payment in Advance'), ('LC', 'Letter of Credit'), ('DC', 'Documentary Collection'), ('X_Y_NET_T', 'X/Y Net T'), ('TRADE_DISCOUNT', 'Trade Discount')], max_length=20, verbose_name='Vade Şartı')),
                ('payment_method', models.CharField(choices=[('BANK_TRANSFER', 'Banka Havalesi'), ('CASH', 'Nakit'), ('CREDIT_CARD', 'Kredi Kartı'), ('CHEQUE', 'Çek'), ('EFT', 'EFT'), ('PROMISSORY_NOTE', 'Senet'), ('OTHER', 'Diğer')], max_length=20, verbose_name='Ödeme Yöntemi')),
                ('incoterms', models.CharField(choices=[('EXW', 'Ex Works'), ('FCA', 'Free Carrier'), ('FAS', 'Free Alongside Ship'), ('FOB', 'Free On Board'), ('CFR', 'Cost and Freight'), ('CIF', 'Cost, Insurance and Freight'), ('CPT', 'Carriage Paid To'), ('CIP', 'Carriage and Insurance Paid To'), ('DAP', 'Delivered At Place'), ('DPU', 'Delivered at Place Unloaded'), ('DDP', 'Delivered Duty Paid')], max_length=20, verbose_name='Teslim Şekli (Incoterms)')),
                ('trade_discount', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('due_in_days', models.DurationField()),
                ('due_discount', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('due_discount_days', models.DurationField()),
                ('invoice_accepted', models.DateField()),
                ('description', models.TextField(max_length=500)),
                ('status', models.CharField(choices=[('draft', 'Taslak'), ('approved', 'Onaylandı'), ('rejected', 'Reddedildi'), ('ordered', 'Sipariş verildi'), ('billed', 'Faturalandı'), ('paid', 'Ödendi'), ('cancelled', 'İptal edildi')], default='draft', max_length=20)),
                ('currency', core.fields.CurrencyField(choices=[('TRY', 'Türk Lirası'), ('USD', 'ABD Doları'), ('EUR', 'Euro'), ('GBP', 'İngiliz Sterlini'), ('JPY', 'Japon Yeni'), ('CHF', 'İsviçre Frangı'), ('RUB', 'Rus Rublesi'), ('CNY', 'Çin Yuanı'), ('SEK', 'İsveç Kronu'), ('AUD', 'Avustralya Doları')], default='TRY', max_length=6)),
                ('delivery_address', models.CharField(max_length=250, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='core.company')),
            ],
            options={
                'verbose_name': 'historical procurement order',
                'verbose_name_plural': 'historical procurement orders',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='MaterialDemand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('demand_no', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('uom', core.fields.UOMField(choices=[('ADT', 'Adet'), ('KG', 'Kilogram'), ('G', 'Gram'), ('L', 'Litre'), ('ML', 'Mililitre'), ('M', 'Metre'), ('BOX', 'Koli'), ('PLT', 'Palet')], default='ADT', max_length=4, verbose_name='Birim')),
                ('deadline', models.DateField()),
                ('description', models.TextField(max_length=500)),
                ('status', models.CharField(choices=[('submitted', 'Gönderildi'), ('approved', 'Onaylandı'), ('rejected', 'Reddedildi'), ('cancelled', 'İptal Edildi'), ('ordered', 'Sipariş Verildi'), ('received', 'Teslim Alındı'), ('closed', 'Kapandı')], default='draft', max_length=20)),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='demands', to='core.material')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProcurementOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('payment_term', models.CharField(choices=[('NET_T', 'Net T'), ('DUE_ON_RECEIPT', 'Due on Receipt'), ('CIA', 'Cash in Advance'), ('CWO', 'Cash with Order'), ('COD', 'Cash on Delivery'), ('CAD', 'Cash Against Documents'), ('EOM', 'End of Month'), ('T_EOM', 'T Days End of Month'), ('PROX', 'Proximo'), ('PARTIAL_ADVANCE', 'Partial Payment in Advance'), ('LC', 'Letter of Credit'), ('DC', 'Documentary Collection'), ('X_Y_NET_T', 'X/Y Net T'), ('TRADE_DISCOUNT', 'Trade Discount')], max_length=20, verbose_name='Vade Şartı')),
                ('payment_method', models.CharField(choices=[('BANK_TRANSFER', 'Banka Havalesi'), ('CASH', 'Nakit'), ('CREDIT_CARD', 'Kredi Kartı'), ('CHEQUE', 'Çek'), ('EFT', 'EFT'), ('PROMISSORY_NOTE', 'Senet'), ('OTHER', 'Diğer')], max_length=20, verbose_name='Ödeme Yöntemi')),
                ('incoterms', models.CharField(choices=[('EXW', 'Ex Works'), ('FCA', 'Free Carrier'), ('FAS', 'Free Alongside Ship'), ('FOB', 'Free On Board'), ('CFR', 'Cost and Freight'), ('CIF', 'Cost, Insurance and Freight'), ('CPT', 'Carriage Paid To'), ('CIP', 'Carriage and Insurance Paid To'), ('DAP', 'Delivered At Place'), ('DPU', 'Delivered at Place Unloaded'), ('DDP', 'Delivered Duty Paid')], max_length=20, verbose_name='Teslim Şekli (Incoterms)')),
                ('trade_discount', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('due_in_days', models.DurationField()),
                ('due_discount', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('due_discount_days', models.DurationField()),
                ('invoice_accepted', models.DateField()),
                ('description', models.TextField(max_length=500)),
                ('status', models.CharField(choices=[('draft', 'Taslak'), ('approved', 'Onaylandı'), ('rejected', 'Reddedildi'), ('ordered', 'Sipariş verildi'), ('billed', 'Faturalandı'), ('paid', 'Ödendi'), ('cancelled', 'İptal edildi')], default='draft', max_length=20)),
                ('currency', core.fields.CurrencyField(choices=[('TRY', 'Türk Lirası'), ('USD', 'ABD Doları'), ('EUR', 'Euro'), ('GBP', 'İngiliz Sterlini'), ('JPY', 'Japon Yeni'), ('CHF', 'İsviçre Frangı'), ('RUB', 'Rus Rublesi'), ('CNY', 'Çin Yuanı'), ('SEK', 'İsveç Kronu'), ('AUD', 'Avustralya Doları')], default='TRY', max_length=6)),
                ('delivery_address', models.CharField(max_length=250, null=True)),
                ('vendor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.company')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProcurementInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('invoice_number', models.CharField(max_length=50)),
                ('po', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='procurement.procurementorder')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalProcurementOrderLine',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('quantity', core.fields.UOMField(choices=[('ADT', 'Adet'), ('KG', 'Kilogram'), ('G', 'Gram'), ('L', 'Litre'), ('ML', 'Mililitre'), ('M', 'Metre'), ('BOX', 'Koli'), ('PLT', 'Palet')], default='ADT', max_length=4, verbose_name='Birim')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=32)),
                ('tax_rate', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('material', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='core.material')),
                ('po', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='procurement.procurementorder')),
            ],
            options={
                'verbose_name': 'historical procurement order line',
                'verbose_name_plural': 'historical procurement order lines',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='ProcurementOrderLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('quantity', core.fields.UOMField(choices=[('ADT', 'Adet'), ('KG', 'Kilogram'), ('G', 'Gram'), ('L', 'Litre'), ('ML', 'Mililitre'), ('M', 'Metre'), ('BOX', 'Koli'), ('PLT', 'Palet')], default='ADT', max_length=4, verbose_name='Birim')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=32)),
                ('tax_rate', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.material')),
                ('po', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='procurement.procurementorder')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
