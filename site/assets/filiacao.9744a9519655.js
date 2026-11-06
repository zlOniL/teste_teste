(()=>{
  let step=0;
  const els=[...document.querySelectorAll('.step')], labels=[...document.querySelectorAll('.progress-labels li')], form=document.querySelector('#affiliationForm');
  const progress=document.querySelector('#progressValue'), count=document.querySelector('#stepCount');
  function show(n){step=n;els.forEach((el,i)=>el.classList.toggle('active',i===n));labels.forEach((el,i)=>el.classList.toggle('active',i<=n));progress.style.width=((n+1)*25)+'%';count.textContent=`ETAPA 0${n+1} / 04`;window.scrollTo({top:0,behavior:'smooth'});}
  function error(n,msg){document.querySelector('#err'+n).textContent=msg||''}
  function digits(v){return String(v).replace(/\D/g,'')}
  function validate(n){error(n,'');if(n===0){if(!document.querySelector('#declaration').checked){error(0,'Confirme a declaração para continuar.');return false}return true}
    if(n===1){const f=form.elements, name=f['name'].value.trim(),title=digits(f['title'].value),zone=digits(f['zone'].value),section=digits(f['section'].value),phone=digits(f['phone'].value);
      if(name.length<5){error(1,'Informe seu nome completo.');return false}if(title.length!==12){error(1,'O título eleitoral deve conter 12 dígitos.');return false}if(!Number(zone)||!Number(section)){error(1,'Informe zona e seção eleitoral válidas.');return false}if(phone.length<10||phone.length>11){error(1,'Informe um celular com DDD.');return false}if(f['email'].value&&!f['email'].checkValidity()){error(1,'Confira seu endereço de e-mail.');return false}return true}
    if(n===2){if(!document.querySelector('#privacyAck').checked){error(2,'Confirme que leu o aviso de privacidade.');return false}const file=document.querySelector('#photoInput').files[0];if(file&&(file.size>5000000||!['image/jpeg','image/png','image/webp'].includes(file.type))){error(2,'A foto deve ser JPG, PNG ou WebP e ter até 5 MB.');return false}return true}return true;
  }
  document.querySelectorAll('[data-next]').forEach(btn=>btn.addEventListener('click',()=>{if(validate(step))show(step+1)}));
  document.querySelectorAll('[data-prev]').forEach(btn=>btn.addEventListener('click',()=>show(step-1)));
  ['title','zone','section'].forEach(n=>{const el=form.elements[n];el.addEventListener('input',()=>{el.value=digits(el.value).slice(0,n==='title'?12:4)})});
  form.elements['phone'].addEventListener('input',e=>{let d=digits(e.target.value).slice(0,11);e.target.value=d.length>6?`(${d.slice(0,2)}) ${d.slice(2,-4)}-${d.slice(-4)}`:d.length>2?`(${d.slice(0,2)}) ${d.slice(2)}`:d});
  const file=document.querySelector('#photoInput'), preview=document.querySelector('#photoPreview'), uploadText=document.querySelector('#uploadText');
  let lastURL=null;
  file.addEventListener('change',()=>{if(lastURL)URL.revokeObjectURL(lastURL);const f=file.files[0];if(!f){preview.hidden=true;return};if(f.size>5000000||!['image/jpeg','image/png','image/webp'].includes(f.type)){error(2,'A foto deve ser JPG, PNG ou WebP e ter até 5 MB.');preview.hidden=true;return;}error(2,'');lastURL=URL.createObjectURL(f);preview.src=lastURL;preview.hidden=false;uploadText.textContent=f.name});
  form.addEventListener('submit', event => { event.preventDefault(); error(2,'Demonstração: não há envio de dados nesta versão.'); });
  document.querySelector('#copyProtocol').addEventListener('click',async()=>{const t=document.querySelector('#protocolValue').textContent;try{await navigator.clipboard.writeText(t);document.querySelector('#copyProtocol').textContent='Copiado!'}catch(e){document.querySelector('#copyProtocol').textContent='Selecione o protocolo'}});
})();
