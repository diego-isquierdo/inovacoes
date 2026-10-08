# Planejamento — Painel de Gestão · Integrações

Atualize o status de cada item ao concluir e registre o motivo no [`LOG.md`](LOG.md).
Legenda: ✅ concluído · 🔄 em andamento · ⏳ pendente · ⛔ bloqueado · ❓ depende de resposta do Diego

Referências: [`Serviços ADV/PLANEJAMENTO.md`](../Serviços%20ADV/PLANEJAMENTO.md) (arquitetura), [`LOG_SOP.md`](../LOG_SOP.md) (regras de S&OP), [`extracao/PLANEJAMENTO_EXTRACAO.md`](extracao/PLANEJAMENTO_EXTRACAO.md) e [`extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](extracao/PLANEJAMENTO_EXTRACAO_HORAS.md). **Regra nº 1 do LOG_SOP:** o motor do ADV é referência de arquitetura, não de categorias; o modelo de Integrações nasce dos dados reais.

## Decisões do Diego (07/10/2026)

| # | Decisão | Consequência no projeto |
|---|---|---|
| 1 | Ewerton saiu do time, mas tem demandas em seu nome; os tickets dele entram nas análises | Extração **sem filtro de agente**. Horas dele entram como histórico; fora da capacidade futura e do S&OP. Tickets abertos no nome dele aparecem no Diagnóstico como "sem responsável ativo" |
| 2 | **Backlog ativo = tudo que não é "Suspenso"** (com variações) | `backlog_ativo` = backlog geral − status que casem `suspens`. Aguardando cliente **continua ativo** |
| 3 | **Projeto = ticket cujo tipo é Projeto.** Projetos são a base do time; demais tickets são analisados, com foco menor | Aba **Projetos** é o centro do painel; demais famílias em abas/seções secundárias |
| 4 | Tipo **"Erro"** = suporte, ligado à **sustentação em produção** | Família Suporte/Sustentação por Type de erro |
| 5 | **SLA = prazos "Data Início" e "Data Fim"** | SLA por ticket/projeto, sem tabela fixa de dias por categoria (ver risco abaixo) |
| 6 | Time único. **Orçamento, Macro escopo e Especificação são tratados por outro time** | Não entram em capacidade/S&OP do time; ganham uma visão própria da fila: volume por tipo, tempo de vida e andamento, no geral e por produto |
| 7 | Commit e push **pelo Claude, ao comando do usuário** | Nada é commitado sozinho; só quando o Diego pedir (ver Fase 7) |

### Respostas da segunda rodada (07/10/2026)

| # | Decisão | Consequência |
|---|---|---|
| 8 | Macro escopo/Especificação/Orçamento: identificar por **status + tag e também por Type** | Coluna `tipo_fila` (Orçamento · Macro escopo · Especificação) por status → tag → Type, tabelas editáveis no script |
| 9 | Data Início/Fim são **datas reais** de entrega; considerar também a **Data limite para entrega** | Data limite = prazo planejado; Data Início/Fim = realizado. SLA e "planejado × realizado" usam as duas |
| 10 | Suporte = **apenas "Integrações - Suporte"** | Tipos "Erro…" **não** são suporte: ficam em "Outros" e aparecem no Diagnóstico para decisão |
| 11 | **Consultoria** é duradoura (cliente contrata horas e aciona sob demanda); **Dúvidas** são pontuais e de vida curta | Consultoria = carteira contínua com consumo de horas (`horas_consultoria`); Dúvidas = família própria, só volume e tempo de vida |
| 12 | Cancelado fora dos backlogs e de "fechados no ano" | Flag própria `cancelado_no_ano` |
| 13 | Estimativas (Estim. TOTAL, PO Dev/HML/Orç) são usadas | Horas estimadas × apontadas por projeto entra no painel |
| 14 | Tickets do Ewerton mantêm o nome dele como analista | Coluna "Agente no time atual" = *Não (ex-integrante)*; sem reatribuição forçada |
| 15 | Extração diária às **21h** | Tarefa "Painel Integrações - Atualizar tickets", seg-sex 21:00 |
| 16 | `LOG.md` do ADV fica como está | Sem alteração |

## Fase 0 — Descoberta ✅

- ✅ Análise de `MAPA_MCPS.md`, `LOG_SOP.md` e MDs do ADV
- ✅ Grupo `INTEGRACOES` (id 158000818748); área "Integração" do Painel de Serviços (`area_id = 2`)
- ✅ 5 respostas anteriores e 7 decisões desta rodada consolidadas
- ✅ Levantamento no Freshdesk: **31 status** (incluem fluxo de projeto e orçamento), Types próprios de Integrações, campos de data e estimativa (ver extração)
- ❓ Perguntas restantes no fim deste arquivo

## Fase 1 — Extração Freshdesk 🔄 (plano em [`extracao/PLANEJAMENTO_EXTRACAO.md`](extracao/PLANEJAMENTO_EXTRACAO.md))

1. ✅ `extracao_integracoes.py` criado em `MCP - Fresk\freshdesk_mcp\scripts\` (derivado de `extracao_servicos_adv.py`: grupo `INTEGRACOES`, sem filtro de produto nem de agente, saída/estado próprios) — compila e a lógica de flags/classificação foi testada offline
2. ✅ Cancelado terminal; suspensos detectados por `suspens`
3. ✅ `compact()` ampliado (prazos, estimativas, orçamento, causa raiz); `STATE_VERSION = 2`
4. ✅ Flags: `backlog_geral`, `backlog_ativo`, `suspenso`, `novo_no_ano`, `concluido_no_ano`, `resolvido_no_ano`, `cancelado_no_ano`; derivados `familia`, `tipo_fila`, `ativo_na_equipe`
5. ✅ Verificação cruzada com os novos recortes (implementada, **ainda não executada** contra o Freshdesk)
6. ✅ Snapshot diário (`snapshots/AAAA-MM-DD.json`) e relatório de qualidade dos campos no resumo da execução
7. ✅ Primeira execução `--full --verify` em 08/10/2026 (18 min, verificação batida; ver LOG). Qualidade: Data limite 59%, Data Início/Fim 2%/6%, estimativas 0%
8. ✅ Scripts de agendamento em `automacao\` (21:00 seg-sex); ✅ tarefa criada no Agendador em 08/10/2026 (seg-sex 21:00, incremental)

Critério de pronto: verificação cruzada 100% batida e relatório de qualidade revisado.

## Fase 2 — Horas apontadas ⏳ (plano em [`extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](extracao/PLANEJAMENTO_EXTRACAO_HORAS.md))

