// ---------------- estado e constantes ----------------
// Time (Painel de Serviços, área Integração). Ex-integrantes mantêm o nome nos tickets e nas horas históricas.
const TEAM_DEFAULT=["Amanda Maria Pinheiro","Elder Galvao Quirino Ribeiro","Lucas Silva Monteiro","Thais Majory de Paulo Santos"];
const EX_DEFAULT=["Ewerton Vital de Carvalho"];
const SHORT={"Amanda Maria Pinheiro":"Amanda Pinheiro","Elder Galvao Quirino Ribeiro":"Elder Ribeiro","Lucas Silva Monteiro":"Lucas Monteiro","Thais Majory de Paulo Santos":"Thais Santos","Ewerton Vital de Carvalho":"Ewerton Carvalho"};
// Famílias de demanda (campo Type do Freshdesk, definidas na extração). Projeto é o foco do painel.
const FAMS=[
  {k:"Projeto",lab:"Projetos",c:"var(--serie-2)"},
  {k:"Consultoria",lab:"Consultoria",c:"var(--serie-3)"},
  {k:"Suporte",lab:"Suporte",c:"var(--serie-1)"},
  {k:"Bug",lab:"Bugs",c:"var(--serie-6)"},
  {k:"Dúvidas",lab:"Dúvidas",c:"var(--serie-4)"},
  {k:"Orçamento",lab:"Orçamento",c:"var(--serie-5)"},
  {k:"Outros",lab:"Outros",c:"var(--muted-foreground)"},
];
const FAM_KEYS=FAMS.map(f=>f.k);
const FAM_LAB=Object.fromEntries(FAMS.map(f=>[f.k,f.lab]));
const FAM_COL=Object.fromEntries(FAMS.map(f=>[f.k,f.c]));
const CARGA=["Projeto","Consultoria","Suporte","Bug"]; // demanda do time (Dúvidas e Orçamento: volume e fila)
const FILAS=["Orçamento","Macro escopo","Especificação"];
const DEFAULT_PARAMS={time:TEAM_DEFAULT.slice(),ex:EX_DEFAULT.slice(),vencendo_dias:15,parado_dias:30,fator_produtivo:0.85,teto_backlog:0.9,horas_mes_padrao:147,ref_horas:{}};
const S={db:null,assets:null,user:null,canEdit:false,bases:null,params:JSON.parse(JSON.stringify(DEFAULT_PARAMS)),T:null,H:null,C:null,view:"geral",loadErr:null,loaded:{},ready:false,
  bl:{fam:"",st:"",dono:"",prod:"",prazo:"",escopo:"geral",q:"",limite:200},pj:{prod:"",dono:""},fila:{prod:""}};
