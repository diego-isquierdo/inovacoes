# Log do projeto — Painel de Gestão · Serviços Técnicos

Diário de decisões, descobertas e execuções relevantes, **do mais recente para o
mais antigo**. Cada entrada diz o que foi feito, por quê e o resultado. O
histórico técnico de cada execução do script fica em
`freshdesk_mcp\scripts\registry.jsonl` e `scripts\logs\`. Aqui entra só o que
muda o entendimento do projeto.

Modelo de entrada:

```
## 2026-09-30 — Versionamento no GitHub (`painel-st-v0.5.0`)

- Repositório: https://github.com/diego-isquierdo/inovacoes. Um repositório para todos os projetos de inovação, e o painel na pasta **`painel-servicos-tecnicos/`** (o "sub-repositório", por decisão do Diego).
- A pasta espelha `Painel de Gestão\Serviços Técnicos` (MAPA, PLANEJAMENTO, LOG, `extracao/`, `automacao/`, `painel/`), então os links funcionam nos dois lugares. Os scripts Python que vivem em outros projetos entram como cópia em `extracao/scripts/tickets` e `extracao/scripts/horas`.
- Novos só no repositório:
  - `README.md` da raiz e do painel;
  - `VERSIONAMENTO.md`, com o plano, o mapa origem → repositório e a rotina;
  - `tarefas/README.md`, com as tarefas agendadas do Claude, seus ids e horários;
  - `ferramentas/sincronizar_repo.ps1`, que copia as versões em uso para um clone e faz o commit.
- **Fora do versionamento** (`.gitignore`, pedido do Diego para as planilhas): `.env`, **planilhas das extrações (`*.xlsx`)**, bases JSON, `output/`, `cache/`, logs, `registry.jsonl`, `estado_botao.json`, `manifesto.json`, `ultima_atualizacao.json`, pedidos e a trava.
- `.ps1` e `.vbs` versionados byte a byte (CRLF e BOM) via `.gitattributes`.
- Varredura antes do commit: nenhum token, chave ou e-mail nos arquivos.

## 2026-09-30 — Fases 5.2 e 5.3 montadas (falta liberar as pastas das tarefas novas)

- **Tarefas agendadas do Claude** (ligadas ao computador, aprovação automática, 3 pastas), ambas com o roteiro de `automacao/mensageiro_prompt.md`:
  - "Mensageiro do painel (botão Atualizar)" (`trig_014VFMUxsPSn9JeGY2GDfNpk`): sem horário; o botão a agenda para o minuto seguinte.
  - "Coleta do painel (após o Agendador)" (`trig_01RreKZegbVLgyEGU2Bozw2k`): dias úteis às 07:50 e 12:50 (horário de Brasília).
- **Roteiro do mensageiro:**
  - modo **pedido**: entrega `pedido_atualizacao.json` ao vigia, acompanha `estado_botao.json` minuto a minuto (até 20 min) e espelha a etapa no painel;
  - modo **coleta**: compara os SHA-256 do manifesto com os de `cfg/bases`;
  - **carga**: confere o hash, envia as 2 bases como arquivos do painel, grava `cfg/bases` (agora com `sha256`), apaga os arquivos antigos e grava `cfg/atualizacao`;
  - **falha**: grava o motivo e libera o botão em 15 min.
  - O roteiro nunca lê o conteúdo das bases.
- **Painel (versão 7):** botão **Atualizar** no cabeçalho, visível para quem edita, com um selo de estado: Disponível, Na fila, Pedido entregue, Atualizando (etapa), Carregando, Hibernando até HH:MM, Falhou · nova tentativa às HH:MM, e Disponível das 07:00 às 21:40. O botão acompanha a última atualização e a origem, e só aceita cliques das 07:00 às 21:40.
  - Banco: `cfg/mensageiro` (id da tarefa) e `cfg/atualizacao` (estado).
- **Primeiro teste** (coleta disparada pelo Claude às 05:09 UTC): a execução **não recebeu as pastas**, a mesma situação da PoC antes da liberação. O painel registrou "Falhou" e liberou em 15 min, como previsto. Falta o Diego liberar o acesso às pastas das 2 tarefas novas no app desktop.

## 2026-09-30 — Fase 5.1 validada no Windows

- As 3 tarefas foram instaladas pelo Diego. Gravei o pedido de teste `teste-5.1-0458` na pasta e o vigia foi disparado à mão às 02:00 (fora da janela 07:00–22:00).
- Resultado: pedido aceito → `atualizar_bases.ps1 -ForcarTickets -Origem botao` → **ok em 2 min 1 s** (tickets 53 s, horas 67 s) → pedido arquivado em `pedidos\atendido_20260930_020241.json`.
- `estado_botao.json`: status ok, último sucesso às 02:02, botão **liberado às 07:02** (5 h). A trava `.executando` foi removida no fim.
- `manifesto.json`: 4 bases com tamanho e SHA-256 (tickets JSON 1,0 MB; horas JSON 4,9 MB; as 2 planilhas).
- Números da base (sem ADV): backlog 863 · novos no ano 2.145 · concluídos 438 · resolvidos 1.143 · 6.372 apontamentos (sem mudança nas horas desde 29/09).
- Próximo: 5.2 (mensageiro de verdade: pedido pelo banco → pedido na pasta → acompanha → carrega as bases no painel) e 5.3 (botão no painel).

