# Planejamento — Painel de Gestão · Serviços Técnicos

Atualize o status de cada item ao concluir e registre o motivo no [`LOG.md`](LOG.md).
Legenda: ✅ concluído · 🔄 em andamento · ⏳ pendente · ⛔ bloqueado

## Fase 0 — Descoberta ✅

- ✅ Análise do backlog (planilha de 28/09) e protótipo visual no canvas
- ✅ Análise do portal modelo "Customizações & Estratégia" (estrutura, banco, sincronização, S&OP)
- ✅ Análise dos scripts existentes (`backlog_servicos.py`, presets, registry, logs)
- ✅ Decisão de arquitetura: dados via script + arquivos, não via MCP (custo de tokens)

## Fase 1 — Extração Freshdesk ✅ (validada em 29/09/2026)

Detalhes técnicos: [`extracao/PLANEJAMENTO_EXTRACAO.md`](extracao/PLANEJAMENTO_EXTRACAO.md)

- ✅ Extração única cobrindo os três recortes: Backlog, Novos no ano, Concluídos no ano (+ Resolvidos no ano)
- ✅ Colunas novas: Data do Fechamento, Data da Resolução, Status desde, Reaberto em, Prioridade, Tipo, ID da empresa
- ✅ Fonte trocada de busca + 1 chamada por ticket para listagem com `stats` e `requester` embutidos
- ✅ Modo incremental com estado local
- ✅ Verificação cruzada automática contra a busca do Freshdesk
- ✅ Execução completa e incremental validadas com dados reais (4 recortes batem 100% com a busca do Freshdesk)
- ⏳ Decidir a recuperação dos tickets Closed já arquivados em 2026 (ver pendências)
- ✅ Agendamento instalado no Windows (dias úteis 07:30 e 12:30; segundas 07:15 completo) e testado em 29/09
- ⏳ Aposentar `backlog_servicos.py` para Serviços Técnicos (as 3 planilhas antigas deixam de ser atualizadas; o script continua servindo a presets de outros times)

## Fase 2 — Fonte de horas apontadas ✅ (validada em 29/09/2026)

