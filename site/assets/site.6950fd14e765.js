
    (function(){
      const menuButton=document.getElementById('menuButton');
      const menu=document.getElementById('menu');
      const topButton=document.getElementById('scrollTop');
      const toast=document.getElementById('toast');
      document.getElementById('year').textContent=new Date().getFullYear();
      function closeMenu(){menu.classList.remove('open');menuButton.setAttribute('aria-expanded','false');menuButton.setAttribute('aria-label','Abrir menu')}
      menuButton.addEventListener('click',()=>{const open=menu.classList.toggle('open');menuButton.setAttribute('aria-expanded',String(open));menuButton.setAttribute('aria-label',open?'Fechar menu':'Abrir menu')});
      menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
      document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu()});
      function onScroll(){topButton.classList.toggle('show',window.scrollY>450)}
      window.addEventListener('scroll',onScroll,{passive:true});onScroll();
      topButton.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
      let toastTimer;
      function inform(message){toast.textContent=message;toast.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.classList.remove('show'),2600)}
      document.getElementById('copyAddress').addEventListener('click',async function(){const address='Avenida Civit, nº 271, Parque Residencial Laranjeiras, Serra - ES, CEP 29165-032';try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(address)}else{const el=document.createElement('textarea');el.value=address;el.style.position='fixed';el.style.left='-9999px';document.body.appendChild(el);el.select();if(!document.execCommand('copy'))throw new Error('Falha');el.remove()}inform('Endereço copiado com sucesso.')}catch(e){inform('Selecione e copie o endereço exibido acima.')}});
    })();
  

  (function(){
    'use strict';
    // CONFIGURAÇÃO DO CONTATO: use DDI + DDD + número, apenas dígitos.
    // Exemplo de formato: 5527999999999. Não utilize um número fictício.
    const WHATSAPP_NUMERO = '';
    const WHATSAPP_MENSAGEM = 'Olá! Gostaria de entrar em contato com o PL Serra.';
    const waButton = document.getElementById('whatsappButton');
    const waHint = document.getElementById('whatsappHint');
    const waClose = document.getElementById('waHintClose');
    function dismissHint(){waHint.classList.remove('is-open');waHint.setAttribute('aria-hidden','true');waButton.setAttribute('aria-expanded','false')}
    waButton.addEventListener('click',function(){
      const digits = (window.PL_SERRA_WHATSAPP_NUMERO || WHATSAPP_NUMERO).replace(/\D/g,'');
      if(/^55\d{10,11}$/.test(digits)){
        window.open('https://wa.me/'+digits+'?text='+encodeURIComponent(WHATSAPP_MENSAGEM),'_blank','noopener,noreferrer');
      }else{
        const isOpen=waHint.classList.toggle('is-open');
        waHint.setAttribute('aria-hidden',String(!isOpen));waButton.setAttribute('aria-expanded',String(isOpen));
        if(isOpen)waClose.focus();
      }
    });
    waClose.addEventListener('click',function(){dismissHint();waButton.focus()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')dismissHint()});
    document.addEventListener('click',function(e){if(!waButton.contains(e.target)&&!waHint.contains(e.target))dismissHint()});

    const root = document.querySelector('.site-carousel');
    const slides = [...root.querySelectorAll('.carousel-slide')];
    const dots = [...root.querySelectorAll('.carousel-dot')];
    const counter = document.getElementById('carCurrent');
    const prev = document.getElementById('carPrev');
    const next = document.getElementById('carNext');
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let current = 0, interval = null, hover = false, focused = false;
    function go(index){
      current=(index+slides.length)%slides.length;
      slides.forEach((slide,i)=>{
        const selected=(i===current);
        slide.classList.toggle('is-active',selected);
        slide.setAttribute('aria-hidden',String(!selected));
        // Remove inactive slide links from the keyboard tab sequence.
        slide.querySelectorAll('a').forEach(el=>{if(selected)el.removeAttribute('tabindex');else el.setAttribute('tabindex','-1')});
      });
      dots.forEach((dot,i)=>dot.setAttribute('aria-current',String(i===current)));
      counter.textContent=String(current+1).padStart(2,'0');
    }
    function stop(){if(interval!==null){window.clearInterval(interval);interval=null}}
    function start(){stop();if(!prefersReducedMotion&&!hover&&!focused&&!document.hidden){interval=window.setInterval(()=>go(current+1),6500)}}
    prev.addEventListener('click',()=>{go(current-1);start()});
    next.addEventListener('click',()=>{go(current+1);start()});
    dots.forEach(dot=>dot.addEventListener('click',()=>{go(Number(dot.dataset.slide));start()}));
    root.addEventListener('mouseenter',()=>{hover=true;stop()});
    root.addEventListener('mouseleave',()=>{hover=false;start()});
    root.addEventListener('focusin',()=>{focused=true;stop()});
    root.addEventListener('focusout',()=>{window.requestAnimationFrame(()=>{focused=root.contains(document.activeElement);start()})});
    root.addEventListener('keydown',e=>{
      if(e.key==='ArrowRight'){e.preventDefault();go(current+1);start()}
      else if(e.key==='ArrowLeft'){e.preventDefault();go(current-1);start()}
    });
    document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();else start()});
    go(0);start();
  })();
  