- ✅ **Nenhum script novo**: reaproveita `extracao_horas_apontadas.py` (base global já inclui a área 2; 2.092 h em 2026 até 07/10)
- ⏳ Garantir atualização da base antes de cada carga do painel (a tarefa das 21h cobre só tickets)
- ⏳ Filtro por `area_id = 2` e lista de analistas ativos (Amanda, Lucas Monteiro, Thais, Elder; Ewerton como histórico)

## Fase 3 — Modelo analítico ✅ (v1 em 08/10/2026)

- ⏳ **Famílias** por Type: Projeto · Suporte/Sustentação (Erro) · Consultoria · Orçamento e pré-venda (outro time) · Outros. Fallback por Tags/Assunto, "Padrão" sinalizado (LOG_SOP §2)
- ⏳ **SLA por Data Início/Data Fim**: para cada ticket com as duas datas, prazo = Data Fim; situação = *No prazo / Vencendo (último X% da janela) / Atrasado · n dias / Sem prazo definido*; para encerrados, *Entregue no prazo* se resolução/fechamento ≤ Data Fim. "Sem prazo definido" **vira achado do Diagnóstico**, não é escondido
- ⏳ **Projetos**: portfólio com avanço pelo status do fluxo de projeto (Mapeamento → Em desenvolvimento → Aguardando aprovação da homologação → Resolvido/Closed), prazo, horas apontadas × estimadas (campos de estimativa), responsável, produto, dias parado (`status_desde`)
- ⏳ **Suporte/sustentação**: volume, idade, reincidência por cliente/integração, causa raiz e tipo de resolução. SLA do suporte: mesma regra de datas se existirem; senão, indicadores de idade (decisão sobre metas pendente ❓)
- ⏳ **Fila de orçamento/escopo/especificação**: volume por tipo (e por status do fluxo 16–25), tempo de vida (idade e tempo no status), entrada × saída por semana (snapshots), geral e por produto. É visão de **acompanhamento**, sem capacidade do time
- ⏳ Marcos de prazo para além das duas datas ficam para uma segunda etapa (Diego: "trabalharemos para estabelecer marcos")

## Fase 4 — Painel (artefato claude.ai) ✅ v1 publicada: https://claude.ai/artifact/F9d7dSiJd8zvSuNov3jQ2m

Abas: **Visão geral** · **Projetos** (principal) · **Diagnóstico** · **SLA/Prazos** · **Backlog** (geral × ativo × suspenso) · **Suporte** · **Fila de Orçamento** · **Time** · **Horas** · **S&OP** · **Configuração**. Wireframe da Visão geral no canvas Design. Motor genérico por família, sem squads, design system Projuris, validação em Node.js contra dados reais antes de cada publicação (LOG_SOP §8).

