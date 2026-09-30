# Botão "Atualizar tudo" — viabilidade e mapa de execução

> Criado em 29/09/2026 e revisto no mesmo dia com as decisões do Diego (§10).
> Status: **planejado, não iniciado**. Registre o andamento em [`../LOG.md`](../LOG.md)
> e marque as fases em [`../PLANEJAMENTO.md`](../PLANEJAMENTO.md) (Fase 5).

## 1. O que se pede

Um botão **Atualizar** no painel que:

1. roda as duas extrações, Freshdesk (tickets) e Painel de Serviços (horas);
2. regrava as planilhas das extrações (`Base de Serviços Técnicos.xlsx`, `Horas Apontadas <ANO>.xlsx`) e os JSON;
3. carrega as bases novas no painel, e todas as abas se recalculam;
4. depois disso **hiberna por no mínimo 5 horas**;
5. funciona do **app desktop, do navegador e do celular** (decisão 3).

O **Agendador do Windows continua** (07:30 e 12:30 nos dias úteis, e o completo na segunda às 07:15), e **cada execução agendada também conta para a hibernação** (decisão 1). Por isso, toda execução, do botão ou do Agendador, precisa terminar com o painel carregado.

## 2. Restrições que decidem a arquitetura

| Fato | Consequência |
|---|---|
| A API do Painel de Serviços só responde da rede da empresa (403 fora dela, LOG 29/09) | As extrações **rodam no computador do Diego**, pelo `atualizar_bases.ps1`, como hoje. |
| As credenciais ficam só nos `.env` do computador | Nada de extração na nuvem ou no navegador. |
| O painel é uma página do claude.ai e não enxerga o computador | Precisa de um intermediário. |
| O painel pode chamar o conector **Claude Code Remote** (disparar uma tarefa agendada) de qualquer dispositivo | O botão funciona no navegador e no celular: ele **dispara uma tarefa agendada do Claude**. |
| Uma tarefa agendada do Claude, ligada ao computador, consegue gravar arquivos na pasta conectada, ler os arquivos gerados, enviar arquivos ao painel e gravar no banco do painel | Essa tarefa faz o papel de **mensageiro**: leva o pedido ao computador e traz as bases para o painel. |
| O Windows executa bem o `.ps1`; o ambiente de comandos do Claude no computador é Linux e não roda o `.ps1` | Quem **executa** é o Windows: um vigia do Agendador olha a cada 5 min se existe um pedido. |

## 3. Caminhos avaliados

| # | Caminho | Situação |
|---|---|---|
| **B** | **Botão → tarefa agendada do Claude ("mensageiro") → pedido na pasta → vigia do Windows roda o `.ps1` → mensageiro carrega as bases no painel** | **Escolhido.** Funciona de qualquer dispositivo e cobre também as execuções agendadas. |
| A | Botão → MCP local no computador (só no app desktop) | Fica como **otimização futura** (5.5): é mais rápido e não gasta tokens, mas não atende navegador e celular. |
| C | Pedido gravado no OneDrive pelo painel | Descartado: o conector Microsoft 365 é só leitura. |
| D | Extrações na nuvem | Descartado: 403 do Painel de Serviços e regra das credenciais. |

## 4. Arquitetura alvo (caminho B)

```
 PAINEL (qualquer dispositivo)                    NUVEM (Claude)                        COMPUTADOR DO DIEGO (Windows)
 ─────────────────────────────                    ──────────────                        ─────────────────────────────
 [Atualizar] ─ checa cfg/atualizacao ─┐
   └─ fire_trigger("Mensageiro") ─────┼──► Tarefa "Mensageiro do painel"
                                      │     1. confere a hibernação (cfg/atualizacao)
                                      │     2. grava automacao\pedido_atualizacao.json ───► Vigia (Agendador, a cada 5 min)
                                      │     3. grava cfg/atualizacao = "na fila"               └─ roda atualizar_bases.ps1 -ForcarTickets
                                      │                                                         ├─ extração de tickets (Freshdesk)
                                      │                                                         ├─ extração de horas (Painel de Serviços)
                                      │                                                         ├─ grava planilhas + JSON + manifesto.json
                                      │     4. acompanha manifesto/estado (a cada ~1 min) ◄──────┘
                                      │     5. lê os 2 JSON e envia ao painel (upload)
 painel recalcula ◄── cfg/bases ◄─────┴──── 6. grava cfg/bases e cfg/atualizacao (fim + 5 h)

 Execuções AGENDADAS: o .ps1 roda sozinho às 07:15/07:30/12:30 e grava o manifesto;
 a tarefa "Mensageiro" também é agendada para 07:50 e 12:50, faz só os passos 4–6
 e registra origem = "agendado".
```