## 2026-09-30 — PoC fechada; Fase 5.1 (Windows) entregue para instalação

- **PoC ok:** clique no app desktop às 04:48:44 (UTC); a tarefa foi agendada para 04:50, rodou com o computador, leu o pedido no banco (`origem_pedido: banco`), gravou e leu na pasta e enviou o arquivo à página. O ciclo completo levou **2 min 21 s**, sem nenhuma aprovação.
- **5.1 entregue:**
  - `atualizar_bases.ps1` ganhou:
    - `-Origem agendado|botao|manual` e `-PedidoId`;
    - trava `.executando` (sai com código 2 se já houver outra execução; a trava vence em 30 min);
    - `estado_botao.json` com a etapa atual e a hibernação: 5 h depois de um sucesso e 15 min depois de uma falha, nunca antes da hibernação de um sucesso anterior. Uma execução parcial (`-SoTickets`) não mexe na hibernação;
    - `manifesto.json` com caminho, tamanho, SHA-256 e data das 2 bases JSON e das 2 planilhas;
    - todos os JSON gravados em UTF-8 sem BOM e de forma atômica.
  - Novos `vigia_pedidos.ps1` + `vigia_oculto.vbs`: a cada 5 min, das 07:00 às 22:00, sem abrir janela. Atende `pedido_atualizacao.json`:
    - recusa o pedido se o botão estiver hibernando;
    - espera se houver outra execução em andamento, e recusa depois de 30 min;
    - arquiva cada pedido em `pedidos\` e registra o que fez em `logs\vigia.log`.
  - `agendar_atualizacao.ps1` passou a criar também a tarefa "Painel Serviços Técnicos - Vigia de pedidos" e a conferir as 3 tarefas.
- Testado aqui com PowerShell 7 e Python simulado: sucesso, falha, hibernação, trava ativa, trava vencida, pedido inválido e pedido esperando mais de 30 min. Corrigido na hora: a trava `.executando` só é enxergada com `Get-Item -Force`.
- Falta: instalar no Windows (rodar `agendar_atualizacao.ps1` de novo) e testar com um pedido real.

## 2026-09-30 — PoC do botão: acionamento pela página roda sem o computador (e a solução)

Testes do mesmo mensageiro, por forma de acionamento:

| Forma de acionamento | Pedido chegou? | Computador disponível? | Tempo |
|---|---|---|---|
| Clique na página (`fire_trigger` pelo conector) | sim | **não**: a execução rodou só na nuvem, sem as ferramentas do computador | ~19 s |
| Acionamento pelo Claude nesta conversa | sim | sim | ~28 s |
| **Execução agendada (`run_once_at`)** | pelo banco | **sim**: gravou, leu e enviou sem aprovação | ~45 s |

- Conclusão: a execução só recebe o computador quando é disparada pelo agendador ou por uma sessão já ligada a ele. O acionamento direto a partir da página não recebe.
- Solução adotada: o botão **agenda** a tarefa para o minuto seguinte (`update_trigger` com `run_once_at`), e o mensageiro lê o pedido no banco. Custo: 1 a 2 minutos a mais de espera. O roteiro do mensageiro foi atualizado e reassinado pelo app desktop, e a página da PoC foi republicada com essa mudança.
- Falta: um clique do Diego na página para confirmar o caminho completo.

## 2026-09-30 — PoC do botão: acesso às pastas liberado

- Depois que o Diego liberou o acesso no app desktop, a execução de 04:03 (UTC) fez todos os passos **sem pedir aprovação**:
  - gravou `automacao\poc\pedido_poc.json`;
  - leu `ultima_atualizacao.json` (2.208 bytes);
  - enviou um arquivo à página (123 bytes);
  - gravou o resultado no banco.
- Tempo de execução: 4 min 17 s na primeira vez que as pastas foram usadas.
- **Em aberto:** essa execução chegou **sem o pedido** (`sem-pedido`). Não dá para saber se o clique na página às 04:00:49 acionou a tarefa, porque ela também pode ter sido rodada manualmente pelo app.
- A página da PoC passou a gravar o resultado do acionamento (`poc/disparo`), para que o próximo clique seja conclusivo.
- Teste pelo celular adiado por decisão do Diego.

## 2026-09-29 — PoC do botão Atualizar (Fase 5.0): primeiros resultados

- Montado:
  - página de teste "PoC Botão Atualizar" (artefato separado, sem mexer no painel), com um botão que dispara a tarefa pelo conector Claude Code Remote;
  - tarefa agendada "PoC Mensageiro do painel" (ligada ao computador, aprovação automática, sem horário: só por disparo).
- Os dois testes foram disparados pelo Claude:

| Critério | Resultado |
|---|---|
| Disparo da tarefa pelo conector | ok |
| A tarefa começa no computador | ok · ~55 s depois do disparo |
| Grava o resultado no banco da página | ok · ~70 s de ponta a ponta |
| Grava ou lê na pasta `automacao` | **falhou**: a execução da tarefa não recebeu nenhuma pasta conectada (lista vazia), mesmo com as 3 pastas declaradas na tarefa |
| Envia um arquivo à página | não testado (o roteiro parou no passo da pasta) |
| Disparo pelo botão da página no navegador e no celular | pendente (teste do Diego) |

- Bloqueio atual: o acesso às pastas nas execuções da tarefa. A 1ª versão da tarefa foi criada sem pastas; foi recriada com elas, e a execução continuou sem acesso. Próximo passo: o Diego confere no app desktop se há uma aprovação pendente de pastas para a tarefa e repete o teste pelo botão da página.

## 2026-09-29 — Botão "Atualizar tudo": decisões e revisão do plano

- Decisões do Diego:
  1. as execuções agendadas contam para a hibernação;
  2. depois de uma falha, o botão libera em 15 min;
  3. o botão precisa funcionar também no navegador e no celular;
  4. o Agendador continua.
- Por causa da decisão 3, o caminho principal passa a ser o **B**:
  - o botão dispara uma tarefa agendada do Claude ("mensageiro"), que grava um pedido na pasta `automacao\`;
  - um **vigia do Windows** (a cada 5 min) roda o `atualizar_bases.ps1`;
  - o mensageiro carrega as bases no painel.
- O MCP local (caminho A) vira otimização opcional para o desktop.
- Por causa da decisão 1, toda execução agendada também precisa chegar ao painel. O mensageiro faz uma **coleta** às 07:50 e às 12:50.
- Efeito colateral a decidir: com execuções às 07:30 e às 12:30, o botão só libera depois de ~17:30.
- Tempo esperado pelo botão: ~10–15 min. Próximo passo: provas de conceito da Fase 5.0.

## 2026-09-29 — Viabilidade do botão "Atualizar tudo" (hibernação de 5 h)

- Pedido: um botão no painel que roda as duas extrações, regrava as planilhas, carrega o painel e depois hiberna por pelo menos 5 h.
- Conclusão: **viável pelo caminho A**. O painel chama um **MCP local** no computador do Diego (`host:atualizador-painel`), que dispara o `atualizar_bases.ps1` e devolve as bases compactadas para o painel carregar. Leva cerca de 2 a 3 min e não gasta tokens.
- Limites: funciona só para o **dono do painel (Diego)**, **no app Claude para desktop**, com o computador ligado e na rede da empresa ou VPN. Para os demais, o botão mostra o status e a contagem da hibernação.
- Descartados:
  - nuvem, por causa do 403 do Painel de Serviços e da regra das credenciais;
  - pedido pelo OneDrive, porque o conector é só leitura.
- Tarefa agendada do Claude acionada pelo painel (caminho B) fica como opção futura para acionar do navegador ou do celular.
- Hibernação em 3 camadas: painel, MCP local (fonte da verdade, `estado_botao.json`) e trava contra execução simultânea com o Agendador.
- Próximo passo: prova de conceito (Fase 5.0), que é bloqueante. Plano em `automacao/PLANEJAMENTO_BOTAO_ATUALIZAR.md`.

## 2026-09-29 — Squad Dados: esforço pela média real por subcategoria

- Decisões do Diego:
  - Os tickets de Dados passam a valer a **média real da sua subcategoria**. A média usa os tickets concluídos nos últimos 60 dias que têm horas apontadas, é **recalculada a cada carga** e vale em **todo o painel** (S&OP geral, S&OP por squad, Diagnóstico e Plano de Ação).
  - **Mínimo de 1 h por ticket** daqui para frente. Por isso Migrações passa de 0,7 h para 1 h.
  - "Importação de Dados e Documentos" conta como **Importação de anexos**.
  - Ativação continua em 1 h, o padrão.
- Subcategorias de Dados: Importação de dados, Importação de anexos, Scripts e Migrações, pela ordem subtipo → tags → assunto. Uma subcategoria com menos de 3 tickets na janela usa o valor da Configuração (10 h).
- Esforço com as bases de 29/09: Importação de dados 12,3 h · Importação de anexos 3,4 h · Scripts 2,9 h · Migrações 1,0 h. A média ponderada pelas entradas é de cerca de 4,8 h por ticket.
- Novo quadro no squad Dados, **Saldo de horas por subcategoria**, com backlog, saldo (total e ativo), entradas e horas de entrada por subcategoria.

| | Backlog total | Backlog ativo |
|---|---|---|
| Saldo de Dados no backlog | 585 h | 308 h |
| Entradas de Dados | 330 h/mês | 330 h/mês |
| Squad Dados, saldo em 3 meses | −848 h · 4,3 pessoas | −571 h · 3,6 pessoas |
| S&OP geral, saldo em 3 meses | −1.359 h · 7,7 pessoas | −850 h · 6,3 pessoas |
| Plano de Ação, contratar após as alavancas | ~1,8 pessoa | ~1,0 pessoa |

- Leitura: só as entradas de Dados (330 h/mês) já passam da capacidade do squad (cerca de 242 h/mês). **Importação de dados** é 63% dessas horas (209 h/mês) e 73% do saldo do backlog de Dados (428 h). É ali que o kit de importação e o reforço do squad fazem diferença.

## 2026-09-29 — S&OP refeito: esforço padrão 1 h / 10 h, cenários backlog total × ativo

- Decisão do Diego: o esforço padrão fica **1 h por ativação e 10 h por ticket de dados** (editável em Configuração). O esforço real apontado deixa de ser cenário do S&OP; fica só como referência de calibração (abas Horas e Plano de Ação).
- Backlog: cada ticket vale o esforço padrão do tipo **menos as horas já apontadas** nele.
- Capacidade: mantida em capacidade do Painel de Serviços × 85% (cerca de 484 h/mês nos 3 meses do horizonte, 121 h por pessoa).
- Novos cenários, aplicados no S&OP geral, no S&OP por squad, no Diagnóstico e no Plano de Ação:
  - **Backlog total**: os 794 tickets abertos.
  - **Backlog ativo**: 367 tickets. Saem os 427 que estão aguardando o cliente ou a validação dele, suspensos, com fornecedor ou cancelados.
- Novo quadro no S&OP geral, **Leitura da capacidade (por mês)**, que mostra a capacidade contra as entradas, antes do backlog.
- Resultado (horizonte de 3 meses):

| | Backlog total | Backlog ativo |
|---|---|---|
| Backlog (h) | 1.611 | 828 |
| Entradas (h/mês) | 937 | 937 |
| Saldo em 3 meses | −2.969 h | −2.186 h |
| Pessoas necessárias | 12,2 | 10,0 |
| Squad Dados (2 pessoas) | −2.458 h · 8,8 pessoas | −1.907 h · 7,3 pessoas |
| Squad Ativação (2 pessoas) | −511 h · 3,4 pessoas | −279 h · 2,8 pessoas |

- Leitura: só as **entradas de Dados** (68,7 tickets/mês × 10 h = 687 h) já passam da capacidade inteira do time (484 h). Com 1 h / 10 h, o backlog cresce mesmo com o backlog zerado. Ativação cabe com folga no squad (250 h de entrada contra 363 h de capacidade); o gargalo é Dados.
- Plano de Ação: déficit de 990 h/mês no backlog total (contratar cerca de 5,8 pessoas depois das alavancas) e de 729 h/mês no backlog ativo (cerca de 4,7 pessoas). No cenário ativo, a alavanca "encerrar por inatividade" não conta, porque esses tickets já estão fora da demanda.

## 2026-09-29 — Painel: quadro "Análise real" no Plano de Ação

- Novo quadro no topo da aba **Plano de Ação**: esforço médio real por tipo de demanda, com base nos tickets **concluídos (resolvidos ou fechados) nos últimos 60 dias** (31/07 a 29/09) e nas horas apontadas no Painel de Serviços (todos os analistas).
- Dados subdividido em **Importações, Migrações e Scripts** (subtipo → tags → assunto; "script" > "migra" > "import/anexo/carga de dados").
- Média calculada só sobre tickets com horas apontadas (a cobertura aparece na tabela). Comparado ao racional padrão (Ativação 1 h, Dados 10 h).
- Resultado com as bases de 29/09:

| Demanda | Concluídos | Com horas | Média | Mediana | 75% até |
|---|---|---|---|---|---|
| Ativação | 202 | 134 | 1,05 h | 0,79 h | 1,25 h |
| Dados (total) | 50 | 44 | 4,14 h | 2,08 h | 4,17 h |
| ↳ Importações | 25 | 23 | 6,49 h | 3,08 h | 6,17 h |
| ↳ Migrações | 16 | 13 | 0,72 h | 0,50 h | 0,67 h |
| ↳ Scripts | 9 | 8 | 2,94 h | 2,12 h | 4,08 h |

- Leitura: Ativação confirma o racional de 1 h. Dados fica bem abaixo das 10 h. Migrações com 0,7 h sugere que o esforço de migração é apontado fora do ticket (projeto ou atividade interna); precisa ser confirmado antes de calibrar.

## AAAA-MM-DD — título curto
**Contexto:** …  **Decisão/Resultado:** …  **Impacto:** …  **Pendências:** …
```

