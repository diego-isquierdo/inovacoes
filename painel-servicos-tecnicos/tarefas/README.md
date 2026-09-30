# Tarefas agendadas do Claude

Criadas pelo Claude (Cowork) em 30/09/2026. Todas estão **ligadas ao computador do Diego** (SOFT009125), rodam com **aprovação automática** e têm acesso a estas pastas:

- `…\Inovações\Painel de Gestão\Serviços Técnicos`
- `…\Inovações\MCP - Fresk\freshdesk_mcp\scripts\output\Serviços Técnicos`
- `…\Inovações\MCP Painel de Serviços`

| Tarefa | Id | Quando roda | Roteiro |
|---|---|---|---|
| Mensageiro do painel (botão Atualizar) | `trig_014VFMUxsPSn9JeGY2GDfNpk` | Sem horário. O botão do painel agenda para o minuto seguinte (`update_trigger` + `run_once_at`) | [`../automacao/mensageiro_prompt.md`](../automacao/mensageiro_prompt.md) |
| Coleta do painel (após o Agendador) | `trig_01RreKZegbVLgyEGU2Bozw2k` | `CRON_TZ=America/Sao_Paulo 50 7,12 * * 1-5` (dias úteis, 07:50 e 12:50) | o mesmo roteiro |
| PoC Mensageiro do painel | `trig_0149eLyeDbX3fJkvkgpw7wMp` | Só por disparo. **Temporária**: apagar depois da validação da Fase 5 | teste (página "PoC Botão Atualizar") |

## Por que o botão agenda em vez de disparar

A PoC de 30/09 mostrou que uma execução disparada direto pela página (`fire_trigger`) roda **sem** o computador. As execuções iniciadas pelo agendador recebem o computador. Por isso o botão agenda a tarefa para o minuto seguinte, e o mensageiro lê o pedido no banco do painel (ver LOG 30/09).

## Banco do painel usado pelas tarefas

| Documento | Quem grava | Conteúdo |
|---|---|---|
| `cfg/mensageiro` | Claude (instalação) | `trigger_id` do mensageiro e da coleta |
| `cfg/atualizacao` | página (pedido) e mensageiro (andamento) | status, etapa, origem, pedido_id, último sucesso, `proximo_liberado_em` |
| `cfg/bases` | mensageiro (ou upload manual) | arquivos carregados: asset, gerado_em, linhas, sha256 |

Ao mudar um roteiro, atualize `automacao/mensageiro_prompt.md` e a tarefa correspondente (a mudança precisa ser aprovada pelo app desktop ligado ao computador).
