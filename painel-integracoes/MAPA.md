# Painel de Gestão · Integrações — Mapa do projeto

> Ponto de entrada. Último ajuste: 07/10/2026 (análise inicial; nada construído ainda).
> Mantenha curto; detalhes em [`PLANEJAMENTO.md`](PLANEJAMENTO.md) e [`LOG.md`](LOG.md).

## Objetivo

Portal vivo de gestão do time de **Integrações** (desenvolvimento de integrações: projetos, suporte, consultorias, bugs), recriando o painel do time de [Serviços ADV](../Serviços%20ADV/MAPA.md) com ajustes para trabalho orientado a projetos e prazos por marco.

## Onde está cada coisa

| O quê | Onde | Situação |
|---|---|---|
| Planejamento, log, mapa | `Painel de Gestão\Integrações\` | ✅ criados em 07/10/2026 |
| Guia transversal de S&OP | [`../LOG_SOP.md`](../LOG_SOP.md) | referência |
| Mapa de MCPs | [`../../MAPA_MCPS.md`](../../MAPA_MCPS.md) | referência (nota: lista `Integrações/` como placeholder vazio na raiz; o local real é esta pasta) |
| Tickets — script | `extracao_integracoes.py` em `MCP - Fresk\freshdesk_mcp\scripts\` | ⏳ a criar (modelo: `extracao_servicos_adv.py`) |
| Tickets — base | `scripts\output\Integrações\` | ⏳ |
| Horas — script | reaproveita `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py` | ✅ sem script novo |
| Painel | artefato claude.ai | ⏳ |

## Fontes de dados

| Fonte | Escopo | Situação |
|---|---|---|
| Freshdesk (API v2) | Grupo **INTEGRACOES** (`group_id` 158000818748), sem filtro de produto | ⏳ extração a criar; `/groups` retorna 403 com a chave atual (esperado — exige Admin), resolver o grupo pelo campo Group |
| Painel de Serviços v2 | Área **Integração** (`area_id = 2`), 5 membros | ✅ fonte pronta |

## Time (Painel de Serviços, área Integração)

| Analista | E-mail | `freshdesk_agent_id` | Horas 2026* | Citado pelo Diego |
|---|---|---|---|---|
| Lucas Silva Monteiro | lucas.monteiro@starian.com | 158010714349 | 740 h 10 | ✅ |
| Amanda Maria Pinheiro | amanda.pinheiro@starian.com | 158010714337 | 578 h 55 | ✅ |
| Elder Galvao Quirino Ribeiro | elder.ribeiro@starian.com | 158010714346 | 316 h 35 | ✅ |
| Thais Majory de Paulo Santos | thais.santos@starian.com | 158013890212 | 282 h 05 | ✅ |
| Ewerton Vital de Carvalho | ewerton.carvalho@starian.com | 158010714339 | 174 h 30 | ❌ ex-integrante (tickets e horas entram como histórico) |

\* 01/01–07/10/2026, resumo do Painel de Serviços. Total da área: 2.092 h 15 em 1.082 apontamentos. Tipo de apontamento: Faturável 1.504 h · Interno 322 h 30 · Não faturável 237 h · Apoio a outro time 28 h 40.

Diferença para o ADV: lá a área "Serviços" era compartilhada com o Técnico e o isolamento era por lista de analistas; aqui a área "Integração" é própria.

## Classificação no Freshdesk (ponto de partida)

Campo **Type** com tipos próprios do time: *Integrações - Orçamento*, *- Dúvidas*, *- Projeto*, *- Consultoria*, *- Suporte*; também aparecem *Erro de Integração* e *Dúvidas - Solicitação de orientação*. Campos úteis: Módulo (3 níveis, por integração/fornecedor), Tipo de Resolução, Causa Raiz, Tipo de apontamento. Em amostra de 30 tickets abertos, *Categorização de produtos* e *Subtipo* vieram vazios.

## Pendências

Ver "Perguntas para o Diego" em [`PLANEJAMENTO.md`](PLANEJAMENTO.md#perguntas-para-o-diego).
