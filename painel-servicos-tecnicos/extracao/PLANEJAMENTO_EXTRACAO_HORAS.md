# Extração de horas apontadas — Painel de Serviços v2 (planejamento técnico)

Script: `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py`
Voltar ao [mapa do projeto](../MAPA.md) · [planejamento geral](../PLANEJAMENTO.md) · [log](../LOG.md) · [extração de tickets](PLANEJAMENTO_EXTRACAO.md)

## 1. Escopo e decisões (Diego, 29/09/2026)

- **Visão do ANO:** `work_date` de 01/01 a 31/12 do ano corrente, ou o de `--ano`.
- **Todos os campos que a API fornece**, sem descartar nenhum. Campos aninhados
  viram colunas `pai.filho`; listas viram JSON na célula.
- **Rascunhos não entram.** Só apontamentos confirmados (`GET /apontamentos`).
- **Capacidade, fechamento, calendário, disponibilidade e férias entram**, cada
  um em uma aba.
- **Usuários:** o Diego e o painel que será construído.
- **Áreas:** todas as áreas que o token enxerga. A área vira coluna e o painel
  filtra Serviços Técnicos.
- **Chave com a base de tickets:** número do ticket, `ticket_id` ↔ `ID do ticket`
  (ver [MAPA](../MAPA.md#chave-de-ligação-entre-as-bases-número-do-ticket)).

## 2. Fonte e rotas (todas só leitura, sob `/api/v2/apontamentos`)

| Aba | Rota | Chamadas |
|---|---|---|
| Apontamentos | `GET /apontamentos?mine=false&date_from&date_to&sort=date_asc&page_size=100` | paginado até `total` |
| Áreas | `GET /areas?include_inactive=true` (se não houver permissão: `/me/areas`) | 1 |
| Analistas · Membros | `GET /analysts?area_id` · `GET /members?area_id` | 2 por área |
| Capacidade | `GET /reports/capacity?area_id&month` | 12 × áreas |
| Meta de produtividade | `GET /reports/productivity-goal?year_month` | 12 |
| Fechamento (Totais / Analistas / Tipos) | `GET /reports/closing?month&area_id` | meses até o atual × áreas |
| Disponibilidade · Alocações · Férias | `GET /calendar/availability?year_month=AAAA-07&span=6` | 1 (julho ± 6 meses cobre o ano) |
| Calendário | `GET /calendar?year_month&analyst_id` | meses até o atual × analistas |

- **Autenticação:** `Authorization: Bearer <token>`. O OpenAPI não declara esquema
  de segurança; confirmar na primeira execução real.
- **Configuração:** o mesmo `.env` do MCP (`mcp_server\.env`: `PAINEL_SERVICOS_BASE_URL`, `PAINEL_SERVICOS_TOKEN`). Nunca versionar nem compartilhar.
- **Rota sem permissão** (401/403/404/422): não derruba a extração. Vira uma
  linha na aba **Execução** e as demais abas saem normalmente.
- **Erros transitórios:** retry limitado em 429, 5xx e falhas de rede. O script só
  faz GET; nenhuma escrita no Painel.

## 3. Saídas

Na pasta `MCP Painel de Serviços\output\`, sobrescritas a cada execução:

| Arquivo | Conteúdo |
|---|---|
| `Horas Apontadas <ANO>.xlsx` | Uma aba por tabela (seção 2) + aba **Execução** (resumo e status de cada consulta) |
| `horas_apontadas_<ANO>.json` | `{meta, tabelas: {<aba>: {colunas, linhas}}}` para a carga do painel |

**Colunas derivadas na aba Apontamentos:** `horas` (= `duration_seconds` / 3600,
4 casas) e `mes` (AAAA-MM). Os segundos originais são mantidos.

## 4. Validação (checklist da primeira execução real)

1. `total` informado pela API = linhas extraídas, sem IDs duplicados.
2. Agosto/2026 comparado com `mcp_server\Apontamentos_Servicos_Agosto2026.xlsx`
   (1.379 apontamentos): quantidade, soma de horas e IDs.
3. Status de cada rota na aba Execução; permissões faltantes registradas no LOG.
4. Cruzamento com a base de tickets pelo número do ticket: quantos apontamentos
   têm ticket, quantos desses tickets existem na base de Serviços Técnicos e quais
   não existem (outros grupos, ou arquivados).

## 5. Status

- ✅ Script testado offline e depois com dados reais (29/09/2026, 86 s, 250 chamadas, 0 consultas negadas).
- ✅ Validação: 6.372 = total da API = IDs únicos; agosto idêntico à planilha de referência; 1.140 tickets cruzados com a base de Serviços Técnicos.
- ✅ Saída compacta para o painel: `horas_apontadas_<ANO>_painel.json` (sem o texto dos trâmites, ~4,8 MB).
- ✅ Roda no computador do Diego (a API responde 403 fora da rede da empresa), via `automacao\atualizar_bases.ps1`.
- ⚠️ Os dados começam em junho/2026 (confirmar se o Painel entrou em uso nessa data).
- ⏳ Incremental: não é necessário, porque o ano inteiro leva ~1,5 min.
