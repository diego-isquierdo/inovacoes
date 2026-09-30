# Mapa de melhorias · Indicadores e análises do painel

> Criado em 30/09/2026, a partir dos levantamentos do Diego. Status: **planejado, não iniciado** (Fase 7 do [`PLANEJAMENTO.md`](PLANEJAMENTO.md)).
> Registre o andamento no [`LOG.md`](LOG.md).

## 1. Objetivo

Fazer o painel passar de uma visão **histórica de backlog** para uma ferramenta de **gestão diária e planejamento semanal**: capacidade, SLA, forecast, distribuição por analista e priorização. O painel deve antecipar problemas de capacidade e de SLA, e não só mostrá-los depois que o período fecha.

## 2. Decisões tomadas (30/09/2026)

| Tema | Decisão |
|---|---|
| **Esforço por ticket** | Média por subcategoria, sem estimativa individual: Ativação = padrão (1 h); dados = média real de 60 dias da subcategoria, com mínimo de 1 h. O **saldo** de cada ticket é o esforço menos as horas já apontadas nele, nunca abaixo de 0. O campo "Estimativa (h)" do Freshdesk fica fora por enquanto. |
| **Data planejada** | **Sugerida pelo painel e ajustável à mão.** O painel monta o plano pela ordem de risco e pela capacidade de cada analista. O "Data Início" do Freshdesk, quando existe, entra como data fixa. Quem edita o painel pode mudar a data de qualquer ticket, e a data manual vale mais que as outras. |
| **Priorização** | **Formulário no painel**: um botão "Priorizar" registra a solicitação, e o painel recalcula o plano e mostra o impacto. |
| **SLA** | **Dias corridos desde a abertura, sem pausa.** "Próximo do vencimento" = últimos 25% do prazo. Os vencidos parados com o cliente aparecem separados, para não esconder a origem do atraso. |
| **Backlog total × ativo** | Mantidos. Total = tudo que não foi resolvido nem fechado. Ativo = total sem os tickets aguardando o cliente (ou a validação dele), suspensos, com fornecedor ou cancelados. Os tickets em "Aguardando execução agendada" continuam no ativo. |
| **Forecast** | Novos tickets dos **3 últimos meses completos** ÷ 3, no total e por tipo de serviço. A janela anda sozinha: a partir de 01/10 passa a ser jul–set. |

### Tipos de serviço e SLA

| Tipo de serviço | Como é identificado (regra atual do painel) | SLA | "Próximo do vencimento" a partir de |
|---|---|---:|---:|
| Ativações | Tudo o que não é Dados | 7 dias | 5,25 dias (restam ≤ 1,75) |
| Importação de Dados | Dados: "import" ou "carga de dados" sem documento ou anexo | 28 dias | 21 dias (restam ≤ 7) |
| Importação de Anexos | Dados: importação de documentos, arquivos ou anexos (inclui "Importação de Dados e Documentos") | 14 dias | 10,5 dias (restam ≤ 3,5) |
| Scripts | Dados: "script" | 14 dias | 10,5 dias |
| Migrações | Dados: "migra" | 7 dias | 5,25 dias |
| Dados (outros) | Dados sem subcategoria (raro: 0,3 por mês) | 14 dias (provisório) | — |

Os prazos e o limite de 25% ficam editáveis em Configuração (`cfg/params.sla`).

## 3. Linha de base (bases de 30/09/2026, backlog total de 863 tickets)

Estes números mostram o tamanho do problema e servem para validar a implementação: o painel novo precisa chegar aos mesmos valores.

| Tipo | Backlog | Ativo | Dentro | Próximo | Vencido | Vencidos ativos | Atraso mediano |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ativações | 713 | 355 | 78 | 27 | **608** | 257 | 55 d |
| Importação de Dados | 45 | 24 | 11 | 2 | 32 | 11 | 40 d |
| Importação de Anexos | 35 | 16 | 4 | 0 | 31 | 13 | 76 d |
| Scripts | 41 | 19 | 4 | 0 | 37 | 15 | 43 d |
| Migrações | 29 | 17 | 3 | 1 | 25 | 13 | 58 d |
| **Total** | **863** | **431** | **100 (12%)** | **30** | **733 (85%)** | **309** | |

| Analista | Tickets | Vencidos | Próximos | Saldo (h) |
|---|---:|---:|---:|---:|
| Matheus Soares | 406 | 325 | 11 | 380 |
| Rodrigo Meireles | 283 | 270 | 12 | 208 |
| Marcelo Marta | 57 | 52 | 2 | 212 |
| Giovanni Ferreira | 31 | 28 | 0 | 135 |
| Sem responsável ativo | 86 | 58 | 5 | 236 |

