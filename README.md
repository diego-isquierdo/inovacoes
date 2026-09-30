# Inovações

Projetos de inovação e automação do Diego Isquierdo (Starian · Projuris).
Cada projeto fica em uma pasta própria na raiz deste repositório.

| Projeto | Pasta | O que é |
|---|---|---|
| Painel de Gestão · Serviços Técnicos | [`painel-servicos-tecnicos/`](painel-servicos-tecnicos/) | Portal vivo do time de Serviços Técnicos: extração de tickets (Freshdesk) e horas (Painel de Serviços), automação no Windows, painel com S&OP e botão "Atualizar" |

## Regras do repositório

- **Nada de segredos**: `.env`, tokens e chaves ficam só no computador (ver `.gitignore`). Cada projeto traz um `.env.example`.
- **Nada de dados de clientes**: bases geradas, planilhas, logs e estados de execução não são versionados.
- Cada projeto tem um `MAPA.md` (ponto de entrada), um `PLANEJAMENTO.md` (fases e status) e um `LOG.md` (decisões datadas).
