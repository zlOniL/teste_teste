"""Site institucional PL Serra: noticias e contatos com administração autenticada.

Publicação institucional. A prévia da filiação incorporada ao site não coleta dados.
"""
from __future__ import annotations

import hashlib
import html
import json
import hmac
import io
import os
import re
import secrets
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image, UnidentifiedImageError
from starlette.middleware.sessions import SessionMiddleware

BASE = Path(__file__).resolve().parent
SITE = BASE / 'site'
DATA = BASE / 'data'
MEDIA = DATA / 'media'
DB_PATH = Path(os.environ.get('PL_SERRA_DATABASE', str(DATA / 'pl_serra.db')))
MAX_IMAGE = 5 * 1024 * 1024
CATEGORIES = ('Notícia', 'Comunicado', 'Evento', 'Institucional')

# configuração local, nunca versionar .env real
if (BASE / '.env').exists():
    for line in (BASE / '.env').read_text('utf-8').splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"'))

app = FastAPI(title='PL Serra | Portal institucional', docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1024)

class CachedFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        # Versioned stylesheet/script URLs are safe for long-lived immutable caching.
        if re.search(r'\.[a-f0-9]{12}\.(css|js)$', path):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        else:
            response.headers['Cache-Control'] = 'public, max-age=604800'
        return response

app.mount('/assets', CachedFiles(directory=str(SITE/'assets')), name='assets')

app.add_middleware(SessionMiddleware,
                   secret_key=os.getenv('SESSION_SECRET') or secrets.token_hex(32),
                   session_cookie='pl_serra_admin',
                   same_site='strict',
                   https_only=os.getenv('COOKIE_SECURE', '0') == '1',
                   max_age=60 * 60 * 6)
MEDIA.mkdir(parents=True, exist_ok=True)
app.mount('/media', CachedFiles(directory=str(MEDIA)), name='media')
templates = Environment(loader=FileSystemLoader(str(BASE / 'templates')),
                        autoescape=select_autoescape(['html', 'xml']))


def public_site_url():
    """Full public HTTPS origin, configured by the site owner after deploying."""
    raw = os.getenv('SITE_URL', '').strip().rstrip('/')
    parts = urlparse(raw)
    if parts.scheme == 'https' and parts.hostname and not parts.username and not parts.password:
        return raw
    return ''