| Entradas por mês | jun | jul | ago | set (parcial) | Forecast jun–ago |
|---|---:|---:|---:|---:|---:|
| Ativações | 218 | 344 | 188 | 326 | 250,0 |
| Importação de Dados | 12 | 25 | 14 | 14 | 17,0 |
| Importação de Anexos | 13 | 18 | 10 | 7 | 13,7 |
| Scripts | 20 | 21 | 13 | 10 | 18,0 |
| Migrações | 13 | 28 | 18 | 8 | 19,7 |
| **Total** | **276** | **437** | **243** | **365** | **318,7** |
| Saídas (resolvidos ou fechados) | 630 | 379 | 142 | 107 | |

Leituras que o painel novo precisa deixar evidentes:

- **85% do backlog já passou do SLA**, e 309 desses tickets estão ativos, isto é, dependem do time.
- As saídas caíram de 630 (junho) para 142 (agosto), enquanto as entradas seguem em ~320 por mês. Pelo volume de tickets, a fila cresce.
- Matheus e Rodrigo concentram 80% dos tickets (quase todos ativações). Em horas, a carga é mais equilibrada.
- **86 tickets sem responsável ativo**, que respondem por 236 h de saldo.
- O "Data Início" do Freshdesk está preenchido em só 157 tickets do backlog (18%), 11 deles no futuro. Por isso o plano precisa ser sugerido pelo painel.

## 4. Requisitos × painel atual

| # | Requisito | Hoje no painel | O que muda |
|---|---|---|---|
| 1 | Backlog total e ativo, com o saldo de cada ticket | Já existem (S&OP geral e por squad), com saldo = esforço da subcategoria − horas apontadas | Manter. Mostrar o saldo em horas em todas as visões (backlog, analista, plano) e a origem do esforço |
| 2 | Forecast mensal (3 meses completos ÷ 3), total e por tipo | Entradas médias por tipo (Ativação × Dados) e por subcategoria de Dados, só dentro do S&OP | Indicador próprio de forecast por tipo de serviço. **Tendência** do backlog para os próximos 6 meses (cresce, estabiliza ou reduz), em tickets e em horas |
| 3 | SLA por ticket (limite, planejada, situação) e consolidados | Não existe | Novo cálculo por ticket e nova aba **SLA** com consolidados por tipo e por analista |
| 4 | Carteira nominal por analista | A aba Time mostra backlog, idade e ocupação | Nova aba **Carteira por analista**: tickets, saldo (h), dentro, próximos e vencidos, horas planejadas × capacidade, mix por tipo |
| 5 | Planejamento semanal | Não existe | Nova aba **Planejamento semanal**: data planejada sugerida e ajustável, carga por analista e semana, o que antecipar, os atrasados e o volume represado |
| 6 | Priorização com impacto | Não existe | Formulário **Priorizar**, lista de priorizações e impacto no plano (o que foi deslocado e o novo risco de SLA) |
| 7 | Visão executiva (8 perguntas) | Visão geral e Diagnóstico respondem parte | Nova primeira aba **Visão executiva**, com uma resposta por pergunta (seção 8) |

## 5. Modelo de dados

### 5.1 Campos calculados por ticket (no painel, a cada carga; nada muda nas extrações)

| Campo | Regra |
|---|---|
| `tipo_servico` | Ativações · Importação de Dados · Importação de Anexos · Scripts · Migrações · Dados (outros) |
| `ativo` | Regra do backlog ativo (seção 2) |
| `esforco_h` / `saldo_h` | Esforço da subcategoria e saldo = max(0, esforço − horas apontadas) |
| `sla_dias`, `data_limite` | `data_limite` = `criado_em` + `sla_dias` (dias corridos) |
| `situacao_sla` | Dentro · Próximo do vencimento · Vencido (em aberto). Para os concluídos: No prazo · Fora do prazo, pela data de resolução ou fechamento |
| `dias_atraso` | max(0, hoje − `data_limite`); nos concluídos, saída − `data_limite` |
| `data_planejada`, `origem_data` | Manual (painel) > "Data Início" do Freshdesk > sugerida pelo plano |
| `semana_planejada` | Semana (segunda a domingo) da `data_planejada` |
| `risco_plano` | `data_planejada` > `data_limite` → "vai vencer no plano" |
| `prioridade_painel` | Da priorização registrada, se houver |

### 5.2 Novos documentos no banco do painel

| Documento | Quem grava | Conteúdo |
|---|---|---|
| `cfg/params.sla` | Configuração | Dias por tipo, % para "próximo", horizonte do plano (padrão 8 semanas) |
| `plano/{ticket}` | Quem edita (ajuste manual) | `data_planejada`, `responsavel` (opcional, para redistribuir), `nota`, `por` (id do usuário), `em` |
| `prioridades/{id}` | Quem edita (formulário) | ticket, tipo, responsável, data da solicitação, solicitante, prioridade (P1 Urgente · P2 Alta · P3 Normal), data planejada pedida, motivo, status (ativa/atendida/cancelada) e o **impacto calculado no momento do registro** (tickets deslocados, novos riscos de SLA) |