## Fase 5 — S&OP ⏳

Só entra a demanda **do time**: projetos e suporte (e consultoria, se o Diego confirmar). A fila de orçamento é contexto, não carga. Projetos entram pelo cronograma (Data Início/Fim + estimativa), suporte por forecast histórico. Capacidade sem o Ewerton. Parâmetros (teto, parada, forecast) a decidir ❓ (LOG_SOP §10).

## Fase 6 — Automação ✅ (sem botão "Atualizar"; tarefa das 21h + carga por tarefa agendada do Claude, 08/10/2026)

Reaproveitar Mensageiro + vigia vs. trilha própria — mesma decisão pendente do ADV.

## Fase 7 — Versionamento ✅ (primeiro envio em 08/10/2026, commit 68d4694)

Repositório `diego-isquierdo/inovacoes`, pasta `painel-integracoes/`. **Commit e push pelo Claude somente quando o Diego mandar.** Antes do primeiro push: garantir `.gitignore` para `output/` e `cache/` (dado de cliente) e conferir que nenhum `.env`/chave entre no commit.

## Riscos

1. **Cobertura de Data Início/Data Fim.** Numa amostra de 30 tickets do tipo Projeto (mistura de abertos e encerrados), **só 1 tinha Data Início e 3 tinham Data Fim**. Se a cobertura real for essa, o SLA da decisão 5 não funciona hoje. Mitigações: medir na primeira carga; definir com o time o preenchimento obrigatório na entrada do projeto; fallback temporário por `Data limite para Entrega` (8/30) ou `due_by`, **somente se o Diego aprovar**.
2. **Ticket = projeto?** Projetos grandes aparecem como vários tickets (ex.: vários tickets "Projeto <cliente>" para frentes diferentes do mesmo cliente). Painel deve permitir agrupar por cliente/projeto.
3. **Tickets de ex-integrante** sem reatribuição distorcem carteira; tratados como achado.
4. **Histórico de status** inexistente na listagem: andamento da fila nasce dos snapshots diários e só fica rico após semanas.

## Respostas da terceira rodada (08/10/2026)

| # | Decisão | Consequência |
|---|---|---|
| 17 | Projeto em fase de especificação/escopo fica **só em Projetos** | `tipo_fila` vazio para tickets de família Projeto |
| 18 | Tipos "Erro…" e "Falha…" = **bug** | Família **Bug** (sustentação em produção corretiva), separada de Suporte (`Integrações - Suporte`) |
| 19 | Entregue no prazo = Data Fim ≤ Data limite para entrega; aberto atrasado = hoje > Data limite sem Data Fim | Regra do SLA no painel (Fase 3) |
| 20 | Campo de **horas contratadas de consultoria** ainda não existe; será criado | Ver observação de manutenção abaixo |
| 21 | Rodar `--full --verify` agora | Executada em 08/10/2026 (resultado no `LOG.md`) |
| 22 | Criar a tarefa das 21h | ✅ Tarefa "Painel Integrações - Atualizar tickets" criada (seg-sex 21:00) |

### Observação de manutenção — campo de horas contratadas (Consultoria)

Consultoria é demanda duradoura: o cliente contrata um pacote de horas e aciona sob demanda. Hoje o Freshdesk só tem **Horas utilizadas (serviço de consultoria)** (`cf_horas_utilizadas_servio_de_consultoria`); o saldo contratado ainda não existe.

Quando o campo for criado no Freshdesk (tipo número/decimal, sugestão de rótulo "Horas contratadas (serviço de consultoria)"):
1. Descobrir o nome técnico (`GET /ticket_fields` ou `freshdesk_list_ticket_fields`, formato `cf_...`).
2. Preencher `CAMPO_HORAS_CONTRATADAS` em `MCP - Fresk\freshdesk_mcp\scripts\extracao_integracoes.py`. A coluna `horas_contratadas` já está reservada na base e no `compact()`; nenhuma outra mudança no script.
3. Rodar `--full` para repopular o estado (o estado guarda só os campos conhecidos na época da coleta).
4. No painel: saldo = contratadas − utilizadas, consumo mensal e alerta de saldo baixo.
Até lá, o painel mostra só o consumo por cliente/ticket.

## Perguntas em aberto

Nenhuma bloqueante. Próximos passos: validar o relatório de qualidade da primeira carga (cobertura de Data Início/Fim/Data limite e estimativas) e iniciar a Fase 3 (modelo analítico) e a Fase 4 (painel).
