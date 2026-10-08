function colChart(data,series,o){o=o||{};const W=o.w||640,Hh=o.h||220,pl=36,pr=8,pt=18,pb=26;const n=data.length;
  const lines=[...(o.line?[o.line]:[]),...(o.lines||[])];
  const mx=Math.max(1,...data.map(d=>o.stack?series.reduce((s,se)=>s+(d[se.k]||0),0):Math.max(...series.map(se=>d[se.k]||0))),...lines.map(ln=>Math.max(...data.map(d=>d[ln.k]||0))));
  const nice=niceMax(mx);const y=v=>pt+(Hh-pt-pb)*(1-v/nice);const bw=(W-pl-pr)/n;let g="";
  for(let i=0;i<=4;i++){const v=nice*i/4;g+=`<line x1="${pl}" x2="${W-pr}" y1="${y(v)}" y2="${y(v)}" stroke="var(--border)"/><text x="${pl-6}" y="${y(v)+4}" text-anchor="end">${nf(v)}</text>`;}
  data.forEach((d,i)=>{const x0=pl+i*bw;
    if(o.stack){let acc=0;series.forEach(se=>{const v=d[se.k]||0;if(v>0){g+=`<rect x="${x0+bw*.18}" y="${y(acc+v)}" width="${bw*.64}" height="${y(acc)-y(acc+v)}" fill="${se.c}"><title>${esc(se.l)}: ${nf(v,o.dec)}</title></rect>`;}acc+=v;});
      if(acc>0||!o.hideZero)g+=`<text class="v" x="${x0+bw/2}" y="${y(acc)-4}" text-anchor="middle">${nf(acc,o.dec)}</text>`;}
    else{const sw=bw*.72/series.length;series.forEach((se,j)=>{const v=d[se.k]||0;g+=`<rect x="${x0+bw*.14+j*sw}" y="${y(v)}" width="${sw-2}" height="${y(0)-y(v)}" rx="2" fill="${se.c}"><title>${esc(se.l)}: ${nf(v,o.dec)}</title></rect>`;if(o.labels!==false)g+=`<text class="v" x="${x0+bw*.14+j*sw+(sw-2)/2}" y="${y(v)-4}" text-anchor="middle">${nf(v,o.dec)}</text>`;});}
    g+=`<text x="${x0+bw/2}" y="${Hh-8}" text-anchor="middle">${esc(d.lab)}</text>`;});
  lines.forEach(ln=>{const pts=data.map((d,i)=>`${pl+i*bw+bw/2},${y(d[ln.k]||0)}`).join(" ");g+=`<polyline points="${pts}" fill="none" stroke="${ln.c}" stroke-width="2" stroke-dasharray="5 4"/>`;data.forEach((d,i)=>{g+=`<circle cx="${pl+i*bw+bw/2}" cy="${y(d[ln.k]||0)}" r="3" fill="${ln.c}"><title>${esc(ln.l)}: ${nf(d[ln.k],o.dec)}</title></circle>`;});});
  return `<svg viewBox="0 0 ${W} ${Hh}" width="100%" role="img" aria-label="${esc(o.aria||"gráfico")}">${g}</svg>`;}
function niceMax(v){const p=Math.pow(10,Math.floor(Math.log10(v)));const f=v/p;return (f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*p;}
function legend(items){return `<div class="legend">${items.map(([c,l])=>`<span><i style="background:${c}"></i>${esc(l)}</span>`).join("")}</div>`;}
function hbars(rows,o){o=o||{};const mx=Math.max(1,...rows.map(r=>r.parts?r.parts.reduce((s,p)=>s+p.v,0):r.v));
  return rows.map(r=>{const tot=r.parts?r.parts.reduce((s,p)=>s+p.v,0):r.v;const segs=(r.parts||[{v:r.v,c:o.c||"var(--primary)"}]).map(p=>`<span style="width:${p.v/mx*100}%;background:${p.c}" title="${esc(p.l||"")}: ${nf(p.v,o.dec)}"></span>`).join("");
    return `<div class="bar"><span class="t" title="${esc(r.l)}">${esc(r.l)}</span><span class="track">${segs}</span><span class="num">${nf(tot,o.dec)}${o.suf||""}</span></div>`;}).join("");}
const kpi=(l,v,d,cls)=>`<div class="kpi ${cls||""}"><span class="lab">${l}</span><span class="val">${v}</span><span class="det">${d||""}</span></div>`;
const CS="var(--serie-saida)";