Os dois são escritos só por quem edita o painel (regra atual do banco) e lidos por todos.

## 6. Regras de cálculo

### 6.1 Capacidade semanal

- Por analista: capacidade mensal do Painel de Serviços × fator produtivo (85%) ÷ semanas úteis do mês. Isso já considera férias e ausências cadastradas.
- A primeira semana usa só os dias úteis que faltam.
- Os tickets "Sem responsável ativo" vão para uma fila **a distribuir**, sem capacidade própria. O painel sugere o analista com mais folga naquele tipo (dentro do squad do tipo).

### 6.2 Plano sugerido (ordem de atendimento)

1. Tickets com **data manual** ou **"Data Início" futura**: ficam na data informada e consomem a capacidade daquela semana.
2. Os demais tickets **ativos**, nesta ordem:
   1. **Priorizados**: P1, depois P2 e P3, e pela data pedida;
   2. **Vencidos**, do maior atraso para o menor;
   3. **Próximos do vencimento**, pela data limite;
   4. **Dentro do SLA**, pela data limite.
   
   Cada ticket é alocado na primeira semana em que o seu responsável tem saldo de capacidade, somando o saldo em horas. Um ticket maior que a folga da semana ocupa as semanas seguintes.
3. Tickets **fora do ativo** (aguardando o cliente etc.) não entram no plano e aparecem numa lista "aguardando terceiros".
4. O que não couber no horizonte (8 semanas) fica **represado** e é somado por semana de chegada.
5. O plano é refeito a cada carga de bases, a cada ajuste manual e a cada priorização. Datas manuais nunca são movidas pelo painel.

### 6.3 Impacto de uma priorização

Na hora do registro, o painel calcula o plano **antes** e **depois** da prioridade e grava a diferença:

- os tickets que mudaram para uma semana mais tarde (**deslocados**) e em quantos dias;
- os tickets que **passam a vencer no plano** (`data_planejada` > `data_limite`) por causa da nova prioridade;
- as horas tiradas da semana de cada analista.

O formulário mostra esse impacto antes de confirmar.

### 6.4 Forecast e tendência

- Forecast por tipo = entradas dos 3 últimos meses completos ÷ 3. A faixa mínimo–máximo dos 3 meses vira um intervalo de confiança simples.
- Vazão prevista (tickets por mês) = capacidade produtiva ÷ esforço médio ponderado do mix de entrada. A vazão real observada (saídas dos 3 meses) aparece lado a lado.
- Projeção para 6 meses: `backlog(m+1) = backlog(m) + forecast − vazão`, em tickets e em horas de saldo, nos cenários total e ativo.
- Classificação: **cresce** (mais de +5% no horizonte), **estabiliza** (±5%) ou **reduz** (menos de −5%).

## 7. Telas

| Aba | Conteúdo |
|---|---|
| **Visão executiva** (nova, primeira) | 8 cartões de resposta (seção 8), com um selo de estado e o link para a aba de detalhe |
| **SLA** (nova) | Selos de dentro, próximo e vencido (quantidade e %); vencidos por tipo; vencidos por analista; distribuição dos dias de atraso; vencidos ativos × aguardando terceiros; SLA cumprido nos concluídos por mês |
| **Carteira por analista** (nova) | Uma linha por analista: tickets, saldo (h), dentro/próximo/vencido, horas planejadas nas próximas 4 semanas × capacidade (sobrecarga ou folga) e mix por tipo. O detalhe abre a lista nominal |
| **Planejamento semanal** (nova) | Grade analista × semana com horas planejadas / capacidade, marcada acima de 100%. Listas da semana, "antecipar por risco de SLA", "atrasados" e "represado". Edição da data planejada e do responsável por ticket |
| **Priorizações** (nova) | Botão Priorizar (também na linha do ticket no Backlog e no Planejamento), lista de priorizações com impacto e status |
| Backlog (ajuste) | Novas colunas: tipo de serviço, SLA, data limite, situação, dias de atraso, saldo (h), data planejada, prioridade; filtros por situação do SLA e por semana |
| S&OP geral e por squad (ajuste) | Forecast por tipo de serviço e curva de tendência de 6 meses |
| Visão geral / Diagnóstico | Mantidas; os achados passam a citar o SLA e a tendência |

## 8. Visão executiva: pergunta → indicador

