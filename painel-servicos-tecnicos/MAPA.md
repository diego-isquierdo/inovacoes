# Painel de Gestão · Serviços Técnicos — Mapa do projeto

> Ponto de entrada do projeto. Leia este arquivo primeiro: ele aponta para o
> planejamento, o log de decisões e a documentação técnica de cada fonte.
> Mantenha-o curto; os detalhes ficam nos arquivos linkados.
> Última atualização: 30/09/2026.

## Objetivo

Construir um **portal vivo** de gestão do time de Serviços Técnicos (grupo
`SRV TECNICO` do Freshdesk, sem o produto Projuris ADV), no mesmo modelo do
portal "Customizações & Estratégia":

- dados atualizados automaticamente;
- visão de saúde da operação;
- capacidade do time;
- depois, uma **S&OP** (vazão × capacidade real, com as horas apontadas).

## Onde está cada coisa

| O quê | Onde | Observação |
|---|---|---|
| Este mapa, planejamento e log | `Painel de Gestão\Serviços Técnicos\` | Documentação do projeto (sem dado de cliente) |
| Planejamento geral (fases) | [`PLANEJAMENTO.md`](PLANEJAMENTO.md) | Status de cada fase e próximos passos |
| Log de decisões e execuções | [`LOG.md`](LOG.md) | Diário datado: o que foi decidido, por quê e com que resultado |
| **Tickets** — planejamento técnico | [`extracao/PLANEJAMENTO_EXTRACAO.md`](extracao/PLANEJAMENTO_EXTRACAO.md) | Fonte, regras dos recortes, incremental, validação |
| **Tickets** — script | `MCP - Fresk\freshdesk_mcp\scripts\extracao_servicos_tecnicos.py` | Roda no computador do Diego (`.env` e `.venv` do projeto MCP Freshdesk) |
| **Tickets** — base gerada | `MCP - Fresk\freshdesk_mcp\scripts\output\Serviços Técnicos\` | `Base de Serviços Técnicos.xlsx` + `base_servicos_tecnicos.json` |
| **Tickets** — estado incremental | `MCP - Fresk\freshdesk_mcp\scripts\cache\servicos_tecnicos\estado.json` | Todos os tickets do grupo já vistos; preserva os fechados que o Freshdesk arquiva |
| **Horas** — planejamento técnico | [`extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](extracao/PLANEJAMENTO_EXTRACAO_HORAS.md) | Fonte (Painel de Serviços v2), abas, validação |
| **Horas** — script | `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py` | Configuração no `.env` dessa pasta (URL + token do Painel) |
| **Horas** — base gerada | `MCP Painel de Serviços\output\` | `Horas Apontadas <ANO>.xlsx` + `horas_apontadas_<ANO>.json` (completo) + `horas_apontadas_<ANO>_painel.json` (carga do painel) |
| **Automação** das duas extrações | [`automacao\`](automacao/LEIA-ME.md) | `atualizar_bases.ps1` (roda tudo), `agendar_atualizacao.ps1` (Agendador do Windows), `ultima_atualizacao.json` (status) |
| **Botão "Atualizar tudo"** — viabilidade e plano | [`automacao/PLANEJAMENTO_BOTAO_ATUALIZAR.md`](automacao/PLANEJAMENTO_BOTAO_ATUALIZAR.md) | Painel → tarefa agendada do Claude → vigia do Windows → extrações → carga; hibernação de 5 h (planejado) |
| Histórico técnico de execuções | `scripts\registry.jsonl` e `scripts\logs\` de cada projeto | Uma linha por execução (metadados, nunca dado de cliente) |
| Referência da API Freshdesk | `MCP - Fresk\freshdesk_mcp\docs\freshdesk_api_reference.md` | Campos, IDs, limitações (inclui o arquivamento de tickets Closed) |
| Referência da API do Painel de Serviços | `MCP Painel de Serviços\OpenAI.json` (OpenAPI 3.1) e skill `integrar-painel-servicos-projuris` | Contratos de apontamentos, relatórios, capacidade, calendário |
| MCP do Painel de Serviços | `%USERPROFILE%\.claude\mcp-servers\painel-servicos\` (cópia em `MCP Painel de Serviços\mcp_server\`) | O `.env` da cópia é usado pela extração de horas |
| **Painel (v1)** | Artefato "Painel Serviços Técnicos" (claude.ai) · fonte em [`painel/painel_v1.html`](painel/painel_v1.html) | Bases carregadas como arquivos do artefato; parâmetros e time no banco (`cfg/params`, `cfg/bases`) |
| **Melhorias de indicadores (Fase 7)** | [`MAPA_MELHORIAS_INDICADORES.md`](MAPA_MELHORIAS_INDICADORES.md) | SLA por tipo, forecast, carteira por analista, planejamento semanal, priorização, visão executiva (planejado) |
| **Tarefas agendadas do Claude** | Mensageiro (botão) e Coleta (07:50/12:50) · ver [`tarefas/README.md`](tarefas/README.md) no repositório | Roteiro em [`automacao/mensageiro_prompt.md`](automacao/mensageiro_prompt.md) |
| **Versionamento (GitHub)** | https://github.com/diego-isquierdo/inovacoes · pasta `painel-servicos-tecnicos/` | Só código e documentação; nunca `.env`, bases, planilhas ou logs. **Versionamento manual pelo Diego, só depois de validar** (decisão de 30/09). Rotina em [`VERSIONAMENTO.md`](VERSIONAMENTO.md) |
| Protótipo visual (canvas) | Artefato "Dashboard · Backlog de Serviços Técnicos" (claude.ai) | Estudo de layout com dados estáticos de 28/09; não é o painel final |
| Modelo de referência | Artefato "Customizações & Estratégia" (claude.ai) | Portal vivo com banco, sincronização agendada e S&OP |

## Fontes de dados

| Fonte | Conteúdo | Situação |
|---|---|---|
| Freshdesk (API v2) | Tickets do grupo SRV TECNICO: status, agente, subtipo, datas (criação, resolução, fechamento), 1ª resposta | **Pronta**: extração única e incremental validada (29/09) |
| Painel de Serviços v2 (API) | Horas apontadas por analista e ticket, capacidade, fechamento mensal, calendário, férias | **Pronta**: validada em 29/09. Dados a partir de jun/2026. Só acessível da rede da empresa |
| Equipe e ausências | Jornada, férias, ausências | Parcialmente coberto pelo Painel de Serviços (capacidade, calendário, férias) |

## Chave de ligação entre as bases: número do ticket

As duas bases se ligam pelo **número do ticket do Freshdesk**:

| Base | Coluna com o número do ticket |
|---|---|
| Tickets (`Base de Serviços Técnicos`) | **ID do ticket** |
| Horas (`Horas Apontadas <ANO>`, aba Apontamentos) | **`ticket_id`** (texto; a API chama de `id` o identificador do próprio apontamento) |

- Um ticket pode ter **vários apontamentos** (vários analistas e dias), e há
  apontamentos **sem ticket** (atividades internas).
- A ligação analista ↔ agente do Freshdesk sai da aba **Membros**
  (`freshdesk_agent_id`).

Toda análise que cruze horas e tickets usa essa chave. Ver LOG 29/09.

## Fluxo de dados (alvo)

```
Freshdesk API ─────────► extracao_servicos_tecnicos.py ─► estado.json ─► base_servicos_tecnicos.json ─┐
Painel de Serviços API ─► extracao_horas_apontadas.py ─────────────────► horas_apontadas_<ANO>.json ──┼─► painel (banco do artefato)
                          (ambos no computador do Diego)            chave: número do ticket ───────────┘
