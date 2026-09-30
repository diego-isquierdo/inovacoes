# Automação das extrações

Os dois scripts desta pasta atualizam as bases do painel **no computador do Diego**. Não dá para rodar na nuvem: o Painel de Serviços só aceita conexões feitas da rede da empresa.

| Arquivo | Para quê |
|---|---|
| `atualizar_bases.ps1` | Roda as duas extrações em sequência e grava o resultado em `ultima_atualizacao.json` e em `logs\` |
| `agendar_atualizacao.ps1` | Cria as tarefas no Agendador de Tarefas do Windows (rodar uma vez) |
| `vigia_pedidos.ps1` + `vigia_oculto.vbs` | Atende o botão **Atualizar** do painel: a cada 5 min, das 07:00 às 22:00, procura `pedido_atualizacao.json` e, se houver, roda a atualização |

**O que cada execução faz:**
1. **Tickets:** extração incremental. Se a base já foi gerada no dia, não roda de novo (regra combinada). Para forçar, use `-ForcarTickets`; para a extração completa, `-TicketsFull`.
2. **Horas:** extração do ano inteiro, cerca de 1,5 minuto.

**Arquivos que cada execução grava nesta pasta:**

| Arquivo | Conteúdo |
|---|---|
| `ultima_atualizacao.json` | Status de cada extração da última execução |
| `estado_botao.json` | Estado para o botão: etapa, resultado, origem (agendado ou botão), último sucesso e **quando o botão volta a ficar disponível** (5 h depois de um sucesso; 15 min depois de uma falha) |
| `manifesto.json` | As bases geradas (caminho, tamanho, SHA-256, data), para a carga no painel |
| `.executando` | Trava enquanto uma atualização roda (some ao terminar; vence em 30 min) |
| `pedidos\` | Histórico dos pedidos do botão (atendido, recusado, falhou, invalido), com os 50 mais recentes |
| `logs\vigia.log` | Uma linha por pedido recebido e o que o vigia fez com ele |

**Instalação (uma vez, no PowerShell):**

```powershell
cd "$env:USERPROFILE\OneDrive - Starian\Projuris\Diego\Inovações\Painel de Gestão\Serviços Técnicos\automacao"
.\agendar_atualizacao.ps1                          # dias úteis às 07:30 e 12:30; segundas também às 07:15 com --full; vigia a cada 5 min
Start-ScheduledTask -TaskName "Painel Serviços Técnicos - Atualizar bases"   # rodar agora, para testar
```

**Como o Claude acompanha:** ele lê `ultima_atualizacao.json` (status de cada extração) e os logs. Assim confere se as bases estão em dia antes de analisar, sem precisar executar nada.
