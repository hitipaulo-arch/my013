from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

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
    'Código M': 'codigo_m', 'Marca': 'marca', 'Modelo/Descrição': 'modelo',
    'Nº de Série/Ref.': 'numero_serie', 'Quantidade': 'quantidade',
    'Patrimônio': 'patrimonio', 'Responsável': 'responsavel', 'Departamento': 'departamento',
}


def normalize_row(row):
    result = {key.strip() if isinstance(key, str) else key: value.strip() if isinstance(value, str) else value
              for key, value in row.items() if key is not None}
    for canonical, aliases in CANON_MAP.items():
        if result.get(canonical) in (None, ''):
            for alias in [canonical, *aliases]:
                if result.get(alias) not in (None, ''):
                    result[canonical] = result[alias]
                    break
    quantity = result.get('Quantidade')
    if quantity in (None, ''):
        result['Quantidade'] = 1
    else:
        try:
            text = str(quantity).replace('\u00a0', '').replace(' ', '').replace(',', '.')
            number = float(text)
            if not number.is_integer() or number < 1:
                raise ValueError
            result['Quantidade'] = int(number)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f'Quantidade inválida: {quantity!r}; informe um inteiro maior que zero.')
    for key in ('Nº de Série/Ref.', 'Patrimônio', 'Responsável', 'Departamento'):
        if result.get(key) in ('', 'NULL', 'null'):
            result[key] = None
    return result


class Command(BaseCommand):
    help = 'Importa ou atualiza itens do inventário a partir de um arquivo CSV.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Caminho do arquivo CSV')
        parser.add_argument('--encoding', default='utf-8-sig', help='Codificação (padrão: utf-8-sig)')
        parser.add_argument('--delimiter', help='Delimitador; por padrão é detectado automaticamente')
        parser.add_argument('--dry-run', action='store_true', help='Valida e simula sem gravar no banco')

    def handle(self, *args, **options):
        path = Path(options['csv_path'])
        if not path.is_file():
            raise CommandError(f'Arquivo não encontrado: {path}')
        try:
            with path.open('r', encoding=options['encoding'], newline='') as source:
                sample = source.read(8192)
                source.seek(0)
                delimiter = options['delimiter']
                if delimiter is None:
                    try:
                        delimiter = csv.Sniffer().sniff(sample, delimiters=',;\t|').delimiter
                    except csv.Error:
                        delimiter = ','
                reader = csv.DictReader(source, delimiter=delimiter)
                if not reader.fieldnames:
                    raise CommandError('O CSV está vazio ou não contém cabeçalho.')
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise CommandError(f'Não foi possível ler o CSV: {exc}') from exc
        if len(reader.fieldnames) == 1:
            raise CommandError('Cabeçalho inválido: não foi possível identificar as colunas do CSV.')

        counts = {'total': 0, 'criados': 0, 'atualizados': 0, 'pulados': 0}
        # Cache local também garante que códigos repetidos no mesmo CSV sejam simulados corretamente.
        known = {obj.codigo_m: obj for obj in Item.objects.all()}
        pending_new = set()
        with transaction.atomic():
            for line, raw in enumerate(rows, start=2):
                counts['total'] += 1
                try:
                    normalized = normalize_row(raw)
                except ValueError as exc:
                    raise CommandError(f'Linha {line}: {exc}') from exc
                data = {field: normalized.get(column) for column, field in MODEL_FIELDS.items()}
                data['marca'] = data['marca'] or ''
                data['modelo'] = data['modelo'] or ''
                code = data['codigo_m']
                if not code:
                    counts['pulados'] += 1
                    continue
                obj = known.get(code)
                if obj is None:
                    obj = Item(**data)
                    known[code] = obj
                    pending_new.add(code)
                    counts['criados'] += 1
                    if not options['dry_run']:
                        obj.save()
                    continue
                changed = any(getattr(obj, field) != value for field, value in data.items())
                if changed:
                    for field, value in data.items():
                        setattr(obj, field, value)
                    counts['atualizados'] += 1
                    if not options['dry_run'] and code not in pending_new:
                        obj.save()
                    elif not options['dry_run']:
                        # The pending object was already inserted, so persist the subsequent row update.
                        obj.save()
                else:
                    counts['pulados'] += 1
            if options['dry_run']:
                transaction.set_rollback(True)

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN: nenhuma alteração foi gravada.'))
        self.stdout.write(self.style.SUCCESS(
            'Importação concluída. ' + ' '.join(f'{key}={value}' for key, value in counts.items())
            + f" (delimitador={delimiter!r})"
        ))
