# Vigia de pedidos do botão "Atualizar" do Painel de Gestão · Serviços Técnicos.
#
# Roda a cada 5 min pelo Agendador do Windows (tarefa "... - Vigia de pedidos", via vigia_oculto.vbs).
# O mensageiro (tarefa agendada do Claude) grava automacao\pedido_atualizacao.json quando o botão
# é pressionado. Este vigia:
#   1) não havendo pedido, sai na hora (custo zero);
#   2) recusa o pedido se o botão estiver em hibernação (estado_botao.json -> proximo_liberado_em);
#   3) espera o próximo ciclo se outra atualização estiver rodando (trava .executando);
#   4) senão, roda atualizar_bases.ps1 -ForcarTickets -Origem botao e arquiva o pedido em pedidos\.
#
# Tudo fica registrado em logs\vigia.log (uma linha por evento; ciclos sem pedido não registram nada).

$ErrorActionPreference = "Continue"
$Aqui      = $PSScriptRoot
$ArqPedido = Join-Path $Aqui "pedido_atualizacao.json"
$ArqEstado = Join-Path $Aqui "estado_botao.json"
$ArqTrava  = Join-Path $Aqui ".executando"
$Pasta     = Join-Path $Aqui "pedidos"
$Script    = Join-Path $Aqui "atualizar_bases.ps1"
$TRAVA_MIN = 30
$ESPERA_MAX_MIN = 30   # pedido esperando a trava por mais que isso é recusado

if (-not (Test-Path $ArqPedido)) { exit 0 }

New-Item -ItemType Directory -Force -Path (Join-Path $Aqui "logs"), $Pasta | Out-Null
$LogVigia = Join-Path $Aqui "logs\vigia.log"
function Registra($msg) {
    $linha = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "  " + $msg
    [System.IO.File]::AppendAllText($LogVigia, $linha + "`r`n", (New-Object System.Text.UTF8Encoding $false))
}
function Arquiva($sufixo, $motivo) {
    $destino = Join-Path $Pasta ("{0}_{1}.json" -f $sufixo, (Get-Date -Format "yyyyMMdd_HHmmss"))
    Move-Item -Path $ArqPedido -Destination $destino -Force
    Registra "pedido $sufixo -> $(Split-Path $destino -Leaf)$(if ($motivo) { ' · ' + $motivo })"
    # mantém só os 50 pedidos mais recentes
    Get-ChildItem $Pasta -Filter *.json | Sort-Object LastWriteTime -Descending | Select-Object -Skip 50 | Remove-Item -Force -ErrorAction SilentlyContinue
}

# 1) lê o pedido
try { $pedido = Get-Content -Raw -Encoding UTF8 $ArqPedido | ConvertFrom-Json } catch { $pedido = $null }
if (-not $pedido -or -not $pedido.pedido_id) { Arquiva "invalido" "JSON ilegível ou sem pedido_id"; exit 0 }
$id = [string]$pedido.pedido_id

# 2) hibernação
$estado = $null
if (Test-Path $ArqEstado) { try { $estado = Get-Content -Raw -Encoding UTF8 $ArqEstado | ConvertFrom-Json } catch { } }
if ($estado -and $estado.proximo_liberado_em) {
    $libera = [datetime]::Parse([string]$estado.proximo_liberado_em)
    if ((Get-Date) -lt $libera) { Arquiva "recusado" "$id · botão hibernando até $($libera.ToString('dd/MM HH:mm'))"; exit 0 }
}

# 3) trava
if (Test-Path $ArqTrava) {
    $idade = ((Get-Date) - (Get-Item -Force $ArqTrava).LastWriteTime).TotalMinutes
    if ($idade -lt $TRAVA_MIN) {
        $esperando = ((Get-Date) - (Get-Item -Force $ArqPedido).LastWriteTime).TotalMinutes
        if ($esperando -gt $ESPERA_MAX_MIN) { Arquiva "recusado" "$id · outra atualização ocupou o computador por mais de $ESPERA_MAX_MIN min"; exit 0 }
        Registra "pedido $id aguardando: outra atualização em andamento"
        exit 0
    }
}

# 4) executa
Registra "pedido $id aceito · iniciando atualizar_bases.ps1 -ForcarTickets -Origem botao"
& $Script -ForcarTickets -Origem botao -PedidoId $id
$codigo = $LASTEXITCODE
if ($codigo -eq 0)     { Arquiva "atendido" "$id · ok" }
elseif ($codigo -eq 2) { Registra "pedido $id aguardando: trava apareceu no último instante" }
else                   { Arquiva "falhou" "$id · código $codigo (ver estado_botao.json e logs)" }
exit 0
