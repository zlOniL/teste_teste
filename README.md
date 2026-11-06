# PL Serra: versão pronta para deploy em VPS com Docker

**Comece pelo arquivo [GUIA_PUBLICACAO.md](GUIA_PUBLICACAO.md)**.

---

# PL Serra / ES | Site institucional + notícias + área administrativa

Projeto criado a partir do site institucional já desenvolvido, preservando o carrossel, a logomarca, as cores, as lideranças, Jair Bolsonaro, PL Mulher, PL Comunidades, histórico, endereço e **a demonstração de filiação existente**.

## Atualizações solicitadas

- Remoção da faixa de três cartões `PL · 22 / Serra · ES / Laranjeiras` que ficava abaixo do carrossel.
- Nova seção **Notícias & atualizações** imediatamente abaixo dos três banners, alimentada automaticamente pelo banco de dados.
- Novo rodapé com telefone, Instagram, Facebook, YouTube, endereço e link discreto para **Área administrativa**.
- Login administrativo em `/admin/login`, painel em `/admin`, cadastro/edição/exclusão de notícias, status de rascunho ou publicado e envio opcional de imagem.
- Cadastro dos canais de contato no painel, incluindo número do WhatsApp flutuante.

## Arquivos e execução

- `site/index.html`: página pública; pode ser aberta diretamente como uma prévia local sem servidor.
- `app.py`: servidor FastAPI, autenticação, notícias e API pública.
- `templates`: login, painel, editor de notícias e página completa de notícia.
- `setup.py`: cria o arquivo `.env` com segredo de sessão e cadastra o usuário administrador, **sem senha padrão**.
- `data`: banco SQLite e imagens enviadas; os arquivos reais não são incluídos no pacote.

### Para testar localmente

Requer Python 3.11+.

```bash
cd pl_serra_site_admin_noticias
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python setup.py
uvicorn app:app --host 127.0.0.1 --port 8000
```

Abra:

- Site público: `http://127.0.0.1:8000`
- Painel administrativo: `http://127.0.0.1:8000/admin`

No `setup.py`, informe nome de usuário e senha de pelo menos 12 caracteres. As credenciais são armazenadas como hash `scrypt` no SQLite. O banco é criado automaticamente em `data/pl_serra.db`.

### Publicação em servidor

O site **não está publicado na internet**. Para uso real:

1. Configure um domínio e proxy reverso com HTTPS, usando Caddy/Nginx ou plataforma de hospedagem.
2. Gere o `.env` via `python setup.py` e configure `COOKIE_SECURE=1` antes de iniciar o serviço em produção HTTPS.
3. Não publique `.env`, `data/pl_serra.db`, o diretório `data` nem credenciais como arquivos estáticos.
4. Faça backup periódico de `data/pl_serra.db` e `data/media/` com acesso restrito; limite quem pode acessar o painel administrativo.
5. Cadastre os endereços oficiais e número de telefone/WhatsApp em **Painel > Canais de contato**. O site não inclui números nem perfis de redes sociais inventados.
6. Para operações públicas com maior criticidade, adicione monitoramento, limites de requisição na borda, controle de acesso, política de privacidade e revisão de segurança antes de divulgar a URL.

**Atenção sobre a filiação:** o formulário incorporado no HTML permanece uma **demonstração**. Este painel administra **notícias e canais de contato**, não solicitações eleitorais nem dados de eleitores. O sistema de filiação com armazenamento seguro desenvolvido em outra etapa é um projeto separado; ele não foi integrado ao backend deste pacote. Para torná-lo real, seria necessário unir os dois serviços, realizar auditoria de segurança, adequar o tratamento de dados sensíveis à LGPD e validar o procedimento oficial com o partido e o TSE. Não peça dados pessoais ou fotos de documentos usando esta prévia.

## Funcionamento das notícias

- Até nove notícias com status **Publicado** são exibidas na página inicial, mais recentes primeiro.
- Notícias em **Rascunho** ficam visíveis só no painel, não na API pública.
- O editor recebe: título, resumo, texto completo, categoria e uma imagem opcional JPG/PNG/WebP de até 5 MB.
- Imagens são convertidas para WebP e têm seus metadados removidos.
- Cada notícia publicada ganha página própria em `/noticias/<slug>`.
- Quando não existem notícias, o site exibe um bloco institucional indicando que a seção aguarda as primeiras publicações, sem notícias inventadas.
- Se o HTML for aberto fora do servidor (`file://`), o conteúdo de notícias dinâmicas e os canais de contato não carregarão. A prévia estática continuará visível.

## Informações de segurança

Inclui autenticação com senhas derivadas com `scrypt` e sal aleatório, sessão assinada com segredo configurável, cookie HTTP-only/same-site, token CSRF nos formulários administrativos, limitação simples de tentativas de login por IP, consultas SQL parametrizadas, templates com escape de HTML, limites de tamanho nos uploads e ausência de credenciais padrão. A proteção de tentativas em memória é básica e deve ser complementada por um controle no proxy reverso ao publicar em produção.

