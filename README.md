# Gestão de ferramentas

Aplicação Django para manter o inventário de ferramentas, com gestão pelo Admin e importação CSV.

## Início rápido

Com Python 3.10 ou superior instalado, execute na pasta principal do projeto:

```bash
python iniciar_servidor.py
```

O script cria `.venv` se necessário, instala/verifica as dependências, aplica as migrações e inicia o servidor em http://127.0.0.1:8000/. Encerre com `Ctrl+C`. Para criar o usuário administrador na primeira execução, abra outro terminal e execute `python gestao_ferramentas/manage.py createsuperuser` (com o ambiente virtual ativado).

## Requisitos e execução manual

- Python 3.10 ou superior
- Dependências em `requirements.txt`

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd gestao_ferramentas
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse http://127.0.0.1:8000/admin/ e autentique-se. A aplicação usa SQLite por padrão, criando `db.sqlite3` localmente.

## Importar CSV pela linha de comando

```bash
python manage.py import_itens caminho/itens.csv --dry-run
python manage.py import_itens caminho/itens.csv
```

O cabeçalho deve conter `Código M`; os demais nomes aceitam variantes documentadas no comando. Colunas reconhecidas: `Marca`, `Modelo/Descrição`, `Nº de Série/Ref.`, `Quantidade`, `Patrimônio`, `Responsável` e `Departamento`. O delimitador é detectado automaticamente (`;`, `,`, tabulação ou `|`); use `--delimiter` para defini-lo explicitamente. A codificação padrão é `utf-8-sig`; altere com `--encoding` se necessário.

`--dry-run` valida os dados e mostra os totais sem gravar qualquer inclusão ou atualização. Códigos existentes são atualizados. Quantidade deve ser um inteiro positivo; linhas sem `Código M` são ignoradas.

Também é possível importar/exportar pelo Admin, em **Itens do inventário** → **Import/Export**. Faça primeiro uma simulação (dry run) e revise o resultado.

## Configuração para produção

Defina as variáveis de ambiente `DJANGO_SECRET_KEY` (chave secreta forte), `DJANGO_DEBUG=False` e `DJANGO_ALLOWED_HOSTS` (hosts separados por vírgula). A configuração padrão serve apenas para desenvolvimento local; não publique a chave de desenvolvimento.

## Testes e verificações

Na pasta `gestao_ferramentas`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```
