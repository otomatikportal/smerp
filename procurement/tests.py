from decimal import Decimal
from django.test import TestCase
from core.models import Company, Material
from procurement.models import ProcurementOrder, ProcurementOrderLine

class ProcurementOrderCalculationTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Vendor", legal_name="Test Vendor Ltd.")
        self.material1 = Material.objects.create(name="Test Material 1", category="supplied")
        self.material2 = Material.objects.create(name="Test Material 2", category="supplied")
        self.po = ProcurementOrder.objects.create(
            vendor=self.company,
            payment_term="NET_T",
            payment_method="BANK_TRANSFER",
            incoterms="EXW",
            trade_discount=Decimal("0.05"),  # 5%
            due_in_days="7 0:00:00",
            due_discount=Decimal("0.02"),   # 2%
            due_discount_days="5 0:00:00",
            description="Test PO",
            status="draft",
            currency="TRY",
            delivery_address="Test Address"
        )
        ProcurementOrderLine.objects.create(
            po=self.po,
            material=self.material1,
            quantity=10,
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("0.18")  # 18%
        )
        ProcurementOrderLine.objects.create(
            po=self.po,
            material=self.material2,
            quantity=5,
            unit_price=Decimal("200.00"),
            tax_rate=Decimal("0.08")  # 8%
        )

    def test_total_price_without_tax(self):
        # (10*100) + (5*200) = 1000 + 1000 = 2000
        # discount = 2000 * (0.05 + 0.02) = 140
        # total = 2000 - 140 = 1860
        self.assertEqual(self.po.total_price_without_tax, Decimal("1860.00"))

    def test_total_price_with_tax(self):
        # tax: (10*100*0.18) + (5*200*0.08) = 180 + 80 = 260
        # total = 1860 + 260 = 2120
        self.assertEqual(self.po.total_price_with_tax, Decimal("2120.00"))

    def test_last_payment_date(self):
        from datetime import date, timedelta
        # NET_T: invoice_date + due_in_days
        po = ProcurementOrder.objects.create(
            vendor=self.company,
            payment_term="NET_T",
            payment_method="BANK_TRANSFER",
            incoterms="EXW",
            trade_discount=Decimal("0.05"),
            due_in_days=timedelta(days=7),
            due_discount=Decimal("0.02"),
            due_discount_days=timedelta(days=5),
            invoice_date=date(2025, 7, 22),
            description="Test PO",
            status="draft",
            currency="TRY",
            delivery_address="Test Address"
        )
        self.assertEqual(po.last_payment_date, date(2025, 7, 29))

        # EOM: end of invoice_date's month
        po.payment_term = "EOM"
        po.save()
        self.assertEqual(po.last_payment_date, date(2025, 7, 31))

        # T_EOM: end of next month + due_in_days
        po.payment_term = "T_EOM"
        po.save()
        # End of next month (August 2025) is 2025-08-31 + 7 days = 2025-09-07
        self.assertEqual(po.last_payment_date, date(2025, 9, 7))

        # PARTIAL_ADVANCE: invoice_date + due_in_days
        po.payment_term = "PARTIAL_ADVANCE"
        po.save()
        self.assertEqual(po.last_payment_date, date(2025, 7, 29))

        # X_Y_NET_T: invoice_date + due_in_days
        po.payment_term = "X_Y_NET_T"
        po.save()
        self.assertEqual(po.last_payment_date, date(2025, 7, 29))
from django.test import TestCase

# Create your tests here.
