"""Gera a base de horas SOMENTE da area "Integracao" a partir da base global do Painel de Servicos.

Entrada : MCP Painel de Servicos/output/horas_apontadas_<ANO>_painel.json (todas as areas)
Saida   : MCP - Fresk/freshdesk_mcp/scripts/output/Integracoes/horas_integracoes_painel.json
Motivo  : o painel de Integracoes nao precisa (nem deve carregar) horas de outros times.
Uso     : python preparar_base_horas_integracoes.py [--ano 2026]
"""
import argparse
import json
from datetime import date
from pathlib import Path

INOV = Path(__file__).resolve().parents[3]  # .../Inovacoes
AREA_NOME = "Integração"
ap = argparse.ArgumentParser()
ap.add_argument("--ano", type=int, default=date.today().year)
args = ap.parse_args()

src = INOV / "MCP Painel de Serviços" / "output" / f"horas_apontadas_{args.ano}_painel.json"
dst_dir = INOV / "MCP - Fresk" / "freshdesk_mcp" / "scripts" / "output" / "Integrações"
j = json.loads(src.read_text(encoding="utf-8"))
T = j["tabelas"]


def rows(name):
    t = T[name]
    return t["colunas"], [dict(zip(t["colunas"], l)) for l in t["linhas"]]


_, areas = rows("Áreas")
area_ids = {a["id"] for a in areas if a.get("name") == AREA_NOME}
assert area_ids, f"area {AREA_NOME!r} nao encontrada"
_, analistas = rows("Analistas")
analyst_ids = {a["id"] for a in analistas if a["area_id"] in area_ids}

keep = {
    "Áreas": lambda r: r["id"] in area_ids,
    "Apontamentos": lambda r: r["area_id"] in area_ids,
    "Analistas": lambda r: r["area_id"] in area_ids,
    "Membros": lambda r: r["area_id"] in area_ids,
    "Capacidade": lambda r: r["area_id"] in area_ids,
    "Meta de produtividade": lambda r: True,
    "Fechamento - Totais": lambda r: r["area_id"] in area_ids,
    "Fechamento - Analistas": lambda r: r["area_id"] in area_ids,
    "Fechamento - Tipos": lambda r: r["area_id"] in area_ids,
    "Alocações": lambda r: r["area_name"] == AREA_NOME,
    "Férias": lambda r: r["area_name"] == AREA_NOME,
    "Disponibilidade": lambda r: r["area_name"] == AREA_NOME,
    "Calendário": lambda r: r["analyst_id"] in analyst_ids,
}
out = {}
for name, fn in keep.items():
    cols, rs = rows(name)
    out[name] = {"colunas": cols, "linhas": [[r[c] for c in cols] for r in rs if fn(r)]}
meta = dict(j.get("meta", {}))
meta.update({"base": "Horas Integrações", "area": AREA_NOME, "origem": src.name,
             "apontamentos": len(out["Apontamentos"]["linhas"])})
dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir / "horas_integracoes_painel.json"
dst.write_text(json.dumps({"meta": meta, "tabelas": out}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("ok", dst, {k: len(v["linhas"]) for k, v in out.items()}, round(dst.stat().st_size / 1e6, 2), "MB")
