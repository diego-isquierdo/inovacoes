"""Extracao UNICA e INCREMENTAL da base de tickets de Servicos Tecnicos.

Substitui as tres extracoes separadas do `backlog_servicos.py` (Backlog,
Novos Tickets por Ano, Concluidos por Ano) por UMA base consolidada, da qual
os tres recortes saem por filtro (colunas-flag). Planejamento completo, mapa
de decisoes e historico em:
    Painel de Gestao/Servicos Tecnicos/extracao/PLANEJAMENTO_EXTRACAO.md

Por que e mais eficiente que o script antigo
--------------------------------------------
1. Fonte = LISTAGEM (`GET /tickets?updated_since=...&include=stats,requester`),
   nao a busca. A listagem traz 100 tickets por pagina JA com `stats`
   (1a resposta, closed_at, resolved_at) e `requester` (nome) — elimina a
   chamada extra por ticket (`GET /tickets/{id}`) que dominava o tempo do
   script antigo (~3.300 chamadas -> ~250).
2. Incremental: guarda um ESTADO local (todos os tickets do grupo ja vistos)
   e, nas execucoes seguintes, so pede o que mudou desde a ultima
   sincronizacao (`updated_since` = ultima sync - margem). Qualquer mudanca
   num ticket (status, agente, grupo, fechamento) atualiza `updated_at`,
   entao ele volta na listagem e e reclassificado.
3. Uma extracao alimenta os tres recortes (eles se sobrepoem — ver doc).

Garantias de completude (so na execucao completa, `--full`)
-----------------------------------------------------------
- A listagem so enxerga tickets atualizados desde 01/01 do ano. Tickets de
  backlog parados desde antes disso sao descobertos pela BUSCA por status
  (barata: so IDs) e completados com `GET /tickets/{id}`.
- Verificacao cruzada: para cada recorte, compara o total do estado com o
  total que a busca do Freshdesk devolve para o mesmo filtro. Divergencias
  entram no log e no resumo da execucao; IDs que a busca achou e o estado
  nao tinha sao buscados um a um e incorporados.

Saidas (pasta nao versionada — dado de cliente)
-----------------------------------------------
    scripts/output/Servicos Tecnicos/Base de Servicos Tecnicos.xlsx
    scripts/output/Servicos Tecnicos/base_servicos_tecnicos.json   (p/ o painel)
Estado incremental (tambem nao versionado):
    scripts/cache/servicos_tecnicos/estado.json

Uso:
    .venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py            # incremental (ou completa se nao houver estado)
    .venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py --full     # relista o ano (sem apagar o estado) + verificacao
    .venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py --verify   # incremental + verificacao cruzada
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
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
BASE_NAME = "Base de Serviços Técnicos"
GROUP_NAME = "SRV TECNICO"
EXCLUDE_PRODUCT = "Projuris ADV"
OUTPUT_SUBDIR = "Serviços Técnicos"

STATE_DIR = SCRIPTS_DIR / "cache" / "servicos_tecnicos"  # dado de cliente — nao versionado (scripts/cache/ no .gitignore)
STATE_PATH = STATE_DIR / "estado.json"
STATE_VERSION = 1

OVERLAP = timedelta(minutes=15)  # margem de seguranca na janela incremental
LIST_PAGE_CAP = 300              # a API recusa page > 300 em /tickets
RATE_FLOOR = 8                   # abaixo disso de requisicoes restantes, pausa ate a janela renovar
TERMINAL_KEYWORDS = ("closed", "encerrado", "resolved", "resolvido")

# Colunas da base (ordem do .xlsx). As 3 ultimas sao os recortes.
COLUMNS = [
    ("id", "ID do ticket"),
    ("assunto", "Assunto"),
    ("status", "Status"),
    ("agente", "Agente"),
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
    ("data_inicio", "Data Início"),
    ("data_fim", "Data Fim"),
    ("workflow_se", "Workflow (SE)"),
    ("solicitante", "Nome completo"),
    ("id_contato", "ID de contato"),
    ("id_empresa", "ID da empresa"),
    ("backlog", "Backlog"),
    ("novo_no_ano", "Novo no ano"),
    ("concluido_no_ano", "Concluído no ano"),
    ("resolvido_no_ano", "Resolvido no ano"),
]
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
    closed = {sid for sid in terminal if any(k in status_labels[sid].lower() for k in ("closed", "encerrado"))}
    resolved = terminal - closed
    return {
        "group_id": resolve("group", GROUP_NAME),
        "exclude_product_id": resolve("product", EXCLUDE_PRODUCT),
        "product_labels": {int(v): k for k, v in choices("product").items()},
        "status_labels": status_labels,
        "terminal": terminal,
        "closed": closed,
        "resolved": resolved,
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
        "cf_subtipo": cf.get("cf_subtipo"),
        "cf_data_incio": cf.get("cf_data_incio"),
        "cf_data_fim": cf.get("cf_data_fim"),
        "cf_workflow_se": cf.get("cf_workflow_se"),
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
# Recortes (flags) — mesmas regras validadas nos presets do backlog_servicos.py
# ---------------------------------------------------------------------------
def flags(rec: dict, meta: dict, year: int) -> dict:
    s = rec.get("status")
    return {
        "backlog": s not in meta["terminal"],
        "novo_no_ano": in_year(rec.get("created_at"), year),
        "concluido_no_ano": s in meta["closed"] and in_year(rec.get("closed_at"), year),
        "resolvido_no_ano": s in meta["resolved"] and in_year(rec.get("resolved_at"), year),
    }


def in_scope(rec: dict, meta: dict) -> bool:
    return rec.get("group_id") == meta["group_id"] and rec.get("product_id") != meta["exclude_product_id"]


def cohort_counts(tickets: dict, meta: dict, year: int, exclude_product: bool) -> dict:
    out = {"backlog": 0, "novo_no_ano": 0, "concluido_no_ano": 0, "resolvido_no_ano": 0}
    for rec in tickets.values():
        if rec.get("group_id") != meta["group_id"]:
            continue
        if exclude_product and rec.get("product_id") == meta["exclude_product_id"]:
            continue
        for k, v in flags(rec, meta, year).items():
            out[k] += int(v)
    return out


# ---------------------------------------------------------------------------
# Verificacao cruzada contra a busca do Freshdesk (nivel grupo, antes de excluir produto)
# ---------------------------------------------------------------------------
async def verify(client, state: dict, meta: dict, year: int, logger) -> dict:
    g = meta["group_id"]
    y0, y1 = f"{year - 1}-12-31", f"{year + 1}-01-01"
    closed_id = min(meta["closed"])
    resolved_id = min(meta["resolved"])
    cohorts = {
        "backlog": [f"group_id:{g} AND status:{sid}" for sid in sorted(meta["status_labels"]) if sid not in meta["terminal"]],
        "novo_no_ano": [f"group_id:{g} AND created_at:>'{y0}' AND created_at:<'{y1}'"],
        "concluido_no_ano": [f"group_id:{g} AND status:{closed_id} AND closed_at:>'{y0}' AND closed_at:<'{y1}'"],
        "resolvido_no_ano": [f"group_id:{g} AND status:{resolved_id} AND resolved_at:>'{y0}' AND resolved_at:<'{y1}'"],
    }
    local = cohort_counts(state["tickets"], meta, year, exclude_product=False)
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
                     and not flags(state["tickets"][str(i)], meta, year)[name]]
            for tid in missing + stale:
                t = await fetch_one(client, tid, logger)
                if t:
                    merge(state["tickets"], compact(t))
                    fetched += 1
            entry.update({"ids_na_busca": len(ids), "faltavam": len(missing), "desatualizados": len(stale)})
        report[name] = entry
        logger.info("verificação %-17s estado=%d busca=%d %s", name, entry["estado"], remote,
                    "" if entry["diferenca"] == 0 else f"(dif {entry['diferenca']:+d})")
    after = cohort_counts(state["tickets"], meta, year, exclude_product=False)
    for name in report:
        report[name]["estado_apos_ajuste"] = after[name]
    report["_buscados_individualmente"] = fetched
    return report


# ---------------------------------------------------------------------------
# Saidas
# ---------------------------------------------------------------------------
def build_rows(state: dict, meta: dict, agents: dict, year: int) -> list[dict]:
    rows = []
    for rec in state["tickets"].values():
        if not in_scope(rec, meta):
            continue
        f = flags(rec, meta, year)
        if not (f["backlog"] or f["novo_no_ano"] or f["concluido_no_ano"] or f["resolvido_no_ano"]):
            continue
        created = parse_dt(rec.get("created_at"))
        fr = parse_dt(rec.get("first_responded_at"))
        rid = rec.get("responder_id")
        rows.append({
            "id": rec["id"],
            "assunto": rec.get("subject", ""),
            "status": meta["status_labels"].get(rec.get("status"), rec.get("status")),
            "agente": agents.get(str(rid), rid) if rid else "",
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
            "data_inicio": rec.get("cf_data_incio") or "",
            "data_fim": rec.get("cf_data_fim") or "",
            "workflow_se": rec.get("cf_workflow_se") or "",
            "solicitante": rec.get("requester_name", ""),
            "id_contato": rec.get("requester_id") or "",
            "id_empresa": rec.get("company_id") or "",
            **f,
        })
    rows.sort(key=lambda r: r["id"])
    return rows


def write_outputs(rows: list[dict], summary: dict) -> tuple[Path, Path]:
    out_dir = OUTPUT_DIR / sanitize_filename(OUTPUT_SUBDIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON compacto p/ o painel: colunas + linhas (sem repetir chaves por ticket)
    keys = [k for k, _ in COLUMNS]
    json_path = out_dir / "base_servicos_tecnicos.json"
    payload = {"meta": summary, "colunas": keys, "linhas": [[r[k] for k in keys] for r in rows]}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # XLSX p/ leitura humana: aba Tickets (com os recortes como colunas Sim/Não) + aba Execução
    wb = Workbook()
    ws = wb.active
    ws.title = "Tickets"
    ws.append([label for _, label in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    flag_keys = {"backlog", "novo_no_ano", "concluido_no_ano", "resolvido_no_ano"}
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
    log.info("grupo=%s (%s) produto excluído=%s (%s) ano=%d", GROUP_NAME, meta["group_id"], EXCLUDE_PRODUCT,
             meta["exclude_product_id"], year)

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
                     and any(flags(r, meta, year).values()) and not flags(r, meta, year)["backlog"]]
        if preserved:
            log.warning("%d tickets do ano preservados do estado (não retornados pela API — provável arquivamento)", len(preserved))

    # 3) verificacao cruzada
    verification = await verify(client, state, meta, year, log) if (do_verify or mode == "completa") else None

    # 4) nomes de agentes (cache compartilhado com backlog_servicos.py)
    agents = load_agent_cache()
    needed = {r.get("responder_id") for r in state["tickets"].values() if r.get("responder_id") and in_scope(r, meta)}
    await ensure_agents_resolved(client, needed, agents, log)
    await client.aclose()

    # 5) saidas
    state["ultima_sync"] = iso(started)
    rows = build_rows(state, meta, agents, year)
    counts = cohort_counts(state["tickets"], meta, year, exclude_product=True)
    summary = {
        "base": BASE_NAME,
        "gerado_em": iso(now_utc()),
        "modo": mode,
        "janela_desde": iso(since),
        "ano": year,
        "grupo": GROUP_NAME,
        "produto_excluido": EXCLUDE_PRODUCT,
        "linhas": len(rows),
        "recortes": counts,
        "chamadas_listagem": calls,
        "tickets_vistos_listagem": seen,
        "backlog_buscado_individualmente": backlog_extra,
        "preservados_do_estado": len(preserved),
        "verificacao": verification,
    }
    xlsx_path, json_path = write_outputs(rows, summary)
    save_state(state)
    log.info("recortes (sem %s): %s", EXCLUDE_PRODUCT, counts)
    log.info("base salva: %s e %s (%d linhas)", xlsx_path.name, json_path.name, len(rows))

    ctx.result = {k: v for k, v in summary.items() if k not in ("verificacao",)}
    if verification:
        ctx.result["verificacao"] = verification  # so contagens — nunca dado de cliente


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true", help="relista o ano inteiro por cima do estado (sem apagá-lo) + verificação")
    ap.add_argument("--verify", action="store_true", help="roda a verificação cruzada também no modo incremental")
    args = ap.parse_args()
    with run("extracao_servicos_tecnicos",
             f"Base única {BASE_NAME!r}: grupo={GROUP_NAME} excluindo {EXCLUDE_PRODUCT} "
             f"(full={args.full} verify={args.verify})") as ctx:
        run_async(main, ctx, args.full, args.verify)