```

Princípio: **os dados nunca passam pela conversa com o Claude**. Os scripts
extraem e gravam arquivos, e o painel carrega os arquivos. Os MCPs (Freshdesk e
Painel de Serviços) ficam só para consultas pontuais. Ver LOG 29/09/2026.

## Rotina de atualização (combinada em 29/09)

- **Tickets:** se a base já foi gerada no dia, não rodar de novo. A execução
  incremental é barata (segundos) e pode rodar várias vezes; o `--full` roda
  1× por semana.
- **Horas:** extração do ano inteiro a cada execução (~1,5 min).
- **Automação:** `automacao\atualizar_bases.ps1`, agendada no Windows em dias úteis às 07:30 e 12:30 (segundas 07:15 completo).
- **Botão "Atualizar" (Fase 5):** painel → tarefa "Mensageiro" (agendada para o minuto seguinte) → `pedido_atualizacao.json` → vigia do Windows (a cada 5 min, 07:00–22:00) → `atualizar_bases.ps1` → mensageiro carrega as bases no painel. Hibernação: 5 h após sucesso (botão ou Agendador), 15 min após falha. A "Coleta" das 07:50/12:50 carrega no painel o que o Agendador gerou.
- **Time do painel:** Matheus, Rodrigo, Marcelo e Giovanni (Andrei fora).
