# Painel de Gestão · Serviços ADV — Mapa do projeto

> Ponto de entrada do projeto. Leia este arquivo primeiro: ele aponta para o
> planejamento, o log de decisões e a documentação técnica de cada fonte.
> Mantenha-o curto; os detalhes ficam nos arquivos linkados.
> Última atualização: 02/10/2026 (painel publicado, S&OP revisado, versionamento).

## Objetivo

Construir um **portal vivo** de gestão do time de Serviços ADV (grupo
`SRV TECNICO` do Freshdesk, **somente** produto Projuris ADV), nos mesmos
moldes do [`Painel de Gestão · Serviços Técnicos`](../Serviços%20Técnicos/MAPA.md):

- dados atualizados automaticamente;
- visão de saúde da operação;
- capacidade do time;
- depois, uma **S&OP** (vazão × capacidade real, com as horas apontadas).

Este projeto reaproveita a arquitetura já validada no projeto Técnico. Sempre
que uma decisão técnica não estiver registrada aqui, ela segue por padrão o que
foi decidido lá (ver `MAPA.md`, `PLANEJAMENTO.md` e `LOG.md` do projeto Técnico).

## Onde está (ou vai estar) cada coisa

| O quê | Onde | Observação |
|---|---|---|
| Este mapa, planejamento e log | `Painel de Gestão\Serviços ADV\` | Documentação do projeto (sem dado de cliente) |
| Planejamento geral (fases) | [`PLANEJAMENTO.md`](PLANEJAMENTO.md) | Status de cada fase e próximos passos |
| Log de decisões e execuções | [`LOG.md`](LOG.md) | Diário datado: o que foi decidido, por quê e com que resultado |
| **Tickets** — planejamento técnico | ⏳ a criar (`extracao/PLANEJAMENTO_EXTRACAO.md`) | Modelo: [`Serviços Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md`](../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md) |
| **Tickets** — script | ✅ criado e validado: `extracao_servicos_adv.py` em `MCP - Fresk\freshdesk_mcp\scripts\` | Cópia adaptada do script do time Técnico, com o filtro de produto invertido (ver Fonte de dados) |
| **Tickets** — base gerada | ✅ `scripts\output\Serviços ADV\` (gerada em 01/10/2026) | `Base de Serviços ADV.xlsx` + `base_servicos_adv.json` — 212 tickets (Backlog 71 · Novo no ano 197 · Concluído no ano 86 · Resolvido no ano 55) |
| **Tickets** — estado incremental | ✅ `scripts\cache\servicos_adv\estado.json` | Preserva fechados que o Freshdesk arquiva, como no time Técnico |
| **Horas** — planejamento técnico | ⏳ a criar (`extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`) | Modelo: [`Serviços Técnicos/extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO_HORAS.md) |
| **Horas** — script | ✅ **nenhum script novo necessário** — reaproveita integralmente `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py` e a base já gerada para o time Técnico | O script não filtra por time (traz todas as áreas/analistas/ano); a separação ADV × Técnico é feita na carga do painel, por lista de analistas — ver seção "Time e ligação com o Freshdesk" |
| **Automação** das extrações | ✅ tickets agendados (seg-sex 20h); horas sem automação própria (reaproveita a do time Técnico) | `automacao\atualizar_tickets.ps1` + `automacao\agendar_atualizacao.ps1` |
| **Painel** | ✅ publicado: artefato "Painel Serviços ADV" | https://claude.ai/artifact/NNthAUZKErRTB1FG7myfwW · fonte em [`painel/painel_v1.html`](painel/painel_v1.html) |
| **Tarefas agendadas do Claude** | ⏳ a definir (própria tarefa ou reaproveitar o Mensageiro do time Técnico) | Sem botão "Atualizar" ainda — carga das bases é manual (upload de assets no artefato) |
| **Versionamento (GitHub)** | ✅ pasta própria `painel-servicos-adv/` no mesmo repositório | Diferente do time Técnico: aqui o Diego pediu que o Claude faça o commit e o push — ver `Serviços Técnicos/VERSIONAMENTO.md` para o contraste |
| Projeto de referência | [`Painel de Gestão · Serviços Técnicos`](../Serviços%20Técnicos/MAPA.md) | Fonte de todo o padrão arquitetural |

## Fontes de dados

