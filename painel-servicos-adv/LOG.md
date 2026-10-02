# Log de decisões — Painel de Gestão · Serviços ADV

Diário datado: o que foi decidido, por quê e com que resultado. Mais recente primeiro.

## 02/10/2026 — Painel publicado (Fase 3) e S&OP revisado (Fase 4)

**Análise da operação e modelo de dados.** Antes de construir o painel, analisei
os dados reais da base de tickets do ADV (subtipo, tags, campo tipo) em vez de
copiar a estrutura do time Técnico às cegas. Achados usados para definir o
modelo: o campo Subtipo do Freshdesk já tem "Sistemas Mapeados"/"Sistemas Não
Mapeados"; os tickets sem subtipo batem quase 1:1 com "Dúvidas" e "Solicitação
de orçamento"; tags "sem anexos (29h)"/"com anexos (55h)"/"script (10h)" já
eram usadas informalmente pelo time como referência de esforço.

Com o Diego, fechamos o modelo de **6 categorias de demanda** (Viabilidade/
Orçamento com Dúvidas, Importação de Dados, Importação de Documentos, Ações em
Lote/Scripts, Migração Mapeados, Migração Não Mapeados), seus esforços padrão
e SLAs (ver `PLANEJAMENTO.md`, Fase 3), e que "Ajustes de inconsistências" e
"Migração" genérica (sem mapeado/não mapeado no Subtipo) usam Tags e depois
Assunto para decidir, caindo em "Padrão" (ambíguo, sinalizado no painel) na
falta de qualquer pista.

**Construção do painel.** O motor do time Técnico (`painel_v1.html`, ~1.360
linhas) tem o modelo "Dados × Ativação" entranhado em dezenas de funções —
classificação, SLA, esforço, squads, S&OP, e principalmente o Plano de Ação
(catálogo de automações 100% específico do Técnico: tenant, licenças, Legal
Intelligence). Reconstruí a camada de regras de negócio para um motor
generalizado por categoria (sem squads, já que o ADV é time único), mantendo a
casca (CSS, design system Projuris, helpers de gráfico) praticamente idêntica.
Plano de Ação ficou numa versão simplificada (simulação de capacidade × demanda
e cenários de contratação, sem catálogo de automação).

Toda a lógica foi validada rodando o script extraído no Node.js contra as bases
reais (212 tickets, 6.902 apontamentos) antes de cada publicação — sem erros de
sintaxe nem `NaN`/`undefined` em nenhuma das 10 abas.

Publicado o artefato **"Painel Serviços ADV"**:
https://claude.ai/artifact/NNthAUZKErRTB1FG7myfwW — bases carregadas via upload
de assets (`base_servicos_adv.json`, `horas_apontadas_2026_painel.json`) e
gravação do documento `cfg/bases` do banco do artefato (sem botão "Atualizar"
nem Mensageiro nesta primeira versão).

**Correção de rota**: a primeira publicação ficou com mensagem de "sem dados"
porque o upload de arquivo só pode ser feito pela própria página (por quem edita
o artefato) — descobri que o Artifact tool também sabe enviar um arquivo local
direto para o armazenamento de um artefato já publicado (`asset: true`), e usei
isso para carregar as duas bases e gravar `cfg/bases` sem depender de ação manual
na interface.

**S&OP revisado três vezes**, a pedido do Diego, numa sequência de refinamentos:

1. Troca do modelo de "saldo em horizonte fixo de 3 meses" (cópia do time
   Técnico) por uma **simulação mês a mês**: cada mês paga ao backlog no máximo
   90% da capacidade do mês; o excedente rola para o mês seguinte, até zerar ou
   até 6 meses (segurança). Forecast (entradas previstas) fica fora dessa conta
   — é só contexto, pode passar da capacidade, porque não há garantia de que
   essas entradas se confirmem. Propagado para Visão geral, Diagnóstico e Plano
   de Ação. Adicionado quadro "Eficiência dos tickets concluídos" (estimado ×
   apontado), depois ajustado para incluir a coluna Mês conclusão e limitar aos
   últimos 2 meses.
2. Forecast passou de linha tracejada para fatia dentro da própria barra
   empilhada (cor própria), com a capacidade do mês como linha de referência.
3. Criado o quadro **"Projeção viva"** (até 12 meses): pelo menos metade do
   Forecast de cada mês entra de fato na fila; a régua de parada é o backlog
   cair para 50% da capacidade do mês (fila saudável, não zerada). A barra
   ganhou 3 fatias — Pago ao backlog, Metade do Forecast ainda na fila, Backlog
   antigo ainda na fila — com a regra de prioridade "paga o antigo primeiro"; só
   a fatia do Forecast pode passar da linha de capacidade.