(function(){
'use strict';
const grid=document.getElementById('newsGrid');
const status=document.getElementById('newsStatus');
const phone=document.getElementById('footerPhone');
const phoneText=document.getElementById('footerPhoneText');
const networkIds={instagram:'socialInstagram',facebook:'socialFacebook',youtube:'socialYoutube'};
const isValidLink=(url)=>{try{const u=new URL(url);return u.protocol==='https:'}catch{return false}};
function displayContacts(settings){
 const tel=(settings.telefone||'').trim();
 if(tel){phone.href='tel:'+tel.replace(/[^0-9+]/g,'');phone.classList.remove('is-pending');phone.setAttribute('aria-label','Ligar para '+tel);phoneText.textContent=tel;}
 Object.entries(networkIds).forEach(([key,id])=>{const el=document.getElementById(id),url=(settings[key]||'').trim();if(isValidLink(url)){el.href=url;el.target='_blank';el.rel='noopener noreferrer';el.classList.remove('is-pending');el.setAttribute('aria-label',key+' do PL Serra (abre nova aba)')}});
 window.PL_SERRA_WHATSAPP_NUMERO=(settings.whatsapp||'').replace(/\D/g,'');
}
function articleCard(entry){
 const article=document.createElement('article');article.className='news-card';
 const photo=document.createElement('div');photo.className='news-card-image';
 if(entry.imagem){const img=document.createElement('img');img.src=entry.imagem;img.alt='';img.loading='lazy';img.decoding='async';img.width=560;img.height=350;photo.appendChild(img)}else{photo.textContent='PL 22'}
 const body=document.createElement('div');body.className='news-card-content';
 const label=document.createElement('span');label.className='news-card-kicker';label.textContent=entry.categoria||'Notícia';
 const title=document.createElement('h3');title.textContent=entry.titulo;
 const summary=document.createElement('p');summary.textContent=entry.resumo;
 const footer=document.createElement('div');footer.className='news-card-foot';
 const date=document.createElement('span');date.textContent=entry.data_publicacao?new Date(entry.data_publicacao).toLocaleDateString('pt-BR',{day:'2-digit',month:'long',year:'numeric'}):'';
 const link=document.createElement('a');link.href='/noticias/'+encodeURIComponent(entry.slug);link.textContent='Ler notícia →';
 footer.append(date,link);body.append(label,title,summary,footer);article.append(photo,body);return article;
}
async function load(){
 if(location.protocol==='file:'){status.textContent='Prévia local: notícias e canais de contato serão carregados ao publicar o site com o servidor.';return;}
 try{
  const response=await fetch('/api/public',{credentials:'omit',cache:'no-store'});
  if(!response.ok)throw Error('API indisponível');
  const data=await response.json();displayContacts(data.contatos||{});
  if(Array.isArray(data.noticias)&&data.noticias.length){grid.replaceChildren(...data.noticias.map(articleCard));status.textContent='Atualizado pela administração do PL Serra.';}
 }catch{status.textContent='As notícias serão exibidas aqui quando o site estiver conectado ao servidor.';}
}
load();
})();
