"""Cria o primeiro usuário do painel, no banco persistido pelo Compose."""
import getpass
import re
from app import connect, init_db, hash_password, now

init_db()
print('CRIAR ADMINISTRADOR | PL SERRA')
username = input('Usuário (3 a 40 caracteres): ').strip()
if not re.fullmatch(r'[a-zA-Z0-9_.-]{3,40}', username):
    raise SystemExit('Usuário inválido.')
pw = getpass.getpass('Senha forte (mínimo 12 caracteres): ')
check = getpass.getpass('Confirme a senha: ')
if pw != check or len(pw) < 12 or len(set(pw)) < 6:
    raise SystemExit('Senhas não conferem ou são fracas.')
with connect() as db:
    if db.execute('SELECT id FROM admins WHERE username=?', (username,)).fetchone():
        raise SystemExit('Este usuário já existe. Nenhuma alteração feita.')
    db.execute('INSERT INTO admins(username, password_hash, created_at) VALUES(?,?,?)',
               (username, hash_password(pw), now()))
print('Administrador criado com sucesso no banco de dados persistente.')
