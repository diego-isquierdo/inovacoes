
// ---------------- render / eventos ----------------
function drawTabs(){$("#tabs").innerHTML=TABS.map(([v,l])=>`<button role="tab" data-v="${v}" aria-selected="${S.view===v}">${esc(l)}</button>`).join("");
  document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>{S.view=b.dataset.v;try{localStorage.setItem("ig_view",S.view);}catch(e){}render();window.scrollTo(0,0);});}
function drawFresh(){const b=S.bases||{},el=$("#fresh");if(!b.tickets&&!b.horas){el.innerHTML=`<span class="chip warn">Bases não carregadas</span>`;return;}
  const c=(x,l)=>{if(!x)return `<span class="chip warn">${l}: sem carga</span>`;const g=x.gerado_em||"";const h=g?Math.floor((Date.now()-new Date(g))/36e5):null;return `<span class="chip ${h!=null&&h>30?"warn":"ok"}">${l}: ${esc(g.slice(8,10)+"/"+g.slice(5,7)+" "+g.slice(11,16))} UTC</span>`;};
  el.innerHTML=c(b.tickets,"Tickets")+c(b.horas,"Horas")+(S.C?`<span class="chip">Time: ${[...S.params.time].map(short).join(", ")}</span>`:"");}
function drawUpd(){const el=$("#upd");if(!el)return;el.innerHTML=`<span class="chip">Carga manual em Configuração</span>`;}
const VIEWS={geral:vGeral,proj:vProj,diag:vDiag,prazo:vPrazo,backlog:vBacklog,sust:vSust,cons:vCons,fila:vFila,time:vTime,horas:vHoras,sop:vSop,cfg:vCfg};
function render(){drawTabs();drawFresh();drawUpd();const m=$("#main");
  if(S.loadErr){m.innerHTML=`<section class="view"><p class="note">${esc(S.loadErr)}</p></section>`+(S.view==="cfg"?vCfg():"");bind();return;}
  if(!S.db&&S.ready){m.innerHTML=`<section class="view"><p class="note">Este painel lê as bases do banco do artefato. Abra-o no Claude, com sua conta da organização.</p></section>`;return;}
  if(!S.C){m.innerHTML=S.ready?`<section class="view"><p class="note">Nenhuma base carregada ainda. Em Configuração, carregue <span class="mono">base_integracoes.json</span> e <span class="mono">horas_integracoes_painel.json</span>.</p></section>`+(S.view==="cfg"?vCfg():""):`<section class="view"><p class="note">Carregando dados…</p></section>`;bind();return;}
  m.innerHTML=(VIEWS[S.view]||vGeral)();bind();}