## Referência de cores da marca

- Azul: `#015AAA`
- Amarelo: `#FDD303`
- Verde: `#00A54F`

## Fotografias das lideranças (atualização)

A seção **Lideranças** agora utiliza fotografias fornecidas para os três representantes, na ordem em que aparecem no site:
- Valdemar Costa Neto: `site/assets/valdemar.png` (presidência nacional).
- Magno Malta: `site/assets/magnomalta.png` (presidência estadual).
- Pastor Dinho Souza: `site/assets/prdinho.png` (presidência municipal).

Para facilitar a abertura do HTML isoladamente e evitar imagens quebradas, versões WebP dessas fotografias foram incorporadas ao próprio `site/index.html`. Os PNGs originais permanecem no diretório `site/assets/` para futuras trocas.

---

## Otimizações de SEO e velocidade (novembro de 2026)

**O site público agora usa arquivos externos cacheáveis.** O HTML inicial foi reduzido de aproximadamente 517 KB para 38 KB; CSS, JavaScript e imagens agora são arquivos individuais para cache e compressão HTTP. O formulário demonstrativo só carrega quando o visitante se aproxima da seção.

### Melhorias implementadas

- `title` e `meta description` descritivos; idioma `pt-BR`; metadados Open Graph, Twitter Card e imagem de compartilhamento (1200 × 630).
- Dados estruturados `PoliticalParty`/`Organization` com nome, região e endereço informado; notícias individuais com `NewsArticle`.
- Imagens de lideranças WebP responsivas, atributos `width`/`height`, carregamento tardio abaixo da primeira tela e ícones reduzidos.
- CSS e JavaScript externos, com scripts adiados (`defer`), caminhos de assets por hash, cache `immutable` para CSS/JS.
- HTML inicial de notícias renderizado no servidor. Os links das notícias aparecem para buscadores mesmo sem executar JavaScript.
- `robots.txt` público (área administrativa e demonstração excluídas de rastreio); `noindex` para painel e demonstração; sitemap XML criado automaticamente quando houver domínio configurado.
- Canonical e URLs completas para Open Graph quando `SITE_URL` estiver definido.
- `GZipMiddleware` para compressão HTTP e exemplo de configuração de Caddy com `encode zstd gzip` para produção.
- Galeria/carrossel e botão WhatsApp preservados, assim como lideranças, PL Mulher, PL Comunidades, Bolsonaro, notícias e filiação demonstrativa.
- Imagens recém-publicadas em notícias geram também miniaturas de 560 × 350 px em formato WebP.

### Configuração obrigatória de SEO na publicação

**Não foi presumido nenhum domínio.** Depois de comprar/configurar um endereço real HTTPS, adicione em `.env`:

```env
SITE_URL=https://SEU-DOMINIO-REAL.COM.BR
COOKIE_SECURE=1
```

`SITE_URL` deve ser a URL real do site na raiz, sem `/` final. Ao configurar, o backend passa a gerar:

- Página inicial: `<link rel="canonical">` e `og:url` com a URL definitiva.
- Notícias: canonical e metadados por artigo.
- `https://SEU-DOMINIO-REAL.COM.BR/sitemap.xml` contendo a home e notícias publicadas.
- `https://SEU-DOMINIO-REAL.COM.BR/robots.txt` com a referência ao sitemap.

Após a publicação, registre o domínio no [Google Search Console](https://search.google.com/search-console/about), envie o `sitemap.xml`, valide as páginas com inspeção de URL e meça em [PageSpeed Insights](https://pagespeed.web.dev/). O Google não garante indexação nem posição por causa apenas de melhorias técnicas. Testes reais de Core Web Vitals (LCP, INP e CLS) só poderão ser realizados adequadamente na hospedagem definitiva e com tráfego real.

### Abrir localmente

`site/visualizacao-local.html` foi preparado para usar os arquivos locais, mas o gerenciamento de notícias e o painel só funcionam com o backend. Para ver a experiência sem nenhum servidor e sem arquivos externos, use o arquivo separado `PL_Serra_PREVIA_OFFLINE.html`, entregue junto deste pacote. **Essa prévia incorpora recursos em um HTML único por conveniência; não é a versão de produção otimizada.**

### Observações importantes

- `site/filiacao-demonstracao.html` é um formulário de demonstração isolado. A página recebe `X-Robots-Tag: noindex` e só pode ser exibida em iframe da própria origem; não salva filiações.
- A foto de Jair Bolsonaro usa uma origem externa já presente no site anterior e pode depender da conexão e da disponibilidade do servidor dessa imagem.
- Como não temos o domínio, telefone, WhatsApp e perfis sociais oficiais, esses dados continuam pendentes de configuração no painel administrativo.
- Use cache e compressão da hospedagem conforme a documentação de Caddy/Nginx para manter essas otimizações em produção.
