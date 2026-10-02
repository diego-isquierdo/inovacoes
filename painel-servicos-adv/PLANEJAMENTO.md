# Planejamento — Painel de Gestão · Serviços ADV

Atualize o status de cada item ao concluir e registre o motivo no [`LOG.md`](LOG.md).
Legenda: ✅ concluído · 🔄 em andamento · ⏳ pendente · ⛔ bloqueado

As fases seguem a mesma numeração e o mesmo espírito do projeto
[`Serviços Técnicos`](../Serviços%20Técnicos/PLANEJAMENTO.md), que é a
referência arquitetural deste projeto.

## Fase 0 — Descoberta ✅

- ✅ Análise da pasta e da documentação do projeto `Serviços Técnicos` (README, MAPA, PLANEJAMENTO, LOG, extração, automação, orquestrador)
- ✅ Decisão de arquitetura: reaproveitar o padrão já validado (dados via script + arquivos, não via MCP; painel como artefato claude.ai)
- ✅ Filtro de escopo confirmado: grupo `SRV TECNICO`, **somente** produto `Projuris ADV` (espelho do filtro do time Técnico, que exclui esse produto) — ver [`MAPA.md`](MAPA.md#filtro-de-escopo-confirmado-em-01102026)
- ✅ Time confirmado: Renan, Marina, Lucas e Wallef — sem squads nesta primeira versão
- ⏳ Confirmar com o Diego se os mesmos 4 recortes do time Técnico (Backlog, Novo no ano, Concluído no ano, Resolvido no ano) cobrem a necessidade do time ADV, ou se há recorte específico a mais

## Fase 1 — Extração Freshdesk ✅ (validada em 01/10/2026)

Modelo técnico: [`Serviços Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md`](../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md)

- ✅ Script criado: `extracao_servicos_adv.py` (cópia adaptada do script do time Técnico, com o filtro de produto invertido — `somente Projuris ADV`), com saída e estado próprios (`scripts\output\Serviços ADV\`, `scripts\cache\servicos_adv\`), isolado do script do time Técnico
- ✅ Reaproveita a mesma fonte (listagem `GET /tickets` com `stats` e `requester` embutidos) e o mesmo princípio de estado incremental, preservando tickets Closed antes do arquivamento do Freshdesk
- ✅ Primeira execução completa (`--full --verify`) rodada e validada: verificação cruzada 100% batida contra a busca do Freshdesk (ver LOG 01/10). Recortes: Backlog 71 · Novo no ano 197 · Concluído no ano 86 · Resolvido no ano 55 (212 tickets únicos)
- ✅ Agendamento próprio no Windows (02/10/2026): tarefa "Painel Serviços ADV - Atualizar tickets", seg-sex às 20:00, modo incremental — `automacao\atualizar_tickets.ps1` + `automacao\agendar_atualizacao.ps1`. Sem execução completa semanal, botão "Atualizar" nem vigia ainda (ver Fase 5)

## Fase 2 — Fonte de horas apontadas ✅ (sem extração própria necessária)

Modelo técnico: [`Serviços Técnicos/extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO_HORAS.md)

- ✅ Fonte confirmada: Painel de Serviços v2 (mesma API usada pelo time Técnico)
- ✅ **Nenhum script novo é necessário.** `extracao_horas_apontadas.py` não filtra por time — extrai todas as áreas e todos os analistas do ano inteiro. A base já gerada para o time Técnico (`horas_apontadas_<ANO>.json` / `_painel.json`) já contém os apontamentos do time ADV
- ✅ Isolamento confirmado por lista de analistas (não por área — Técnico e ADV compartilham a mesma área "Serviços" no Painel de Serviços). Mapeamento analista ↔ `freshdesk_agent_id` em [`MAPA.md`](MAPA.md#time-e-ligação-com-o-freshdesk-confirmado-em-01102026)
- ⏳ Implementar o filtro por lista de analistas na carga do painel ADV (fica como item da Fase 3, não da extração)

## Fase 3 — Portal vivo ✅ (publicado em 02/10/2026)

- ✅ Artefato "Painel Serviços ADV" publicado: https://claude.ai/artifact/NNthAUZKErRTB1FG7myfwW (banco + arquivos carregados nele — `base_servicos_adv.json` e `horas_apontadas_2026_painel.json`)
- ✅ Abas: Visão geral, Diagnóstico da operação, SLA, Backlog, Time, Horas, S&OP geral, S&OP por Analista, Plano de Ação (simplificado, sem catálogo de automação específico do Técnico), Configuração — sem squads
- ✅ Classificação em **6 categorias de demanda** (análise real das tags/subtipo do Freshdesk, não presumida): Viabilidade/Orçamento (inclui as antigas "Dúvidas"), Importação de Dados, Importação de Documentos, Ações em Lote/Scripts, Migração · Sistemas Mapeados, Migração · Sistemas Não Mapeados — mais "Atividades Internas" (fora do SLA/demanda). Tickets ambíguos (hoje 15) marcados com a regra "Padrão" no Backlog/Diagnóstico
- ✅ Esforço padrão por categoria confirmado com o Diego: Orçamento 2h · Importação de Dados/Documentos 29h · Ações em Lote/Scripts 10h · Migração 29h sem anexo / 55h com anexo (mistura real recalculada a cada carga)
- ✅ SLA por categoria confirmado: Orçamento/Importações 3 dias · Scripts 10 dias · Migração Mapeados 40 dias · Migração Não Mapeados 60 dias
- ✅ Carga das bases: manual via upload de assets no artefato (sem botão "Atualizar" nem Mensageiro — ver Fase 5)
- ✅ Validação de engenharia: toda a lógica (classificação, SLA, S&OP, S&OP por Analista, Plano de Ação) testada no Node.js contra os dados reais antes de cada publicação, sem erros nem `NaN`/`undefined`

## Fase 4 — S&OP ✅ (revisado três vezes em 02/10/2026, a pedido do Diego)

- ✅ **Versão 1** (saldo em horizonte fixo de 3 meses, igual ao time Técnico) — substituída
- ✅ **Versão 2 — simulação mês a mês**: cada mês paga ao backlog no máximo 90% da capacidade do mês; o excedente vai para o mês seguinte, até zerar ou até 6 meses (segurança). Forecast (entradas previstas, por categoria × esforço médio, ponderado pela mistura real de anexos na migração) fica fora da conta do backlog — é só contexto, pode passar da capacidade. Propagado para Visão geral, Diagnóstico e Plano de Ação
- ✅ Gráfico em barras empilhadas (Pago ao backlog + Forecast, linha de Capacidade como referência) nos dois cenários (backlog total e backlog ativo, simulados separadamente)
- ✅ Quadro "Eficiência dos tickets concluídos" (horas estimadas × apontadas × eficiência, com coluna Mês conclusão, limitado aos últimos 2 meses)
- ✅ **Quadro adicional "Projeção viva"** (até 12 meses): pelo menos metade do Forecast de cada mês entra de fato na fila; a régua de parada é o backlog cair para 50% da capacidade do mês (não zerar). Barra empilhada com 3 fatias — Pago ao backlog, Metade do Forecast ainda na fila, Backlog antigo ainda na fila (prioridade: paga o antigo primeiro) — só a fatia do Forecast pode passar da linha de capacidade
- ⏳ Validar com o Diego se a janela de 2/3 meses do Forecast e os parâmetros (90%, metade do forecast, meta de 50%) continuam adequados conforme mais dados entrarem

## Fase 5 — Botão "Atualizar tudo" ⏳

- ⏳ Decidir se reaproveita a mesma infraestrutura do time Técnico (Mensageiro + vigia do Windows) com um pedido próprio para o painel ADV, ou se cria uma trilha separada
- Modelo: [`Serviços Técnicos/automacao/PLANEJAMENTO_BOTAO_ATUALIZAR.md`](../Serviços%20Técnicos/automacao/PLANEJAMENTO_BOTAO_ATUALIZAR.md)

## Fase 6 — Versionamento ✅ (02/10/2026)

- ✅ Mesmo repositório `diego-isquierdo/inovacoes`, pasta própria `painel-servicos-adv/`, espelhando `painel-servicos-tecnicos/`
- ✅ Diferente do time Técnico (onde o versionamento é manual, só pelo Diego — decisão de 30/09/2026 registrada no `VERSIONAMENTO.md` deles): **para o ADV, o Diego pediu explicitamente que o Claude faça o commit e o push**, nesta sessão
- Modelo: [`Serviços Técnicos/VERSIONAMENTO.md`](../Serviços%20Técnicos/VERSIONAMENTO.md)

## Fases futuras (a avaliar conforme necessidade do time ADV)

O projeto Técnico evoluiu para indicadores de gestão operacional (SLA, forecast,
carteira por analista, priorização — Fase 7), S&OP por Analista (Fase 8) e um
orquestrador de atualizações em lote no Freshdesk (Fase 9). Essas fases só
devem ser planejadas para o ADV depois que as Fases 0–4 acima estiverem
validadas com dados reais, para não antecipar decisões sem base.

## Pendências e riscos em aberto

- Mesma limitação do time Técnico: o Freshdesk arquiva tickets Closed, que
  somem da API (`/tickets/archived/{id}`); o estado incremental precisa rodar
  com frequência para não perder fechamentos. Com uma única execução por dia
  (20h), avaliar se é suficiente ou se vale adicionar um segundo horário,
  como fez o time Técnico (07:30 e 12:30).
- Definir a cadência da execução completa (`--full --verify`) — o time
  Técnico roda 1×/semana; para o ADV ainda não há agendamento equivalente.
