# Versionamento — plano e rotina

> Criado em 30/09/2026. Repositório: https://github.com/diego-isquierdo/inovacoes · pasta `painel-servicos-tecnicos/`.

## O que foi planejado

1. **Um repositório, uma pasta por projeto.** `inovacoes` é o repositório de todos os projetos de inovação. O painel é o primeiro "sub-repositório" (a pasta `painel-servicos-tecnicos/`). Projetos futuros entram como pastas irmãs.
2. **A pasta espelha o projeto em uso.** A estrutura repete a de `Painel de Gestão\Serviços Técnicos` (MAPA, PLANEJAMENTO, LOG, `extracao/`, `automacao/`, `painel/`), então os links relativos funcionam nos dois lugares. Os scripts Python que vivem em outros projetos entram como cópia em `extracao/scripts/`.
3. **Só código e documentação.** Nunca entram `.env`, tokens, bases, planilhas, logs, estados de execução nem pedidos. O `.gitignore` da raiz bloqueia esses arquivos e o `sincronizar_repo.ps1` nem os copia.
4. **Scripts do Windows byte a byte.** `.ps1` e `.vbs` ficam como rodam (CRLF, e BOM nos `.ps1`), via `.gitattributes`.
5. **Versões por etiqueta.** Cada marco do painel recebe uma etiqueta `painel-st-vX.Y.Z` (ver a tabela abaixo).

## De onde vem cada arquivo

| No repositório (`painel-servicos-tecnicos/…`) | Origem no computador (`%USERPROFILE%\OneDrive - Starian\Projuris\Diego\Inovações\…`) |
|---|---|
| `MAPA.md`, `PLANEJAMENTO.md`, `LOG.md` | `Painel de Gestão\Serviços Técnicos\` |
| `extracao/*.md` | `Painel de Gestão\Serviços Técnicos\extracao\` |
| `automacao/*.ps1`, `*.vbs`, `*.md`, `poc/poc_botao.html` | `Painel de Gestão\Serviços Técnicos\automacao\` |
| `painel/painel_v1.html` | `Painel de Gestão\Serviços Técnicos\painel\` (fonte do artefato) |
| `extracao/scripts/tickets/extracao_servicos_tecnicos.py` | `MCP - Fresk\freshdesk_mcp\scripts\` |
| `extracao/scripts/tickets/README_scripts_freshdesk.md` | `MCP - Fresk\freshdesk_mcp\scripts\README.md` |
| `extracao/scripts/horas/*` | `MCP Painel de Serviços\scripts\extracao_horas_apontadas.py`, `requirements.txt`, `.env.example` |
| `README.md`, `VERSIONAMENTO.md`, `tarefas/`, `ferramentas/` | só no repositório |

## Rotina para uma nova versão

**Pelo Claude** (com o repositório autorizado na sessão): ele copia as versões em uso, atualiza o LOG, faz o commit, cria a etiqueta e envia.

**Pelo computador** (com o git instalado e um clone local):

```powershell
cd "$env:USERPROFILE\OneDrive - Starian\Projuris\Diego\Inovações\Painel de Gestão\Serviços Técnicos"
powershell -NoProfile -ExecutionPolicy Bypass -File .\ferramentas\sincronizar_repo.ps1 -Clone "C:\git\inovacoes" -Mensagem "painel: <o que mudou>"
```

O script copia os arquivos da tabela acima para o clone, mostra o `git status` e faz o commit. O envio (`git push`) fica por sua conta.

## Versões

| Etiqueta | Data | Conteúdo |
|---|---|---|
| `painel-st-v0.5.0` | 30/09/2026 | Primeira versão versionada: extrações validadas, automação no Windows (Agendador + vigia), painel com 9 abas (S&OP geral, S&OP por squad, Plano de Ação com Análise real), PoC do botão validada, mensageiro e coleta criados (falta liberar as pastas das tarefas e validar o clique real) |