## 5. Regra da hibernação (5 horas)

- **Início:** o fim de qualquer execução bem-sucedida (botão ou Agendador).
- **Fim:** o botão volta às `fim + 5 h`.
- **O que ela bloqueia:** **só o botão.** O Agendador sempre roda nos seus horários (decisão 4) e reinicia a contagem.
- **Falha não hiberna:** depois de um erro, o botão libera de novo em **15 min** (decisão 2), e o painel mantém as bases anteriores.
- **Três camadas:**
  1. **Painel:** botão desabilitado com "disponível às HH:MM", lido de `cfg/atualizacao`.
  2. **Mensageiro:** recusa o pedido se a hibernação ainda estiver valendo, mesmo que alguém dispare a tarefa por fora do painel.
  3. **Vigia do Windows:** fonte da verdade, em `automacao\estado_botao.json`. Ignora pedidos dentro das 5 h e usa a trava `automacao\.executando` contra duas execuções ao mesmo tempo (a trava vence em 30 min).
- **Estados do botão:** `Disponível` · `Na fila (até 5 min)` · `Atualizando… (etapa)` · `Carregando no painel` · `Hibernando até HH:MM` · `Falhou: motivo — nova tentativa às HH:MM`.

> **Efeito prático da decisão 1.** Com execuções às 07:30 e 12:30 (5 h entre elas), o botão fica em hibernação durante quase todo o horário comercial. Ele libera de **~17:30 até 07:30 do dia seguinte** e depois de qualquer falha do agendamento. Se o botão precisar estar disponível à tarde, a opção é tirar a execução das 12:30 do Agendador e deixar a da tarde para o botão.

## 6. O que construir

