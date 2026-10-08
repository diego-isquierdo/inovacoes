# Painel de Gestão · Integrações

Portal vivo do time de **Integrações** (grupo `INTEGRACOES` do Freshdesk; área "Integração" do Painel de Serviços), construído nos mesmos moldes do [`Serviços ADV`](../Serviços%20ADV/README.md) e do [`Serviços Técnicos`](../Serviços%20Técnicos/README.md), com ajustes para demandas de projeto, suporte, consultoria e bugs.

Comece por [`MAPA.md`](MAPA.md). Andamento em [`PLANEJAMENTO.md`](PLANEJAMENTO.md); decisões datadas em [`LOG.md`](LOG.md).

```
Freshdesk API ──────────► extracao_integracoes.py ─┐                ┌─► Painel (artefato claude.ai)
Painel de Serviços API ─► extracao_horas_apontadas.py ─┼─► bases JSON/XLSX ─►│
                          (computador do Diego)    │   + manifesto
Agendador do Windows ── atualizar_bases.ps1 ───────┘
```

Status: **planejamento** (07/10/2026). Nenhum script ou painel criado ainda.
