# Relatório de otimização | PL Serra ES

**Data:** novembro de 2026  
**Base:** versão do site com imagens de Valdemar Costa Neto, Magno Malta e Pastor Dinho Souza.

| Item | Antes | Depois |
|---|---:|---:|
| HTML principal | 517.415 bytes | 38.331 bytes |
| CSS | Embutido na home | Arquivo ~51 KB, cacheável |
| JavaScript | Embutido na home | Arquivo ~9 KB, defer e cacheável |
| Demonstração da filiação | Embutida na home (129 KB no `srcdoc`) | Página separada (~8 KB HTML), carregada sob demanda |
| Retratos/logos | Base64 repetido ou PNG | Arquivos WebP com tamanhos responsivos |
| Notícias no HTML inicial | Carregadas por JavaScript | Títulos e links das notícias publicadas renderizados no servidor |
| Cache dos assets | Sem configuração HTTP específica | `Cache-Control` por tipo e hash |
| Compressão HTTP | Não configurada | GZip, com Caddy zstd/gzip de exemplo |
| Sitemap/robots | Não disponíveis | Rotas implementadas; sitemap quando domínio for configurado |
| SEO social e dados estruturados | Metadados básicos | Open Graph, Twitter, `PoliticalParty`, `NewsArticle`, canonical com domínio |

**Testado por requisições HTTP locais:** retorno de página, CSS/JS/imagens, `robots.txt`, sitemap com domínio de teste, carregamento das notícias publicadas, tags de notícia e não indexação administrativa; a compressão gzip foi verificada nos cabeçalhos. Os dados de teste não foram incluídos no pacote.

**Não medido:** pontuação real do Google PageSpeed Insights, LCP, INP e CLS em produção. Uma tentativa de teste visual automatizado neste ambiente foi bloqueada; portanto, não declaramos uma pontuação de velocidade nem um teste visual final concluído.

**Para ativar o SEO público:** instalar em HTTPS, definir `SITE_URL`, cadastrar domínio no Google Search Console, enviar o sitemap, validar dados e contato e repetir os testes de velocidade com o site online.
