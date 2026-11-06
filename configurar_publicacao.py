"""Assistente local para preparar configuração de produção. Não faz deploy."""
from pathlib import Path
import re
import secrets
import sys

base = Path(__file__).resolve().parent
target = base / '.env'
if target.exists():
    raise SystemExit('O arquivo .env já existe. Nenhum segredo foi alterado. Edite-o manualmente, se necessário.')
print('Configuração da publicação do site PL Serra')
print('Informe um domínio já adquirido, por exemplo: site.exemplo.com.br')
domain = input('Domínio (sem https://): ').strip().lower().rstrip('.')
ok = len(domain) <= 253 and re.fullmatch(r'(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', domain)
if not ok:
    raise SystemExit('Domínio inválido. Exemplo aceito: site.exemplo.com.br')
secret = secrets.token_hex(48)
target.write_text(f'DOMAIN={domain}\nSESSION_SECRET={secret}\n', encoding='utf-8')
try:
    target.chmod(0o600)
except OSError:
    pass
print(f'Configurado para https://{domain}')
print('Arquivo .env gerado. Mantenha-o privado.')
print('Próximo passo: docker compose build')
