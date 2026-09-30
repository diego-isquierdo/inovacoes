# Painel de Gestão · Serviços Técnicos

Portal vivo do time de Serviços Técnicos: grupo **SRV TECNICO** do Freshdesk, sem o produto Projuris ADV.

**Comece por [`MAPA.md`](MAPA.md)**, que diz onde está cada coisa. O andamento está em [`PLANEJAMENTO.md`](PLANEJAMENTO.md) e as decisões datadas em [`LOG.md`](LOG.md).

## Como funciona

```
Freshdesk API ─────────► extracao_servicos_tecnicos.py ──┐                         ┌─► Painel (artefato claude.ai)
Painel de Serviços API ─► extracao_horas_apontadas.py ───┼─► bases JSON/XLSX ──────►│   abas: Visão geral, Diagnóstico,
                          (computador do Diego, rede      │   + manifesto.json       │   Backlog, Time, Horas, S&OP geral,
                           da empresa)                    │                          │   S&OP por squad, Plano de Ação
Agendador do Windows ── atualizar_bases.ps1 ──────────────┘   Mensageiro (tarefa ────┘
Botão "Atualizar" ─► Mensageiro ─► pedido ─► vigia_pedidos.ps1    agendada do Claude)
```

- **Extração**: os scripts rodam no computador do Diego, porque o Painel de Serviços só aceita a rede da empresa. As credenciais ficam nos `.env` locais.
- **Automação** (`automacao/`): o Agendador roda às 07:30 e 12:30 nos dias úteis e às 07:15 na segunda (completo). O vigia atende o botão a cada 5 min.
- **Mensageiro**: tarefa agendada do Claude que leva o pedido do botão ao computador e carrega as bases no painel. Coleta às 07:50 e 12:50. O roteiro está em [`automacao/mensageiro_prompt.md`](automacao/mensageiro_prompt.md) e as tarefas estão descritas em [`tarefas/`](tarefas/).
- **Painel** (`painel/painel_v1.html`): fonte do artefato "Painel Serviços Técnicos". Os dados ficam no banco do artefato (`cfg/*`) e nos arquivos carregados.

## Estrutura desta pasta

| Pasta | Conteúdo | Onde roda de verdade |
|---|---|---|
| `/` | MAPA, PLANEJAMENTO, LOG | `OneDrive…\Inovações\Painel de Gestão\Serviços Técnicos\` |
| `extracao/` | Planejamento técnico das extrações | idem, `extracao\` |
| `extracao/scripts/tickets/` | Cópia de `extracao_servicos_tecnicos.py` e do README dos scripts | `MCP - Fresk\freshdesk_mcp\scripts\` (depende de `lib/`, `client.py` e `backlog_servicos.py` do projeto freshdesk_mcp) |
| `extracao/scripts/horas/` | Cópia de `extracao_horas_apontadas.py`, `requirements.txt` e `.env.example` | `MCP Painel de Serviços\scripts\` |
| `automacao/` | Scripts do Windows, roteiro do mensageiro, PoC do botão, planejamento do botão | `…\Serviços Técnicos\automacao\` |
| `painel/` | Fonte HTML do painel | artefato no claude.ai |
| `tarefas/` | Definição das tarefas agendadas do Claude | claude.ai (tarefas agendadas) |
| `ferramentas/` | `sincronizar_repo.ps1`: copia as versões em uso para um clone deste repositório | computador do Diego |

Como versionar: ver [`VERSIONAMENTO.md`](VERSIONAMENTO.md).
