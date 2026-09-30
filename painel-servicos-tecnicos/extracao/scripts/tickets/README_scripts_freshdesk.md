# Scripts de extração (Freshdesk)

> ⚠️ **Antes de escrever um script novo, leia
> [`docs/freshdesk_api_reference.md`](../docs/freshdesk_api_reference.md).**
> Esse documento já tem os endpoints, IDs de grupo/produto/status e limitações
> conhecidas da API (ex.: `product_id` não é pesquisável em `/search/tickets`)
> mapeados de execuções anteriores. Ler esse doc primeiro evita gastar chamadas
> de API só para redescobrir algo que já sabemos — só rode
> `freshdesk_list_ticket_fields`/`_contact_fields`/`_company_fields` de novo se
> o documento não tiver a resposta ou parecer desatualizado.

Scripts avulsos para consultas/extrações que não fazem sentido como uma
ferramenta MCP permanente (contagens pontuais, cruzamentos ad-hoc, exports).
Rodam direto contra a API do Freshdesk usando o mesmo `client.py` do servidor
MCP, mas fora do protocolo MCP — então não têm o limite de tamanho de
resposta por chamada que o cliente MCP impõe, e uma extração de milhares de
registros roda numa única execução em vez de dezenas de chamadas de ferramenta.

## Padrão de um script novo

```python
from lib.common import run, run_async, get_client, paginate_all

async def main(ctx, ...):
    client = get_client()
    async for item in paginate_all(client, "/companies", logger=ctx.logger):
        ...
    await client.aclose()
    ctx.result = {"total": ...}  # resumo p/ o registro — nunca dados de cliente

if __name__ == "__main__":
    with run("nome_do_script", "descrição curta do que ele faz") as ctx:
        run_async(main, ctx, ...)
```

`lib/common.py` cuida de:
- **Autenticação**: `get_client()` lê `FRESHDESK_DOMAIN`/`FRESHDESK_API_KEY` do
  `.env` da raiz (mesmo client do servidor MCP).
- **Paginação**: `paginate_all(client, path, params, logger=...)` percorre
  todas as páginas de um endpoint de listagem automaticamente.
- **Logging**: cada execução grava um arquivo em `scripts/logs/`, com nome
  `<script>_<timestamp>.log`, além de imprimir no console (UTF-8, sem os
  erros de encoding do console do Windows).
- **Registro de execuções**: ao final, uma linha é adicionada em
  `scripts/registry.jsonl` com script, descrição, duração, status e o
  `ctx.result` (resumo). Nunca inclua dados de cliente ali — só contagens,
  IDs, nomes de filtros etc.

## Rodando um script

```bash
.venv/Scripts/python.exe scripts/count_companies.py
.venv/Scripts/python.exe scripts/list_open_tickets_by_group_and_product.py --group "SRV TECNICO" --product "Projuris ADV"
.venv/Scripts/python.exe scripts/backlog_servicos.py --preset "Backlog de Servicos Tecnicos"
.venv/Scripts/python.exe scripts/refresh_agents_cache.py
.venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py
```

## Extração única de Serviços Técnicos (`extracao_servicos_tecnicos.py`)

Substitui, para Serviços Técnicos, os três presets do `backlog_servicos.py`
(Backlog, Novos Tickets por Ano, Concluídos por Ano) por **uma base única e
incremental**: `scripts/output/Serviços Técnicos/Base de Serviços Técnicos.xlsx`
+ `base_servicos_tecnicos.json` (carga do painel), com os recortes como colunas
(Backlog, Novo no ano, Concluído no ano, Resolvido no ano) e as colunas novas
Data do Fechamento, Data da Resolução, Status desde, Reaberto em, Prioridade, Tipo
e ID da empresa.

- Fonte: `GET /tickets?updated_since&include=stats,requester` (100 tickets/chamada,
  sem a chamada extra por ticket). Estado incremental em
  `scripts/cache/servicos_tecnicos/estado.json` (não versionado).
- `--full` refaz o ano inteiro e roda a verificação cruzada contra a busca;
  sem flag, é incremental (só o que mudou desde a última execução).
- Planejamento, regras e histórico de decisões: pasta
  `Painel de Gestão\Serviços Técnicos\` (MAPA.md, PLANEJAMENTO.md, LOG.md,
  extracao/PLANEJAMENTO_EXTRACAO.md).

```bash
.venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py          # incremental
.venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py --full   # completa + verificação
```

## Convenções

- Um arquivo por extração, nome descritivo em `snake_case`
  (`count_companies.py`, `list_open_tickets_by_group_and_product.py`).
- Parâmetros variáveis (nome de grupo, produto, período) via `argparse` —
  nunca hardcode IDs internos do Freshdesk no script; resolva o nome para o
  ID em tempo de execução (veja `resolve_choice` em
  `list_open_tickets_by_group_and_product.py`) para o script continuar
  funcionando se o Freshdesk mudar algum ID.
- Se o resultado for uma extração grande (CSV/JSON para consumo externo),
  salve em `scripts/output/<nome>_<timestamp>.ext` — essa pasta não é
  versionada (dados de cliente não vão para o git).
- `scripts/logs/` e `scripts/output/` são ignorados pelo git (exceto os
  `.gitkeep`); `scripts/registry.jsonl` **é** versionado — é só metadado de
  auditoria, não dado de cliente.
- `scripts/cache/` também é ignorado pelo git (exceto `.gitkeep`) — guarda
  caches de dados que não são do cliente mas ainda são sensíveis (ex.:
  `agents_cache.json`, nomes/e-mails de agentes/funcionários — PII de
  staff). Mesmo tratamento de `scripts/output/`, motivo diferente.

## Consultando o histórico de execuções

```bash
tail -20 scripts/registry.jsonl
```

Cada linha é um JSON com `script`, `description`, `started_at`, `duration_s`,
`status` e `result`. Serve para responder "quando rodamos essa extração pela
última vez e com que resultado" sem precisar reabrir logs antigos.