---

## 2026-09-29 — Painel: aba "Plano de Ação"

**Pedido:** analisar as principais demandas e responder:
- o que automatizar para destravar a fila;
- o que mais onera em horas por demanda;
- como balancear o time;
- como estabilizar com o menor investimento.

**Conteúdo da aba** (calculada a cada carga das bases):
- **Alavancas com ganho em h/mês e % do déficit coberto**, ordenadas por
  investimento:
  - encerramento por inatividade dos tickets aguardando o cliente há mais de
    30 dias;
  - −25% de horas internas;
  - automação das ativações padronizáveis (−60%);
  - kit de importação de dados (−30%);
  - contratação só para o déficit residual.
- **Volume por subtipo** (candidatos a automação), **peso por demanda** (h por
  ticket concluído) e **onde vão as horas**.
- **Balanceamento:** horas por tipo de cada analista e a divisão ideal do time
  pela demanda.
- **Outras análises:** fila parada, fragmentação dos apontamentos, 1ª resposta,
  reaberturas, entradas sem subtipo.
- **Premissas editáveis** (percentuais e dias de inatividade), salvas em
  `cfg/params.plano`.

**Principais achados** (meses de referência jun–ago):
- **Volume:** Ativação de Serviços (~77 tickets/mês), sem subtipo (~75/mês),
  Manutenção (~28/mês) e Criação de Tenant (~19/mês).
  - O Painel registra ~600 apontamentos/mês de Ativação de Serviços, de ~13 min
    cada: trabalho fragmentado e repetitivo.