Analisei também, a pedido do Diego, se o Forecast considerava corretamente o
tipo de cada chamado e seu esforço estimado (sim — por categoria, com a
mistura real de anexos ponderando o esforço da migração) e trouxe a mesma conta
usando 2 meses em vez de 3 (595,5 h/mês vs. 562,7 h/mês com 3 meses) para
comparação; o painel continua usando 3 meses por padrão.

**Versionamento**: diferente do time Técnico (onde o versionamento é manual,
só pelo Diego — decisão de 30/09/2026), para o ADV o Diego pediu explicitamente
que o Claude faça o commit e o push no GitHub. Ver Fase 6 do `PLANEJAMENTO.md`
e o commit em `painel-servicos-adv/` no repositório `diego-isquierdo/inovacoes`.

**Próximos passos:** validar com o time os parâmetros do S&OP (90%, metade do
Forecast, meta de 50%) conforme mais dados reais entrarem; decidir se vale um
botão "Atualizar" (Fase 5) para a carga das bases.

## 01/10/2026 — Primeira extração de tickets validada (Fase 1 concluída)

**Problema encontrado:** a primeira tentativa de rodar `extracao_servicos_adv.py --full --verify` falhou com erro 401 (API key inválida/rotacionada). Confirmado com o Diego: a chave do Freshdesk havia sido trocada. Como `extracao_servicos_tecnicos.py` e `extracao_servicos_adv.py` compartilham o mesmo `scripts/lib/common.py` e portanto o mesmo `.env` na raiz de `MCP - Fresk\freshdesk_mcp\` (um único arquivo, não uma cópia por script), bastou atualizar esse `.env` com a chave nova (`FRESHDESK_API_KEY=CFkOoxNmAa5RFbUWnDKm`) para corrigir os dois scripts — e também a automação agendada do time Técnico, que usa a mesma pasta.

**Execução validada** (após corrigir a chave): `extracao_servicos_adv.py --full --verify`, concluída em 4.709 s (~78 min — mais lenta que o normal por uma lentidão pontual da API entre as páginas 150–175 da listagem; sem impacto no resultado).

- Verificação cruzada contra a busca do Freshdesk bateu 100% (nível do grupo `SRV TECNICO`, antes do filtro de produto): backlog 873=873, novo no ano 2.348=2.348, concluído no ano 535=535, resolvido no ano 1.254=1.254.
- Recortes do time ADV (produto = Projuris ADV): **Backlog 71 · Novo no ano 197 · Concluído no ano 86 · Resolvido no ano 55** (212 tickets únicos).
- Saída: `Base de Serviços ADV.xlsx` + `base_servicos_adv.json` em `scripts\output\Serviços ADV\`; estado incremental salvo em `scripts\cache\servicos_adv\estado.json`.

**Resultado:** Fase 1 do planejamento concluída e validada, nos mesmos moldes da Fase 1 do time Técnico.

**Próximos passos:** agendamento no Windows (reaproveitar o agendador existente ou criar um próprio) e início do desenho da Fase 3 (abas do painel).

## 01/10/2026 — Atualização da base global de horas (confirmação do recorte ADV)

Rodado `extracao_horas_apontadas.py` (mesmo script e base compartilhada com o
time Técnico — nenhum script novo, conforme decisão da Fase 2) para refrescar
os dados antes de seguir com o painel. Resultado: 6.902 apontamentos no ano,
5.816,93 h totais, 14 analistas (áreas Serviços + Integração), 272 chamadas à
API, 0 consultas sem permissão. Saída: `Horas Apontadas 2026.xlsx` /
`horas_apontadas_2026.json` / `horas_apontadas_2026_painel.json` em
`MCP Painel de Serviços\output\`.

Conferência do recorte do time ADV na base atualizada (filtro por
`analyst_name` em Renan, Marina, Lucas, Wallef): **1.207 apontamentos**,
**1.999,2 h** no ano — primeiro número real de volume de horas do time ADV.

**Próximos passos:** usar esse número como referência ao desenhar a Fase 3
(abas do painel) e a Fase 4 (S&OP) do projeto ADV.

## 01/10/2026 — Script de tickets criado e fonte de horas resolvida sem extração nova

**Contexto:** análise pedida sobre `extracao_horas_apontadas.py` (script de
horas do time Técnico) para avaliar o que poderia ser reaproveitado para o
time ADV.

**Script de tickets:** criado `extracao_servicos_adv.py` em
`MCP - Fresk\freshdesk_mcp\scripts\`, cópia adaptada de
`extracao_servicos_tecnicos.py` com o filtro de produto invertido (somente
`Projuris ADV`, em vez de excluí-lo) e saída/estado próprios
(`scripts\output\Serviços ADV\`, `scripts\cache\servicos_adv\`) — totalmente
isolado do script e dos dados do time Técnico. Sintaxe validada
(`py_compile`); execução real ainda pendente.

**Fonte de horas:** lendo `extracao_horas_apontadas.py` e o planejamento
técnico do time Técnico (`extracao/PLANEJAMENTO_EXTRACAO_HORAS.md`, linha
"Áreas: todas as áreas que o token enxerga. A área vira coluna e o painel
filtra Serviços Técnicos"), confirmou-se que o script **não filtra por time**:
extrai todas as áreas, todos os analistas e o ano inteiro do Painel de
Serviços. Logo, **não é preciso nenhum script novo nem nova execução** para
cobrir o time ADV — a mesma base já gerada para o time Técnico
(`horas_apontadas_<ANO>.json` / `_painel.json`) já contém os apontamentos do
ADV; falta só filtrá-los na carga do painel.

**Achado adicional (consulta à API do Painel de Serviços — `listar_areas` e
`listar_membros`):** existem só 2 áreas cadastradas ("Serviços", 9 membros, e
"Integração", 5 membros), e **os times Técnico e ADV compartilham a mesma
área "Serviços"**. Ou seja, área **não separa** os times — o isolamento tem
que ser feito pela lista de analistas. Mapeamento analista ↔
`freshdesk_agent_id` confirmado e registrado em
[`MAPA.md`](MAPA.md#time-e-ligação-com-o-freshdesk-confirmado-em-01102026).

**Resultado:** `MAPA.md` e `PLANEJAMENTO.md` atualizados — Fase 1 em
andamento (script pronto, falta rodar e validar) e Fase 2 encerrada sem
necessidade de extração própria, restando só o filtro por analista na carga
do painel (Fase 3).

**Próximos passos:** rodar `extracao_servicos_adv.py --full --verify` e
validar contra a busca do Freshdesk; depois decidir o desenho da Fase 3
(abas do painel e como aplicar o filtro de analistas na carga da base de
horas).

## 01/10/2026 — Cenário inicial do projeto

**Contexto:** pedido do Diego para criar o cenário do painel de gestão do time
de Serviços ADV, nos mesmos moldes do painel já em produção para o time de
Serviços Técnicos (`Painel de Gestão\Serviços Técnicos\`).

**Análise feita:** leitura do `README.md`, `MAPA.md`, `PLANEJAMENTO.md` e
`extracao/PLANEJAMENTO_EXTRACAO.md` do projeto Técnico para entender a
arquitetura (extração via script fora da conversa, bases JSON/XLSX, painel
como artefato claude.ai com banco próprio, automação via Agendador do Windows +
botão "Atualizar" + tarefas agendadas do Claude) e o estado de cada fase.

**Decisões confirmadas com o Diego:**

1. **Filtro de escopo**: grupo Freshdesk `SRV TECNICO`, **somente** produto
   `Projuris ADV` — o espelho exato do filtro do time Técnico, que usa o mesmo
   grupo **excluindo** esse produto. Os recortes do ano corrente são os
   mesmos quatro do time Técnico: Backlog, Novo no ano, Concluído no ano,
   Resolvido no ano.
2. **Fonte de horas**: mesma API do Painel de Serviços v2 usada pelo time
   Técnico. Falta confirmar como isolar os apontamentos do time ADV (ver
   pendência no `MAPA.md`).
3. **Time**: Renan, Marina, Lucas e Wallef — time único, sem divisão em
   squads nesta primeira versão (diferente do time Técnico, que divide em
   Dados × Ativação).
4. **Escopo desta primeira entrega**: só a documentação de planejamento
   (`README.md`, `MAPA.md`, `PLANEJAMENTO.md`, `LOG.md`). Nenhum script,
   automação, pasta auxiliar (`extracao/`, `automacao/`, `painel/` etc.) ou
   artefato foi criado ainda — ficam como itens pendentes no `PLANEJAMENTO.md`,
   a construir fase a fase como o time Técnico fez.

**Resultado:** pasta `Painel de Gestão\Serviços ADV\` criada com os quatro
arquivos de planejamento, apontando o projeto Técnico como modelo de
referência em cada decisão ainda em aberto.

**Próximos passos:** iniciar a Fase 1 (extração Freshdesk) quando o Diego
confirmar o item pendente sobre o script (próprio vs. parametrizar o
existente) e revisitar a Fase 2 (horas) para decidir como isolar os dados do
time ADV.
