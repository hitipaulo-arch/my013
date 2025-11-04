# Em inventario/admin.py
from django.contrib import admin
from .models import Item

# Importe as classes necessárias da biblioteca
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields

# 1. Crie uma classe "Resource"
# Esta classe diz à biblioteca quais campos ela deve importar/exportar
class ItemResource(resources.ModelResource):
    # Mapeamento explícito de nomes de colunas (cabecalhos) da planilha para campos do modelo
    # Ajuste os nomes em column_name para casar com os cabeçalhos reais do seu CSV
    codigo_m = fields.Field(attribute='codigo_m', column_name='Código M')
    marca = fields.Field(attribute='marca', column_name='Marca')
    modelo = fields.Field(attribute='modelo', column_name='Modelo/Descrição')
    numero_serie = fields.Field(attribute='numero_serie', column_name='Nº de Série/Ref.')
    quantidade = fields.Field(attribute='quantidade', column_name='Quantidade')
    patrimonio = fields.Field(attribute='patrimonio', column_name='Patrimônio')
    responsavel = fields.Field(attribute='responsavel', column_name='Responsável')
    departamento = fields.Field(attribute='departamento', column_name='Departamento')

    class Meta:
        model = Item
        # Evita recriar registros inalterados e reporta pulados
        skip_unchanged = True
        report_skipped = True
        # Usa o campo único como identificador para atualização (se já existir)
        import_id_fields = ('codigo_m',)

    # Normaliza linhas antes da importação
    def before_import_row(self, row, row_number=None, **kwargs):
        # Mapear variações de cabeçalho para os nomes canônicos usados acima
        canonical = {
            'Código M': ['Codigo M', 'CODIGO M', 'CódigoM', 'CODIGO_M', 'Cod M', 'Cod. M'],
            'Marca': ['marca', 'MARCA'],
            'Modelo/Descrição': ['Modelo', 'Modelo / Descrição', 'Modelo - Descrição', 'Descrição', 'Descricao'],
            'Nº de Série/Ref.': ['No de Série/Ref.', 'N de Série/Ref.', 'Número de Série', 'Numero de Serie', 'Nº de Série', 'Nº Série', 'Nº Série/Ref'],
            'Quantidade': ['Qtde', 'Qtd', 'QTD', 'quantidade', 'QUANTIDADE'],
            'Patrimônio': ['Patrimonio', 'PAT'],
            'Responsável': ['Responsavel', 'RESPONSAVEL'],
            'Departamento': ['Depto', 'Departamento/Setor', 'Setor']
        }

        def first_present(row_map, keys):
            for k in keys:
                if k in row_map and row_map[k] not in (None, ''):
                    return row_map[k]
            return None

        # Preencher valores canônicos a partir de variações, se ausentes
        for canon_key, alt_keys in canonical.items():
            if canon_key not in row or row[canon_key] in (None, ''):
                val = first_present(row, [canon_key] + alt_keys)
                if val is not None:
                    row[canon_key] = val

        # Trim espaços em strings
        for k in list(row.keys()):
            v = row.get(k)
            if isinstance(v, str):
                row[k] = v.strip()

        # Quantidade: padrão 1, converter para int (aceita vírgula)
        q = row.get('Quantidade')
        if q in (None, ''):
            row['Quantidade'] = 1
        else:
            if isinstance(q, str):
                q_clean = q.replace('\u00A0', ' ').replace(',', '.').strip()
            else:
                q_clean = q
            try:
                row['Quantidade'] = int(float(q_clean))
            except Exception:
                row['Quantidade'] = 1

        # Campos opcionais vazios -> None
        for optional_key in ['Nº de Série/Ref.', 'Patrimônio', 'Responsável', 'Departamento']:
            if row.get(optional_key) in ('', 'NULL', 'null'):
                row[optional_key] = None

# 2. Crie uma classe "Admin" que usa a biblioteca
# Nós não usamos mais "admin.site.register(Item)"
@admin.register(Item)
class ItemAdmin(ImportExportModelAdmin):
    # Diga ao admin para usar o Resource que criamos
    resource_class = ItemResource
    
    # (Opcional) Isso melhora a visualização da lista no admin
    list_display = ('codigo_m', 'modelo', 'marca', 'responsavel', 'departamento', 'quantidade')
    search_fields = ('modelo', 'codigo_m', 'responsavel', 'patrimonio')
    list_filter = ('departamento', 'marca', 'responsavel')