- **Peso por ticket:** Importação de Dados (média 7,8 h; mediana 3,1 h),
  Importação de Documentos (3,3 h) e Importação de Dados e Documentos (3,1 h).
  Scripts ficam em 1,9 h.
- **Horas internas ou sem ticket:** ~102 h/mês (~20% das horas do time).
- **Fila parada:** 251 tickets aguardam o cliente há mais de 30 dias.
- **Balanceamento:**
  - Giovanni e Rodrigo são quase 100% de um tipo;
  - Matheus é híbrido (~449 h em Ativação e ~119 h em Dados em jun–ago);
  - Marcelo atua em Dados, com ~79 h em Ativação.
- **Estabilização:**
  - com esforço real, déficit de ~133 h/mês, coberto sem contratar por
    fila + horas internas + automação de ativações;
  - com esforço padrão (1 h / 10 h), déficit de ~990 h/mês: as ações cobrem ~30%
    e faltariam ~5,8 pessoas.
  - A decisão de contratar depende de calibrar o esforço de Dados.

## 2026-09-29 — Painel: S&OP geral + S&OP por squad

**Pedido do Diego:** manter o S&OP geral (todos os tickets × todos os analistas)
e criar a aba **"S&OP por squad"**, com um planejamento por tipo de demanda:
um para Dados e outro para Ativação, com 2 analistas em cada squad.