function bind(){
  const on=(id,ev,fn)=>{const e=document.getElementById(id);if(e)e[ev]=fn;};
  const setf=(o,k,id)=>on(id,"onchange",e=>{o[k]=e.target.value;if(o===S.bl)S.bl.limite=200;render();});
  ["fam","st","dono","prod","prazo"].forEach(k=>setf(S.bl,k,"f_"+k));
  setf(S.pj,"prod","pj_prod");setf(S.pj,"dono","pj_dono");setf(S.fila,"prod","fl_prod");
  document.querySelectorAll("[data-bl-esc]").forEach(b=>b.onclick=()=>{S.bl.escopo=b.dataset.blEsc;S.bl.limite=200;render();});
  on("f_q","oninput",e=>{clearTimeout(bind._q);const v=e.target.value;bind._q=setTimeout(()=>{S.bl.q=v;render();const n=$("#f_q");if(n){n.focus();n.setSelectionRange(v.length,v.length);}},300);});
  on("f_more","onclick",()=>{S.bl.limite+=300;render();});
  on("f_csv","onclick",exportCsv);on("p_save","onclick",saveParams);on("up_file","onchange",e=>upload(e.target.files[0]));
}
async function exportCsv(){const dl=await window.claude?.use?.("downloads");if(!dl){toast("Download indisponível nesta visualização.");return;}
  const L=blFiltered();const head=["Ticket","Assunto","Família","Fila","Produto","Status","Responsável","Situação","Prazo","Data limite","Dias de atraso","Idade (dias)","Parado (dias)","Horas apontadas","Estimativa (h)"];
  const q=v=>'"'+String(v==null?"":v).replace(/"/g,'""')+'"';
  const csv="﻿"+[head.join(";")].concat(L.map(t=>[t.id,t.assunto,FAM_LAB[t.familia],t.fila,t.produto,t.st,t.dono,t.suspenso?"Suspenso":"Ativo",PRAZO_LAB[t.prazo]||"",t.limite?t.limite.toISOString().slice(0,10):"",t.atraso||"",t.idade,t.parado,String(t.horas.toFixed(2)).replace(".",","),t.est||""].map(q).join(";"))).join("\r\n");
  try{await dl.save({filename:"backlog_integracoes.csv",data:new Blob([csv],{type:"text/csv"})});}catch(e){toast("Download não concluído.");}}
async function saveParams(){if(!S.db)return;const g=id=>+document.getElementById(id).value;
  const time=[],ex=[];document.querySelectorAll("select[id^=tm_]").forEach(s=>{if(s.value==="time")time.push(s.dataset.n);else if(s.value==="ex")ex.push(s.dataset.n);});
  if(!time.length){toast("Selecione ao menos uma pessoa no time atual.");return;}
  const ref={};document.querySelectorAll("input[id^=rf_]").forEach(i=>{const v=+i.value;if(v>0)ref[i.dataset.f]=v;});
  const p={...S.params,time,ex,ref_horas:ref,vencendo_dias:Math.max(1,g("p_vd")||15),parado_dias:Math.max(5,g("p_pd")||30),fator_produtivo:Math.min(1,Math.max(0.1,g("p_fp")/100||0.85)),teto_backlog:Math.min(1,Math.max(0.3,g("p_tb")/100||0.9)),horas_mes_padrao:g("p_hp")||147,atualizado_em:new Date().toISOString()};
  try{await S.db.doc("cfg/params").set(p);toast("Parâmetros salvos");}catch(e){toast(e&&e.code==="invalid_argument"?"Você não tem permissão para alterar os parâmetros.":"Não foi possível salvar. Tente de novo.");}}
async function upload(file){if(!file||!S.assets||!S.db)return;
  let j;try{j=JSON.parse(await file.text());}catch(e){toast("O arquivo não é um JSON válido.");return;}
  const kind=j.tabelas&&j.tabelas["Apontamentos"]?"horas":(j.colunas&&j.linhas?"tickets":null);
  if(!kind){toast("Arquivo não reconhecido. Use base_integracoes.json ou horas_integracoes_painel.json.");return;}
  toast("Enviando "+(kind==="horas"?"base de horas":"base de tickets")+"…");
  try{const r=await S.assets.upload(file,{type:"application/json"});const old=(S.bases||{})[kind];
    const meta=j.meta||{};const linhas=kind==="horas"?(j.tabelas["Apontamentos"].linhas||[]).length:j.linhas.length;
    const doc={...(S.bases||{}),[kind]:{asset:r.id,gerado_em:meta.gerado_em||"",linhas,enviado_em:new Date().toISOString(),arquivo:file.name}};
    await S.db.doc("cfg/bases").set(doc);
    if(old&&old.asset&&old.asset!==r.id){try{await S.assets.delete(old.asset);}catch(e){}}
    toast("Base carregada");}
  catch(e){toast({too_large:"Arquivo acima de 20 MB.",rate_limited:"Muitas tentativas; aguarde um pouco.",not_granted:"Sem permissão para carregar arquivos."}[e&&e.code]||"Não foi possível carregar o arquivo.");}}

// ---------------- boot ----------------
try{const v=localStorage.getItem("ig_view");if(v&&TABS.some(t=>t[0]===v))S.view=v;}catch(e){}
if(/^#[a-z]+$/.test(location.hash)&&TABS.some(t=>"#"+t[0]===location.hash))S.view=location.hash.slice(1);
window.__TEST__={S,compute,render,VIEWS,burndown,achados,blFiltered,loadFrom(T,H){S.T=T;S.H=H;compute();}};
render();
(async function boot(){const c=window.claude;
  const [db,user]=await Promise.all([c?.use?.("db")??null,c?.use?.("user")??null]);
  S.db=db;S.user=user;S.ready=true;
  if(user){try{S.canEdit=await user.canEdit();}catch(e){}}
  if(S.canEdit){c?.use?.("assets").then(a=>{S.assets=a;if(S.view==="cfg")render();}).catch(()=>{});}
  if(!db){render();return;}
  db.doc("cfg/params").onSnapshot(s=>{S.params=s.exists?{...JSON.parse(JSON.stringify(DEFAULT_PARAMS)),...s.data()}:JSON.parse(JSON.stringify(DEFAULT_PARAMS));if(S.T){compute();}render();},()=>{});
  db.doc("cfg/bases").onSnapshot(s=>{S.bases=s.exists?s.data():null;loadBases();},()=>{S.loadErr="Não foi possível ler o banco do painel.";render();});
})();
})();
</script>
