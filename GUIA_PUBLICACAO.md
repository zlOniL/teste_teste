# Publicação do site PL Serra (ES)

Este pacote publica o **site institucional completo** (carrossel, notícias, lideranças, PL Mulher, PL Comunidades, Bolsonaro, histórico, contato), **painel administrativo** e **banco SQLite persistente**. As imagens de lideranças e a identidade visual estão incluídas.

## Hospedagem necessária

Utilize um **VPS Linux** com **Docker Engine e Docker Compose v2**, um **domínio próprio** e portas TCP **80 e 443** abertas (UDP 443 é opcional). Uma hospedagem que aceita somente HTML/PHP/FTP não executará este backend FastAPI nem o painel. Não enviamos o site automaticamente a nenhum provedor.

## Instalação em 6 etapas

1. **Extraia este ZIP** no seu computador e envie a pasta `PL_Serra_Publicacao_Producao` para o VPS, por exemplo para `/opt/pl-serra`. Não use FTP público para enviar o arquivo `.env`.
2. **Configure o DNS:** crie um registro `A` para o domínio apontando ao IP público do VPS (e `AAAA` se houver IPv6). Aguarde o DNS estar resolvendo.
3. Na pasta do projeto, **gere o arquivo privado de configuração**: `python3 configurar_publicacao.py`. Informe o seu domínio real, **sem** `https://` ou caminho. O script gera um segredo aleatório de sessão. Nunca compartilhe `.env`.
4. **Monte o servidor:** `docker compose build`.
5. **Crie o usuário administrativo** (interativo): `docker compose run --rm --no-deps -it web python scripts/criar_admin.py`. Escolha usuário e senha forte. **Não há credenciais padrão.**
6. **Inicie o site:** `docker compose up -d`. Com o DNS correto e as portas abertas, o Caddy solicitará o certificado HTTPS automaticamente.

Acesse `https://SEU-DOMINIO/` (site público) e `https://SEU-DOMINIO/admin` (painel). O painel gerencia notícias e links de Instagram, Facebook, YouTube, telefone e WhatsApp.

## Comandos úteis

```bash
docker compose ps                       # situação e saúde dos serviços
docker compose logs -f web              # logs do site
docker compose logs -f https            # logs e certificado HTTPS
docker compose restart web              # reiniciar backend
docker compose up -d --build             # aplicar alteração de código
docker compose down                      # parar (SEM apagar volumes)
```

**Nunca execute** `docker compose down -v` em produção: esse comando apaga volumes com o banco e imagens. Guarde cópia do arquivo `.env` de forma segura.

## Backup

Para um backup consistente do banco, use:

```bash
docker compose exec -T web python scripts/backup_sqlite.py
# Veja o nome da cópia em /app/data/backups e faça cópia externa:
docker compose cp web:/app/data/backups ./backup-banco
docker compose cp web:/app/data/media ./backup-imagens
```

Guarde backups fora do servidor, inclusive de `data/media`. Faça isso de forma periódica. O Docker mantém os volumes entre atualizações simples, mas **não substitui o backup externo**.

## SEO e verificação

Depois de publicar, confirme:
- `https://SEU-DOMINIO/` abre sem aviso de certificado.
- `https://SEU-DOMINIO/robots.txt` responde.
- `https://SEU-DOMINIO/sitemap.xml` lista a página inicial e notícias públicas.
- `https://SEU-DOMINIO/admin/login` pede login, sem senha padrão.
- Crie uma notícia de teste como **rascunho**, revise, publique e verifique a URL pública.
- Cadastre o domínio no Google Search Console e envie o sitemap. Meça o desempenho no PageSpeed Insights depois de publicado.

## Segurança e privacidade

- O painel exige senha forte, sessão via cookie seguro e HTTPS. O backend só é acessível **internamente** via Caddy; não expõe a porta 8000 no VPS.
- A publicação usa um único processo de backend para manter a limitação de tentativas de login coerente. Considere monitoramento, firewall, proteção contra abuso e backups automáticos antes de divulgar amplamente.
- **A área de filiação no site é apenas demonstrativa.** Não recebe filiações oficiais, não armazena documentos ou dados eleitorais e não está integrada ao TSE. Para uma filiação real é necessária solução separada validada com direção partidária e responsáveis pela LGPD.
- Não publique dados sensíveis ou credenciais no painel de notícias. Confirme as informações institucionais e os direitos de uso das fotografias antes de colocar o site no ar.
- Este arquivo de instalação é suficiente para hospedar, mas não significa que o site já esteja online. Não há garantia de indexação imediata pelo Google.

## Estrutura

- `compose.yaml`: aplica Docker e define volumes persistentes.
- `Dockerfile`: ambiente Python/FastAPI para produção.
- `Caddyfile`: proxy reverso HTTPS automático.
- `configurar_publicacao.py`: gera `.env` sem senha padrão.
- `scripts/criar_admin.py`: cadastra o primeiro administrador sem deixar senhas no pacote.
- `app.py`, `site/`, `templates/`, `requirements.txt`: aplicação.

**Observação:** para publicar em outra plataforma (Render, Railway, Fly.io, cPanel com Python, Vercel etc.), é necessário adaptar os arquivos e avaliar a persistência do banco. Este pacote foi preparado para VPS com Docker.