**Composição padrão** (editável em Configuração → Squads):
- **Squad Dados:** Marcelo e Giovanni;
- **Squad Ativação:** Matheus e Rodrigo.

O critério foi o histórico: Marcelo e Giovanni concentram as importações e os
scripts; Matheus e Rodrigo, as ativações de serviço. **A confirmar com o Diego.**

**Cálculo por squad:**
- capacidade dos 2 analistas × tempo produtivo;
- demanda = todo o backlog do tipo, qualquer que seja o responsável, mais as
  entradas mensais do tipo × esforço;
- a aba mostra quanto do backlog está com o outro squad ou sem responsável, e o
  "foco" (parcela das horas do squad gasta no próprio tipo).

**Resultado em 3 meses** (capacidade de ~726 h por squad):

| Squad | Esforço padrão | Esforço real |
|---|---|---|
| Dados | faltam 2.458 h (≈8,8 pessoas) | faltam 85 h (≈2,2 pessoas; zera o backlog em ~4,5 meses) |
| Ativação | faltam 511 h (≈3,4 pessoas) | faltam 313 h (≈2,9 pessoas; zera em ~13,5 meses) |

## 2026-09-29 — Painel v1 publicado

**Artefato:** "Painel Serviços Técnicos" (claude.ai), privado até ser
compartilhado. Segue o modelo "Customizações & Estratégia", com banco próprio e
o design system Projuris.

**Abas:**
- **Visão geral:** backlog, entradas × saídas, saldo do fluxo, ocupação, saldo
  do S&OP.
- **Diagnóstico da operação:** veredito "o time dá conta?" e achados automáticos
  sobre fila, concentração, dependência do cliente, apontamento atrasado e
  qualidade dos dados.
- **Backlog:** filtros, tipo e regra por ticket, horas já apontadas, link para o
  Freshdesk, CSV.
- **Time:** por analista: backlog Dados/Ativação, idade, horas × capacidade,
  produtividade do fechamento, carga em meses.
- **Horas:** esforço real por ticket concluído, horas por tipo e atividade,
  tickets com mais horas.
- **S&OP:** dois cenários lado a lado, esforço padrão × esforço real.
- **Configuração:** parâmetros, time, carga das bases e regras.

**Dados:**
- As duas bases foram carregadas como arquivos do artefato (tickets de
  29/09 05:56 e horas de 29/09 13:13).
- O banco guarda os ponteiros (`cfg/bases`) e os parâmetros (`cfg/params`).
- Só quem pode editar o painel altera parâmetros e carrega bases; quem só
  visualiza lê.

