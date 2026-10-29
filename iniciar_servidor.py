#!/usr/bin/env python3
"""Prepara o ambiente Django e inicia o servidor local do inventário."""

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT / 'gestao_ferramentas'
VENV = ROOT / '.venv'
REQUIREMENTS = ROOT / 'requirements.txt'


def run(command, **kwargs):
    subprocess.run(command, check=True, cwd=PROJECT, **kwargs)


def main():
    if not PROJECT.is_dir() or not REQUIREMENTS.is_file():
        raise SystemExit('Não encontrei gestao_ferramentas/ ou requirements.txt. Execute este arquivo na pasta principal do projeto.')

    python = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('Criando ambiente virtual .venv...')
        subprocess.run([sys.executable, '-m', 'venv', str(VENV)], check=True, cwd=ROOT)

    print('Instalando/verificando dependências...')
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(REQUIREMENTS)], check=True, cwd=ROOT)

    env = os.environ.copy()
    env.setdefault('DJANGO_DEBUG', 'True')
    env.setdefault('DJANGO_COOKIE_SECURE', 'False')
    host = env.get('DJANGO_RUNSERVER_HOST', '127.0.0.1')
    port = env.get('DJANGO_RUNSERVER_PORT', '8000')

    print('Aplicando migrações...')
    run([str(python), 'manage.py', 'migrate'], env=env)
    print(f'Servidor iniciado em http://{host}:{port}/ (Ctrl+C para encerrar)')
    run([str(python), 'manage.py', 'runserver', f'{host}:{port}'], env=env)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor encerrado.')
