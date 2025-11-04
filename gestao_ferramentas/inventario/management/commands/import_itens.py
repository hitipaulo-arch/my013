from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Any, Iterable, Optional

from django.core.management.base import BaseCommand, CommandError
from inventario.models import Item


CANON_MAP = {
    'Código M': ['Codigo M', 'CODIGO M', 'CódigoM', 'CODIGO_M', 'Cod M', 'Cod. M', 'codigo m'],
    'Marca': ['marca', 'MARCA'],
    'Modelo/Descrição': ['Modelo', 'Modelo / Descrição', 'Modelo - Descrição', 'Descrição', 'Descricao', 'modelo'],
    'Nº de Série/Ref.': ['No de Série/Ref.', 'N de Série/Ref.', 'Número de Série', 'Numero de Serie', 'Nº de Série', 'Nº Série', 'Nº Série/Ref', 'Numero de Série/Ref.'],
    'Quantidade': ['Qtde', 'Qtd', 'QTD', 'quantidade', 'QUANTIDADE'],
    'Patrimônio': ['Patrimonio', 'PAT', 'patrimonio'],
    'Responsável': ['Responsavel', 'RESPONSAVEL', 'responsável', 'responsavel'],
    'Departamento': ['Depto', 'Departamento/Setor', 'Setor', 'departamento'],
}

MODEL_FIELDS = {
    'Código M': 'codigo_m',
    'Marca': 'marca',
    'Modelo/Descrição': 'modelo',
    'Nº de Série/Ref.': 'numero_serie',
    'Quantidade': 'quantidade',
    'Patrimônio': 'patrimonio',
    'Responsável': 'responsavel',
    'Departamento': 'departamento',
}


def _first_present(row: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for k in keys:
        if k in row and row[k] not in (None, ''):
            return row[k]
    return None


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # Copy to avoid mutating the DictReader internals
    r = dict(row)

    # Fill canonical keys from alternate variants
    for canon_key, alt_keys in CANON_MAP.items():
        if canon_key not in r or r.get(canon_key) in (None, ''):
            val = _first_present(r, [canon_key] + alt_keys)
            if val is not None:
                r[canon_key] = val

    # Trim spaces on all string values
    for k, v in list(r.items()):
        if isinstance(v, str):
            r[k] = v.strip()

    # Quantidade: default 1, accept comma, cast to int
    q = r.get('Quantidade')
    if q in (None, ''):
        r['Quantidade'] = 1
    else:
        if isinstance(q, str):
            q_clean = q.replace('\u00A0', ' ').replace(',', '.').strip()
        else:
            q_clean = q
        try:
            r['Quantidade'] = int(float(q_clean))
        except Exception:
            r['Quantidade'] = 1

    # Optional empties -> None
    for optional_key in ['Nº de Série/Ref.', 'Patrimônio', 'Responsável', 'Departamento']:
        if r.get(optional_key) in ('', 'NULL', 'null'):
            r[optional_key] = None

    return r


class Command(BaseCommand):
    help = (
        "Importa itens do inventário a partir de um CSV.\n"
        "Detecta delimitador automaticamente (ou informe --delimiter).\n"
        "Campos esperados: Código M, Marca, Modelo/Descrição, Nº de Série/Ref., Quantidade, Patrimônio, Responsável, Departamento.\n"
        "Ex.: python manage.py import_itens C:/caminho/arquivo.csv --dry-run"
    )

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Caminho do arquivo CSV a importar')
        parser.add_argument('--encoding', type=str, default='utf-8-sig', help='Encoding do arquivo (padrão: utf-8-sig)')
        parser.add_argument('--delimiter', type=str, default=None, help='Delimitador (padrão: auto)')
        parser.add_argument('--dry-run', action='store_true', help='Não grava no banco, apenas simula')

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        encoding = options['encoding']
        delimiter = options['delimiter']
        dry_run = options['dry_run']

        if not csv_path.exists():
            raise CommandError(f"Arquivo não encontrado: {csv_path}")

        self.stdout.write(self.style.NOTICE(f"Lendo: {csv_path}"))

        with csv_path.open('r', encoding=encoding, newline='') as f:
            sample = f.read(4096)
            f.seek(0)
            if delimiter:
                used_delimiter = delimiter
            else:
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=[',', ';', '\t', '|'])
                    used_delimiter = dialect.delimiter
                except Exception:
                    used_delimiter = ','

            reader = csv.DictReader(f, delimiter=used_delimiter)
            total = 0
            created = 0
            updated = 0
            skipped = 0

            for row in reader:
                total += 1
                nr = normalize_row(row)

                codigo = nr.get('Código M')
                if not codigo:
                    skipped += 1
                    continue

                # Map to model fields
                data = {}
                for col, field in MODEL_FIELDS.items():
                    data[field] = nr.get(col)

                # Create or update
                obj, was_created = Item.objects.get_or_create(codigo_m=data['codigo_m'], defaults=data)
                if was_created:
                    created += 1
                else:
                    changed = False
                    for k, v in data.items():
                        if getattr(obj, k) != v:
                            setattr(obj, k, v)
                            changed = True
                    if changed:
                        if not dry_run:
                            obj.save()
                        updated += 1
                    else:
                        skipped += 1

            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN: nada foi gravado no banco."))

            self.stdout.write(
                self.style.SUCCESS(
                    f"Importação concluída. total={total} criados={created} atualizados={updated} pulados={skipped} (delimitador='{used_delimiter}')"
                )
            )
