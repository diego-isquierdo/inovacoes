# Planejamento técnico — extração de horas apontadas (Painel de Serviços) · Integrações

Modelo: [`Serviços Técnicos/extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](../../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO_HORAS.md). Script existente: `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py` (403 linhas).

## 1. Decisão: nenhum script novo de extração

O script extrai **todas as áreas e analistas** do ano e grava `horas_apontadas_<ANO>.json`, `_painel.json` e `.xlsx` (abas: Apontamentos, Áreas, Analistas, Membros, Capacidade, Fechamento, Calendário). A área "Integração" (`area_id = 2`) já está nessa base. Mesmo raciocínio do ADV (Fase 2 deles).

Validado em 07/10/2026 via MCP (somente leitura): área 2, 01/01–07/10, **2.092 h 15 em 1.082 apontamentos**; Lucas Monteiro 740 h, Amanda 579 h, Elder 317 h, Thais 282 h, Ewerton 175 h.

## 2. Filtro na carga do painel

| Pergunta | Decisão |
|---|---|
| Como isolar o time? | **Por `area_id = 2`.** Diferente do ADV, a área é própria do time |
| Ewerton (ex-integrante)? | **Histórico entra** (as horas dele são de entregas reais do time em 2026), mas ele sai da **capacidade futura**, do S&OP e da carteira atual. Marcar o analista como `ativo=false` numa lista de configuração (aba Configuração do painel), não por regra escondida no código |
| Novos membros? | Se a área ganhar membros, entram sozinhos; se for apoio de outra área, o tipo "Apoio a outro time" já separa |
| Ligação com tickets | `ticket_id` (aba Apontamentos) = ID do ticket Freshdesk |

## 3. Campos relevantes para Integrações

- **Tipo de apontamento**: Faturável, Interno, Não Faturável, Apoio a outro time (+ "Cortesia" existe no Freshdesk). Em 2026: Faturável 1.504 h (72%) · Interno 322 h · Não faturável 237 h · Apoio 29 h. Vira indicador de utilização.
- **Cliente/empresa** e **produto** (o `resumo_horas` aceita agrupar por `cliente`, `produto`, `atividade`).
- **Capacidade** por analista/mês e **calendário** (férias, ausências): alimentam o S&OP; a aba Membros mapeia `freshdesk_agent_id`:

| Analista | `freshdesk_agent_id` | Situação |
|---|---|---|
| Amanda Maria Pinheiro | 158010714337 | ativa |
| Elder Galvao Quirino Ribeiro | 158010714346 | ativo |
| Lucas Silva Monteiro | 158010714349 | ativo |
| Thais Majory de Paulo Santos | 158013890212 | ativa |
| Ewerton Vital de Carvalho | 158010714339 | **ex-integrante** (vínculo ainda na área) |

## 4. Quando rodar o script

O script já tem agenda/rotina própria (usada pelo time Técnico e ADV). Para Integrações: **só garantir que a base global esteja atualizada antes da carga do painel**; se o agendamento atual não cobre o horário desejado, criar uma tarefa que chame o mesmo script (sem alterá-lo). Rodar o script é leitura; não há escrita no Painel de Serviços.

## 5. Ajustes só no painel (não no script)

1. Filtro por área na carga.
2. Lista de analistas ativos (configuração).
3. Agregações por **projeto** (ticket tipo Projeto): horas apontadas × estimativa, por analista e mês.
4. Horas sem `ticket_id` ou de ticket fora do grupo (apoio): aparecer separadas para não distorcer projetos.

## 6. Risco

Token do Painel de Serviços expira: renovar via `POST /api/v2/api-tokens` (procedimento do `MAPA_MCPS.md`); nunca gravar o valor em documentação.
