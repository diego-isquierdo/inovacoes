"""Extracao UNICA e INCREMENTAL da base de tickets de Integracoes.

Derivado de `extracao_servicos_adv.py` (mesma fonte, mesmo estado incremental,
mesma verificacao cruzada). Diferencas para o time ADV:
  - grupo Freshdesk `INTEGRACOES`, SEM filtro de produto e SEM filtro de agente
    (tickets de ex-integrantes, como o Ewerton, entram normalmente);
  - Cancelado e status terminal (fora dos dois backlogs);
  - backlog geral (inclui pendentes com o cliente) x backlog ativo (tudo que
    nao e Suspenso — qualquer status que contenha "suspens");
  - colunas extras de prazo, estimativa, orcamento e causa raiz;
  - `familia` (Projeto, Suporte, Consultoria, Duvidas, Orcamento, Outros) e
    `tipo_fila` (Orcamento, Macro escopo, Especificacao — fila tratada por outro time);
  - snapshot diario (contagens por familia x status x produto) para o
    "andamento da fila".
Planejamento e decisoes:
    Painel de Gestao/Integracoes/PLANEJAMENTO.md
    Painel de Gestao/Integracoes/extracao/PLANEJAMENTO_EXTRACAO.md

Saidas (pasta nao versionada — dado de cliente)
-----------------------------------------------
    scripts/output/Integracoes/Base de Integracoes.xlsx
    scripts/output/Integracoes/base_integracoes.json     (p/ o painel)
    scripts/output/Integracoes/snapshots/AAAA-MM-DD.json
Estado incremental (tambem nao versionado):
    scripts/cache/integracoes/estado.json

Uso:
    .venv/Scripts/python.exe scripts/extracao_integracoes.py            # incremental (ou completa se nao houver estado)
    .venv/Scripts/python.exe scripts/extracao_integracoes.py --full     # relista o ano (sem apagar o estado) + verificacao
    .venv/Scripts/python.exe scripts/extracao_integracoes.py --verify   # incremental + verificacao cruzada
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from lib.common import OUTPUT_DIR, SCRIPTS_DIR, get_client, run, run_async
from client import FreshdeskAPIError  # noqa: E402
from backlog_servicos import ensure_agents_resolved, load_agent_cache  # noqa: E402  (cache de agentes compartilhado)
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Font  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

# ---------------------------------------------------------------------------
# Configuracao de negocio (nomes, nunca IDs — resolvidos em tempo de execucao)
# ---------------------------------------------------------------------------
BASE_NAME = "Base de Integrações"
GROUP_NAME = "INTEGRACOES"
OUTPUT_SUBDIR = "Integrações"

STATE_DIR = SCRIPTS_DIR / "cache" / "integracoes"  # dado de cliente — nao versionado (scripts/cache/ no .gitignore)
STATE_PATH = STATE_DIR / "estado.json"
STATE_VERSION = 2

# Time (Painel de Servicos, area "Integracao"). Ativos = carteira e capacidade atuais;
# ex-integrantes mantem o nome como analista nos tickets e horas historicas.
TIME_ATIVO = {
    158010714337: "Amanda Maria Pinheiro",
    158010714346: "Elder Galvao Quirino Ribeiro",
    158010714349: "Lucas Silva Monteiro",
    158013890212: "Thais Majory de Paulo Santos",
}
TIME_EX = {
    158010714339: "Ewerton Vital de Carvalho",
}

OVERLAP = timedelta(minutes=15)  # margem de seguranca na janela incremental
LIST_PAGE_CAP = 300              # a API recusa page > 300 em /tickets
RATE_FLOOR = 8                   # abaixo disso de requisicoes restantes, pausa ate a janela renovar
TERMINAL_KEYWORDS = ("closed", "encerrado", "resolved", "resolvido", "cancelado")
CANCEL_TAG = "cancelado"      # decisao 08/10: ticket com esta tag conta como Cancelado, em qualquer status
SUSPENDED_KEYWORD = "suspens"  # casa Suspenso e qualquer variacao do rotulo

# Colunas da base (ordem do .xlsx). As 4 ultimas sao os recortes.
COLUMNS = [
    ("id", "ID do ticket"),
    ("assunto", "Assunto"),
    ("status", "Status"),
    ("agente", "Agente"),
    ("ativo_na_equipe", "Agente no time atual"),
    ("criado_em", "Hora da criação"),
    ("atualizado_em", "Hora da última atualização"),
    ("status_desde", "Status desde"),
    ("primeira_resposta_h", "Tempo de resposta inicial (h)"),
    ("data_resolucao", "Data da Resolução"),
    ("data_fechamento", "Data do Fechamento"),
    ("reaberto_em", "Reaberto em"),
    ("tags", "Tags"),
    ("produto", "Produto"),
    ("subtipo", "Subtipo"),
    ("prioridade", "Prioridade"),
    ("tipo", "Tipo"),
    ("familia", "Família"),
    ("tipo_fila", "Fila de orçamento (tipo)"),
    ("tipo_demanda", "Tipo de demanda"),
    ("data_inicio", "Data Início"),
    ("data_fim", "Data Fim"),
    ("data_limite_entrega", "Data limite para entrega"),
    ("data_entrega", "Data da entrega"),
    ("previsao_solucao", "Previsão de solução"),
    ("previsao_vencimento", "Vencimento (due_by)"),
    ("estim_total_h", "Estim. TOTAL (h)"),
    ("estim_po_dev_h", "Estimativa PO Dev (h)"),
    ("estim_po_hml_h", "Estimativa PO HML (h)"),
    ("estim_po_orc_h", "Estimativa PO Orç (h)"),
    ("estimativa_h", "Estimativa (h)"),
    ("horas_consultoria", "Horas utilizadas (consultoria)"),
    ("horas_contratadas", "Horas contratadas (consultoria)"),
    ("data_envio_orcamento", "Data envio orçamento"),
    ("data_aprovacao_proposta", "Data aprovação proposta"),
    ("valor_servico", "Valor do serviço (R$)"),
    ("valor_proposta_previo", "Valor prévio proposta (R$)"),
    ("valor_proposta_final", "Valor final proposta (R$)"),
    ("modulo", "Módulo (3 níveis)"),
    ("tipo_resolucao", "Tipo de resolução"),
    ("causa_raiz", "Causa raiz"),
    ("workflow_se", "Workflow (SE)"),
    ("solicitante", "Nome completo"),
    ("id_contato", "ID de contato"),
    ("id_empresa", "ID da empresa"),
    ("backlog_geral", "Backlog geral"),
    ("backlog_ativo", "Backlog ativo"),
    ("suspenso", "Suspenso"),
    ("novo_no_ano", "Novo no ano"),
    ("concluido_no_ano", "Concluído no ano"),
    ("resolvido_no_ano", "Resolvido no ano"),
    ("cancelado_no_ano", "Cancelado no ano"),
    ("cancelado_origem", "Origem do cancelamento"),
]
FLAG_KEYS = ["backlog_geral", "backlog_ativo", "suspenso", "novo_no_ano",
             "concluido_no_ano", "resolvido_no_ano", "cancelado_no_ano"]

# Classificacao por Type (comparacao sem acento/caixa; ajuste aqui, nunca por ID)
FAMILIA_POR_TYPE = [  # (trecho do Type normalizado, familia) — primeiro que casar
    ("integracoes - projeto", "Projeto"),
    ("integracoes - suporte", "Suporte"),
    ("integracoes - consultoria", "Consultoria"),
    ("integracoes - duvidas", "Dúvidas"),
    ("integracoes - orcamento", "Orçamento"),
    ("erro", "Bug"),    # Erro de Integracao, Erro de Sistema... (decisao 08/10: tratar como bug)
    ("falha", "Bug"),   # Falha na Captura de Dados, Falha no Login...
    ("duvidas", "Dúvidas"),    # tipos gerais ("Dúvidas - Solicitação de orientação")
    ("orcamento", "Orçamento"),  # "Integrações - Solicitação de orçamento" e similares
]
# Campo (a criar no Freshdesk) com o saldo de horas contratado de consultoria. Quando existir,
# preencher com o nome tecnico (ex.: "cf_horas_contratadas_consultoria") — a coluna ja esta reservada.
CAMPO_HORAS_CONTRATADAS = None
# Fila tratada por outro time: por Type, por status do fluxo e por tag (maior prioridade primeiro)
FILA_STATUS = [  # (trecho do rotulo do status normalizado, tipo da fila)
    ("especifica", "Especificação"),
    ("escopo", "Macro escopo"),
    ("orc", "Orçamento"),
    ("proposta", "Orçamento"),
    ("aguardando po", "Orçamento"),
    ("financeiro", "Orçamento"),
]
FILA_TAGS = [("macro", "Macro escopo"), ("especifica", "Especificação"), ("orcamento", "Orçamento")]
PRIORIDADE = {1: "Baixa", 2: "Média", 3: "Alta", 4: "Urgente"}


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def in_year(value: str | None, year: int) -> bool:
    return bool(value) and value[:4] == str(year)


def norm(text) -> str:
    """minusculas e sem acento (para comparar rotulos)."""
    t = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in t if not unicodedata.combining(c) and c != "\u200b").lower().strip()


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip()


async def api_get(client, path: str, params: dict, logger):
    """GET com respeito ao rate limit (compartilhado com outras integracoes) e retry em 429/timeouts."""
    for attempt in range(6):
        try:
            resp = await client.get(path, params=params)
        except FreshdeskAPIError as exc:
            msg = str(exc).lower()
            if "429" in msg or "rate limit" in msg or "timeout" in msg or "falha de rede" in msg:
                wait = 60 if ("429" in msg or "rate" in msg) else 10
                logger.warning("%s em %s (tentativa %d/6) — aguardando %ss", exc.__class__.__name__, path, attempt + 1, wait)
                await asyncio.sleep(wait)
                continue
            raise
        if resp.rate_limit_remaining is not None and resp.rate_limit_remaining <= RATE_FLOOR:
            logger.info("Rate limit quase no fim (%s/%s) — pausando 60s", resp.rate_limit_remaining, resp.rate_limit_total)
            await asyncio.sleep(60)
        return resp
    raise FreshdeskAPIError(f"Desisti de {path} apos 6 tentativas (rate limit/rede).")


# ---------------------------------------------------------------------------
# Metadados do Freshdesk (grupo, produto, status) — resolvidos por nome
# ---------------------------------------------------------------------------
async def load_metadata(client, logger) -> dict:
    resp = await api_get(client, "/ticket_fields", {}, logger)
    fields = {f.get("name"): f for f in (resp.data or [])}

    def choices(name):
        return (fields.get(name) or {}).get("choices") or {}

    def resolve(name, label):
        for k, v in choices(name).items():
            if k.strip().lower() == label.strip().lower():
                return v
        raise ValueError(f"Opção {label!r} não encontrada no campo {name!r}. Opções: {list(choices(name))}")

    status_labels = {int(sid): " / ".join(lbls) for sid, lbls in choices("status").items()}
    terminal = {sid for sid, lbl in status_labels.items() if any(k in lbl.lower() for k in TERMINAL_KEYWORDS)}
    cancelled = {sid for sid in terminal if "cancelado" in status_labels[sid].lower()}
    closed = {sid for sid in terminal if any(k in status_labels[sid].lower() for k in ("closed", "encerrado"))}
    resolved = terminal - closed - cancelled
    suspended = {sid for sid, lbl in status_labels.items() if SUSPENDED_KEYWORD in norm(lbl)}
    return {
        "group_id": resolve("group", GROUP_NAME),
        "product_labels": {int(v): k for k, v in choices("product").items()},
        "status_labels": status_labels,
        "terminal": terminal,
        "closed": closed,
        "resolved": resolved,
        "cancelled": cancelled,
        "suspended": suspended,
    }


# ---------------------------------------------------------------------------
# Normalizacao: ticket da API -> registro compacto do estado
# ---------------------------------------------------------------------------
def compact(t: dict) -> dict:
    """Guarda so o que a base usa (valores brutos; rotulos sao aplicados na saida)."""
    cf = t.get("custom_fields") or {}
    st = t.get("stats") or {}
    req = t.get("requester") or {}
    rec = {
        "id": t["id"],
        "subject": t.get("subject") or "",
        "status": t.get("status"),
        "group_id": t.get("group_id"),
        "product_id": t.get("product_id"),
        "responder_id": t.get("responder_id"),
        "requester_id": t.get("requester_id"),
        "company_id": t.get("company_id"),
        "priority": t.get("priority"),
        "type": t.get("type"),
        "tags": t.get("tags") or [],
        "created_at": t.get("created_at"),
        "updated_at": t.get("updated_at"),
        "first_responded_at": st.get("first_responded_at"),
        "resolved_at": st.get("resolved_at"),
        "closed_at": st.get("closed_at"),
        "reopened_at": st.get("reopened_at"),
        "status_updated_at": st.get("status_updated_at"),
        "due_by": t.get("due_by"),
        "cf_subtipo": cf.get("cf_subtipo"),
        "cf_data_incio": cf.get("cf_data_incio"),
        "cf_data_fim": cf.get("cf_data_fim"),
        "cf_workflow_se": cf.get("cf_workflow_se"),
        "cf_resolution_due": cf.get("cf_resolution_due"),
        "cf_data_limite_para_entrega": cf.get("cf_data_limite_para_entrega"),
        "cf_data_da_entrega": cf.get("cf_data_da_entrega"),
        "cf_estim_total": cf.get("cf_estim_total"),
        "cf_estimativa_po_dev": cf.get("cf_estimativa_po_dev"),
        "cf_estimativa_po_hml": cf.get("cf_estimativa_po_hml"),
        "cf_estimativa_po_or": cf.get("cf_estimativa_po_or"),
        "cf_estimativa_h560279": cf.get("cf_estimativa_h560279"),
        "cf_horas_consultoria": cf.get("cf_horas_utilizadas_servio_de_consultoria"),
        "cf_horas_contratadas": cf.get(CAMPO_HORAS_CONTRATADAS) if CAMPO_HORAS_CONTRATADAS else None,
        "cf_data_envio_oramento": cf.get("cf_data_envio_oramento"),
        "cf_data_aprovao_proposta": cf.get("cf_data_aprovao_proposta"),
        "cf_valor_do_servio_r": cf.get("cf_valor_do_servio_r"),
        "cf_valor_prvio_proposta": cf.get("cf_valor_prvio_proposta"),
        "cf_valor_final_proposta": cf.get("cf_valor_final_proposta"),
        "cf_tipo_de_demanda": cf.get("cf_tipo_de_demanda"),
        "cf_mdulo_3_niveis": cf.get("cf_mdulo_3_niveis"),
        "cf_tipo_de_resoluo": cf.get("cf_tipo_de_resoluo"),
        "cf_causa_raiz": cf.get("cf_causa_raiz"),
    }
    if req.get("name"):
        rec["requester_name"] = req["name"]
    return rec


def merge(state_tickets: dict, rec: dict) -> None:
    old = state_tickets.get(str(rec["id"]))
    if old and "requester_name" not in rec and old.get("requester_name"):
        rec["requester_name"] = old["requester_name"]  # detalhe individual sem include=requester
    state_tickets[str(rec["id"])] = rec


# ---------------------------------------------------------------------------
# Coleta
# ---------------------------------------------------------------------------
async def scan_updated_since(client, since: datetime, group_id: int, known_ids: set[int], logger) -> tuple[list[dict], int, int]:
    """Percorre TODA a listagem de tickets atualizados desde `since` (todos os grupos),
    em janelas de ate 300 paginas, e devolve os do grupo MAIS os ja conhecidos do estado
    (um ticket que saiu do grupo volta com outro group_id e sai do recorte).
    Retorna (tickets, vistos, chamadas)."""
    kept: dict[int, dict] = {}
    seen = calls = 0
    cursor = since
    while True:
        last_updated = None
        full_window = False
        for page in range(1, LIST_PAGE_CAP + 1):
            resp = await api_get(client, "/tickets", {
                "updated_since": iso(cursor), "include": "stats,requester", "per_page": 100,
                "page": page, "order_by": "updated_at", "order_type": "asc",
            }, logger)
            calls += 1
            items = resp.data or []
            seen += len(items)
            for t in items:
                if t.get("group_id") == group_id or t["id"] in known_ids:
                    kept[t["id"]] = t
            if items:
                last_updated = items[-1].get("updated_at")
            if page % 25 == 0:
                logger.info("listagem: página %d da janela desde %s (vistos %d, do grupo %d)", page, iso(cursor), seen, len(kept))
            if not resp.next_page or not items:
                break
            if page == LIST_PAGE_CAP:
                full_window = True
        if not full_window or not last_updated:
            break
        # janela cheia (300 paginas): reabre a partir do ultimo updated_at visto (duplicatas sao deduplicadas)
        logger.info("janela de 300 páginas esgotada — reabrindo a partir de %s", last_updated)
        cursor = parse_dt(last_updated)
    return list(kept.values()), seen, calls


async def search_ids(client, base: str, logger, lo: date | None = None, hi: date | None = None) -> set[int]:
    """IDs de uma busca, contornando o teto de 300 resultados por bisseccao em created_at."""
    parts = [base]
    if lo:
        parts.append(f"created_at:>'{lo.isoformat()}'")
    if hi:
        parts.append(f"created_at:<'{hi.isoformat()}'")
    query = '"' + " AND ".join(parts) + '"'
    resp = await api_get(client, "/search/tickets", {"query": query, "page": 1}, logger)
    data = resp.data or {}
    total = data.get("total", 0)
    if total == 0:
        return set()
    if total <= 300:
        ids = {t["id"] for t in data.get("results", [])}
        page = 2
        while page <= 10 and (page - 1) * 30 < total:
            r = await api_get(client, "/search/tickets", {"query": query, "page": page}, logger)
            res = (r.data or {}).get("results", [])
            if not res:
                break
            ids |= {t["id"] for t in res}
            page += 1
        return ids
    lo2 = lo or date(2015, 1, 1)
    hi2 = hi or (date.today() + timedelta(days=2))
    if (hi2 - lo2).days <= 1:
        logger.warning("busca não divisível por dia (%d resultados): %s", total, query)
        return {t["id"] for t in data.get("results", [])}
    mid = lo2 + (hi2 - lo2) / 2
    return (await search_ids(client, base, logger, lo2, mid)) | (await search_ids(client, base, logger, mid, hi2))


async def search_total(client, base: str, logger) -> int:
    resp = await api_get(client, "/search/tickets", {"query": f'"{base}"', "page": 1}, logger)
    return (resp.data or {}).get("total", 0)


async def fetch_one(client, ticket_id: int, logger) -> dict | None:
    try:
        resp = await api_get(client, f"/tickets/{ticket_id}", {"include": "stats,requester"}, logger)
        return resp.data
    except FreshdeskAPIError as exc:
        if "404" in str(exc):
            return None
        raise


# ---------------------------------------------------------------------------
# Recortes (flags) — mesmas regras validadas no script do time Tecnico
# ---------------------------------------------------------------------------
def tag_cancelled(rec: dict) -> bool:
    return any(norm(t) == CANCEL_TAG for t in (rec.get("tags") or []))


def cancel_date(rec: dict) -> str | None:
    return rec.get("closed_at") or rec.get("resolved_at") or rec.get("updated_at")


def flags(rec: dict, meta: dict, year: int, tag_cancel: bool = True) -> dict:
    """tag_cancel=False reproduz so a regra por status (usada na verificacao cruzada)."""
    s = rec.get("status")
    by_tag = tag_cancel and tag_cancelled(rec)
    cancelled = s in meta["cancelled"] or by_tag
    backlog = s not in meta["terminal"] and not by_tag
    return {
        "backlog_geral": backlog,  # inclui pendentes com o cliente e suspensos
        "backlog_ativo": backlog and s not in meta["suspended"],
        "suspenso": backlog and s in meta["suspended"],
        "novo_no_ano": in_year(rec.get("created_at"), year),
        "concluido_no_ano": s in meta["closed"] and not by_tag and in_year(rec.get("closed_at"), year),
        "resolvido_no_ano": s in meta["resolved"] and not by_tag and in_year(rec.get("resolved_at"), year),
        "cancelado_no_ano": cancelled and in_year(cancel_date(rec), year),
    }


def in_scope(rec: dict, meta: dict) -> bool:
    return rec.get("group_id") == meta["group_id"]


def cohort_counts(tickets: dict, meta: dict, year: int, tag_cancel: bool = True) -> dict:
    out = {k: 0 for k in FLAG_KEYS}
    for rec in tickets.values():
        if rec.get("group_id") != meta["group_id"]:
            continue
        for k, v in flags(rec, meta, year, tag_cancel).items():
            out[k] += int(v)
    return out


def local_verify_counts(tickets: dict, meta: dict, year: int) -> dict:
    """Contagens comparaveis com a busca do Freshdesk: regra so por status + coorte da tag."""
    out = cohort_counts(tickets, meta, year, tag_cancel=False)
    out["cancelado_por_tag"] = sum(1 for r in tickets.values() if r.get("group_id") == meta["group_id"]
                                   and tag_cancelled(r) and in_year(r.get("updated_at"), year))
    return out


def familia(rec: dict) -> str:
    t = norm(rec.get("type"))
    for trecho, fam in FAMILIA_POR_TYPE:
        if trecho in t:
            return fam
    return "Outros"


def tipo_fila(rec: dict, meta: dict) -> str:
    """Fila de orcamento/macro escopo/especificacao (outro time): por status do fluxo, tag ou Type.
    Ticket do tipo Projeto fica so em Projetos (decisao 08/10): nunca entra na fila."""
    if familia(rec) == "Projeto":
        return ""
    st = norm(meta["status_labels"].get(rec.get("status"), ""))
    for trecho, tipo in FILA_STATUS:
        if trecho in st:
            return tipo
    tags = [norm(x) for x in (rec.get("tags") or [])]
    for trecho, tipo in FILA_TAGS:
        if any(trecho in x for x in tags):
            return tipo
    return "Orçamento" if familia(rec) == "Orçamento" else ""


# ---------------------------------------------------------------------------
# Verificacao cruzada contra a busca do Freshdesk (nivel grupo, antes do filtro de produto)
# ---------------------------------------------------------------------------
async def verify(client, state: dict, meta: dict, year: int, logger) -> dict:
    g = meta["group_id"]
    y0, y1 = f"{year - 1}-12-31", f"{year + 1}-01-01"
    closed_id = min(meta["closed"])
    resolved_id = min(meta["resolved"])
    cancel_id = min(meta["cancelled"])
    open_ids = sorted(sid for sid in meta["status_labels"] if sid not in meta["terminal"])
    cohorts = {
        "backlog_geral": [f"group_id:{g} AND status:{sid}" for sid in open_ids],
        "backlog_ativo": [f"group_id:{g} AND status:{sid}" for sid in open_ids if sid not in meta["suspended"]],
        "suspenso": [f"group_id:{g} AND status:{sid}" for sid in open_ids if sid in meta["suspended"]],
        "novo_no_ano": [f"group_id:{g} AND created_at:>'{y0}' AND created_at:<'{y1}'"],
        "concluido_no_ano": [f"group_id:{g} AND status:{closed_id} AND closed_at:>'{y0}' AND closed_at:<'{y1}'"],
        "resolvido_no_ano": [f"group_id:{g} AND status:{resolved_id} AND resolved_at:>'{y0}' AND resolved_at:<'{y1}'"],
        "cancelado_no_ano": [f"group_id:{g} AND status:{cancel_id} AND updated_at:>'{y0}' AND updated_at:<'{y1}'"],
        "cancelado_por_tag": [f"group_id:{g} AND tag:'{CANCEL_TAG}' AND updated_at:>'{y0}' AND updated_at:<'{y1}'"],
    }
    local = local_verify_counts(state["tickets"], meta, year)
    report, fetched = {}, 0
    for name, queries in cohorts.items():
        remote = 0
        for q in queries:
            remote += await search_total(client, q, logger)
        entry = {"estado": local[name], "busca": remote, "diferenca": local[name] - remote}
        if local[name] < remote:
            # a busca conhece tickets que o estado nao tem: descobre os IDs e completa um a um
            ids: set[int] = set()
            for q in queries:
                ids |= await search_ids(client, q, logger)
            missing = [i for i in ids if str(i) not in state["tickets"]]
            stale = [i for i in ids if str(i) in state["tickets"]
                     and not (name in FLAG_KEYS and flags(state["tickets"][str(i)], meta, year, False)[name])]
            for tid in missing + stale:
                t = await fetch_one(client, tid, logger)
                if t:
                    merge(state["tickets"], compact(t))
                    fetched += 1
            entry.update({"ids_na_busca": len(ids), "faltavam": len(missing), "desatualizados": len(stale)})
        report[name] = entry
        logger.info("verificação %-17s estado=%d busca=%d %s", name, entry["estado"], remote,
                    "" if entry["diferenca"] == 0 else f"(dif {entry['diferenca']:+d})")
    after = local_verify_counts(state["tickets"], meta, year)
    for name in report:
        report[name]["estado_apos_ajuste"] = after[name]
    report["_buscados_individualmente"] = fetched
    return report


# ---------------------------------------------------------------------------
# Saidas
# ---------------------------------------------------------------------------
def num(v):
    return v if v not in (None, "") else ""


def build_rows(state: dict, meta: dict, agents: dict, year: int) -> list[dict]:
    rows = []
    for rec in state["tickets"].values():
        if not in_scope(rec, meta):
            continue
        f = flags(rec, meta, year)
        if not any(f.values()):
            continue
        created = parse_dt(rec.get("created_at"))
        fr = parse_dt(rec.get("first_responded_at"))
        rid = rec.get("responder_id")
        rows.append({
            "id": rec["id"],
            "assunto": rec.get("subject", ""),
            "status": meta["status_labels"].get(rec.get("status"), rec.get("status")),
            "agente": agents.get(str(rid), rid) if rid else "",
            "ativo_na_equipe": ("Sim" if rid in TIME_ATIVO else "Não (ex-integrante)" if rid in TIME_EX
                                else "Fora do time" if rid else "Sem responsável"),
            "criado_em": rec.get("created_at") or "",
            "atualizado_em": rec.get("updated_at") or "",
            "status_desde": rec.get("status_updated_at") or "",
            "primeira_resposta_h": round((fr - created).total_seconds() / 3600, 2) if (fr and created) else "",
            "data_resolucao": rec.get("resolved_at") or "",
            "data_fechamento": rec.get("closed_at") or "",
            "reaberto_em": rec.get("reopened_at") or "",
            "tags": "; ".join(rec.get("tags") or []),
            "produto": meta["product_labels"].get(rec.get("product_id"), rec.get("product_id") or ""),
            "subtipo": rec.get("cf_subtipo") or "",
            "prioridade": PRIORIDADE.get(rec.get("priority"), rec.get("priority") or ""),
            "tipo": rec.get("type") or "",
            "familia": familia(rec),
            "tipo_fila": tipo_fila(rec, meta),
            "tipo_demanda": rec.get("cf_tipo_de_demanda") or "",
            "data_inicio": rec.get("cf_data_incio") or "",
            "data_fim": rec.get("cf_data_fim") or "",
            "data_limite_entrega": rec.get("cf_data_limite_para_entrega") or "",
            "data_entrega": rec.get("cf_data_da_entrega") or "",
            "previsao_solucao": rec.get("cf_resolution_due") or "",
            "previsao_vencimento": rec.get("due_by") or "",
            "estim_total_h": num(rec.get("cf_estim_total")),
            "estim_po_dev_h": num(rec.get("cf_estimativa_po_dev")),
            "estim_po_hml_h": num(rec.get("cf_estimativa_po_hml")),
            "estim_po_orc_h": num(rec.get("cf_estimativa_po_or")),
            "estimativa_h": num(rec.get("cf_estimativa_h560279")),
            "horas_consultoria": num(rec.get("cf_horas_consultoria")),
            "horas_contratadas": num(rec.get("cf_horas_contratadas")),
            "data_envio_orcamento": rec.get("cf_data_envio_oramento") or "",
            "data_aprovacao_proposta": rec.get("cf_data_aprovao_proposta") or "",
            "valor_servico": num(rec.get("cf_valor_do_servio_r")),
            "valor_proposta_previo": num(rec.get("cf_valor_prvio_proposta")),
            "valor_proposta_final": num(rec.get("cf_valor_final_proposta")),
            "modulo": json.dumps(rec["cf_mdulo_3_niveis"], ensure_ascii=False) if isinstance(rec.get("cf_mdulo_3_niveis"), (dict, list)) else (rec.get("cf_mdulo_3_niveis") or ""),
            "tipo_resolucao": rec.get("cf_tipo_de_resoluo") or "",
            "causa_raiz": rec.get("cf_causa_raiz") or "",
            "workflow_se": rec.get("cf_workflow_se") or "",
            "solicitante": rec.get("requester_name", ""),
            "id_contato": rec.get("requester_id") or "",
            "id_empresa": rec.get("company_id") or "",
            "cancelado_origem": ("Status" if rec.get("status") in meta["cancelled"] else "Tag" if tag_cancelled(rec) else ""),
            **f,
        })
    rows.sort(key=lambda r: r["id"])
    return rows


def quality_report(rows: list[dict]) -> dict:
    """Cobertura dos campos que sustentam o SLA e as analises (so contagens)."""
    proj = [r for r in rows if r["familia"] == "Projeto"]
    proj_abertos = [r for r in proj if r["backlog_geral"]]

    def pct(lst, key):
        return round(100 * sum(1 for r in lst if r[key] not in ("", None)) / len(lst), 1) if lst else None
    return {
        "projetos": len(proj),
        "projetos_abertos": len(proj_abertos),
        "projetos_abertos_pct_data_inicio": pct(proj_abertos, "data_inicio"),
        "projetos_abertos_pct_data_fim": pct(proj_abertos, "data_fim"),
        "projetos_abertos_pct_data_limite_entrega": pct(proj_abertos, "data_limite_entrega"),
        "projetos_abertos_pct_estimativa_total": pct(proj_abertos, "estim_total_h"),
        "tickets_sem_type": sum(1 for r in rows if not r["tipo"]),
        "familia_outros": sum(1 for r in rows if r["familia"] == "Outros"),
        "backlog_com_agente_ex_integrante": sum(1 for r in rows if r["backlog_geral"] and r["ativo_na_equipe"].startswith("Não")),
        "backlog_sem_responsavel": sum(1 for r in rows if r["backlog_geral"] and r["ativo_na_equipe"] == "Sem responsável"),
    }


def write_snapshot(rows: list[dict], out_dir: Path) -> Path:
    """Contagens do dia do backlog geral por familia x status x produto (andamento da fila)."""
    snap_dir = out_dir / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    cont: dict[tuple, int] = {}
    for r in rows:
        if r["backlog_geral"]:
            k = (r["familia"], r["tipo_fila"], r["status"], r["produto"])
            cont[k] = cont.get(k, 0) + 1
    payload = {
        "data": date.today().isoformat(),
        "colunas": ["familia", "tipo_fila", "status", "produto", "qtd"],
        "linhas": [[*k, v] for k, v in sorted(cont.items(), key=lambda kv: [str(x) for x in kv[0]])],
    }
    path = snap_dir / f"{date.today().isoformat()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path


def write_outputs(rows: list[dict], summary: dict) -> tuple[Path, Path]:
    out_dir = OUTPUT_DIR / sanitize_filename(OUTPUT_SUBDIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON compacto p/ o painel: colunas + linhas (sem repetir chaves por ticket)
    keys = [k for k, _ in COLUMNS]
    json_path = out_dir / "base_integracoes.json"
    payload = {"meta": summary, "colunas": keys, "linhas": [[r[k] for k in keys] for r in rows]}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # XLSX p/ leitura humana: aba Tickets (com os recortes como colunas Sim/Não) + aba Execução
    wb = Workbook()
    ws = wb.active
    ws.title = "Tickets"
    ws.append([label for _, label in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    flag_keys = set(FLAG_KEYS)
    for r in rows:
        ws.append([("Sim" if r[k] else "Não") if k in flag_keys else r[k] for k in keys])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{max(len(rows) + 1, 2)}"
    for idx, (k, label) in enumerate(COLUMNS, start=1):
        width = max([len(label)] + [len(str(r[k])) for r in rows[:500]]) + 2
        ws.column_dimensions[get_column_letter(idx)].width = min(width, 60)

    ws2 = wb.create_sheet("Execução")
    ws2.append(["Item", "Valor"])
    for cell in ws2[1]:
        cell.font = Font(bold=True)
    for k, v in summary.items():
        ws2.append([k, json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v])
    ws2.column_dimensions["A"].width = 34
    ws2.column_dimensions["B"].width = 90

    xlsx_path = out_dir / f"{sanitize_filename(BASE_NAME)}.xlsx"
    wb.save(xlsx_path)
    return xlsx_path, json_path


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if state.get("versao") != STATE_VERSION:
        return None
    return state


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(STATE_PATH)  # escrita atomica: um erro no meio nao corrompe o estado anterior


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
async def main(ctx, force_full: bool, do_verify: bool) -> None:
    log = ctx.logger
    client = get_client()
    started = now_utc()
    year = date.today().year
    meta = await load_metadata(client, log)
    log.info("grupo=%s (%s) ano=%d; suspensos=%s", GROUP_NAME, meta["group_id"], year,
             sorted(meta["status_labels"][i] for i in meta["suspended"]))

    # O estado NUNCA e descartado, nem no --full: o Freshdesk arquiva tickets Closed antigos
    # (somem da listagem e da busca), e o estado e o unico lugar onde esse historico sobrevive.
    state = load_state()
    mode = "completa" if (force_full or state is None) else "incremental"
    if state is None:
        state = {"versao": STATE_VERSION, "ultima_sync": None, "tickets": {}}
    if mode == "completa":
        since = datetime(year, 1, 1, tzinfo=timezone.utc)
    else:
        since = parse_dt(state["ultima_sync"]) - OVERLAP
    log.info("modo=%s — listando tickets atualizados desde %s", mode, iso(since))

    # 1) listagem (fonte principal)
    known = {int(k) for k in state["tickets"]}
    group_tickets, seen, calls = await scan_updated_since(client, since, meta["group_id"], known, log)
    before = len(state["tickets"])
    seen_now = {t["id"] for t in group_tickets}
    for t in group_tickets:
        merge(state["tickets"], compact(t))
    log.info("listagem: %d tickets vistos em %d chamadas; %d do grupo ou já conhecidos (estado: %d -> %d)",
             seen, calls, len(group_tickets), before, len(state["tickets"]))

    # 2) completa: backlog parado desde antes da janela (nao aparece na listagem)
    backlog_extra = 0
    preserved: list = []
    if mode == "completa":
        for sid in sorted(meta["status_labels"]):
            if sid in meta["terminal"]:
                continue
            ids = await search_ids(client, f"group_id:{meta['group_id']} AND status:{sid}", log)
            for tid in ids:
                if str(tid) not in state["tickets"]:
                    t = await fetch_one(client, tid, log)
                    if t:
                        merge(state["tickets"], compact(t))
                        backlog_extra += 1
        log.info("backlog anterior à janela: %d tickets buscados individualmente", backlog_extra)
        # tickets do ano que o estado tem mas a API nao devolveu mais (tipicamente Closed arquivados)
        preserved = [r for k, r in state["tickets"].items()
                     if int(k) not in seen_now and in_scope(r, meta)
                     and any(flags(r, meta, year).values()) and not flags(r, meta, year)["backlog_geral"]]
        if preserved:
            log.warning("%d tickets do ano preservados do estado (não retornados pela API — provável arquivamento)", len(preserved))

    # 3) verificacao cruzada
    verification = await verify(client, state, meta, year, log) if (do_verify or mode == "completa") else None

    # 4) nomes de agentes (cache compartilhado com backlog_servicos.py e extracao_servicos_tecnicos.py)
    agents = load_agent_cache()
    needed = {r.get("responder_id") for r in state["tickets"].values() if r.get("responder_id") and in_scope(r, meta)}
    await ensure_agents_resolved(client, needed, agents, log)
    for aid, nome in {**TIME_ATIVO, **TIME_EX}.items():  # agente desativado (ex.: ex-integrante) nao resolve na API
        agents.setdefault(str(aid), nome)
    await client.aclose()

    # 5) saidas
    state["ultima_sync"] = iso(started)
    rows = build_rows(state, meta, agents, year)
    counts = cohort_counts(state["tickets"], meta, year)
    summary = {
        "base": BASE_NAME,
        "gerado_em": iso(now_utc()),
        "modo": mode,
        "janela_desde": iso(since),
        "ano": year,
        "grupo": GROUP_NAME,
        "linhas": len(rows),
        "recortes": counts,
        "chamadas_listagem": calls,
        "tickets_vistos_listagem": seen,
        "backlog_buscado_individualmente": backlog_extra,
        "preservados_do_estado": len(preserved),
        "qualidade": quality_report(rows),
        "verificacao": verification,
    }
    xlsx_path, json_path = write_outputs(rows, summary)
    snap_path = write_snapshot(rows, json_path.parent)
    save_state(state)
    log.info("recortes: %s", counts)
    log.info("qualidade dos campos: %s", summary["qualidade"])
    log.info("base salva: %s, %s e snapshot %s (%d linhas)", xlsx_path.name, json_path.name, snap_path.name, len(rows))

    ctx.result = {k: v for k, v in summary.items() if k not in ("verificacao",)}
    if verification:
        ctx.result["verificacao"] = verification  # so contagens — nunca dado de cliente


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true", help="relista o ano inteiro por cima do estado (sem apagá-lo) + verificação")
    ap.add_argument("--verify", action="store_true", help="roda a verificação cruzada também no modo incremental")
    args = ap.parse_args()
    with run("extracao_integracoes",
             f"Base única {BASE_NAME!r}: grupo={GROUP_NAME}, todos os produtos e agentes "
             f"(full={args.full} verify={args.verify})") as ctx:
        run_async(main, ctx, args.full, args.verify)
