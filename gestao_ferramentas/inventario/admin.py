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