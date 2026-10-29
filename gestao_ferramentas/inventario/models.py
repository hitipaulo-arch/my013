from django.core.validators import MinValueValidator
from django.db import models


class Item(models.Model):
    codigo_m = models.CharField('Código M', max_length=100, unique=True)
    marca = models.CharField('Marca', max_length=150, blank=True)
    modelo = models.CharField('Modelo/Descrição', max_length=255, blank=True)
    numero_serie = models.CharField('Nº de Série/Ref.', max_length=150, blank=True, null=True)
    quantidade = models.PositiveIntegerField('Quantidade', default=1, validators=[MinValueValidator(1)])
    patrimonio = models.CharField('Patrimônio', max_length=100, blank=True, null=True)
    responsavel = models.CharField('Responsável', max_length=150, blank=True, null=True)
    departamento = models.CharField('Departamento', max_length=150, blank=True, null=True)

    class Meta:
        ordering = ['codigo_m']
        verbose_name = 'Item do inventário'
        verbose_name_plural = 'Itens do inventário'

    def __str__(self):
        return f'{self.codigo_m} — {self.modelo or self.marca or "Item"}'