Detalhes técnicos: [`extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](extracao/PLANEJAMENTO_EXTRACAO_HORAS.md)

- ✅ Fonte identificada: Painel de Serviços v2 (API REST do MCP `painel-servicos`)
- ✅ Campos mapeados (OpenAPI): analista, área, atividade, tipo, produto, empresa, ticket, trâmite, duração, datas
- ✅ Chave de ligação com os tickets: número do ticket (`ticket_id` ↔ `ID do ticket`)
- ✅ Script `extracao_horas_apontadas.py` (visão do ano, todos os campos, capacidade, fechamento, calendário, férias) testado offline
- ✅ Execução real (no computador do Diego — a API só aceita a rede da empresa) e validação: total = IDs únicos (6.372), agosto 100% igual à referência, 1.140 tickets cruzados com a base
- ✅ Automação: `automacao\atualizar_bases.ps1` + agendamento no Windows (`agendar_atualizacao.ps1`)
- ⏳ Confirmar se o Painel de Serviços só tem apontamentos a partir de junho/2026
- ✅ Agendamento instalado e testado (29/09, 13:12)

## Fase 3 — Portal vivo 🔄 (v1 publicada em 29/09/2026)

Regras da v1 (ver LOG): classificação Dados × Ativação (subtipo/tags → assunto), esforço padrão editável (Ativação 1 h, Dados 10 h), aba **Diagnóstico da operação**, time = Matheus, Rodrigo, Marcelo, Giovanni (Andrei fora), carga por botão.

- ✅ Artefato "Painel Serviços Técnicos" publicado (banco + arquivos, design system Projuris); fonte em `painel\painel_v1.html`
- ✅ Abas: Visão geral · Diagnóstico da operação · Backlog · Time · Horas · S&OP geral · **S&OP por squad** (Dados × Ativação, 2 analistas cada) · **Plano de Ação** (alavancas, automação, peso por demanda, balanceamento) · Configuração
- ⏳ Confirmar a composição dos squads (padrão: Dados = Marcelo + Giovanni; Ativação = Matheus + Rodrigo)
- ✅ Bases de 29/09 carregadas; parâmetros e time salvos no banco
- ⏳ Carga automática das bases após cada execução agendada (hoje: botão ou Claude)
- ⏳ Lapidar com o Diego: calibrar esforço de Dados, ajustar achados e visões
- ⏳ Compartilhar com o time (menu Compartilhar do artefato)
- ⏳ Validar com o Diego as premissas do Plano de Ação (% de ganho por automação, dias de inatividade) e priorizar as ações

## Fase 4 — S&OP 🔄 (primeira versão dentro do painel)

- ✅ Vazão mensal: entradas × saídas (resolvidos ou fechados)
- ✅ Capacidade real: capacidade do Painel × horas apontadas (ocupação)
- ✅ Esforço médio real por tipo e por subtipo de Dados (quadro "Análise real", últimos 60 dias). Fica como referência; o S&OP usa o padrão
- ✅ Saldo capacidade − demanda por mês, pessoas necessárias e meses para zerar o backlog (2 cenários)
- ✅ S&OP refeito em 29/09: esforço padrão 1 h / 10 h (editável); cenários backlog total × backlog ativo; quadro "Leitura da capacidade"
- ✅ Dados pela média real por subcategoria (importação de dados, importação de anexos, scripts, migrações), 60 dias, mínimo 1 h, recalculada a cada carga (29/09)
- ⏳ Confirmar com o squad como as migrações são apontadas (média real abaixo de 1 h)
- ⏳ Validar a contagem de entradas de Dados (68,7/mês): é o número que decide a conclusão, porque sozinho passa da capacidade do time

## Fase 5 — Botão "Atualizar tudo" ⏳ (planejado e revisto em 29/09/2026)

Plano: [`automacao/PLANEJAMENTO_BOTAO_ATUALIZAR.md`](automacao/PLANEJAMENTO_BOTAO_ATUALIZAR.md). Caminho escolhido: botão → tarefa agendada do Claude ("mensageiro") → vigia do Windows roda as extrações → mensageiro carrega o painel. Funciona do desktop, do navegador e do celular.

- ✅ Decisões: agendados contam para a hibernação; falha libera em 15 min; acionar de qualquer dispositivo; Agendador continua
- ✅ Execução das 12:30 mantida (o botão libera depois de ~17:30)
- ✅ 5.0 Provas de conceito (30/09): botão agenda a tarefa (update_trigger + run_once_at), a execução roda com o computador, pedido lido do banco, ciclo em 2 min 21 s, sem aprovações
- ✅ 5.1 (validada 30/09: pedido atendido em 2 min 1 s, hibernação e manifesto ok) Vigia do Windows + ajustes no `atualizar_bases.ps1` (trava, estado, manifesto, origem)
- ✅ 5.2 (coleta validada 30/09: bases carregadas com sha256, arquivos antigos apagados) Tarefa "Mensageiro do painel" (modos pedido e coleta 07:50/12:50)
- 🔄 5.3 (publicado 30/09, versão 7) Botão no painel com hibernação de 5 h (`cfg/atualizacao`)
- ⏳ 5.4 Validação contra a carga manual
- ⏳ 5.5 (opcional) Atalho mais rápido no desktop via MCP local

## Fase 6 — Versionamento ✅ (30/09/2026)

- ✅ Repositório `diego-isquierdo/inovacoes` com a pasta `painel-servicos-tecnicos/` (sub-repositório do painel), espelhando a pasta do projeto
- ✅ `.gitignore` bloqueia segredos (`.env`), bases, **planilhas das extrações** (`*.xlsx`), logs e estados de execução
- ✅ `VERSIONAMENTO.md` (plano, mapa origem → repositório, rotina) e `ferramentas/sincronizar_repo.ps1`
- ✅ Etiqueta `painel-st-v0.5.0`
- ⏳ A cada marco: sincronizar, registrar no LOG e criar a etiqueta — **manualmente pelo Diego e só depois de validar** (decisão de 30/09: o Claude não faz commits)

## Fase 7 — Indicadores de gestão operacional ⏳ (planejada em 30/09/2026)

Mapa: [`MAPA_MELHORIAS_INDICADORES.md`](MAPA_MELHORIAS_INDICADORES.md). Decisões: esforço pela média da subcategoria (saldo por ticket), data planejada sugerida pelo painel e ajustável à mão, priorização por formulário no painel, SLA em dias corridos sem pausa ("próximo" = últimos 25% do prazo).

- 🔄 7.1 (publicada 30/09, versão 8; linha de base reproduzida — aguarda validação) Motor de cálculo (tipo de serviço, SLA, saldo, situação) — aceite: reproduzir a linha de base de 30/09 (863 · 431 · 100/30/733)
- 🔄 7.2 (publicada 30/09, aguarda validação) Forecast (3 meses completos ÷ 3, por tipo) e tendência de 6 meses
- 🔄 7.3 (publicada 30/09, aguarda validação) Aba SLA + colunas de SLA no Backlog
- ⏳ 7.4 Carteira por analista
- ⏳ 7.5 Planejamento semanal (plano sugerido + ajuste manual em `plano/{ticket}`)
- ⏳ 7.6 Priorização (formulário + impacto no plano)
- ⏳ 7.7 Visão executiva (8 perguntas)
- ⏳ 7.8 Validação com o Diego (versionamento manual depois do aceite)

## Pendências e riscos em aberto

- **Tickets Closed são arquivados pelo Freshdesk** e somem da API (ver LOG 29/09). Isso explica a queda do "Concluídos por Ano" de 1.579 para 438 e faz "Novo no ano" subcontar. Decisão pendente: recuperação única dos arquivados de 2026 (teste ID a ID ~3 h, ou exportação da interface). Daqui em diante, o estado incremental preserva os fechamentos antes do arquivamento, desde que a extração rode com frequência.
- 1.140 tickets deste ano estão em **Resolved** e não contam como "concluídos" pela regra validada (só Closed). Decidir no painel se a vazão usa Closed, Resolved ou os dois.
- Chamados sem responsável e sem subtipo (qualidade de dado) — tratar no painel como ofensores.
