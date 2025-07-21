from django.test import TestCase
from core.models import Material

class MaterialModelTest(TestCase):
    def test_internal_code_generation(self):
        material = Material.objects.create(
            name="Test Malzeme",
            category="supplied",
            description="Test açıklaması"
        )
        self.assertIsNotNone(material.internal_code)
        self.assertEqual(len(material.internal_code), 14)
        self.assertTrue(material.internal_code.startswith("TED-"))