**Classificação Dados × Ativação** (aplicada no painel):
- 430 tickets de Dados e 1.942 de Ativação;
- no backlog, 145 Dados e 649 Ativação;
- 670 tickets foram classificados pelo Assunto, porque não têm subtipo.

**Primeiros números** (meses de referência jun–ago; set/26 com apontamento
atrasado, 25 h de 588 h):
- **Esforço real por ticket concluído:** Ativação média 0,85 h (mediana 0,67 h);
  Dados média 2,7 h (mediana 0,92 h; 75% até 3,1 h). O padrão de 10 h para
  Dados está bem acima do observado.
- **Fluxo:** entram ~319 tickets/mês e saem ~384 (média jun–ago, puxada pelas
  627 saídas de junho). Em agosto entraram 243 e saíram 142: o backlog cresceu.
- **Capacidade produtiva do time:** ~500 h/mês (4 pessoas × capacidade do Painel
  × 85%).
- **S&OP 3 meses:**
  - com esforço padrão, faltam ~2.970 h (≈12 pessoas necessárias);
  - com esforço real, faltam ~400 h (≈5,1 pessoas para 4 no time).
- **Fila:** Matheus e Rodrigo concentram 78% do backlog; 48% dos tickets
  aguardam o cliente; 83 estão sem responsável ativo; 320 estão parados há mais
  de 30 dias.

**Pendências:**
- calibrar o esforço de Dados;
- carga automática das bases no painel depois de cada execução agendada (hoje é
  pelo botão em Configuração, ou pelo Claude);
- confirmar se os apontamentos só existem a partir de junho.

## 2026-09-29 — Agendamento instalado e primeira execução automática

- Tarefas criadas no Agendador do Windows:
  - "Painel Serviços Técnicos - Atualizar bases": dias úteis às 07:30 e 12:30;
  - "… (semanal full)": segundas às 07:15.
- A primeira instalação falhou por um erro no `agendar_atualizacao.ps1`
  (verificação antes de definir a variável). Corrigido; o script agora para com
  mensagem clara e confere se as duas tarefas foram criadas.
- **Teste às 13:12:**
  - tickets **pulados** (a base já era de hoje, 05:57), como previsto;
  - horas **ok** em 64 s: 6.372 apontamentos, 0 consultas negadas;
  - gerou pela primeira vez o `horas_apontadas_2026_painel.json` (4,9 MB).
- Ajustes no `atualizar_bases.ps1`, na mesma data:
  - a saída do Python ia parar dentro do `ultima_atualizacao.json` e os acentos
    saíam quebrados no log;
  - agora a saída vai só para o log, em UTF-8, e o JSON traz apenas
    status/detalhe.

## 2026-09-29 — Horas extraídas e validadas; automação das extrações

**Execução** (no computador do Diego, 12:59): 6.372 apontamentos, 5.518 h, 14
analistas, 2 áreas (Serviços e Integração), 250 chamadas, 86 s, **nenhuma
consulta sem permissão**. As 13 abas saíram completas.

**Validação:**
- Total da API = linhas extraídas = IDs únicos (6.372); todos confirmados.
- **Agosto:** os 1.379 apontamentos da planilha de referência estão todos na
  extração, com as mesmas durações (0 divergências). A área Serviços em agosto
  soma 1.380 apontamentos e 1.154,4 h, iguais à referência mais 1 lançamento
  posterior. A diferença para o total do mês (1.669) é a área Integração.
- **Os apontamentos começam em junho/2026** (jun 2.382 · jul 2.219 · ago 1.669 ·
  set 102 até agora). Não há dado de jan–mai: provavelmente o Painel de
  Serviços entrou em uso em junho. **A confirmar.** A visão do ano de horas cobre
  jun–set.
- **Cruzamento com os tickets pelo `ticket_id`** (área Serviços):
  - 4.959 dos 5.440 apontamentos têm ticket (3.240 h com ticket, 620 h sem);
  - 1.267 tickets distintos, dos quais **1.140 estão na base de Serviços
    Técnicos** (1.630 h);
  - os 127 restantes são de outros grupos ou já arquivados pelo Freshdesk.
- A área **Serviços** tem 9 analistas no Painel. O **time do painel** é Matheus,
  Rodrigo, Marcelo e Giovanni. Lucas Schwartz, Marina, Renan e Wallef aparecem
  na mesma área (provavelmente ADV). O Andrei tem 273 h apontadas no período e
  sai das análises.

**Mudanças:**
- **JSON compacto para o painel:** `horas_apontadas_<ANO>_painel.json` (~4,8 MB).
  O JSON completo tem 21,7 MB, e 75% disso é o texto HTML dos trâmites. A
  planilha e o JSON completo continuam com todos os campos.
- **Automação:** `automacao\atualizar_bases.ps1` roda tickets (pula se já rodou
  no dia) e horas, e grava `ultima_atualizacao.json` + log.
  `automacao\agendar_atualizacao.ps1` cria as tarefas no Agendador do Windows:
  dias úteis às 07:30 e 12:30, e toda segunda às 07:15 uma extração completa de
  tickets. O Claude acompanha lendo `ultima_atualizacao.json`.

