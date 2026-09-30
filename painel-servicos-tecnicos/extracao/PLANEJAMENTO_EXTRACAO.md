# Extração Freshdesk — Serviços Técnicos (planejamento técnico)

Script: `MCP - Fresk\freshdesk_mcp\scripts\extracao_servicos_tecnicos.py`
Voltar ao [mapa do projeto](../MAPA.md) · [planejamento geral](../PLANEJAMENTO.md) · [log](../LOG.md)

## 1. Escopo

Universo: tickets do grupo **`SRV TECNICO`**, **excluindo o produto `Projuris ADV`**
(mesmo filtro dos presets validados do `backlog_servicos.py`). Grupo e produto são
resolvidos **por nome** a cada execução — nenhum ID fixo no código.

A base guarda um ticket se ele pertence a **pelo menos um** recorte do ano corrente:

| Recorte (coluna) | Regra | Equivale ao antigo preset |
|---|---|---|
| **Backlog** | Status atual não é Closed nem Resolved | "Backlog de Serviços Técnicos" |
| **Novo no ano** | `created_at` no ano corrente, qualquer status | "Novos Tickets por Ano - Serviços Técnicos" |
| **Concluído no ano** | Status **Closed** e `closed_at` no ano corrente | "Concluídos por Ano - Serviços Técnicos" |
| **Resolvido no ano** | Status **Resolved** e `resolved_at` no ano corrente | novo (sem preset antigo) |

Os recortes **se sobrepõem** (um ticket criado e fechado neste ano está em "Novo" e
"Concluído"). Contagens por recorte = filtrar a coluna, nunca somar recortes.

"Ano corrente" é calculado a cada execução (`date.today().year`). O estado guarda o
histórico de anos anteriores, então a virada de ano não perde dados.

## 2. Colunas da base

| Coluna | Origem na API | Novo? |
|---|---|---|
| ID do ticket, Assunto, Status, Agente | `id`, `subject`, `status` (rótulo), `responder_id` → nome via cache de agentes | |
| Hora da criação / da última atualização | `created_at` / `updated_at` | |
| **Status desde** | `stats.status_updated_at` — tempo no status atual | ✅ |
| Tempo de resposta inicial (h) | `stats.first_responded_at − created_at` | |
| **Data da Resolução** | `stats.resolved_at` | ✅ |
| **Data do Fechamento** | `stats.closed_at` | ✅ |
| **Reaberto em** | `stats.reopened_at` | ✅ |
| Tags, Produto, Subtipo | `tags`, `product_id` (rótulo), `cf_subtipo` | |
| **Prioridade, Tipo** | `priority` (rótulo), `type` | ✅ |
| Data Início, Data Fim, Workflow (SE) | `cf_data_incio`, `cf_data_fim`, `cf_workflow_se` | |
| Nome completo, ID de contato | `requester.name`, `requester_id` | |
| **ID da empresa** | `company_id` | ✅ |
| **Backlog, Novo no ano, Concluído no ano, Resolvido no ano** | calculados (seção 1) | ✅ |

"Data Fim" (`cf_data_fim`) é um campo manual quase sempre vazio. A data de
encerramento oficial é **Data do Fechamento** (`closed_at`).

## 3. Como os dados são coletados

### 3.1 Fonte principal: listagem com dados embutidos

`GET /tickets?updated_since=<data>&include=stats,requester&per_page=100&order_by=updated_at&order_type=asc`

- Traz 100 tickets por chamada **já com** `stats` (1ª resposta, resolução,
  fechamento) e `requester` (nome). No script antigo cada ticket exigia uma
  chamada extra (`GET /tickets/{id}`), o que dominava o tempo de execução.
- A listagem não filtra por grupo: percorre o helpdesk inteiro e o grupo é
  filtrado localmente. Em 29/09/2026 são cerca de 21 mil tickets atualizados no
  ano, cerca de 220 chamadas.
- A API recusa `page > 300`. Se uma janela chegar a 300 páginas, o script reabre a
  listagem a partir do último `updated_at` visto e remove duplicatas.

### 3.2 Modo completo (`--full` ou primeira execução)

1. Listagem desde 01/01 do ano corrente (seção 3.1).
2. **Backlog parado desde antes de 01/01:** busca por status não terminal (só
   IDs) e completa um a um o que a listagem não trouxe.
3. **Verificação cruzada** (seção 4).

### 3.3 Modo incremental (padrão quando existe estado)

