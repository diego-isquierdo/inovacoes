# Painel de Gestão · Serviços ADV

Portal vivo do time de Serviços ADV: grupo **SRV TECNICO** do Freshdesk, **somente** o produto Projuris ADV — o recorte espelhado do time de Serviços Técnicos (que usa o mesmo grupo, excluindo esse produto).

Este projeto é construído **nos mesmos moldes** do [`Painel de Gestão · Serviços Técnicos`](../Serviços%20Técnicos/README.md), reaproveitando arquitetura, scripts e decisões já validadas ali. Em caso de dúvida sobre como algo funciona, o projeto Técnico é a referência.

**Comece por [`MAPA.md`](MAPA.md)**, que diz onde está (ou vai estar) cada coisa. O andamento está em [`PLANEJAMENTO.md`](PLANEJAMENTO.md) e as decisões datadas em [`LOG.md`](LOG.md).

## Como funciona (alvo — ver Fase 0 no planejamento)

```
Freshdesk API ─────────► extracao_servicos_adv.py ────┐                         ┌─► Painel (artefato claude.ai)
Painel de Serviços API ─► extracao_horas_apontadas.py ─┼─► bases JSON/XLSX ──────►│   abas: a definir a partir do
                          (computador do Diego, rede   │   + manifesto.json       │   modelo do time Técnico
                           da empresa)                  │                          │
Agendador do Windows ── atualizar_bases.ps1 ────────────┘   Mensageiro (tarefa ────┘
Botão "Atualizar" ─► Mensageiro ─► pedido ─► vigia_pedidos.ps1    agendada do Claude)
```

- **Extração**: mesma arquitetura do time Técnico — scripts rodam no computador do Diego (rede da empresa), credenciais em `.env` locais. A definir: script próprio (`extracao_servicos_adv.py`) ou parâmetro de filtro no script existente.
- **Horas apontadas**: mesma fonte (Painel de Serviços v2). A definir: como isolar os apontamentos do time ADV (por área, por analista, ou por ticket cruzado).
- **Automação e Painel**: a construir seguindo o padrão de `automacao/` e `painel/` do projeto Técnico, depois que a extração estiver validada.

## Time

Renan, Marina, Lucas e Wallef — time único, sem divisão em squads (nesta primeira versão).

## Estrutura desta pasta

Nesta primeira etapa só a documentação de planejamento foi criada. As subpastas abaixo serão criadas quando cada fase avançar, seguindo o padrão do projeto Técnico:

| Pasta (futura) | Conteúdo | Modelo (Serviços Técnicos) |
|---|---|---|
| `extracao/` | Planejamento técnico das extrações | [`extracao/PLANEJAMENTO_EXTRACAO.md`](../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO.md), [`extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`](../Serviços%20Técnicos/extracao/PLANEJAMENTO_EXTRACAO_HORAS.md) |
| `automacao/` | Scripts do Windows, roteiro do mensageiro | [`automacao/`](../Serviços%20Técnicos/automacao/) |
| `painel/` | Fonte HTML do painel | [`painel/painel_v1.html`](../Serviços%20Técnicos/painel/painel_v1.html) |
| `tarefas/` | Definição das tarefas agendadas do Claude | [`tarefas/`](../Serviços%20Técnicos/tarefas/) |
| `ferramentas/` | Scripts de apoio (ex.: sincronizar repositório) | [`ferramentas/`](../Serviços%20Técnicos/ferramentas/) |
| `orquestrador/` | Atualizações em lote no Freshdesk (fase futura) | [`orquestrador/`](../Serviços%20Técnicos/orquestrador/) |

Versionamento: a definir se este projeto entra no mesmo repositório `diego-isquierdo/inovacoes` (pasta própria, análoga a `painel-servicos-tecnicos/`) — ver [`VERSIONAMENTO.md`](../Serviços%20Técnicos/VERSIONAMENTO.md) do projeto Técnico como referência.