| Pergunta | Indicador | Fonte |
|---|---|---|
| Qual é o backlog atual? | Backlog total (tickets e saldo em h) | §5.1 |
| Quanto desse backlog está ativo? | Backlog ativo (tickets, h e % do total) | §2 |
| Quantos tickets estão fora do SLA? | Vencidos (quantidade e %), próximos do vencimento e atraso mediano | §6 / aba SLA |
| Onde estão concentrados os atrasos? | Top tipos e analistas por vencidos e por dias de atraso | aba SLA |
| Quantos novos tickets esperar por mês? | Forecast total e por tipo (3 meses completos ÷ 3), com a faixa | §6.4 |
| A capacidade absorve o forecast e reduz o backlog? | Capacidade (h/mês) × forecast (h/mês) × saldo; meses para zerar ou "não zera" | S&OP |
| Quais analistas ou tipos têm gargalo? | Analistas > 100% nas próximas 4 semanas; tipos com vencidos ou forecast acima da capacidade do squad | Carteira / Planejamento |
| Qual a tendência do backlog? | Projeção de 6 meses e selo cresce/estabiliza/reduz | §6.4 |

## 9. Fases de execução

| Fase | Entrega | Critério de aceite |
|---|---|---|
| **7.1 Motor de cálculo** | Tipo de serviço, ativo, saldo, SLA, data limite, situação e atraso por ticket; `cfg/params.sla` editável | Com as bases de 30/09, reproduz a linha de base da seção 3 (863 · 431 · 100/30/733) |
| **7.2 Forecast e tendência** | Forecast por tipo com a janela móvel; projeção de 6 meses; selo de tendência | Jun–ago = 318,7 por mês (Ativação 250,0 · Dados 17,0 · Anexos 13,7 · Scripts 18,0 · Migrações 19,7); em 01/10 a janela muda sozinha para jul–set |
| **7.3 Aba SLA + colunas no Backlog** | Consolidados, vencidos por tipo e por analista, atraso, concluídos no prazo | Totais batem com o motor; o filtro do Backlog por situação bate com os selos |
| **7.4 Carteira por analista** | Tabela nominal e detalhe | A soma dos analistas com "a distribuir" = backlog total |
| **7.5 Planejamento semanal** | Plano sugerido, `plano/{ticket}` para ajustes, grade analista × semana, listas de antecipar, atrasados e represado | Nenhuma semana passa da capacidade no plano sugerido (o excesso vira represado); uma data manual se mantém depois de recarregar as bases |
| **7.6 Priorização** | Formulário, `prioridades/{id}`, impacto antes e depois | Uma prioridade de teste mostra os tickets deslocados e os novos riscos e fica registrada com o impacto |
| **7.7 Visão executiva** | 8 cartões | Cada cartão leva à aba de detalhe com o mesmo número |
| **7.8 Validação** | Revisão com o Diego e registro no LOG | Aceite do Diego. O versionamento (commit e etiqueta `painel-st-v0.6.0`) só depois do aceite, feito **manualmente** pelo Diego (decisão de 30/09) |

Ordem: 7.1 → 7.2 → 7.3 → 7.4 → 7.5 → 7.6 → 7.7 → 7.8. A 7.7 pode ser publicada parcialmente a cada fase.

## 10. Riscos e pontos de atenção

| Ponto | Tratamento |
|---|---|
| **SLA sem pausa**: os tickets que aguardam o cliente vencem mesmo sem depender do time | Mostrar sempre os vencidos ativos separados dos vencidos aguardando terceiros. A pausa pelo histórico de status fica para uma fase futura (exige extrair o histórico) |
| **Tickets Closed arquivados** pelo Freshdesk somem da API | As entradas de jun–set estão completas, porque a base preserva os tickets vistos. Entradas e SLA dos concluídos de meses antigos podem vir subcontados; o painel indica o período confiável |
| **Setembro parcial** até 30/09 | O forecast usa só meses completos; o mês corrente aparece à parte |
| **86 tickets sem responsável ativo** (236 h) | Fila "a distribuir" com sugestão de analista; conta como gargalo na visão executiva |
| **Capacidade semanal derivada da mensal** | Aceitável para o plano. Se o Painel de Serviços tiver disponibilidade diária, trocar na 7.5 |
| **Esforço por média** subestima projetos grandes e superestima os pequenos | Mostrar sempre a origem do esforço e o número de tickets com horas acima do esforço |
| **Plano sugerido × realidade** | Ajuste manual sempre vence; a data sugerida é rotulada como "sugerida" |
| **Volume de escrita no banco** (ajustes e priorizações) | Documentos pequenos, um por ticket ou prioridade, muito abaixo do limite de 25 mil documentos |

## 11. Fora do escopo agora (candidatos futuros)

- Estimativa individual pelo campo "Estimativa (h)" do Freshdesk (decisão de 30/09: usar a média por subcategoria).
- Pausa do SLA enquanto o ticket aguarda o cliente (exige o histórico de status).
- Uso pelo celular.
- Alertas proativos (por exemplo, aviso diário dos tickets que vencem em 48 h).