1. Listagem desde `última sincronização − 15 min` (margem de segurança).
2. Todo ticket que mudou (status, agente, grupo, fechamento) atualiza `updated_at`
   e volta na listagem. Um ticket que **saiu do grupo** volta com outro `group_id`
   e sai dos recortes automaticamente.
3. A verificação cruzada é opcional (`--verify`).

### 3.4 Arquivamento de tickets Closed (limitação da fonte)

O Freshdesk **arquiva** tickets Closed: eles deixam de aparecer em `/tickets` e em
`/search/tickets` e só respondem em `/tickets/archived/{id}`. Não existe listagem
de arquivados. Consequências:

- O estado **nunca apaga** um ticket, nem no `--full`. Quem foi visto fechado
  continua na base depois de arquivado. No `--full`, esses tickets aparecem como
  `preservados_do_estado` no resumo.
- Rodar a extração com frequência (horas, não semanas) garante que todo
  fechamento seja capturado antes do arquivamento.
- Fechamentos arquivados **antes** do estado existir (a maior parte de jan–mar/2026)
  não estão na base. A recuperação está pendente de decisão (ver PLANEJAMENTO).

### 3.5 Estado incremental

`scripts\cache\servicos_tecnicos\estado.json`: todos os tickets do grupo já
vistos (registro compacto, valores brutos) e a data da última sincronização. A
gravação é atômica: uma falha no meio não corrompe o estado anterior. Apagar o
arquivo ou usar `--full` força uma extração completa. É dado de cliente e não é
versionado (`scripts/cache/` está no `.gitignore`).

## 4. Validação

**Automática** (em todo `--full` e com `--verify`). Para cada recorte, compara o
total do estado com o total que a busca do Freshdesk devolve para o mesmo filtro,
no nível do grupo (antes de excluir o produto):

- **Estado menor que a busca:** o script descobre os IDs pela busca e busca um a
  um os que faltavam ou estavam desatualizados.
- **Estado maior que a busca:** registra a diferença. A busca do Freshdesk tem
  imprecisões nas bordas de data (ver LOG 29/09), então a listagem com `stats` é
  tratada como a fonte da verdade.
- O resultado vai para a aba **Execução** da planilha, para o `meta` do JSON e
  para o `registry.jsonl`.

**Manual** (regra de ouro herdada dos presets): um filtro novo só vale depois de
bater o total com o que a interface do Freshdesk mostra.

## 5. Saídas

Na pasta `scripts\output\Serviços Técnicos\`, sobrescritas a cada execução:

| Arquivo | Para quê | Formato |
|---|---|---|
| `Base de Serviços Técnicos.xlsx` | Leitura humana e conferência | Aba **Tickets** (recortes como Sim/Não, com autofiltro) + aba **Execução** (resumo e verificação) |
| `base_servicos_tecnicos.json` | Carga do painel | `{meta, colunas, linhas}`: linhas como listas, sem repetir as chaves (arquivo compacto) |

As três planilhas antigas (Backlog / Novos / Concluídos) **não são mais geradas**
por este fluxo. O `backlog_servicos.py` continua existindo para presets de outros
times.

## 6. Custo e desempenho

| | Script antigo (3 presets) | Extração única — completa | Extração única — incremental |
|---|---|---|---|
| Chamadas à API | ~3.400 (busca + 1 por ticket, × 3 presets) | ~220 de listagem + ~40 de verificação | poucas (tickets alterados desde a última execução) |
| Tempo | ~50 min | ~15 min | ~1–2 min |
| Tokens do Claude | ~0 (fora da conversa) | ~0 | ~0 |

O rate limit (200 requisições/min) é **compartilhado com outras integrações**. O
script pausa 60 s quando restam 8 requisições ou menos e tenta de novo em caso de
erro 429 ou de rede.

## 7. Como rodar

```bash
.venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py            # incremental (completa se não houver estado)
.venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py --verify   # incremental + verificação cruzada
.venv/Scripts/python.exe scripts/extracao_servicos_tecnicos.py --full     # completa + verificação (recomendado 1×/semana)
```

Cadência sugerida: incremental a cada 1–2 h em horário comercial; `--full` uma vez
por semana, para pegar qualquer resíduo que o incremental não veja.

## 8. Próximas evoluções

- Agendamento no computador do Diego (Fase 1, último item).
- Ligação com a fonte de horas apontadas (Fase 2): a chave provável é o **ID do ticket**.
- Nome da empresa (hoje só o ID; a resolução por `/companies` pode entrar no estado como cache).
