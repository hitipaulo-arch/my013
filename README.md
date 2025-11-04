# gestao_ferramentas

Django project scaffold created with `django-admin startproject`.

Quick start (PowerShell):

```powershell
Set-Location 'C:\Users\automacao\my-project\Controle_Ferramenta'
.\.venv\Scripts\Activate.ps1
python -m django --version
python manage.py runserver
```

Notes:
# gestao_ferramentas

[![Django CI](https://github.com/hitipaulo-arch/my013/actions/workflows/django-ci.yml/badge.svg)](https://github.com/hitipaulo-arch/my013/actions/workflows/django-ci.yml)

Projeto Django para gestão de ferramentas.

## Como rodar (PowerShell)

```powershell
Set-Location 'C:\\Users\\automacao\\my-project\\Controle_Ferramenta'
.\\.venv\\Scripts\\Activate.ps1
python -m django --version
Set-Location .\\gestao_ferramentas
python manage.py runserver
```

## Importação pelo Admin (django-import-export)

1. Acesse http://127.0.0.1:8000/admin/ e entre com seu usuário admin.
2. Vá em "Itens do Inventário" → "Import".
3. Selecione o arquivo CSV (UTF-8). Cabeçalhos esperados:
	- Código M, Marca, Modelo/Descrição, Nº de Série/Ref., Quantidade, Patrimônio, Responsável, Departamento
4. Faça um "Dry run" e, se estiver ok, confirme a importação.

Observações:
- Campo identificador único: "Código M" (atualiza se já existir).
- Suporte a XLSX via `openpyxl` já instalado.

## Notas
- Virtualenv: `.venv` com Django e dependências instaladas.
- Banco: SQLite (`db.sqlite3`) (ignorado pelo `.gitignore`).
