# Log de decisões — Painel de Gestão · Integrações

Diário datado, mais recente primeiro.

## 08/10/2026 — Decisões finais da rodada, execução e agendamento

Respostas: projetos em especificação ficam só em Projetos; tipos Erro/Falha = família **Bug**; regra de prazo confirmada (Data Fim ≤ Data limite para entrega); campo de horas contratadas de consultoria será criado (reservado no script e documentado em `PLANEJAMENTO.md`); autorizada a execução `--full --verify` e a criação da tarefa agendada.

Script ajustado (família Bug, `tipo_fila` vazio para Projeto, `CAMPO_HORAS_CONTRATADAS`). Tarefa do Windows "Painel Integrações - Atualizar tickets" criada (seg-sex 21:00, incremental). Primeira execução completa iniciada em segundo plano; resultado será registrado aqui.

## 08/10/2026 (3) — Fases 3 e 4: modelo analítico e painel publicado

Regra de cancelamento por tag aplicada no script (`cancelado` em qualquer status; verificação por tag: 44 = 44). Efeito: backlog geral 166, ativo 130, suspenso 36, concluído no ano 42, resolvido 104, cancelado 44 (classificados por família).

**Painel publicado:** https://claude.ai/artifact/F9d7dSiJd8zvSuNov3jQ2m (fonte em `painel/painel_v1.html`, montada de `painel/partes/` por `montar.sh`). Abas: Visão geral, Projetos (centro), Diagnóstico, Prazos, Backlog (geral/ativo/suspenso), Suporte e Bugs, Consultoria, Fila de orçamento (geral e por produto), Time, Horas, S&OP, Configuração. Bases carregadas por upload de assets e `cfg/bases` no banco do artefato; base de horas só da área Integração (`ferramentas/preparar_base_horas_integracoes.py`).

**Validação:** `painel/teste_node.js` roda o motor contra as bases reais; 12 visões sem exceção, NaN ou undefined. Projetos abertos (49): 23 atrasados, 20 sem data limite, 3 entregues com atraso e 3 entregues a encerrar, segundo a regra Data limite × Data Fim. Achados: 20 tickets de ex-integrante, 35 com agente de fora do time, 68 parados > 30 dias no ativo.

**Pendências:** (1) automatizar a geração da base de horas e o upload (hoje manual, como no ADV); (2) snapshots diários ainda não alimentam a aba de fila; (3) painel não tem Plano de Ação; (4) S&OP usa mediana de horas dos encerrados como referência (Projeto: 4 projetos de base) e consultoria sem referência; (5) campo de horas contratadas pendente.

## 08/10/2026 (2) — Primeira extração completa validada

`extracao_integracoes.py --full --verify` concluída em 1.074 s (~18 min; 22.754 tickets varridos, 351 do grupo). Verificação cruzada batida em backlog geral (168), backlog ativo (132), suspenso (36), novo no ano (259), concluído no ano (84) e cancelado (0). Resolvido no ano: estado 99 × busca 104; os 5 faltantes foram buscados um a um e a base final tem 104. Base: 356 tickets em `scripts/output/Integrações/`; execução incremental seguinte levou 2,5 s.

**Backlog geral por família:** Projeto 49 · Orçamento 45 · Consultoria 44 · Suporte 18 · Dúvidas 9 · Bug 2 · Outros 1 (após incluir fallbacks por Type). Fila do outro time no backlog: Orçamento 39 + Macro escopo 6.

**Qualidade dos dados (projetos abertos, n=49):** Data Início 2,0% · Data Fim 6,1% · **Data limite para entrega 59,2%** · Estim. TOTAL 0%. 28 tickets sem Type. Produto: Enterprise 129, Empresas 37, Acordos 2 (backlog).

**Achados:** (1) Data Início/Fim quase não preenchidas — o SLA depende hoje da Data limite; (2) 20 tickets abertos no nome do Ewerton e 4 sem responsável; (3) 35 tickets abertos com agentes de fora do time atual (outros grupos atendendo tickets do grupo INTEGRACOES); (4) o status Cancelado não é usado: cancelamento ocorre pela tag `cancelado` (44 tickets, em geral Closed) — `cancelado_no_ano` ficará 0 até decidir tratar a tag; (5) Types sem acento/variações ("Integrações - Solicitação de orçamento", "Dúvidas - Solicitação de orientação") ganharam regra de fallback.

