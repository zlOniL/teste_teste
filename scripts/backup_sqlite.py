"""Backup consistente do SQLite para data/backups dentro do volume persistente."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from app import DB_PATH

folder = DB_PATH.parent / 'backups'
folder.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_UTC')
dest = folder / f'pl_serra_{stamp}.db'
with sqlite3.connect(DB_PATH) as src, sqlite3.connect(dest) as dst:
    src.backup(dst)
print('Backup concluído:', dest)
print('ATENÇÃO: também salve a pasta /app/data/media em outro local.')