const TABS=[["geral","Visão geral"],["proj","Projetos"],["diag","Diagnóstico"],["prazo","Prazos"],["backlog","Backlog"],["sust","Suporte e Bugs"],["cons","Consultoria"],["fila","Fila de orçamento"],["time","Time"],["horas","Horas"],["sop","S&OP"],["cfg","Configuração"]];
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nf=(n,d)=>(n==null||!isFinite(n))?"–":Number(n).toLocaleString("pt-BR",{maximumFractionDigits:d||0,minimumFractionDigits:d||0});
const pct=(n,d)=>(n==null||!isFinite(n))?"–":nf(n*100,d||0)+"%";
const MES=["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];
const mlab=m=>MES[+m.slice(5,7)-1]+"/"+m.slice(2,4);
const norm=s=>String(s||"").normalize("NFD").replace(/[̀-ͯ​]/g,"").toLowerCase().trim();
const short=n=>SHORT[n]||n||"";
function toast(t){const el=$("#toast");if(!el)return;el.textContent=t;el.hidden=false;clearTimeout(toast._t);toast._t=setTimeout(()=>el.hidden=true,4000);}
const TODAY=new Date();const curMonth=TODAY.toISOString().slice(0,7);
const dt=s=>{if(!s)return null;const d=new Date(String(s).length===10?s+"T12:00:00":s);return isNaN(d)?null:d;};
const days=(a,b)=>{const d=dt(a);return d?Math.floor(((b||TODAY)-d)/864e5):null;};
const fdia=d=>{if(!d)return "–";return d.toLocaleDateString("pt-BR",{day:"2-digit",month:"2-digit",year:"2-digit"});};
function median(a){if(!a.length)return null;const s=[...a].sort((x,y)=>x-y);const m=s.length>>1;return s.length%2?s[m]:(s[m-1]+s[m])/2;}
function quant(a,q){if(!a.length)return null;const s=[...a].sort((x,y)=>x-y);return s[Math.min(s.length-1,Math.floor(q*(s.length-1)))];}
const mean=a=>a.length?a.reduce((s,x)=>s+x,0)/a.length:null;
const sum=(a,f)=>a.reduce((s,x)=>s+(f?f(x):x),0);
function addMonths(m,k){const d=new Date(Date.UTC(+m.slice(0,4),+m.slice(5,7)-1+k,1));return d.toISOString().slice(0,7);}
function countBy(L,f){const o={};for(const x of L){const k=f(x);o[k]=(o[k]||0)+1;}return o;}

// ---------------- prazos (decisão do Diego, 07-08/10/2026) ----------------
// Prazo combinado = "Data limite para entrega". Data Início/Fim = execução real. Aberto: atrasado se hoje > limite sem Data Fim.
// Encerrado: no prazo quando (Data Fim | Data da entrega | resolução/fechamento) <= limite.
const PRAZO_LAB={atrasado:"Atrasado",vencendo:"Vencendo",no_prazo:"No prazo",sem_prazo:"Sem prazo definido",entregue_prazo:"Entregue no prazo",entregue_atraso:"Entregue com atraso",entregue_aberto:"Entregue (a encerrar)"};
const PRAZO_CLS={atrasado:"bad",vencendo:"warn",no_prazo:"ok",sem_prazo:"gray",entregue_prazo:"ok",entregue_atraso:"bad",entregue_aberto:"info"};
function prazoDe(t,P){
  const lim=dt(t.data_limite_entrega),fim=dt(t.data_fim)||dt(t.data_entrega);
  t.limite=lim;t.atraso=0;t.faltam=null;
  if(t.backlog_geral){
    if(!lim)return "sem_prazo";
    if(fim)return fim<=lim?"entregue_aberto":"entregue_atraso";
    const f=Math.ceil((lim-TODAY)/864e5);t.faltam=f;
    if(f<0){t.atraso=-f;return "atrasado";}
    return f<=P.vencendo_dias?"vencendo":"no_prazo";
  }
  if(t.concluido_no_ano||t.resolvido_no_ano){
    if(!lim)return "sem_prazo";
    const ref=fim||dt(t.data_resolucao)||dt(t.data_fechamento);if(!ref)return "sem_prazo";
    t.atraso=Math.max(0,Math.floor((ref-lim)/864e5));return ref<=lim?"entregue_prazo":"entregue_atraso";
  }
  return "";
}

// ---------------- carga ----------------
function rowsOf(tb){const c=tb.colunas;return tb.linhas.map(r=>{const o={};for(let i=0;i<c.length;i++)o[c[i]]=r[i];return o;});}
async function fetchAsset(id){const r=await fetch("/_blob/"+id);if(!r.ok)throw new Error("HTTP "+r.status);return r.json();}
async function loadBases(){
  const b=S.bases||{};
  try{
    if(b.tickets&&b.tickets.asset&&S.loaded.tickets!==b.tickets.asset){const j=await fetchAsset(b.tickets.asset);S.Tmeta=j.meta;S.T=rowsOf(j);S.loaded.tickets=b.tickets.asset;}
    if(b.horas&&b.horas.asset&&S.loaded.horas!==b.horas.asset){const j=await fetchAsset(b.horas.asset);S.Hmeta=j.meta;S.H={};for(const k in j.tabelas)S.H[k]=rowsOf(j.tabelas[k]);S.loaded.horas=b.horas.asset;}
    S.loadErr=null;
  }catch(e){S.loadErr="Não foi possível ler uma das bases ("+e.message+"). Carregue o arquivo de novo em Configuração.";}
  compute();render();
}

// ---------------- cálculo ----------------
function compute(){
  if(!S.T){S.C=null;return;}
  const P=S.params,team=new Set((P.time||[]).map(norm)),ex=new Set((P.ex||[]).map(norm));
  const T=S.T.map(t=>{
    const n=norm(t.agente);let dono,donoTipo;
    if(!t.agente){dono="Sem responsável";donoTipo="sem";}
    else if(team.has(n)){dono=short(canon(t.agente,P.time));donoTipo="time";}
    else if(ex.has(n)){dono=short(canon(t.agente,P.ex))+" (ex)";donoTipo="ex";}
    else{dono=t.agente;donoTipo="fora";}
    const saida=t.data_resolucao||t.data_fechamento||"";
    const o={...t,dono,donoTipo,st:String(t.status||"").split(" / ")[0],idade:days(t.criado_em),parado:days(t.status_desde||t.atualizado_em),
      saida,mesEnt:(t.criado_em||"").slice(0,7),mesSai:(t.concluido_no_ano||t.resolvido_no_ano)?saida.slice(0,7):"",produto:t.produto||"Sem produto",fila:t.tipo_fila||""};
    o.est=num(t.estim_total_h)||num(t.estimativa_h)||(num(t.estim_po_dev_h)+num(t.estim_po_hml_h)+num(t.estim_po_orc_h))||null;
    o.prazo=prazoDe(o,P);
    return o;});
  const byId=new Map(T.map(t=>[String(t.id),t]));
  const BL=T.filter(t=>t.backlog_geral);
  // horas (somente área Integração) -----------------------------------------------------------
  let A=[],capM={},teamH={},hTk=new Map(),months=[];
  if(S.H){
    A=S.H["Apontamentos"]||[];
    for(const c of (S.H["Capacidade"]||[])){if(!team.has(norm(c.analyst_name)))continue;(capM[c.year_month]=capM[c.year_month]||{})[c.analyst_name]=(c.capacity_seconds||0)/3600;}
    for(const a of A){const k=String(a.ticket_id||"").trim();if(k)hTk.set(k,(hTk.get(k)||0)+(a.horas||0));}
    months=[...new Set(A.map(a=>a.mes))].sort();
  }
  for(const t of T)t.horas=hTk.get(String(t.id))||0;
  const ano=curMonth.slice(0,4),fm=[];for(let i=1;i<=+curMonth.slice(5,7);i++)fm.push(ano+"-"+String(i).padStart(2,"0"));
  const fluxo=fm.map(m=>({m,lab:mlab(m),ent:T.filter(t=>t.novo_no_ano&&t.mesEnt===m).length,sai:T.filter(t=>t.mesSai===m).length,canc:T.filter(t=>t.cancelado_no_ano&&days(t.saida||t.atualizado_em)!=null&&(t.saida||t.atualizado_em).slice(0,7)===m).length}));
  const fechados=fm.filter(m=>m<curMonth).slice(-3);
  // esforço de referência por família: mediana de horas dos encerrados no ano (ou valor definido em Configuração)
  const ref={};for(const f of FAM_KEYS){const v=T.filter(t=>t.familia===f&&(t.concluido_no_ano||t.resolvido_no_ano)&&t.horas>0).map(t=>t.horas);
    const o=(P.ref_horas||{})[f];ref[f]=o>0?{h:o,n:v.length,fonte:"definido"}:(v.length>=3?{h:median(v),n:v.length,fonte:"mediana dos encerrados"}:{h:null,n:v.length,fonte:"sem base"});}
  S.C={T,BL,byId,A,hTk,months,capM,fluxo,fechados,team,ex,ref,fm};
  for(const t of T){const r=t.est||(ref[t.familia]&&ref[t.familia].h)||0;t.esfRef=t.est?"estimativa":(r?"referência":"");t.saldo=Math.max(0,r-t.horas);}
}
function num(v){const n=+v;return isFinite(n)&&v!==""&&v!=null?n:0;}
function canon(nome,lista){const n=norm(nome);return (lista||[]).find(x=>norm(x)===n)||nome;}
const isTeam=t=>t.donoTipo==="time";
const prodList=()=>[...new Set((S.C?S.C.T:[]).map(t=>t.produto))].sort();
const donoList=()=>[...new Set((S.C?S.C.BL:[]).map(t=>t.dono))].sort();

// ---------------- S&OP: simulação mês a mês (modelo do ADV, LOG_SOP §5) ----------------
// Cada mês paga ao backlog no máximo `teto` da capacidade do time atual; o excedente rola para o mês seguinte.
function capacidadeMes(m){const C=S.C,P=S.params;const h=sum(Object.values(C.capM[m]||{}));return (h>0?h:C.team.size*P.horas_mes_padrao)*P.fator_produtivo;}
function demandaMedia(){const C=S.C;const o={};for(const f of CARGA){const r=C.ref[f].h||0;const n=mean(C.fechados.map(m=>C.T.filter(t=>t.novo_no_ano&&t.familia===f&&t.mesEnt===m).length))||0;o[f]={n,h:n*r,ref:C.ref[f]};}return o;}
function burndown(ativoSo){
  const C=S.C,P=S.params,dem=demandaMedia();
  const L=C.BL.filter(t=>CARGA.includes(t.familia)&&(!ativoSo||t.backlog_ativo));
  let rest=sum(L,t=>t.saldo);const h0=rest;const meses=[];let m=curMonth;const fc=sum(Object.values(dem),x=>x.h);
  for(let i=0;i<12&&(rest>0.5||i===0);i++){
    const cap=capacidadeMes(m),pago=Math.min(rest,cap*P.teto_backlog);rest-=pago;
    meses.push({m,lab:mlab(m),cap,pago,fc,rest});m=addMonths(m,1);if(i>0&&rest<=0.5)break;}
  return {h0,meses,fim:rest<=0.5?meses.length:null,fc,dem,n:L.length,semRef:L.filter(t=>!t.esfRef).length};
}
