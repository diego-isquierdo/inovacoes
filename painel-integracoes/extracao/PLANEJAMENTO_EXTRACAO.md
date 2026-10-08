# Planejamento técnico — extração de tickets (Freshdesk) · Integrações

Modelo: [`Serviços ADV` / `extracao_servicos_adv.py`](../../../MCP%20-%20Fresk/freshdesk_mcp/scripts/extracao_servicos_adv.py) (606 linhas, já validado em produção) e [`Serviços Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md`](../../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md).
Decisões do Diego de 07/10/2026 estão em [`../LOG.md`](../LOG.md).

## 1. Escopo e regras

| Item | Regra |
|---|---|
| Grupo | `INTEGRACOES` (resolvido **por nome** a cada execução, sem ID no código) |
| Produto | **sem filtro de produto** — todos os produtos do grupo. O produto vira coluna e dimensão de análise (campo nativo `product_id`; está preenchido nos tickets amostrados, ao contrário do campo "Categorização de produtos", que veio vazio) |
| Agente | **sem filtro de agente.** Tickets do Ewerton (ex-integrante) entram normalmente; o escopo é o grupo, não a lista de analistas |
| Terminais | Closed/Encerrado, Resolved/Resolvido e **Cancelado** (id 15). Cancelado é terminal nos dois backlogs e ganha flag própria (ver 2). Atenção: o script do ADV só reconhece closed/resolved; aqui `TERMINAL_KEYWORDS` ganha `cancelado` |
| Suspenso | Status 28 "Suspenso" **e qualquer variação** do rótulo: casamento por substring `suspens` (case-insensitive), nunca por ID. Variações futuras entram sozinhas |

## 2. Recortes (colunas de flag na base)

| Flag | Regra |
|---|---|
| `backlog_geral` | status ∉ terminais — **inclui** Aguardando cliente, fornecedor, validações e Suspenso |
| `backlog_ativo` | `backlog_geral` **e** status não suspenso (decisão 2). Continua contando Aguardando cliente: só "suspenso" sai |
| `suspenso` | `backlog_geral` e status casa `suspens` (= geral − ativo; permite mostrar os três números) |
| `novo_no_ano` | `created_at` no ano corrente |
| `concluido_no_ano` | Closed e `closed_at` no ano |
| `resolvido_no_ano` | Resolved e `resolved_at` no ano |
| `cancelado_no_ano` | Cancelado e `updated_at`/`status_updated_at` no ano (data de cancelamento aproximada — Freshdesk não grava data específica; a tag `cancelado` também existe e é usada em tickets Closed) |

Observação: "abertos no ano" e "fechados no ano" do pedido = `novo_no_ano` e `concluido_no_ano` + `resolvido_no_ano`. O ADV já usa essa nomenclatura.

## 3. Colunas da base (acréscimos ao conjunto do ADV)

O ADV já traz: ID, assunto, status, agente, datas de criação/atualização/resolução/fechamento, status desde, 1ª resposta, reaberto, tags, produto, subtipo, prioridade, tipo, **Data Início, Data Fim**, workflow SE, solicitante, empresa e os flags.

Para Integrações, acrescentar (todos já existem no Freshdesk; nomes técnicos validados):

| Coluna | Campo Freshdesk | Uso |
|---|---|---|
| `previsao_vencimento` | `due_by` | referência secundária de prazo |
| `previsao_solucao` | `cf_resolution_due` (Previsão de Solução) | prazo alternativo |
| `data_limite_entrega` | `cf_data_limite_para_entrega` | prazo (preenchido em 8 de 30 projetos amostrados) |
| `data_entrega` | `cf_data_da_entrega` | entrega realizada |
| `estim_total_h`, `estim_po_dev_h`, `estim_po_hml_h`, `estim_po_orc_h`, `estimativa_h` | `cf_estim_total`, `cf_estimativa_po_*`, `cf_estimativa_h560279` | esforço estimado por projeto (vazios na amostra: confirmar uso) |
| `horas_consultoria` | `cf_horas_utilizadas_servio_de_consultoria` | consumo em consultorias (8 de 30) |
| `valor_servico`, `valor_proposta_previo/final` | `cf_valor_do_servio_r`, `cf_valor_*_proposta` | fila de orçamento (valor, só se o Diego quiser) |
| `data_envio_orcamento`, `data_aprovacao_proposta` | `cf_data_envio_oramento`, `cf_data_aprovao_proposta` | andamento da fila de orçamento |
| `tipo_demanda` | `cf_tipo_de_demanda` | Requisição / Incidente / Problema / Liberação |
| `modulo` | `cf_mdulo_3_niveis` | integração/fornecedor (vazio na amostra) |
| `tipo_resolucao`, `causa_raiz` | `cf_tipo_de_resoluo`, `cf_causa_raiz` | análise de suporte/sustentação |
| `ativo_na_equipe` | derivado: agente ∈ membros atuais | marca tickets de ex-integrante (Ewerton) |
| `familia` | derivado de `tipo` (ver 4) | Projeto, Suporte, Consultoria, Orçamento, Outros |

`compact()` precisa guardar os brutos novos (hoje guarda só subtipo, data início/fim e workflow). Aumentar `STATE_VERSION` para forçar reconstrução do estado.

## 4. Classificação de família (campo Type)