| Fonte | Conteúdo | Situação |
|---|---|---|
| Freshdesk (API v2) | Tickets do grupo SRV TECNICO, **somente** produto Projuris ADV: status, agente, subtipo, datas (criação, resolução, fechamento), 1ª resposta | ⏳ Filtro confirmado (01/10/2026); extração ainda não construída |
| Painel de Serviços v2 (API) | Horas apontadas por analista e ticket, capacidade, fechamento mensal, calendário, férias | ✅ Mesma fonte e mesma base do time Técnico; isolamento do ADV confirmado por lista de analistas (ver abaixo) |
| Equipe e ausências | Jornada, férias, ausências | Parcialmente coberto pelo Painel de Serviços (capacidade, calendário, férias), como no time Técnico |

## Filtro de escopo (confirmado em 01/10/2026)

Espelho exato do filtro do time Técnico, invertendo o critério de produto:

| Time | Grupo Freshdesk | Produto |
|---|---|---|
| Serviços Técnicos | `SRV TECNICO` | **exclui** `Projuris ADV` |
| Serviços ADV | `SRV TECNICO` | **somente** `Projuris ADV` |

Os recortes do ano corrente são os mesmos do time Técnico (ver
[`Serviços Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md`](../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md#1-escopo)):

| Recorte (coluna) | Regra |
|---|---|
| **Backlog** | Status atual não é Closed nem Resolved |
| **Novo no ano** | `created_at` no ano corrente, qualquer status |
| **Concluído no ano** | Status **Closed** e `closed_at` no ano corrente |
| **Resolvido no ano** | Status **Resolved** e `resolved_at` no ano corrente |

Grupo e produto resolvidos **por nome** a cada execução, sem ID fixo no código —
mesmo princípio do script do time Técnico.

## Chave de ligação entre as bases: número do ticket

Mesma chave do projeto Técnico: o **ID do ticket** do Freshdesk liga a base de
tickets à aba Apontamentos da base de horas (`ticket_id`).

## Time e ligação com o Freshdesk (confirmado em 01/10/2026)

Achado importante: no Painel de Serviços só existem **duas áreas** — "Serviços"
(`area_id = 1`) e "Integração" (`area_id = 2`) — e **os times Técnico e ADV
compartilham a mesma área** ("Serviços", 9 membros). Ou seja, **área não separa
os times**; a separação é só pela lista de analistas.

Mapeamento confirmado via `listar_membros` (aba **Membros** da base de horas,
mesma base já extraída para o time Técnico):

| Analista | E-mail | `freshdesk_agent_id` | Time |
|---|---|---|---|
| Renan Miguel Thomas | renan.thomas@starian.com | 158010714338 | **ADV** |
| Marina Cristina Soares Esteves | marina.esteves@starian.com | 158010714324 | **ADV** |
| Lucas Schwartz dos Santos | lucas.santos@starian.com | 158010714315 | **ADV** |
| Wallef Igor Franco Amorim | wallef.amorim@starian.com | 158010863070 | **ADV** |
| Matheus Estrogildo Torres Soares | matheus.soares@starian.com | 158010863080 | Técnico |
| Rodrigo Meireles da Silva | rodrigo.silva@starian.com | 158012514666 | Técnico |
| Marcelo Augusto Barbosa Batista Marta | marcelo.marta@starian.com | 158010714322 | Técnico |
| Giovanni Teixeira Ferreira | giovanni.ferreira@starian.com | 158014851024 | Técnico |
| Andrei Luis Rhoden | andrei.rhoden@starian.com | 158010714323 | (fora dos dois painéis) |

Na carga do painel ADV, a aba **Apontamentos** da base de horas deve ser
filtrada por `analyst_name` (ou `analyst_id`/`freshdesk_agent_id`) pertencente
a este grupo — o mesmo princípio que liga analista ↔ agente no projeto
Técnico, só que usado para filtrar em vez de só exibir.

## Time

Renan, Marina, Lucas e Wallef — time único, sem squads (confirmado em
01/10/2026; a revisitar se o time crescer ou se fizer sentido dividir por tipo
de demanda, como o time Técnico fez na Fase 3).

## Pendências e decisões em aberto

- Tarefas agendadas do Claude / botão "Atualizar": tarefa própria ou
  reaproveitar o "Mensageiro" do time Técnico — hoje a carga das bases no
  painel ADV é manual (upload de assets).
- Validar com o Diego, conforme mais dados entrarem, se os parâmetros do S&OP
  (90% de capacidade reservada ao backlog, metade do Forecast virando fila na
  Projeção viva, meta de 50% da capacidade) continuam adequados.

Essas pendências seguem o mesmo roteiro de perguntas que o time Técnico
resolveu nas Fases 0 a 2 do seu projeto — ver
[`Serviços Técnicos/PLANEJAMENTO.md`](../Serviços%20Técnicos/PLANEJAMENTO.md).
