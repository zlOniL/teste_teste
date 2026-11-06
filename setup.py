"""Configuração inicial. Executar python setup.py no terminal."""
from pathlib import Path
import getpass
import os
import re
import secrets
from app import connect, init_db, hash_password, now, BASE

def main():
    init_db()
    env=BASE/'.env'
    if not env.exists():
        secret=secrets.token_hex(32)
        env.write_text('SESSION_SECRET='+secret+'\nCOOKIE_SECURE=0\n',encoding='utf-8')
        try: os.chmod(env,0o600)
        except OSError: pass
        print('Criado .env. Para produção com HTTPS: COOKIE_SECURE=1')
    username=input('Usuário administrador (ex.: administrador): ').strip()
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{3,40}',username):
        raise SystemExit('Usuário inválido: 3-40 caracteres, letras/números/._-')
    password=getpass.getpass('Senha forte (min. 12 caracteres): ')
    confirm=getpass.getpass('Confirme a senha: ')
    if password!=confirm or len(password)<12 or len(set(password))<6:
        raise SystemExit('Senha inválida ou confirmação diferente. Use ao menos 12 caracteres variados.')
    with connect() as c:
        old=c.execute('SELECT id FROM admins WHERE username=?',(username,)).fetchone()
        if old:
            raise SystemExit('Usuário já existe. Nenhuma alteração realizada.')
        c.execute('INSERT INTO admins(username,password_hash,created_at) VALUES (?,?,?)',
                  (username,hash_password(password),now()))
    print('Administrador cadastrado. Inicie: uvicorn app:app --host 127.0.0.1 --port 8000')

if __name__=='__main__':main()