def json_for_html(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def render_initial_news(rows):
    """Server-rendered news links remain discoverable without JavaScript."""
    rendered = []
    for row in rows:
        title = html.escape(row['titulo'])
        summary = html.escape(row['resumo'])
        category = html.escape(row['categoria'])
        slug = html.escape(row['slug'], quote=True)
        date = html.escape((row['published_at'] or '')[:10])
        src = row['imagem'] or ''
        if src:
            thumb = src.replace('/media/', '/media/thumbs/')
            if (MEDIA / 'thumbs' / Path(src).name).is_file(): src = thumb
            image = f'<img src="{html.escape(src,quote=True)}" alt="" loading="lazy" decoding="async" width="560" height="350">'
        else:
            image = 'PL 22'
        rendered.append(f"""<article class="news-card"><div class="news-card-image">{image}</div>
        <div class="news-card-content"><span class="news-card-kicker">{category}</span>
        <h3>{title}</h3><p>{summary}</p>
        <div class="news-card-foot"><time datetime="{date}">{date}</time>
        <a href="/noticias/{slug}">Ler notícia →</a></div></div></article>""")
    return ''.join(rendered)


# Cache the static shell only, not the news list; server-side HTML changes on publication.
HOME_SHELL = (SITE / 'index.html').read_text('utf-8')

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


def init_db():
    with connect() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            resumo TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status in ('rascunho','publicado')),
            imagem TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            published_at TEXT
        );
        CREATE TABLE IF NOT EXISTS contatos (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL DEFAULT ''
        );
        ''')
        for k in ('telefone', 'whatsapp', 'instagram', 'facebook', 'youtube'):
            c.execute('INSERT OR IGNORE INTO contatos(chave,valor) VALUES (?,?)', (k, ''))


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f'scrypt$16384$8$1${salt.hex()}${digest.hex()}'


def verify_password(password, encoded):
    try:
        alg,n,r,p,salt,digest = encoded.split('$')
        if alg != 'scrypt': return False
        value = hashlib.scrypt(password.encode('utf-8'), salt=bytes.fromhex(salt),
                              n=int(n),r=int(r),p=int(p),dklen=32)
        return hmac.compare_digest(value,bytes.fromhex(digest))
    except (ValueError, TypeError, MemoryError):
        return False


def safe_slug(text):
    t = unicodedata.normalize('NFKD', text)
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
    return t[:72] or 'noticia'


def unique_slug(conn,title,skip_id=None):
    base=safe_slug(title)
    suffix=base; i=2
    while conn.execute('SELECT 1 FROM noticias WHERE slug=? AND id!=?',(suffix,skip_id or -1)).fetchone():
        suffix=f'{base[:64]}-{i}'; i+=1
    return suffix


def csrf(request):
    if not request.session.get('csrf'):
        request.session['csrf'] = secrets.token_urlsafe(32)
    return request.session['csrf']


def check_csrf(request,submitted):
    expected=request.session.get('csrf')
    if not expected or not submitted or not hmac.compare_digest(str(submitted), expected):
        raise HTTPException(status_code=403,detail='Solicitação inválida. Recarregue a página e tente novamente.')


def current_admin(request):
    admin_id=request.session.get('admin_id')
    if not isinstance(admin_id,int): return None
    with connect() as c:
        return c.execute('SELECT id,username FROM admins WHERE id=?',(admin_id,)).fetchone()


def admin_only(request):
    adm=current_admin(request)
    return adm if adm else None


def html_template(name, request, status_code=200, **values):
    # Jinja2 autoescape para textos inseridos pela administração
    resp=HTMLResponse(templates.get_template(name).render(**values,csrf=csrf(request)),status_code=status_code)
    resp.headers['Cache-Control']='no-store'
    resp.headers['X-Robots-Tag']='noindex, nofollow'
    return resp


def home_redirect(path='/admin'):
    return RedirectResponse(path,status_code=303)


def image_processing_sync(blob):
    try:
        im = Image.open(io.BytesIO(blob))
        if im.format not in ('JPEG','PNG','WEBP'):
            raise ValueError('Envie uma imagem JPG, PNG ou WebP.')
        if im.width*im.height > 20_000_000 or min(im.size) < 100:
            raise ValueError('Dimensões inválidas ou excessivas.')
        im.thumbnail((1600, 1200))
        out=io.BytesIO()
        # reencodar remove EXIF e outros metadados por privacidade
        im.convert('RGB').save(out, format='WEBP', quality=84, method=4)
        return out.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as e:
        raise ValueError(str(e) if str(e) else 'Imagem inválida')


async def maybe_save_upload(upload):
    if not upload or not upload.filename:
        return None
    if upload.content_type not in ('image/jpeg','image/png','image/webp'):
        raise ValueError('A foto deve ser JPG, PNG ou WebP.')
    blob=await upload.read(MAX_IMAGE+1)
    if len(blob)>MAX_IMAGE:
        raise ValueError('Imagem acima do limite de 5 MB.')
    data=image_processing_sync(blob)
    filename=uuid.uuid4().hex+'.webp'
    (MEDIA/filename).write_bytes(data)
    thumbs = MEDIA / 'thumbs'
    thumbs.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(data)) as cover:
        cover.thumbnail((560, 350), Image.Resampling.LANCZOS)
        thumb_out = io.BytesIO()
        cover.save(thumb_out, format='WEBP', quality=73, method=4)
        (thumbs / filename).write_bytes(thumb_out.getvalue())
    return f'/media/{filename}'


def clean_form(form):
    title=str(form.get('titulo','')).strip()
    summary=str(form.get('resumo','')).strip()
    body=str(form.get('conteudo','')).strip()
    category=str(form.get('categoria','Notícia'))
    status=str(form.get('status','rascunho'))
    if not 5<=len(title)<=160: raise ValueError('O título precisa ter entre 5 e 160 caracteres.')
    if not 10<=len(summary)<=330: raise ValueError('O resumo precisa ter entre 10 e 330 caracteres.')
    if not 15<=len(body)<=30_000: raise ValueError('O conteúdo precisa ter entre 15 e 30.000 caracteres.')
    if category not in CATEGORIES: raise ValueError('Categoria inválida.')
    if status not in ('rascunho','publicado'): raise ValueError('Status inválido.')
    return title,summary,body,category,status


def clean_settings(form):
    keys=['telefone','whatsapp','instagram','facebook','youtube']
    result={k:str(form.get(k,'')).strip() for k in keys}
    if len(result['telefone'])>35: raise ValueError('Telefone muito longo.')
    if result['whatsapp'] and not re.fullmatch(r'55\d{10,11}',re.sub(r'\D','',result['whatsapp'])):
        raise ValueError('WhatsApp deve conter DDI 55, DDD e número.')
    result['whatsapp']=re.sub(r'\D','',result['whatsapp'])
    for key in ('instagram','facebook','youtube'):
        u=result[key]
        if u:
            parsed=urlparse(u)
            if parsed.scheme!='https' or not parsed.hostname or len(u)>500 or parsed.username or parsed.password:
                raise ValueError(f'Informe URL HTTPS válida para {key}.')
    return result


init_db()
# Chaves de sessão só válidas com SESSION_SECRET constante no .env
app.state.login_attempts={}

@app.middleware('http')
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN' if request.url.path == '/filiacao-demonstracao.html' else 'DENY'
    if request.url.path.startswith('/admin'):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response

@app.get('/', response_class=HTMLResponse)
async def homepage():
    with connect() as c:
        news = c.execute("SELECT titulo,slug,resumo,categoria,imagem,published_at FROM noticias WHERE status='publicado' ORDER BY published_at DESC,id DESC LIMIT 9").fetchall()
    page = HOME_SHELL
    if news:
        page = page.replace('<!-- PL_SERRA_NEWS_SSR -->', render_initial_news(news))
    base = public_site_url()
    if base:
        url = base + '/'
        tags = f'<link rel="canonical" href="{html.escape(url,quote=True)}">'
        tags += f'<meta property="og:url" content="{html.escape(url,quote=True)}">'
        page = page.replace('</head>', tags + '</head>', 1)
        for p in ('og:image', 'twitter:image'):
            page = page.replace('content="/assets/compartilhamento.jpg"', f'content="{base}/assets/compartilhamento.jpg"')
        page = page.replace('"logo":"/assets/logo-320.webp"', '"logo":"'+base+'/assets/logo-320.webp"')
        page = page.replace('"image":"/assets/compartilhamento.jpg"', '"image":"'+base+'/assets/compartilhamento.jpg"')
    return HTMLResponse(page,headers={'Cache-Control':'public, max-age=30, stale-while-revalidate=60'})

@app.get('/filiacao-demonstracao.html')
async def filiacao_demo():
    return FileResponse(SITE / 'filiacao-demonstracao.html', media_type='text/html',
                        headers={'Cache-Control':'public, max-age=86400',
                                 'X-Robots-Tag':'noindex, nofollow'})

@app.get('/robots.txt')
async def robots():
    rules = 'User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nDisallow: /filiacao-demonstracao.html\n'
    if public_site_url(): rules += f'Sitemap: {public_site_url()}/sitemap.xml\n'
    return PlainTextResponse(rules, headers={'Cache-Control':'public,max-age=3600'})

@app.get('/sitemap.xml')
async def sitemap():
    base = public_site_url()
    if not base: raise HTTPException(404, 'Configure SITE_URL com o domínio HTTPS antes de gerar o sitemap.')
    with connect() as c:
        news = c.execute("SELECT slug,updated_at FROM noticias WHERE status='publicado' ORDER BY published_at DESC").fetchall()
    entries = [f'<url><loc>{html.escape(base+"/",quote=True)}</loc><changefreq>weekly</changefreq></url>']
    for item in news:
        entries.append(f'<url><loc>{html.escape(base+"/noticias/"+item["slug"],quote=True)}</loc><lastmod>{html.escape((item["updated_at"] or "")[:10])}</lastmod></url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(entries)+'</urlset>'
    return Response(xml,media_type='application/xml',headers={'Cache-Control':'public,max-age=1800'})

@app.get('/api/public')
async def public_data():
    with connect() as c:
        news=c.execute('SELECT titulo,slug,resumo,categoria,imagem,published_at FROM noticias WHERE status=? ORDER BY published_at DESC,id DESC LIMIT 9',('publicado',)).fetchall()
        contacts=dict((x['chave'],x['valor']) for x in c.execute('SELECT chave,valor FROM contatos'))
    def mini(uri):
        return (uri.replace('/media/', '/media/thumbs/') if uri and (MEDIA/'thumbs'/Path(uri).name).is_file() else uri)
    items=[{'titulo':x['titulo'],'slug':x['slug'],'resumo':x['resumo'],'categoria':x['categoria'],
            'imagem':mini(x['imagem']),'data_publicacao':x['published_at']} for x in news]
    return JSONResponse({'noticias':items,'contatos':contacts},headers={'Cache-Control':'public,max-age=30,stale-while-revalidate=60'})

@app.get('/noticias/{slug}')
async def public_news(request:Request,slug:str):
    with connect() as c:
        news=c.execute('SELECT * FROM noticias WHERE slug=? AND status=?',(slug,'publicado')).fetchone()
    if not news: raise HTTPException(404,'Notícia não encontrada.')
    base = public_site_url()
    canonical = f'{base}/noticias/{slug}' if base else None
    news_img = (base + news['imagem']) if base and news['imagem'] else (base+'/assets/compartilhamento.jpg' if base else '/assets/compartilhamento.jpg')
    schema = {
        '@context':'https://schema.org', '@type':'NewsArticle',
        'headline':news['titulo'], 'description':news['resumo'],
        'datePublished':news['published_at'], 'dateModified':news['updated_at'],
        'publisher':{'@type':'Organization','name':'Partido Liberal - Serra (ES)'},
        'image':[news_img]
    }
    if canonical: schema['mainEntityOfPage'] = canonical
    body = templates.get_template('noticia.html').render(noticia=news,canonical_url=canonical,share_image=news_img,
                                                       json_ld=json_for_html(schema))
    return HTMLResponse(body, headers={'Cache-Control':'public,max-age=30,stale-while-revalidate=60'})

@app.get('/admin')
async def dashboard(request:Request):
    adm=admin_only(request)
    if not adm:return home_redirect('/admin/login')
    with connect() as c:
        news=c.execute('SELECT * FROM noticias ORDER BY created_at DESC,id DESC').fetchall()
        settings=dict((x['chave'],x['valor']) for x in c.execute('SELECT chave,valor FROM contatos'))
    return html_template('admin.html',request,admin=adm,noticias=news,contatos=settings,
                         saved=request.query_params.get('salvo')=='1')

@app.get('/admin/login')
async def login_form(request:Request):
    if admin_only(request):return home_redirect()
    return html_template('login.html',request,error=None)

@app.post('/admin/login')
async def login(request:Request):
    form=await request.form()
    check_csrf(request,form.get('csrf'))
    username=str(form.get('username','')).strip()[:80]
    password=str(form.get('password',''))[:1024]
    ip=(request.client.host if request.client else 'local')
    history=app.state.login_attempts.get(ip,[])
    import time
    recent=[t for t in history if time.monotonic()-t<900]
    if len(recent)>=8:
        return html_template('login.html',request,error='Muitas tentativas. Tente novamente mais tarde.',status_code=429)
    with connect() as c:
        user=c.execute('SELECT * FROM admins WHERE username=?',(username,)).fetchone()
    # Faz a verificação mesmo para usuário inexistente para mitigar descoberta de usuário
    valid=verify_password(password,user['password_hash'] if user else DUMMY_HASH)
    if not user or not valid:
        recent.append(time.monotonic());app.state.login_attempts[ip]=recent
        return html_template('login.html',request,error='Usuário ou senha inválidos.',status_code=401)
    app.state.login_attempts.pop(ip,None)
    request.session.clear()
    request.session['admin_id']=user['id']
    request.session['csrf']=secrets.token_urlsafe(32)
    return home_redirect()

@app.post('/admin/logout')
async def logout(request:Request):
    form=await request.form();check_csrf(request,form.get('csrf'))
    request.session.clear()
    return home_redirect('/admin/login')

@app.get('/admin/noticias/nova')
async def new_form(request:Request):
    adm=admin_only(request)
    if not adm:return home_redirect('/admin/login')
    return html_template('editor.html',request,admin=adm,item=None,categories=CATEGORIES,error=None)

@app.post('/admin/noticias/nova')
async def new_article(request:Request):
    adm=admin_only(request)
    if not adm:return home_redirect('/admin/login')
    form=await request.form();check_csrf(request,form.get('csrf'))
    try:
        title,summary,body,category,status=clean_form(form)
        img=await maybe_save_upload(form.get('foto'))
        with connect() as c:
            slug=unique_slug(c,title)
            moment=now()
            c.execute('''INSERT INTO noticias(titulo,slug,resumo,conteudo,categoria,status,imagem,created_at,updated_at,published_at)
                         VALUES (?,?,?,?,?,?,?,?,?,?)''',
                      (title,slug,summary,body,category,status,img,moment,moment,moment if status=='publicado' else None))
    except ValueError as exc:
        return html_template('editor.html',request,admin=adm,item=dict(form),categories=CATEGORIES,error=str(exc),status_code=422)
    return home_redirect('/admin?salvo=1')

@app.get('/admin/noticias/{news_id}/editar')
async def edit_form(request:Request,news_id:int):
    adm=admin_only(request)
    if not adm:return home_redirect('/admin/login')
    with connect() as c:
        news=c.execute('SELECT * FROM noticias WHERE id=?',(news_id,)).fetchone()
    if not news:raise HTTPException(404)
    return html_template('editor.html',request,admin=adm,item=news,categories=CATEGORIES,error=None)

@app.post('/admin/noticias/{news_id}/editar')
async def edit_article(request:Request,news_id:int):
    adm=admin_only(request)
    if not adm:return home_redirect('/admin/login')
    form=await request.form();check_csrf(request,form.get('csrf'))
    with connect() as c:
        old=c.execute('SELECT * FROM noticias WHERE id=?',(news_id,)).fetchone()
    if not old:raise HTTPException(404)
    try:
        title,summary,body,category,status=clean_form(form)
        img=await maybe_save_upload(form.get('foto'))
        if not img:img=old['imagem']
        with connect() as c:
            slug=old['slug'] if title==old['titulo'] else unique_slug(c,title,news_id)
            published=old['published_at'] or (now() if status=='publicado' else None)
            c.execute('''UPDATE noticias SET titulo=?,slug=?,resumo=?,conteudo=?,categoria=?,status=?,imagem=?,updated_at=?,published_at=? WHERE id=?''',
                      (title,slug,summary,body,category,status,img,now(),published,news_id))
    except ValueError as exc:
        item=dict(form);item.update(id=news_id,imagem=old['imagem'])
        return html_template('editor.html',request,admin=adm,item=item,categories=CATEGORIES,error=str(exc),status_code=422)
    return home_redirect('/admin?salvo=1')

@app.post('/admin/noticias/{news_id}/excluir')
async def delete_article(request:Request,news_id:int):
    adm=admin_only(request)
    if not adm:return home_redirect('/admin/login')
    form=await request.form();check_csrf(request,form.get('csrf'))
    with connect() as c:
        c.execute('DELETE FROM noticias WHERE id=?',(news_id,))
    return home_redirect('/admin?salvo=1')

@app.post('/admin/contatos')
async def save_contacts(request:Request):
    adm=admin_only(request)
    if not adm:return home_redirect('/admin/login')
    form=await request.form();check_csrf(request,form.get('csrf'))
    try: values=clean_settings(form)
    except ValueError as exc:
        with connect() as c:
            news=c.execute('SELECT * FROM noticias ORDER BY created_at DESC').fetchall()
        return html_template('admin.html',request,admin=adm,noticias=news,contatos=dict(form),saved=False,error=str(exc),status_code=422)
    with connect() as c:
        for k,v in values.items(): c.execute('UPDATE contatos SET valor=? WHERE chave=?',(v,k))
    return home_redirect('/admin?salvo=1')

# hash fixo de dummy para equilibrar tempo dos logins; não é credencial válida
DUMMY_HASH=hash_password(secrets.token_urlsafe(24))

@app.get('/assets/logo.jpg')
async def logo_file():
    return FileResponse(SITE/'assets'/'logo.jpg',media_type='image/jpeg')