| # | Peça | Onde | Detalhe |
|---|---|---|---|
| 1 | **Vigia do Windows** | `automacao\vigia_pedidos.ps1` + nova tarefa no `agendar_atualizacao.ps1` | A cada 5 min, de 07:00 às 22:00: se existir `pedido_atualizacao.json` válido, fora da hibernação e sem trava, roda `atualizar_bases.ps1 -ForcarTickets -Origem botao` e apaga o pedido (renomeia para `pedido_atendido_*.json`). |
| 2 | **Ajustes no `atualizar_bases.ps1`** | `automacao\` | `-Origem botao\|agendado`; cria e remove a trava; grava `estado_botao.json` (início, fim, etapa, resultado, origem) e `manifesto.json` (caminho, tamanho, SHA-256 e `gerado_em` de cada base). Corrige o `ultima_atualizacao.json`: o de 29/09 às 13:12 ainda saiu com a saída do Python misturada, gerado antes da correção. |
| 3 | **Tarefa agendada "Mensageiro do painel"** | tarefa agendada do Claude, ligada ao computador | Um único roteiro fixo, com dois modos: **pedido** (acionada pelo botão: passos 1–6) e **coleta** (07:50 e 12:50 nos dias úteis e 07:35 na segunda: passos 4–6). Não lê o conteúdo das bases para a conversa; só transfere os arquivos. Precisa de **aprovação automática** nas configurações da tarefa, porque roda sem ninguém para aprovar. |
| 4 | **Botão no painel** | `painel\painel_v1.html` | Botão no cabeçalho com os estados; capacidade `mcp` com o servidor **Claude Code Remote** e a ferramenta `fire_trigger`; leitura ao vivo de `cfg/atualizacao`; tratamento de erros (sem permissão, conector ausente, falha da tarefa). |
| 5 | **Documento `cfg/atualizacao`** | banco do painel | `{status, etapa, origem, pedido_em, ultimo_inicio, ultimo_fim, resultado, detalhe, proximo_liberado_em}`. Todos leem, só o Diego grava. |
| 6 | **Documentação** | `automacao\LEIA-ME.md`, `MAPA.md`, `LOG.md` | Instalação, teste, como desligar e como aprovar a tarefa. |

## 7. Fases e critérios de aceite

| Fase | Entrega | Aceite |
|---|---|---|
| **5.0 Provas de conceito** (bloqueante) | (a) o painel dispara uma tarefa de teste pelo **Claude Code Remote**, no navegador e no celular; (b) uma tarefa agendada grava um arquivo na pasta `automacao\`, lê o `manifesto.json` e envia um arquivo de teste ao painel, sem pedir aprovação | Os dois funcionam de ponta a ponta. Anotar o tempo de disparo e o consumo de tokens de uma execução do mensageiro. |
| 5.1 Windows | Vigia + ajustes no `.ps1` (trava, estado, manifesto, origem) | Um pedido gravado à mão é atendido em até 5 min. Um 2º pedido dentro das 5 h é ignorado. Durante a execução, a trava impede o Agendador de rodar em paralelo. |
| 5.2 Mensageiro | Tarefa com os modos pedido e coleta | Depois de uma execução, `cfg/bases` aponta para os arquivos novos, os antigos são removidos e `cfg/atualizacao` fica com `proximo_liberado_em` = fim + 5 h. A coleta das 07:50 carrega a base das 07:30. |
| 5.3 Botão | Estados, contagem, mensagens de erro | Clique no celular → "Na fila" → "Atualizando" → abas recalculadas em ~10–15 min → "Hibernando até HH:MM". Com falha simulada, libera em 15 min. |
| 5.4 Validação | Comparação com a carga manual | Mesmos totais (tickets, apontamentos, horas) do manifesto, hash confere e log registrado. |
| 5.5 (opcional) Atalho no desktop | MCP local (caminho A) | Só se o tempo de ~10–15 min incomodar. |

## 8. Tempo esperado

| Etapa | Tempo |
|---|---|
| Disparo da tarefa + gravação do pedido | ~1–2 min |
| Espera do vigia | até 5 min |
| Tickets incremental + horas do ano | ~1,5–2 min (29/09: horas em 62,9 s) |
| Coleta, envio das bases e gravação no banco | ~2–4 min |
| **Total pelo botão** | **~10–15 min** |

O `--full` semanal (~15 min) continua só no Agendador. O botão nunca dispara o completo.

## 9. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Computador desligado, app desktop fechado ou fora da rede | O mensageiro não consegue gravar o pedido e marca "Falhou: computador indisponível" (libera em 15 min). |
| A tarefa para esperando uma aprovação | Ligar a aprovação automática na tarefa; a fase 5.0 confirma. |
| Custo de tokens por execução (botão + 2 coletas por dia) | Roteiro curto e fixo, sem ler dados para a conversa. Medir na 5.0 e, se pesar, reduzir as coletas ou adotar o caminho A no desktop. |
| Extração falha no meio | O painel mantém as bases anteriores, mostra o erro e não hiberna. |
| Pedido duplicado (dois cliques, dois dispositivos) | O painel grava "na fila" antes de disparar, e o vigia atende um pedido por vez. |
| Dados de clientes trafegando | Os mesmos arquivos que já vão para o painel hoje, transferidos como arquivos, sem passar pela conversa. Credenciais seguem no `.env`. |

## 10. Decisões do Diego (29/09/2026)

1. **As execuções agendadas contam para a hibernação: sim.** Toda execução agendada é carregada no painel pela coleta do mensageiro.
2. **Depois de uma falha, liberar em 15 min: sim.**
3. **Acionar fora do app desktop (navegador e celular): sim.** Por isso o caminho B é o principal.
4. **O Agendador continua** nos horários atuais e nunca é bloqueado pela hibernação.

**Em aberto:** a execução das 12:30 fica ou sai? Ver o efeito prático no §5.
