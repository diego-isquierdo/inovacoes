# Versionamento — Painel de Gestão · Integrações

Repositório: https://github.com/diego-isquierdo/inovacoes · pasta `painel-integracoes/` (irmã de `painel-servicos-tecnicos/` e `painel-servicos-adv/`).

**Quem versiona:** o Claude faz o commit e o push **somente quando o Diego pedir** (decisão de 07/10/2026). Primeiro envio: 08/10/2026.

## De onde vem cada arquivo

| No repositório (`painel-integracoes/…`) | Origem (`%USERPROFILE%\OneDrive - Starian\Projuris\Diego\Inovações\…`) |
|---|---|
| `README.md`, `MAPA.md`, `PLANEJAMENTO.md`, `LOG.md`, `VERSIONAMENTO.md` | `Painel de Gestão\Integrações\` |
| `extracao/*.md` | `Painel de Gestão\Integrações\extracao\` |
| `extracao/scripts/tickets/extracao_integracoes.py` | `MCP - Fresk\freshdesk_mcp\scripts\` |
| `automacao/*.ps1` | `Painel de Gestão\Integrações\automacao\` |
| `ferramentas/*.py` | `Painel de Gestão\Integrações\ferramentas\` |
| `painel/painel_v1.html`, `painel/partes/`, `painel/montar.sh`, `painel/teste_node.js` | `Painel de Gestão\Integrações\painel\` |

A extração de horas reaproveita `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py` (já versionado em outro projeto).

## O que nunca entra

`.env`, tokens, chaves, bases JSON/XLSX, snapshots, logs, `ultima_atualizacao.json`, `manifesto_integracoes.json`, `painel_teste.html` (gerado). O `.gitignore` da raiz bloqueia esses arquivos; nomes de clientes são trocados por `<cliente>` nos documentos.

## Painel

`painel_v1.html` é montado de `painel/partes/` por `painel/montar.sh` (gera também `painel_teste.html`, só para o teste). `node painel/teste_node.js <pasta das bases>` valida o motor contra as bases reais antes de cada publicação.