| Família | Type do Freshdesk | Observação |
|---|---|---|
| **Projeto** (foco do painel) | `Integrações - Projeto` | decisão 3: ticket tipo Projeto = projeto |
| **Suporte / sustentação** | somente `Integrações - Suporte` (decisão do Diego, 07/10) | tipos "Erro…"/"Falha…" caem em Outros e são tema de decisão |
| **Consultoria** | `Integrações - Consultoria` | |
| **Orçamento / pré-venda** (outro time) | `Integrações - Orçamento`, tickets de Macro escopo e Especificação | ver pergunta ❓ abaixo |
| **Dúvidas** | `Integrações - Dúvidas` | pontuais, vida curta: só volume e tempo de vida |
| **Outros** | demais Types (inclui Erro de Integração) | sinalizados no Diagnóstico |

Classificação em **uma função com tabela editável** (substrings do Type, depois Tags e Assunto como fallback; sem pista = "Padrão", marcado ambíguo — regra do LOG_SOP §2). Nunca por ID.

✅ **Macro escopo / Especificação / Orçamento** (decisão 8): identificados por status → tag → Type, nesta ordem (coluna `tipo_fila`). Não são valores do campo Type; existem como **status** (16–25: Aguardando PO, Em definição de escopo (Orç Prévio), Em definição de escopo e estimativa, Aguardando aprovação da proposta, Em especificação, Aguardando aprovação da especificação, Definição da especificação funcional…) e como tags (ex.: "Validação macro"). As listas ficam em `FILA_STATUS`/`FILA_TAGS` no script.

## 5. Verificação cruzada

Mesma técnica do ADV (compara o estado local com a busca do Freshdesk por grupo, e completa os faltantes). Ajustes:
- `backlog` por status: somar as buscas de **todos** os status não terminais, inclusive Suspenso; `backlog_ativo` = soma excluindo status suspensos.
- Sem etapa "antes do filtro de produto" (não há mais filtro de produto); a verificação passa a ser no mesmo nível do que entra na base.
- Incluir `cancelado_no_ano` na verificação (busca por status Cancelado).

## 6. Snapshots diários (novo, para "andamento da fila" e "tempo de vida")

O Freshdesk não entrega histórico de transições de status pela listagem. Para a visão pedida na decisão 6 (volume por tipo, tempo de vida, andamento da fila de orçamento):
- **Tempo de vida**: já deriva de `created_at`, `status_updated_at`, `resolved_at`/`closed_at` (idade do ticket aberto; tempo até resolução).
- **Andamento da fila**: a cada execução, gravar um **snapshot** (`snapshots/AAAA-MM-DD.json`: contagem por família × status × produto). A série diária forma o fluxo (entrou, saiu, parado) sem depender de API de histórico. Começa vazia e ganha valor com o tempo; retroativamente, aproximação por datas dos tickets.
- Opcional, fase posterior: `GET /tickets/{id}/conversations` ou Activities (se o plano permitir) para histórico real de transições, só dos tickets de orçamento, via script.

## 7. Saídas e estado

| Item | Caminho |
|---|---|
| XLSX | `scripts\output\Integrações\Base de Integrações.xlsx` |
| JSON do painel | `scripts\output\Integrações\base_integracoes.json` |
| Snapshots | `scripts\output\Integrações\snapshots\` |
| Estado incremental | `scripts\cache\integracoes\estado.json` (nunca descartado, nem no `--full`: preserva Closed arquivados) |
| Log/registry | padrão `lib.common` (`run(...)`) |

Dado de cliente: pastas `output/` e `cache/` continuam fora do versionamento.

## 8. Mudanças no código (a partir de `extracao_servicos_adv.py`)

1. Constantes: `GROUP_NAME="INTEGRACOES"`, `BASE_NAME`, `OUTPUT_SUBDIR`, `STATE_DIR`, remover `INCLUDE_PRODUCT`.
2. `load_metadata`: remover `include_product_id`; manter `product_labels`; calcular `terminal` (closed/resolved/cancelado) e `suspended` (status que casam `suspens`).
3. `compact()`: novos campos da seção 3; `STATE_VERSION = 2`.
4. `in_scope()`: só grupo. `cohort_counts`/`flags`/`verify`: novos flags (seção 2).
5. `build_rows`: colunas novas, `familia`, `ativo_na_equipe`, tags e produto.
6. `write_outputs`: novo nome de JSON e aba de snapshots.
7. Rótulo de agente: o cache de agentes compartilhado pode não resolver agente desativado (Ewerton). Fallback: mapa `freshdesk_agent_id → nome` vindo da aba Membros da base de horas.
8. Agendamento: `automacao\atualizar_tickets.ps1` e `agendar_atualizacao.ps1` copiados do ADV, tarefa própria "Painel Integrações - Atualizar tickets".

## 9. Riscos

- Lentidão da API na execução completa (no ADV levou ~78 min com ~2.300 tickets; o grupo INTEGRACOES é menor — a medir). Rodar `--full --verify` fora do horário.
- Cobertura de **Data Início/Data Fim** (base do SLA): ver [`../PLANEJAMENTO.md`](../PLANEJAMENTO.md), item de risco.
- Rate limit compartilhado com os outros scripts: não rodar duas extrações ao mesmo tempo.
