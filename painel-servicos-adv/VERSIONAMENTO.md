# Versionamento — plano e rotina

> Criado em 02/10/2026. Repositório: https://github.com/diego-isquierdo/inovacoes · pasta `painel-servicos-adv/`.

## O que foi planejado

1. **Mesmo repositório do time Técnico, pasta irmã.** `inovacoes` continua sendo o repositório de todos os projetos de inovação; `painel-servicos-adv/` é a segunda pasta de projeto, ao lado de `painel-servicos-tecnicos/`.
2. **A pasta espelha o projeto em uso.** Estrutura igual à de `Painel de Gestão\Serviços ADV` (MAPA, PLANEJAMENTO, LOG, `painel/`, `automacao/`, `extracao/scripts/tickets/`), para os links relativos funcionarem nos dois lugares.
3. **Só código e documentação.** Nunca entram `.env`, tokens, bases, planilhas, logs ou estados de execução — mesmo `.gitignore` da raiz do repositório (bloqueia `**/output/`, `**/cache/`, `*.xlsx`, `**/horas_apontadas_*.json` etc.) já cobre os arquivos deste projeto.
4. **Diferença deliberada em relação ao time Técnico**: lá, o versionamento é manual — "o Claude não faz commits" (decisão do Diego, 30/09/2026, registrada em `painel-servicos-tecnicos/VERSIONAMENTO.md`). Para o ADV, o Diego pediu explicitamente, em 02/10/2026, que o Claude registrasse as alterações e fizesse o commit e o push neste repositório. Essa autorização vale para este pedido; não assume commits automáticos em pedidos futuros sem confirmação.

## De onde vem cada arquivo

| No repositório (`painel-servicos-adv/…`) | Origem no computador (`%USERPROFILE%\OneDrive - Starian\Projuris\Diego\Inovações\…`) |
|---|---|
| `MAPA.md`, `PLANEJAMENTO.md`, `LOG.md`, `README.md`, `VERSIONAMENTO.md` | `Painel de Gestão\Serviços ADV\` |
| `automacao\atualizar_tickets.ps1`, `agendar_atualizacao.ps1` | `Painel de Gestão\Serviços ADV\automacao\` |
| `painel\painel_v1.html` | `Painel de Gestão\Serviços ADV\painel\` (fonte do artefato publicado) |
| `extracao\scripts\tickets\extracao_servicos_adv.py` | `MCP - Fresk\freshdesk_mcp\scripts\` (mesmo projeto Freshdesk do time Técnico; script próprio, filtro de produto invertido) |

A extração de horas **não tem script próprio** neste projeto (reaproveita integralmente `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py`, já versionado em `painel-servicos-tecnicos/extracao/scripts/horas/`) — por isso não é copiada de novo aqui.

## Artefato publicado

Painel: https://claude.ai/artifact/NNthAUZKErRTB1FG7myfwW ("Painel Serviços ADV"). Bases carregadas via upload de assets no próprio artefato (sem botão "Atualizar" nem Mensageiro nesta primeira versão).

## Versões

| Data | Conteúdo |
|---|---|
| 02/10/2026 | Primeiro commit: Fases 0–3 do planejamento (filtro de escopo, extração de tickets validada, fonte de horas confirmada sem script próprio, painel publicado com 10 abas e motor de 6 categorias de demanda) e Fase 4 (S&OP com simulação mês a mês de 90%, quadro de eficiência e quadro "Projeção viva" até 12 meses) |