## 2026-09-29 — Horas: API do Painel bloqueia acesso fora da rede da empresa

**Contexto:** o MCP `painel-servicos` foi copiado para `mcp_server\`. Ele tem
URL base `https://servicos.projuris.com.br` e token Bearer no `.env`, com as
variáveis `PAINEL_SERVICOS_BASE_URL` e `PAINEL_SERVICOS_TOKEN`.

**Resultado:** da nuvem da sessão, o servidor responde **403 do nginx em
qualquer rota**, até na raiz e com o token válido. Ou seja, o acesso é restrito
por origem de rede (IP ou VPN), não por permissão. A cópia do token foi apagada
da nuvem.

**Decisões:**
- A extração de horas **roda no computador do Diego**, que tem acesso ao Painel.
- O script passou a ler o mesmo `.env` do MCP (`mcp_server\.env`) e aceita
  `PAINEL_SERVICOS_BASE_URL`.
- O `.venv` do MCP painel-servicos não tem `openpyxl`, então a extração usa o
  `.venv` do projeto Freshdesk, que tem httpx, python-dotenv e openpyxl.

## 2026-09-29 — Regras do painel v1 (decisões do Diego)

**Modelo:** o portal "Customizações & Estratégia" é a base do painel, com as
adaptações abaixo.

**Classificação de demanda (nova):** todo ticket é **Dados** ou **Ativação**.
- **Dados** quando o **Subtipo** ou as **Tags** falam de importação (de dados, de
  anexos/documentos, ou só "importação"), migração ou scripts.
- Se Subtipo e Tags não tiverem informação, a análise usa o **Assunto** por
  último, porque é descritivo e menos preciso.
- Todo o resto é **Ativação**.
- A regra usada fica registrada por ticket (subtipo, tags ou assunto), para
  auditoria.

**Esforço padrão para a S&OP**, editável no painel: Ativação ≈ 1 h e Dados ≈
10 h por ticket. Depois será calibrado com as horas apontadas.

**Aba nova "Diagnóstico da operação":**
- fila e saúde do time;
- análises das extrações;
- a pergunta central: **o time atual dá conta da demanda ou é preciso trazer
  mais gente?**

**Time atual:** Matheus Soares, Rodrigo Meireles, Marcelo Marta e Giovanni
Ferreira.
- **Andrei Rhoden saiu do time** e não aparece mais nas análises. Os tickets
  abertos no nome dele entram como "sem responsável ativo" (a redistribuir).

**Carga dos dados:** botão de carga no painel. Os JSONs das bases vão para o
banco do artefato; a automação vem depois, com a tarefa agendada.