## 07/10/2026 (3) — Script de extração e automação criados

Respostas do Diego (decisões 8–16 no `PLANEJAMENTO.md`). Criado `extracao_integracoes.py` (772 linhas) a partir do script do ADV e `automacaotualizar_tickets.ps1` + `agendar_atualizacao.ps1` (21:00). Compilação e checagem de sintaxe OK; flags e classificação testados offline com status e Types reais. **Nada executado contra o Freshdesk e nenhuma tarefa agendada ainda** (pendente de OK). Suporte = só "Integrações - Suporte" (erros ficam em "Outros"); Consultoria e Dúvidas separadas; Ewerton mantido como analista. Commit/push não feitos (aguardando comando).

## 07/10/2026 (2) — Respostas do Diego e planejamento das extrações

**Decisões:** (1) Ewerton não está mais no time, mas seus tickets entram nas análises — extração sem filtro de agente; (2) backlog ativo = tudo que não é "Suspenso" (e variações); (3) projeto = ticket de tipo Projeto, base do time; (4) tipo "Erro" = suporte/sustentação em produção; (5) SLA baseado em Data Início e Data Fim; (6) time único; Orçamento, Macro escopo e Especificação são de outro time — só visão de volume por tipo, tempo de vida e andamento da fila, geral e por produto; (7) commit/push pelo Claude, ao comando do usuário.

**Análise feita (somente leitura):** 31 status do Freshdesk (fluxo de projeto e de orçamento já existem como status), campos de data/estimativa, amostra de 30 tickets Projeto, scripts `extracao_servicos_adv.py` e `extracao_horas_apontadas.py`.

**Achados:** Macro escopo e Especificação não existem no Type — só como status/tag; Data Início/Fim preenchidas em 1 e 3 de 30 tickets Projeto (risco para o SLA); produto nativo preenchido, "Categorização de produtos" vazia; estimativas vazias na amostra; a extração de horas não precisa de script novo (área 2 já está na base).

**Entregas:** `extracao/PLANEJAMENTO_EXTRACAO.md`, `extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`, `PLANEJAMENTO.md` reescrito. Nenhum script criado ainda; aguardando respostas das 9 perguntas.

## 07/10/2026 — Análise inicial e planejamento

**Pedido do Diego:** recriar para Integrações o painel de gestão do time de Serviços ADV; time de desenvolvimento de integrações (projetos, suporte, consultorias, bugs); prazos por projeto, com marcos e SLA a estabelecer; extração Freshdesk no mesmo formato, filtro Grupo = INTEGRACOES, com backlog geral (inclui pendentes com cliente) e ativo (com o time + em aberto), abertos no ano e fechados no ano; horas no mesmo formato; analistas Amanda, Lucas Monteiro, Thais e Elder.

**Análise feita:** `MAPA_MCPS.md`, `LOG_SOP.md` e README/MAPA/PLANEJAMENTO/LOG de `Serviços ADV`; consulta somente leitura ao Painel de Serviços (membros e resumo de horas da área Integração) e ao Freshdesk (campos de ticket e uma amostra de 30 tickets do grupo).

**Achados:**
- Grupo `INTEGRACOES` existe (id 158000818748); `/groups` dá 403 com a chave atual.
- Field Type já tem 5 tipos próprios de Integrações — base da classificação.
- Área "Integração" do Painel de Serviços é própria (5 membros); inclui o Ewerton, não citado pelo Diego.
- Horas 2026: 2.092 h, 72% faturáveis.
- `MAPA_MCPS.md` descreve `Integrações/` como placeholder vazio na raiz de `Inovações`; o projeto vive em `Painel de Gestão\Integrações\`. Ajustar o mapa quando o Diego confirmar.
- O `LOG.md` do ADV contém uma API key do Freshdesk em texto claro (entrada de 01/10/2026) — recomendada rotação e limpeza.

**Decisão:** nada de script, painel ou agendamento foi criado; esta entrega é só documentação (README, MAPA, PLANEJAMENTO, LOG). Aguardando as respostas das perguntas do `PLANEJAMENTO.md` antes da Fase 1.
