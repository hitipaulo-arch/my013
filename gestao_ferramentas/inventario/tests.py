import tempfile

from django.db import IntegrityError, transaction
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .management.commands.import_itens import normalize_row
from .models import Item


class ItemModelTests(TestCase):
    def test_codigo_m_is_unique(self):
        Item.objects.create(codigo_m='A-1')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Item.objects.create(codigo_m='A-1')


class ImportItensTests(TestCase):
    def run_csv(self, content, *args):
        handle = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', suffix='.csv', delete=False)
        try:
            handle.write(content)
            handle.close()
            call_command('import_itens', handle.name, *args, stdout=None)
        finally:
            Path(handle.name).unlink(missing_ok=True)

    def test_dry_run_does_not_write_new_items(self):
        self.run_csv('Código M,Marca,Quantidade\nA-1,Acme,2\n', '--dry-run')
        self.assertFalse(Item.objects.exists())

    def test_import_creates_and_updates_by_code(self):
        self.run_csv('Código M,Marca,Quantidade\nA-1,Acme,2\n')
        self.run_csv('Código M,Marca,Quantidade\nA-1,Acme,3\n')
        self.assertEqual(Item.objects.get(codigo_m='A-1').quantidade, 3)
        self.assertEqual(Item.objects.count(), 1)

    def test_invalid_quantity_fails_loudly(self):
        with self.assertRaises(CommandError):
            self.run_csv('Código M,Quantidade\nA-1,abc\n')
        self.assertFalse(Item.objects.exists())

    def test_quantity_normalization_rejects_fractional_value(self):
        with self.assertRaises(ValueError):
            normalize_row({'Código M': 'A-1', 'Quantidade': '2,5'})
