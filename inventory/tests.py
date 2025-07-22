from django.test import TestCase
from .models import InventoryLocation

class InventoryLocationTestCase(TestCase):
    def test_name_auto_generation(self):
        # Test with area=1, section=2, shelf=3, bin=4
        loc = InventoryLocation(area=1, section=2, shelf=3, bin=4)
        loc.save()
        self.assertEqual(loc.name, "A2-R3-P4")

    def test_name_with_zero_shelf(self):
        # Test with shelf=0 should set middle to 'Z'
        loc = InventoryLocation(area=2, section=1, shelf=0, bin=5)
        loc.save()
        self.assertEqual(loc.name, "B1-Z-P5")

    def test_name_with_missing_bin(self):
        # Test with bin=None should omit end
        loc = InventoryLocation(area=3, section=4, shelf=2, bin=None)
        loc.save()
        self.assertEqual(loc.name, "C4-R2")

    def test_name_with_missing_area(self):
        # Test with area=None should default area_str to 'A'
        loc = InventoryLocation(area=None, section=3, shelf=1, bin=2)
        loc.save()
        self.assertEqual(loc.name, "A3-R1-P2")

    def test_name_with_missing_section(self):
        # Test with section=None should default section_str to '1'
        loc = InventoryLocation(area=1, section=None, shelf=1, bin=2)
        loc.save()
        self.assertEqual(loc.name, "A1-R1-P2")
from django.test import TestCase

# Create your tests here.