**Sequência:** primeiro extrair e validar as horas; só depois construir o painel.
Bloqueio atual: falta copiar o MCP `painel-servicos` (URL + token) para
`MCP Painel de Serviços\mcp_server\`.

## 2026-09-29 — Horas apontadas: fonte, script e chave de ligação

**Fonte definida:** Painel de Serviços v2 (API REST), a mesma do MCP
`painel-servicos`. O código do MCP foi movido para
`%USERPROFILE%\.claude\mcp-servers\painel-servicos\`, pasta protegida que não
pode ser liberada para o Claude. O MCP também não está registrado no app Claude
desktop. A configuração (URL + token) precisa ir para o `.env` da pasta
`MCP Painel de Serviços`.

**Decisões do Diego:**
- Visão do ano, com todos os campos da API.
- Sem rascunhos.
- Com capacidade, fechamento, calendário, disponibilidade e férias.
- Usuários: o Diego e o painel.
- Validação na nuvem, como na extração de tickets.

**Chave de ligação:** o número do ticket liga as duas bases. Na base de tickets é
a coluna `ID do ticket`; na planilha de apontamentos é o número do ticket (campo
`ticket_id` da API — o campo `id` é o identificador do próprio apontamento; a
confirmar com o Diego). Toda análise horas × tickets usa essa chave. Um ticket
pode ter vários apontamentos, e há apontamentos sem ticket.

**Resultado:**
- `scripts\extracao_horas_apontadas.py` criado e testado offline com a API
  simulada: paginação, remoção de duplicados, fallback de rota sem permissão e
  todas as abas.
- Gravados na pasta: `.env.example` e `requirements.txt`.

**Pendência:** URL + token para a validação real.

**Extração de tickets:** a base foi gerada hoje às 05:57, então não roda de novo
(regra combinada). As planilhas antigas de Backlog e Concluídos foram salvas às
08:39 e 09:42 sem registro de execução no `registry.jsonl`. Provavelmente foram
abertas e salvas no Excel; não são uma nova extração.

## 2026-09-29 — Descoberta: o Freshdesk arquiva tickets Closed

**Contexto:** "Concluídos por Ano" caiu de 1.579 (25/09) para 437 (28/09) sem
mudança de filtro que explicasse a diferença.

**Resultado:**
- A busca e a listagem do Freshdesk devolvem hoje **523** tickets Closed no
  grupo com fechamento em 2026 (438 sem o Projuris ADV). O script estava certo;
  o dado mudou.
- Encontrado o motivo: tickets Closed são **arquivados**. Eles somem de
  `/tickets` e de `/search/tickets` e só respondem em `/tickets/archived/{id}`.
- Evidência: IDs de janeiro/2026 ausentes da base (ex.: 212055, 212057,
  212060–212067) retornam como arquivados, com status Closed.
- Na base atual quase não há fechamentos anteriores a abril/2026.

**Impacto:**
- **Concluídos no ano** e **Novo no ano** subcontam os tickets já arquivados.
  Estimativa: pelo menos ~1.100 fechamentos de 2026 arquivados.
- O **estado incremental** passa a ser o guardião do histórico: um ticket
  fechado entra no estado antes de ser arquivado e nunca é removido de lá. Por
  isso o `--full` foi ajustado para **não apagar** o estado.

**Pendências:**
- Decidir se vale uma **recuperação única** dos arquivados de 2026. Não há
  listagem de arquivados: seria preciso testar ID por ID (~34 mil IDs, ~3 h de
  API compartilhada) ou usar uma exportação da interface do Freshdesk.
- Confirmar com o administrador a regra de arquivamento (após quantos dias).

## 2026-09-29 — Extração única e incremental criada e validada

**Decisão:** trocar os 3 presets do `backlog_servicos.py` por uma base única
(`extracao_servicos_tecnicos.py`), com recortes em colunas. As 3 planilhas
antigas deixam de ser atualizadas (escolha do Diego: "só a base única").

**Mudanças:**
- Fonte trocada da busca (+ 1 chamada por ticket) para a listagem com `stats` e
  `requester` embutidos.
- Colunas novas: **Data do Fechamento** (`closed_at`), **Data da Resolução**
  (`resolved_at`), Status desde, Reaberto em, Prioridade, Tipo e ID da empresa.

**Validação** (execução na nuvem da sessão, com a chave do `.env`, autorizada pelo Diego):

| Recorte | Estado | Busca Freshdesk | Sem Projuris ADV | Planilha antiga (28/09) |
|---|---|---|---|---|
| Backlog | 860 | 860 ✅ | 794 | 798 (6 resolvidos/fechados desde então, 2 novos) |
| Novo no ano | 2.264 | 2.264 ✅ | 2.073 | 2.072 (todos os IDs antigos presentes) |
| Concluído no ano (Closed) | 523 | 523 ✅ | 438 | 437 (todos os IDs antigos presentes) |
| Resolvido no ano | 1.195 | 1.195 ✅ | 1.140 | — (novo) |

**Desempenho:**
- Completa: 15,6 min e 213 chamadas de listagem (21.300 tickets do helpdesk
  vistos; 2.582 do grupo). Antes, ~50 min e ~3.400 chamadas.
- Incremental: 10 s sem mudanças; 37 s e 9 chamadas para uma janela de 1 dia.
- Base: 2.372 linhas; JSON de ~1 MB.

**Teste de lógica:** um ticket que sai do grupo volta na listagem com outro
`group_id` e sai dos recortes (teste offline ok).

## 2026-09-29 — Estrutura de documentação criada

Pasta `Painel de Gestão\Serviços Técnicos\` passa a ser a casa do projeto:
`MAPA.md` (entrada), `PLANEJAMENTO.md` (fases), `LOG.md` (este arquivo) e
`extracao\PLANEJAMENTO_EXTRACAO.md` (técnico). Toda a documentação fica
centralizada aqui, por escolha do Diego.

## 2026-09-29 — Arquitetura de dados: script + arquivo, não MCP

**Contexto:** comparação de custo entre alimentar o painel via MCP do Freshdesk
e via script.

**Decisão:** script. Uma busca de 30 tickets pelo MCP custou ~390 mil
caracteres (~3 mil tokens por ticket); o backlog inteiro custaria ~2,5 milhões
de tokens por atualização, contra poucos milhares via script. O MCP fica para
consultas pontuais.

## 2026-09-28 — Análise do portal modelo e protótipo visual

- Portal "Customizações & Estratégia" analisado: app publicado com banco
  próprio, sincronização por tarefa agendada, escrita no Jira, S&OP de
  capacidade × demanda.
- Protótipo do dashboard de backlog feito no canvas de Design, com design system
  Projuris e dados de 28/09 (678 de 797 linhas lidas pelo conector do
  SharePoint).

## 2026-09-24 a 28 — Histórico anterior (presets no `backlog_servicos.py`)

Registrado em `freshdesk_mcp\docs\freshdesk_api_reference.md`, §9:

- Backlog validado com 795 tickets (24/09).
- Concluídos: só Closed, 1.581 tickets (25/09).
- Novos Tickets por Ano (28/09).
- Unificação dos presets em 4 chaves declarativas (28/09).
