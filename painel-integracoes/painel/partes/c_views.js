// ---------------- visões ----------------
const tag=(cls,t)=>`<span class="tag ${cls}">${esc(t)}</span>`;
function prazoTag(t){if(!t.prazo)return "";let x=PRAZO_LAB[t.prazo];if(t.prazo==="atrasado"||t.prazo==="entregue_atraso")x+=" · "+nf(t.atraso)+" d";else if(t.prazo==="vencendo")x+=" · "+nf(t.faltam)+" d";return tag(PRAZO_CLS[t.prazo],x);}
const link=t=>`<a href="https://projuris-helpdesk.freshdesk.com/a/tickets/${esc(t.id)}" target="_blank" rel="noopener">${esc(t.id)}</a>`;
const sel=(id,lab,val,opts,all)=>`<label class="f" for="${id}">${lab}<select id="${id}"><option value="">${all||"Todos"}</option>${opts.map(o=>{const v=Array.isArray(o)?o[0]:o,l=Array.isArray(o)?o[1]:o;return `<option value="${esc(v)}" ${val===v?"selected":""}>${esc(l)}</option>`;}).join("")}</select></label>`;
function bands(L,f,B){return B.map(([l,a,b])=>({l,v:L.filter(t=>{const x=f(t);return x!=null&&x>=a&&x<=b;}).length}));}
const AGE=[["até 30 d",0,30],["31–90 d",31,90],["91–180 d",91,180],["+180 d",181,1e9]];
const IDADE_COL=["var(--serie-3)","var(--serie-2)","var(--serie-1)","var(--destructive)"];
const ordem={atrasado:0,vencendo:1,sem_prazo:2,entregue_atraso:3,entregue_aberto:4,no_prazo:5,entregue_prazo:6};
const sortRisco=(a,b)=>(ordem[a.prazo]??9)-(ordem[b.prazo]??9)||(b.atraso-a.atraso)||(b.idade-a.idade);
function tabela(head,rows,empty){if(!rows.length)return `<p class="hint">${empty||"Nada a mostrar."}</p>`;return `<div class="tblw"><table><thead><tr>${head.map(h=>`<th class="${h[1]||""}">${h[0]}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`;}
const note0=()=>S.C.T.length?"":`<p class="note">Base de tickets vazia.</p>`;

function vGeral(){
  const C=S.C,BL=C.BL,PJ=BL.filter(t=>t.familia==="Projeto");
  const atr=PJ.filter(t=>t.prazo==="atrasado").length;
  const enc=C.T.filter(t=>t.concluido_no_ano||t.resolvido_no_ano).length;
  const fa=FAMS.map(f=>({l:f.lab,parts:[{v:BL.filter(t=>t.familia===f.k&&t.backlog_ativo).length,c:f.c,l:"Ativo"},{v:BL.filter(t=>t.familia===f.k&&t.suspenso).length,c:"var(--serie-4)",l:"Suspenso"}]})).filter(r=>r.parts[0].v+r.parts[1].v>0);
  const hm=C.months.map(m=>{const o={lab:mlab(m)};for(const tp of TIPOS)o[tp]=sum(C.A.filter(a=>a.mes===m&&a.tipo===tp),a=>a.horas||0);o.cap=sum(Object.values(C.capM[m]||{}));return o;});
  return `<section class="view">
   <div class="kpis">
    ${kpi("Backlog geral",nf(BL.length),"inclui pendentes com o cliente e suspensos")}
    ${kpi("Backlog ativo",nf(BL.filter(t=>t.backlog_ativo).length),"tudo que não está suspenso")}
    ${kpi("Suspensos",nf(BL.filter(t=>t.suspenso).length),"fora do ativo")}
    ${kpi("Projetos abertos",nf(PJ.length),nf(PJ.filter(t=>t.backlog_ativo).length)+" ativos")}
    ${kpi("Projetos atrasados",nf(atr),"hoje &gt; data limite, sem Data Fim",atr?"bad":"good")}
    ${kpi("Abertos no ano",nf(C.T.filter(t=>t.novo_no_ano).length),"criados em "+curMonth.slice(0,4))}
    ${kpi("Encerrados no ano",nf(enc),nf(C.T.filter(t=>t.concluido_no_ano).length)+" fechados · "+nf(C.T.filter(t=>t.resolvido_no_ano).length)+" resolvidos")}
    ${kpi("Cancelados no ano",nf(C.T.filter(t=>t.cancelado_no_ano).length),"status ou tag “cancelado”")}
   </div>
   <div class="grid g2">
    <div class="card"><h2>Entradas e saídas por mês</h2><p class="hint">Abertos no mês × encerrados (fechados ou resolvidos) no mês</p>
     ${colChart(C.fluxo,[{k:"ent",c:"var(--serie-2)",l:"Abertos"},{k:"sai",c:CS,l:"Encerrados"}],{aria:"Entradas e saídas por mês"})}${legend([["var(--serie-2)","Abertos"],[CS,"Encerrados"]])}</div>
    <div class="card"><h2>Backlog por família</h2><p class="hint">Ativo e suspenso. Orçamento e Dúvidas são acompanhados, não entram na carga do time.</p>${hbars(fa,{})}${legend([["var(--primary)","Ativo (cor da família)"],["var(--serie-4)","Suspenso"]])}</div>
   </div>
   <div class="grid g2">
    <div class="card"><h2>Horas apontadas por mês</h2><p class="hint">Área Integração, por tipo de apontamento; linha tracejada = capacidade do time atual</p>
     ${hm.length?colChart(hm,TIPOS.map((tp,i)=>({k:tp,c:TIPO_COL[i],l:tp})),{stack:true,line:{k:"cap",c:"var(--foreground)",l:"Capacidade"},aria:"Horas por mês"}):`<p class="hint">Base de horas não carregada.</p>`}${legend(TIPOS.map((tp,i)=>[TIPO_COL[i],tp]))}</div>
    <div class="card"><h2>Prazos dos projetos abertos</h2>${prazoBars(PJ)}<p class="hint">Prazo = Data limite para entrega. Detalhes na aba Prazos.</p></div>
   </div></section>`;
}
const TIPOS=["Faturável","Interno","Não Faturável","Apoio a outro time"];
const TIPO_COL=["var(--serie-saida)","var(--serie-4)","var(--serie-1)","var(--serie-6)"];
function prazoBars(L){const o=countBy(L,t=>t.prazo);const keys=["atrasado","vencendo","no_prazo","entregue_aberto","entregue_atraso","entregue_prazo","sem_prazo"];
  const colv={atrasado:"var(--destructive)",vencendo:"var(--warning)",no_prazo:"var(--success)",entregue_aberto:"var(--serie-2)",entregue_atraso:"var(--destructive)",entregue_prazo:"var(--success)",sem_prazo:"var(--serie-4)"};
  const rows=keys.filter(k=>o[k]).map(k=>({l:PRAZO_LAB[k],v:o[k],c:colv[k]}));return rows.length?hbars(rows,{}):`<p class="hint">Sem projetos.</p>`;}

// ---------- Projetos (centro do painel) ----------
function vProj(){
  const C=S.C,F=S.pj;const base=C.T.filter(t=>t.familia==="Projeto"&&(!F.prod||t.produto===F.prod)&&(!F.dono||t.dono===F.dono));
  const ab=base.filter(t=>t.backlog_geral).sort(sortRisco),enc=base.filter(t=>t.concluido_no_ano||t.resolvido_no_ano);
  const comLim=enc.filter(t=>t.prazo==="entregue_prazo"||t.prazo==="entregue_atraso");
  const noPrazo=comLim.length?comLim.filter(t=>t.prazo==="entregue_prazo").length/comLim.length:null;
  const st=Object.entries(countBy(ab,t=>t.st)).sort((a,b)=>b[1]-a[1]).map(([l,v])=>({l,v}));
  const an=Object.entries(countBy(ab,t=>t.dono)).sort((a,b)=>b[1]-a[1]).map(([l,v])=>({l,v}));
  const row=t=>`<tr><td>${link(t)}</td><td class="wrap">${esc(t.assunto)}</td><td>${esc(t.produto)}</td><td>${esc(t.st)}${t.suspenso?" "+tag("gray","suspenso"):""}</td><td>${esc(t.dono)}</td><td class="n">${nf(t.idade)} d</td><td class="n">${nf(t.parado)} d</td><td>${fdia(t.limite)}</td><td>${prazoTag(t)}</td><td class="n">${nf(t.horas,1)}</td><td class="n">${t.est?nf(t.est,1):"–"}</td></tr>`;
  const hd=[["ID"],["Projeto"],["Produto"],["Status"],["Responsável"],["Idade","n"],["Parado","n"],["Data limite"],["Prazo"],["Horas","n"],["Estim.","n"]];
  return `<section class="view">
   <div class="card"><div class="filters">${sel("pj_prod","Produto",F.prod,prodList())}${sel("pj_dono","Responsável",F.dono,donoList())}</div></div>
   <div class="kpis">
    ${kpi("Projetos abertos",nf(ab.length),nf(ab.filter(t=>t.backlog_ativo).length)+" ativos · "+nf(ab.filter(t=>t.suspenso).length)+" suspensos")}
    ${kpi("Atrasados",nf(ab.filter(t=>t.prazo==="atrasado").length),"hoje &gt; data limite",ab.some(t=>t.prazo==="atrasado")?"bad":"good")}
    ${kpi("Vencendo",nf(ab.filter(t=>t.prazo==="vencendo").length),"até "+S.params.vencendo_dias+" dias do limite")}
    ${kpi("Sem prazo definido",nf(ab.filter(t=>t.prazo==="sem_prazo").length),"sem Data limite para entrega")}
    ${kpi("Encerrados no ano",nf(enc.length),"fechados + resolvidos")}
    ${kpi("Entregues no prazo",pct(noPrazo),comLim.length?nf(comLim.length)+" encerrados com data limite":"sem encerrados com data limite")}
    ${kpi("Horas nos abertos",nf(sum(ab,t=>t.horas),0),"apontadas até hoje")}
   </div>
   <div class="grid g2">
    <div class="card"><h2>Projetos abertos por etapa</h2><p class="hint">Status do fluxo de projeto no Freshdesk</p>${st.length?hbars(st,{}):`<p class="hint">Nenhum projeto aberto.</p>`}</div>
    <div class="card"><h2>Por responsável</h2><p class="hint">Projetos abertos. “(ex)” = ex-integrante, “Fora do time” = agente de outro grupo.</p>${an.length?hbars(an,{}):`<p class="hint">–</p>`}</div>
   </div>
   <div class="card"><h2>Projetos abertos · ordem de risco</h2><p class="hint">Atrasados, vencendo e sem prazo primeiro. Horas = apontadas no Painel de Serviços; Estim. = campo de estimativa do ticket.</p>${tabela(hd,ab.map(row),"Nenhum projeto aberto com este filtro.")}</div>
   <div class="card"><h2>Encerrados no ano · últimos 15</h2>${tabela(hd,enc.sort((a,b)=>String(b.saida).localeCompare(String(a.saida))).slice(0,15).map(row),"Nenhum projeto encerrado.")}</div>
  </section>`;
}

// ---------- Prazos ----------
function vPrazo(){
  const C=S.C,PJ=C.T.filter(t=>t.familia==="Projeto"),ab=PJ.filter(t=>t.backlog_geral);
  const cob=(L,f)=>L.length?L.filter(f).length/L.length:null;
  const keys=Object.keys(PRAZO_LAB);
  const mat=FAM_KEYS.filter(f=>C.T.some(t=>t.familia===f&&t.prazo)).map(f=>`<tr><td>${esc(FAM_LAB[f])}</td>${keys.map(k=>`<td class="n">${nf(C.T.filter(t=>t.familia===f&&t.prazo===k).length)}</td>`).join("")}</tr>`);
  const crit=ab.filter(t=>t.prazo==="atrasado"||t.prazo==="vencendo").sort(sortRisco);
  return `<section class="view">
   <p class="note">Regra do prazo: <b>prazo combinado = Data limite para entrega</b>; <b>Data Início / Data Fim = execução real</b>. Aberto fica <b>atrasado</b> quando hoje passa da data limite sem Data Fim; encerrado fica <b>no prazo</b> quando a data de entrega real (Data Fim, Data da entrega ou resolução) é menor ou igual à data limite. Marcos intermediários entram numa segunda etapa.</p>
   <div class="kpis">
    ${kpi("Projetos abertos com data limite",pct(cob(ab,t=>!!t.data_limite_entrega)),nf(ab.filter(t=>t.data_limite_entrega).length)+" de "+nf(ab.length),cob(ab,t=>!!t.data_limite_entrega)<0.8?"bad":"good")}
    ${kpi("Com Data Início",pct(cob(ab,t=>!!t.data_inicio)),"projetos abertos")}
    ${kpi("Com Data Fim",pct(cob(ab,t=>!!t.data_fim)),"projetos abertos")}
    ${kpi("Com estimativa de horas",pct(cob(ab,t=>!!t.est)),"projetos abertos")}
   </div>
   <div class="card"><h2>Situação de prazo por família</h2><p class="hint">Só aparecem famílias com data limite preenchida em algum ticket.</p>
    ${tabela([["Família"],...keys.map(k=>[PRAZO_LAB[k],"n"])],mat,"Nenhum ticket com data limite.")}</div>
   <div class="card"><h2>Projetos atrasados e vencendo</h2>${tabela([["ID"],["Projeto"],["Responsável"],["Status"],["Data limite"],["Situação"]],crit.map(t=>`<tr><td>${link(t)}</td><td class="wrap">${esc(t.assunto)}</td><td>${esc(t.dono)}</td><td>${esc(t.st)}</td><td>${fdia(t.limite)}</td><td>${prazoTag(t)}</td></tr>`),"Nenhum projeto atrasado ou vencendo.")}</div>
  </section>`;
}

// ---------- Diagnóstico ----------
function achados(){
  const C=S.C,P=S.params,BL=C.BL,PJ=BL.filter(t=>t.familia==="Projeto"),out=[];
  const add=(lvl,t,d,L,k)=>{if(L.length)out.push({lvl,t,d,n:L.length,k,L});};
  add("bad","Projetos atrasados","Hoje passou da data limite e não há Data Fim.",PJ.filter(t=>t.prazo==="atrasado"),"atrasado");
  add("warn","Projetos sem data limite para entrega","Sem prazo combinado não há como medir atraso. Preencher ao abrir o projeto.",PJ.filter(t=>t.prazo==="sem_prazo"));
  add("warn","Projetos sem Data Início ou Data Fim","Execução real sem registro; a leitura de planejado × realizado fica incompleta.",PJ.filter(t=>!t.data_inicio||!t.data_fim));
  add("warn","Projetos sem estimativa de horas","Sem estimativa, o saldo de horas usa a mediana dos encerrados.",PJ.filter(t=>!t.est));
  add("bad","Tickets abertos de ex-integrante","Mantidos no nome do analista que saiu; avaliar reatribuição.",BL.filter(t=>t.donoTipo==="ex"));
  add("warn","Tickets abertos sem responsável","",BL.filter(t=>t.donoTipo==="sem"));
  add("info","Tickets abertos com agente de fora do time","Agentes de outros grupos atendendo tickets do grupo INTEGRACOES.",BL.filter(t=>t.donoTipo==="fora"));
  add("warn","Backlog ativo parado há mais de "+P.parado_dias+" dias","Status sem mudança.",BL.filter(t=>t.backlog_ativo&&t.parado!=null&&t.parado>P.parado_dias));
  add("warn","Tickets sem Type","Sem Type não há família; entram em Outros.",C.T.filter(t=>!t.tipo&&(t.backlog_geral||t.novo_no_ano)));
  add("info","Tipos fora das famílias do time","Erro e Falha são Bug; demais tipos gerais ficam em Outros.",BL.filter(t=>t.familia==="Outros"));
  const sh=[...(C.A||[])].filter(a=>!a.ticket_id);
  if(sh.length)out.push({lvl:"info",t:"Apontamentos sem ticket",d:"Horas não ligadas a ticket (reuniões, atividades internas).",n:sh.length,k:"",L:[],h:sum(sh,a=>a.horas||0)});
  const aband=C.T.filter(t=>t.cancelado_no_ano&&t.horas>0);
  if(aband.length)out.push({lvl:"info",t:"Cancelados com horas apontadas",d:"Esforço consumido em tickets cancelados.",n:aband.length,k:"",L:aband,h:sum(aband,t=>t.horas)});
  return out;
}
function vDiag(){
  const A=achados(),bad=A.filter(a=>a.lvl==="bad").length;
  return `<section class="view">
   <div class="verdict ${bad?"bad":"good"}"><span class="big">${bad?nf(bad)+" achado(s) críticos":"Sem achados críticos"}</span><span>${nf(A.length)} achados no total. Cada linha lista os tickets envolvidos.</span></div>
   <div class="card">${A.map((a,i)=>`<details class="find" style="display:block"><summary style="cursor:pointer;display:flex;gap:12px;align-items:center;flex-wrap:wrap"><span class="chip ${a.lvl}">${nf(a.n)}</span><b>${esc(a.t)}</b>${a.h?`<span class="hint">${nf(a.h,1)} h</span>`:""}<span class="hint" style="flex:1 1 240px">${esc(a.d)}</span></summary>
     ${a.L.length?tabela([["ID"],["Assunto"],["Família"],["Status"],["Responsável"]],a.L.slice(0,60).map(t=>`<tr><td>${link(t)}</td><td class="wrap">${esc(t.assunto)}</td><td>${esc(FAM_LAB[t.familia])}</td><td>${esc(t.st)}</td><td>${esc(t.dono)}</td></tr>`)):""}${a.L.length>60?`<p class="hint">Mostrando 60 de ${nf(a.L.length)}.</p>`:""}</details>`).join("")||`<p class="hint">Nada a apontar.</p>`}</div>
  </section>`;
}

// ---------- Backlog ----------
function blFiltered(){const f=S.bl,q=norm(f.q);return S.C.T.filter(t=>t.backlog_geral&&(f.escopo==="geral"||(f.escopo==="ativo"&&t.backlog_ativo)||(f.escopo==="susp"&&t.suspenso))&&(!f.fam||t.familia===f.fam)&&(!f.st||t.st===f.st)&&(!f.dono||t.dono===f.dono)&&(!f.prod||t.produto===f.prod)&&(!f.prazo||t.prazo===f.prazo)&&(!q||norm(t.assunto).includes(q)||String(t.id).includes(q)||norm(t.solicitante).includes(q))).sort((a,b)=>b.idade-a.idade);}
function vBacklog(){
  const C=S.C,f=S.bl,L=blFiltered(),sts=[...new Set(C.BL.map(t=>t.st))].sort();
  return `<section class="view"><div class="card">
   <div class="filters"><div><div class="hint" style="margin-bottom:4px">Escopo</div><div class="seg" role="group" aria-label="Escopo do backlog">${[["geral","Geral"],["ativo","Ativo"],["susp","Suspenso"]].map(([v,l])=>`<button data-bl-esc="${v}" aria-pressed="${f.escopo===v}">${l}</button>`).join("")}</div></div>
    ${sel("f_fam","Família",f.fam,FAMS.map(x=>[x.k,x.lab]))}${sel("f_st","Status",f.st,sts)}${sel("f_dono","Responsável",f.dono,donoList())}${sel("f_prod","Produto",f.prod,prodList())}${sel("f_prazo","Prazo",f.prazo,["atrasado","vencendo","no_prazo","sem_prazo","entregue_aberto","entregue_atraso"].map(k=>[k,PRAZO_LAB[k]]))}
    <label class="f" for="f_q">Busca<input type="search" id="f_q" value="${esc(f.q)}" placeholder="ticket, assunto, solicitante"></label>
    <button class="btn" id="f_csv">Exportar CSV</button></div>
   <p class="hint">${nf(L.length)} tickets · geral ${nf(C.BL.length)} · ativo ${nf(C.BL.filter(t=>t.backlog_ativo).length)} · suspenso ${nf(C.BL.filter(t=>t.suspenso).length)}</p>
   ${tabela([["ID"],["Assunto"],["Família"],["Produto"],["Status"],["Responsável"],["Idade","n"],["Parado","n"],["Prazo"],["Horas","n"]],L.slice(0,f.limite).map(t=>`<tr><td>${link(t)}</td><td class="wrap">${esc(t.assunto)}</td><td>${esc(FAM_LAB[t.familia])}${t.fila?" "+tag("gray",t.fila):""}</td><td>${esc(t.produto)}</td><td>${esc(t.st)}</td><td>${esc(t.dono)}</td><td class="n">${nf(t.idade)} d</td><td class="n">${nf(t.parado)} d</td><td>${prazoTag(t)}</td><td class="n">${nf(t.horas,1)}</td></tr>`))}
   ${L.length>f.limite?`<div><button class="btn" id="f_more">Mostrar mais</button></div>`:""}</div></section>`;
}

// ---------- Suporte e Bugs (sustentação) ----------
function vSust(){
  const C=S.C,fam=["Suporte","Bug"],ab=C.BL.filter(t=>fam.includes(t.familia)),enc=C.T.filter(t=>fam.includes(t.familia)&&(t.concluido_no_ano||t.resolvido_no_ano));
  const tr=enc.map(t=>days(t.criado_em,dt(t.saida))).filter(x=>x!=null);
  const st=Object.entries(countBy(ab,t=>t.st)).sort((a,b)=>b[1]-a[1]).map(([l,v])=>({l,v}));
  const ag=bands(ab,t=>t.idade,AGE).map((b,i)=>({l:b.l,v:b.v,c:IDADE_COL[i]}));
  return `<section class="view">
   <p class="note">Sustentação em produção: <b>Suporte</b> = Type “Integrações - Suporte”; <b>Bug</b> = Types de Erro e Falha. Tickets do mesmo cliente que se repetem indicam causa raiz a tratar.</p>
   <div class="kpis">
    ${kpi("Abertos",nf(ab.length),nf(ab.filter(t=>t.familia==="Suporte").length)+" suporte · "+nf(ab.filter(t=>t.familia==="Bug").length)+" bug")}
    ${kpi("Idade mediana",nf(median(ab.map(t=>t.idade).filter(x=>x!=null)))+" d","tickets abertos")}
    ${kpi("Parados &gt; "+S.params.parado_dias+" d",nf(ab.filter(t=>t.parado!=null&&t.parado>S.params.parado_dias).length),"sem mudança de status")}
    ${kpi("Encerrados no ano",nf(enc.length),"fechados + resolvidos")}
    ${kpi("Tempo mediano até encerrar",tr.length?nf(median(tr))+" d":"–","criação → resolução/fechamento")}
   </div>
   <div class="grid g2"><div class="card"><h2>Por status</h2>${st.length?hbars(st,{}):`<p class="hint">Nenhum aberto.</p>`}</div>
    <div class="card"><h2>Idade dos abertos</h2>${hbars(ag.map(b=>({l:b.l,parts:[{v:b.v,c:b.c}]})),{})}</div></div>
   <div class="card"><h2>Abertos</h2>${tabela([["ID"],["Assunto"],["Família"],["Status"],["Responsável"],["Idade","n"],["Parado","n"],["Horas","n"]],ab.sort((a,b)=>b.idade-a.idade).map(t=>`<tr><td>${link(t)}</td><td class="wrap">${esc(t.assunto)}</td><td>${esc(FAM_LAB[t.familia])}</td><td>${esc(t.st)}</td><td>${esc(t.dono)}</td><td class="n">${nf(t.idade)} d</td><td class="n">${nf(t.parado)} d</td><td class="n">${nf(t.horas,1)}</td></tr>`),"Nenhum ticket de suporte ou bug aberto.")}</div></section>`;
}

// ---------- Consultoria ----------
function vCons(){
  const C=S.C,ab=C.T.filter(t=>t.familia==="Consultoria"&&t.backlog_geral),enc=C.T.filter(t=>t.familia==="Consultoria"&&(t.concluido_no_ano||t.resolvido_no_ano));
  const uti=sum(ab,t=>num(t.horas_consultoria)),con=sum(ab,t=>num(t.horas_contratadas));
  const mensal=C.fm.map(m=>({lab:mlab(m),h:sum(C.A.filter(a=>a.mes===m&&C.byId.get(String(a.ticket_id))&&C.byId.get(String(a.ticket_id)).familia==="Consultoria"),a=>a.horas||0)}));
  return `<section class="view">
   <p class="note">Consultoria é demanda duradora: o cliente contrata horas e aciona sob demanda. O saldo contratado depende do campo <b>Horas contratadas (consultoria)</b>, ainda não criado no Freshdesk; até lá o painel mostra o consumo. Ao criar o campo, registrar o nome técnico em <span class="mono">CAMPO_HORAS_CONTRATADAS</span> no script de extração.</p>
   <div class="kpis">${kpi("Contratos abertos",nf(ab.length),"tickets de consultoria")}
    ${kpi("Horas utilizadas (campo)",nf(uti,1),"campo do ticket")}
    ${kpi("Horas apontadas",nf(sum(ab,t=>t.horas),1),"Painel de Serviços, tickets abertos")}
    ${kpi("Horas contratadas",con?nf(con,1):"–",con?"saldo "+nf(con-uti,1)+" h":"campo ainda não existe")}</div>
   <div class="grid g2"><div class="card"><h2>Horas por mês</h2>${colChart(mensal,[{k:"h",c:"var(--serie-3)",l:"Horas"}],{aria:"Horas de consultoria por mês"})}</div>
    <div class="card"><h2>Resumo</h2><p class="hint">Encerrados no ano: ${nf(enc.length)}</p></div></div>
   <div class="card"><h2>Consultorias abertas</h2>${tabela([["ID"],["Assunto"],["Produto"],["Status"],["Responsável"],["Horas utilizadas","n"],["Horas apontadas","n"],["Última mudança","n"]],ab.sort((a,b)=>b.horas-a.horas).map(t=>`<tr><td>${link(t)}</td><td class="wrap">${esc(t.assunto)}</td><td>${esc(t.produto)}</td><td>${esc(t.st)}</td><td>${esc(t.dono)}</td><td class="n">${t.horas_consultoria!==""?nf(num(t.horas_consultoria),1):"–"}</td><td class="n">${nf(t.horas,1)}</td><td class="n">${nf(t.parado)} d</td></tr>`),"Nenhuma consultoria aberta.")}</div></section>`;
}

// ---------- Fila de orçamento / macro escopo / especificação (outro time) ----------
function vFila(){
  const C=S.C,F=S.fila;const all=C.T.filter(t=>t.fila&&(!F.prod||t.produto===F.prod));
  const ab=all.filter(t=>t.backlog_geral),enc=all.filter(t=>t.concluido_no_ano||t.resolvido_no_ano);
  const sts=[...new Set(ab.map(t=>t.st))].sort();
  const mat=FILAS.map(q=>`<tr><td>${esc(q)}</td>${sts.map(s=>`<td class="n">${nf(ab.filter(t=>t.fila===q&&t.st===s).length)}</td>`).join("")}<td class="n"><b>${nf(ab.filter(t=>t.fila===q).length)}</b></td></tr>`);
  const prod=prodList().map(p=>({l:p,parts:FILAS.map((q,i)=>({v:all.filter(t=>t.backlog_geral&&t.produto===p&&t.fila===q).length,c:["var(--serie-2)","var(--serie-1)","var(--serie-6)"][i],l:q}))}));
  const fluxo=C.fm.map(m=>({lab:mlab(m),ent:all.filter(t=>t.novo_no_ano&&t.mesEnt===m).length,sai:all.filter(t=>t.mesSai===m).length}));
  const vida=FILAS.map(q=>{const a=ab.filter(t=>t.fila===q).map(t=>t.idade).filter(x=>x!=null),e=enc.filter(t=>t.fila===q).map(t=>days(t.criado_em,dt(t.saida))).filter(x=>x!=null);return `<tr><td>${esc(q)}</td><td class="n">${nf(a.length)}</td><td class="n">${a.length?nf(median(a))+" d":"–"}</td><td class="n">${a.length?nf(quant(a,0.9))+" d":"–"}</td><td class="n">${nf(e.length)}</td><td class="n">${e.length?nf(median(e))+" d":"–"}</td></tr>`;});
  return `<section class="view">
   <p class="note">Orçamento, Macro escopo e Especificação são tratados por outro time: aqui só se acompanha <b>volume por tipo, tempo de vida e andamento</b>. Tipo da fila = status do fluxo, depois tag, depois Type. Projetos ficam só na aba Projetos. O histórico diário (snapshots) vai acumulando na extração; esta visão usa as datas dos tickets.</p>
   <div class="card"><div class="filters">${sel("fl_prod","Produto",F.prod,prodList(),"Geral (todos os produtos)")}</div></div>
   <div class="kpis">${FILAS.map(q=>kpi(q,nf(ab.filter(t=>t.fila===q).length),"na fila agora")).join("")}${kpi("Total na fila",nf(ab.length),nf(enc.length)+" encerrados no ano")}</div>
   <div class="grid g2">
    <div class="card"><h2>Entradas e saídas por mês</h2>${colChart(fluxo,[{k:"ent",c:"var(--serie-2)",l:"Entradas"},{k:"sai",c:CS,l:"Saídas"}],{aria:"Fluxo da fila"})}${legend([["var(--serie-2)","Entradas"],[CS,"Saídas"]])}</div>
    <div class="card"><h2>Fila por produto</h2>${prod.length?hbars(prod.filter(r=>sum(r.parts,p=>p.v)>0),{}):`<p class="hint">–</p>`}${legend([["var(--serie-2)","Orçamento"],["var(--serie-1)","Macro escopo"],["var(--serie-6)","Especificação"]])}</div>
   </div>
   <div class="card"><h2>Tempo de vida</h2><p class="hint">Idade dos abertos e tempo até encerrar dos que saíram no ano</p>${tabela([["Tipo"],["Abertos","n"],["Idade mediana","n"],["Idade p90","n"],["Encerrados","n"],["Tempo mediano","n"]],vida)}</div>
   <div class="card"><h2>Andamento: tipo × status</h2>${tabela([["Tipo"],...sts.map(s=>[esc(s),"n"]),["Total","n"]],mat,"Fila vazia.")}</div></section>`;
}

// ---------- Time ----------
function vTime(){
  const C=S.C,P=S.params,nomes=[...P.time,...P.ex];
  const mC=curMonth;const rows=nomes.map(n=>{const k=norm(n);const mine=C.BL.filter(t=>norm(t.agente)===k);const h=sum(C.A.filter(a=>norm(a.analyst_name)===k&&a.mes===mC),a=>a.horas||0);
    const cap=(C.capM[mC]||{})[n]||0;const isEx=P.ex.includes(n);
    return `<tr><td>${esc(short(n))}${isEx?" "+tag("gray","ex-integrante"):""}</td><td class="n">${nf(mine.filter(t=>t.backlog_ativo).length)}</td><td class="n">${nf(mine.filter(t=>t.familia==="Projeto").length)}</td><td class="n">${nf(mine.filter(t=>t.suspenso).length)}</td><td class="n">${nf(mine.filter(t=>t.backlog_ativo&&t.parado!=null&&t.parado>P.parado_dias).length)}</td><td class="n">${nf(mine.filter(t=>t.prazo==="atrasado").length)}</td><td class="n">${nf(h,1)}</td><td class="n">${isEx?"–":nf(cap,0)}</td><td class="n">${isEx||!cap?"–":pct(h/cap)}</td></tr>`;});
  const fora=Object.entries(countBy(C.BL.filter(t=>t.donoTipo==="fora"),t=>t.dono)).sort((a,b)=>b[1]-a[1]);
  return `<section class="view"><div class="card"><h2>Carteira por analista</h2><p class="hint">Backlog atual; horas e ocupação do mês corrente (${mlab(mC)}). Ex-integrantes ficam visíveis para reatribuição.</p>
   ${tabela([["Analista"],["Ativos","n"],["Projetos","n"],["Suspensos","n"],["Parados","n"],["Atrasados","n"],["Horas no mês","n"],["Capacidade (h)","n"],["Ocupação","n"]],rows)}</div>
   <div class="card"><h2>Sem responsável ou fora do time</h2><p class="hint">${nf(C.BL.filter(t=>t.donoTipo==="sem").length)} abertos sem responsável. Agentes de outros grupos atendendo o grupo INTEGRACOES:</p>${fora.length?hbars(fora.map(([l,v])=>({l,v})),{}):`<p class="hint">Nenhum.</p>`}</div></section>`;
}

// ---------- Horas ----------
function vHoras(){
  const C=S.C;if(!S.H)return `<section class="view"><p class="note">Base de horas não carregada. Veja Configuração.</p></section>`;
  const A=C.A,tot=sum(A,a=>a.horas||0),fat=sum(A.filter(a=>a.tipo==="Faturável"),a=>a.horas||0);
  const hm=C.months.map(m=>{const o={lab:mlab(m)};for(const tp of TIPOS)o[tp]=sum(A.filter(a=>a.mes===m&&a.tipo===tp),a=>a.horas||0);o.cap=sum(Object.values(C.capM[m]||{}));return o;});
  const ativ=Object.entries(A.reduce((o,a)=>{o[a.atividade||"Sem atividade"]=(o[a.atividade||"Sem atividade"]||0)+(a.horas||0);return o;},{})).sort((a,b)=>b[1]-a[1]).slice(0,12).map(([l,v])=>({l,v}));
  const nomes=[...new Set(A.map(a=>a.analyst_name))];
  const an=nomes.map(n=>({l:short(n)+(S.params.ex.some(e=>norm(e)===norm(n))?" (ex)":""),parts:TIPOS.map((tp,i)=>({v:sum(A.filter(a=>a.analyst_name===n&&a.tipo===tp),a=>a.horas||0),c:TIPO_COL[i],l:tp}))})).sort((a,b)=>sum(b.parts,p=>p.v)-sum(a.parts,p=>p.v));
  const fam=FAMS.map(f=>({l:f.lab,v:sum(C.T.filter(t=>t.familia===f.k),t=>t.horas),c:f.c})).filter(r=>r.v>0);
  const semT=sum(A.filter(a=>!a.ticket_id),a=>a.horas||0);
  return `<section class="view"><div class="kpis">
    ${kpi("Horas apontadas no ano",nf(tot),"área Integração")}
    ${kpi("Faturáveis",pct(tot?fat/tot:null),nf(fat)+" h")}
    ${kpi("Sem ticket",pct(tot?semT/tot:null),nf(semT)+" h (reuniões e internas)")}
    ${kpi("Apontamentos",nf(A.length),nf(nomes.length)+" analistas")}</div>
   <div class="grid g2"><div class="card"><h2>Por mês e tipo</h2>${colChart(hm,TIPOS.map((tp,i)=>({k:tp,c:TIPO_COL[i],l:tp})),{stack:true,line:{k:"cap",c:"var(--foreground)",l:"Capacidade"},aria:"Horas por mês"})}${legend(TIPOS.map((tp,i)=>[TIPO_COL[i],tp]))}<p class="hint">Capacidade = time atual. Meses antigos incluem horas de ex-integrante, por isso podem passar da linha.</p></div>
    <div class="card"><h2>Por analista</h2>${hbars(an,{})}${legend(TIPOS.map((tp,i)=>[TIPO_COL[i],tp]))}</div></div>
   <div class="grid g2"><div class="card"><h2>Atividades (top 12)</h2>${hbars(ativ,{c:"var(--primary)"})}</div>
    <div class="card"><h2>Horas por família de ticket</h2>${hbars(fam.map(r=>({l:r.l,parts:[{v:r.v,c:r.c}]})),{})}<p class="hint">Só horas ligadas a um ticket da base.</p></div></div></section>`;
}

// ---------- S&OP ----------
function vSop(){
  const C=S.C,P=S.params;
  if(!S.H)return `<section class="view"><p class="note">S&amp;OP precisa da base de horas (capacidade). Veja Configuração.</p></section>`;
  const X=[["total",burndown(false),"Backlog geral"],["ativo",burndown(true),"Backlog ativo"]];
  const card=([k,B,lab])=>`<div class="card"><h2>${lab}</h2><p class="hint">${nf(B.n)} tickets de projeto, consultoria, suporte e bug · ${nf(B.h0)} h restantes${B.semRef?` · ${nf(B.semRef)} sem estimativa nem referência`:""}</p>
    <div class="kpis"><div class="kpi"><span class="lab">Zera em</span><span class="val">${B.fim?B.fim+" mês(es)":"+12 meses"}</span><span class="det">teto de ${Math.round(P.teto_backlog*100)}% da capacidade</span></div></div>
    ${colChart(B.meses,[{k:"pago",c:"var(--serie-saida)",l:"Pago ao backlog"},{k:"fc",c:"var(--serie-1)",l:"Entradas previstas (contexto)"}],{stack:true,line:{k:"cap",c:"var(--foreground)",l:"Capacidade"},aria:"S&OP "+lab,hideZero:true})}${legend([["var(--serie-saida)","Pago ao backlog"],["var(--serie-1)","Entradas previstas (contexto)"],["var(--foreground)","Capacidade"]])}</div>`;
  const dem=X[0][1].dem;
  return `<section class="view">
   <p class="note">Simulação mês a mês: cada mês paga ao backlog no máximo ${Math.round(P.teto_backlog*100)}% da capacidade do <b>time atual</b> (${[...C.team].length} pessoas × ${Math.round(P.fator_produtivo*100)}% produtivo); o restante rola para o mês seguinte. As entradas previstas ficam fora da conta. Só entra demanda do time: projetos, consultoria, suporte e bugs. Orçamento, macro escopo, especificação e dúvidas ficam de fora.</p>
   <div class="grid g2">${X.map(card).join("")}</div>
   <div class="card"><h2>Premissas de esforço</h2><p class="hint">Horas restantes por ticket = estimativa do Freshdesk menos horas apontadas; sem estimativa, usa a referência da família menos as horas já apontadas. Ajustável em Configuração.</p>
    ${tabela([["Família"],["Referência (h)","n"],["Fonte"],["Base (tickets)","n"],["Entradas/mês (3 meses)","n"],["Horas/mês previstas","n"]],CARGA.map(f=>`<tr><td>${esc(FAM_LAB[f])}</td><td class="n">${C.ref[f].h!=null?nf(C.ref[f].h,1):"–"}</td><td>${esc(C.ref[f].fonte)}</td><td class="n">${nf(C.ref[f].n)}</td><td class="n">${nf(dem[f].n,1)}</td><td class="n">${nf(dem[f].h)}</td></tr>`))}</div></section>`;
}

// ---------- Configuração ----------
function vCfg(){
  const P=S.params,ro=!S.canEdit,dis=ro?"disabled":"";const b=S.bases||{};
  const pessoas=[...new Set([...P.time,...P.ex,...((S.H&&S.H["Analistas"])||[]).map(a=>a.name).filter(Boolean)])].sort();
  const st=(k,lab)=>{const x=b[k];return x?`<span class="chip ok">${lab}: ${esc((x.gerado_em||"").replace("T"," ").slice(0,16))} · ${nf(x.linhas)} linhas</span>`:`<span class="chip warn">${lab}: não carregada</span>`;};
  return `<section class="view">${ro?`<p class="note">Somente leitura. Parâmetros e cargas são mantidos por quem pode editar o painel.</p>`:""}
   <div class="grid g2"><div class="card"><h2>Parâmetros</h2><div class="filters">
     <label class="f" for="p_vd">“Vencendo” a partir de (dias)<input type="number" id="p_vd" min="1" max="90" value="${P.vencendo_dias}" ${dis}></label>
     <label class="f" for="p_pd">Parado após (dias)<input type="number" id="p_pd" min="5" max="180" value="${P.parado_dias}" ${dis}></label>
     <label class="f" for="p_fp">Tempo produtivo (%)<input type="number" id="p_fp" step="5" min="10" max="100" value="${Math.round(P.fator_produtivo*100)}" ${dis}></label>
     <label class="f" for="p_tb">Teto ao backlog (%)<input type="number" id="p_tb" step="5" min="30" max="100" value="${Math.round(P.teto_backlog*100)}" ${dis}></label>
     <label class="f" for="p_hp">Horas/mês sem capacidade cadastrada<input type="number" id="p_hp" min="40" max="220" value="${P.horas_mes_padrao}" ${dis}></label></div>
    <h2 style="margin-top:8px">Esforço de referência por família (h)</h2><p class="hint">Vazio = mediana dos encerrados no ano. Use quando a base for pequena.</p>
    <div class="filters">${CARGA.map(f=>`<label class="f" for="rf_${f}">${FAM_LAB[f]}<input type="number" id="rf_${f}" data-f="${f}" min="0" step="0.5" value="${(P.ref_horas||{})[f]||""}" placeholder="auto" ${dis}></label>`).join("")}</div>
    <h2 style="margin-top:8px">Time</h2><p class="hint">Time atual: entra na capacidade e no S&amp;OP. Ex-integrantes: ficam nos tickets e nas horas históricas, sem capacidade.</p>
    <div style="display:flex;flex-direction:column;gap:6px">${pessoas.map((n,i)=>{const v=P.time.includes(n)?"time":P.ex.includes(n)?"ex":"fora";return `<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap"><span style="min-width:200px">${esc(n)}</span><select id="tm_${i}" data-n="${esc(n)}" ${dis}><option value="time" ${v==="time"?"selected":""}>Time atual</option><option value="ex" ${v==="ex"?"selected":""}>Ex-integrante</option><option value="fora" ${v==="fora"?"selected":""}>Fora do painel</option></select></div>`;}).join("")}</div>
    ${ro?"":`<div><button class="btn pri" id="p_save">Salvar parâmetros</button></div>`}</div>
   <div class="card"><h2>Bases de dados</h2><div class="chips">${st("tickets","Tickets")} ${st("horas","Horas")}</div>
    <p class="hint">Extração de tickets seg-sex às 21h no computador do Diego. Arquivos: <span class="mono">base_integracoes.json</span> e <span class="mono">horas_integracoes_painel.json</span> (só a área Integração).</p>
    ${S.assets?`<label class="f" for="up_file">Carregar arquivo de base (JSON)<input type="file" id="up_file" accept=".json,application/json"></label>`:`<p class="note">A carga de arquivos está disponível só para quem pode editar o painel.</p>`}
    <h2 style="margin-top:8px">Regras</h2><ul class="rules">
     <li><b>Backlog geral</b>: tudo que não está encerrado, resolvido ou cancelado, incluindo pendente com cliente e suspenso. <b>Backlog ativo</b>: geral menos suspenso (qualquer variação do status).</li>
     <li><b>Cancelado</b>: status Cancelado ou tag “cancelado”, em qualquer status; sai dos backlogs e dos encerrados.</li>
     <li><b>Famílias</b> pelo Type: Projeto, Suporte (Integrações - Suporte), Bug (Erro/Falha), Consultoria, Dúvidas, Orçamento, Outros.</li>
     <li><b>Fila de orçamento</b> (outro time): Orçamento, Macro escopo, Especificação, por status, tag e Type; projetos ficam só em Projetos.</li>
     <li><b>Prazo</b>: Data limite para entrega × Data Fim/entrega real.</li></ul></div></div></section>`;
}
