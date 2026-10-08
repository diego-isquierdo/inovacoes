// Valida o motor do painel contra as bases reais (LOG_SOP §8): sem exceções, NaN ou undefined nas visões.
const fs=require("fs"),path=require("path");
const html=fs.readFileSync(path.join(__dirname,"painel_teste.html"),"utf8");
const script=html.slice(html.indexOf("<script>")+8,html.lastIndexOf("</script>"));
const els={};const mk=()=>({innerHTML:"",textContent:"",hidden:false,style:{},set onclick(v){},set onchange(v){},set oninput(v){}});
global.document={querySelector:s=>els[s]||(els[s]=mk()),getElementById:()=>null,querySelectorAll:()=>[]};
global.window={scrollTo(){},claude:undefined};global.localStorage={getItem(){return null},setItem(){}};global.location={hash:""};
global.fetch=async()=>({ok:false});
(0,eval)(script);
const T=global.window.__TEST__;
const dir=process.argv[2];
const rows=tb=>tb.linhas.map(r=>Object.fromEntries(tb.colunas.map((c,i)=>[c,r[i]])));
const tj=JSON.parse(fs.readFileSync(path.join(dir,"base_integracoes.json"),"utf8"));
const hj=JSON.parse(fs.readFileSync(path.join(dir,"horas_integracoes_painel.json"),"utf8"));
const H={};for(const k in hj.tabelas)H[k]=rows(hj.tabelas[k]);
T.loadFrom(rows(tj),H);
let bad=0;
for(const [k,fn] of Object.entries(T.VIEWS)){
  let out;try{out=fn();}catch(e){console.log("ERRO",k,e.stack.split("\n").slice(0,3).join(" | "));bad++;continue;}
  const txt=out.replace(/<[^>]+>/g," ");
  const m=txt.match(/NaN|undefined|\[object|Infinity|null/g);
  console.log(k.padEnd(8),String(out.length).padStart(7),"chars",m?"PROBLEMA: "+[...new Set(m)].join(","):"ok");if(m)bad++;
}
for(const e of ["geral","ativo","susp"]){T.S.bl.escopo=e;console.log("backlog",e,T.blFiltered().length);}
const C=T.S.C;
console.log("famílias BL",JSON.stringify(C.BL.reduce((o,t)=>(o[t.familia]=(o[t.familia]||0)+1,o),{})));
console.log("prazo projetos abertos",JSON.stringify(C.BL.filter(t=>t.familia==="Projeto").reduce((o,t)=>(o[t.prazo]=(o[t.prazo]||0)+1,o),{})));
console.log("ref",JSON.stringify(Object.fromEntries(Object.entries(C.ref).map(([k,v])=>[k,[v.h&&+v.h.toFixed(1),v.n]]))));
console.log("sop total",T.burndown(false).h0.toFixed(0),"h, fim",T.burndown(false).fim,"| ativo",T.burndown(true).h0.toFixed(0),T.burndown(true).fim);
console.log("achados",T.achados().map(a=>a.n+" "+a.t).join(" | "));
process.exit(bad?1:0);
