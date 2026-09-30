# Atualiza as bases do Painel de Gestão · Serviços Técnicos (roda no computador do Diego).
#
#   1) Tickets (Freshdesk)  -> extracao_servicos_tecnicos.py   (incremental; pula se já rodou hoje)
#   2) Horas (Painel de Serviços) -> extracao_horas_apontadas.py (ano inteiro, ~1,5 min)
#
# Por que no computador e não na nuvem: o Painel de Serviços só aceita conexões da
# rede da empresa (403 fora dela) — ver LOG 29/09/2026.
#
# Resultado de cada execução (JSON em UTF-8 sem BOM):
#   automacao\ultima_atualizacao.json -> status resumido das duas extrações
#   automacao\estado_botao.json       -> estado para o botão Atualizar (etapa, resultado, hibernação de 5 h)
#   automacao\manifesto.json          -> bases geradas (caminho, tamanho, SHA-256, data) para a carga no painel
#   automacao\logs\atualizacao_AAAAMMDD_HHMMSS.log -> saída completa
#
# Trava: automacao\.executando impede duas execuções ao mesmo tempo (botão x Agendador).
# Vence sozinha em 30 min, se o processo morrer.
#
# Uso (PowerShell):
#   .\atualizar_bases.ps1                 # rotina normal (Agendador)
#   .\atualizar_bases.ps1 -ForcarTickets  # roda os tickets mesmo que já tenham rodado hoje
#   .\atualizar_bases.ps1 -TicketsFull    # tickets com --full (relista o ano + verificação) — 1x/semana
#   .\atualizar_bases.ps1 -SoTickets | -SoHoras
#   .\atualizar_bases.ps1 -ForcarTickets -Origem botao -PedidoId <id>   # chamado pelo vigia_pedidos.ps1

param(
    [switch]$ForcarTickets,
    [switch]$TicketsFull,
    [switch]$SoTickets,
    [switch]$SoHoras,
    [ValidateSet("agendado", "botao", "manual")][string]$Origem = "agendado",
    [string]$PedidoId = ""
)

$ErrorActionPreference = "Continue"
$Inov      = Join-Path $env:USERPROFILE "OneDrive - Starian\Projuris\Diego\Inovações"
$Freshdesk = Join-Path $Inov "MCP - Fresk\freshdesk_mcp"
$Painel    = Join-Path $Inov "MCP Painel de Serviços"
$Aqui      = $PSScriptRoot
$Python    = Join-Path $Freshdesk ".venv\Scripts\python.exe"   # tem httpx, python-dotenv e openpyxl
$SaidaTk   = Join-Path $Freshdesk "scripts\output\Serviços Técnicos"
$BaseTk    = Join-Path $SaidaTk "Base de Serviços Técnicos.xlsx"
$Ano       = (Get-Date).Year
$HIBERNA_H = 5      # horas de hibernação do botão após um sucesso
$FALHA_MIN = 15     # minutos até o botão liberar após uma falha
$TRAVA_MIN = 30     # minutos até a trava vencer

$ArqEstado = Join-Path $Aqui "estado_botao.json"
$ArqTrava  = Join-Path $Aqui ".executando"
$ArqManif  = Join-Path $Aqui "manifesto.json"

$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8   # acentos corretos no log

function Agora { (Get-Date).ToString("o") }
function Grava-Json($objeto, $caminho) {
    # UTF-8 sem BOM e gravação atômica (arquivo temporário + troca)
    $json = $objeto | ConvertTo-Json -Depth 6
    $tmp = "$caminho.tmp"
    [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding $false))
    Move-Item -Path $tmp -Destination $caminho -Force
}
function Le-Json($caminho) {
    if (-not (Test-Path $caminho)) { return $null }
    try { return (Get-Content -Raw -Encoding UTF8 $caminho | ConvertFrom-Json) } catch { return $null }
}

# ---------- trava ----------
if (Test-Path $ArqTrava) {
    $idade = ((Get-Date) - (Get-Item -Force $ArqTrava).LastWriteTime).TotalMinutes
    if ($idade -lt $TRAVA_MIN) {
        Write-Host "==> Outra atualização está em andamento (trava de $([int]$idade) min). Nada a fazer."
        exit 2
    }
    Write-Host "==> Trava vencida ($([int]$idade) min): assumindo a execução."
}
Grava-Json ([ordered]@{ pid = $PID; inicio = (Agora); origem = $Origem; pedido_id = $PedidoId }) $ArqTrava

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path (Join-Path $Aqui "logs") | Out-Null
$log = Join-Path $Aqui "logs\atualizacao_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

# ---------- estado do botão ----------
$ant = Le-Json $ArqEstado
$ultimoSucesso = $null
if ($ant -and $ant.ultimo_sucesso) { $ultimoSucesso = [string]$ant.ultimo_sucesso }
$estado = [ordered]@{
    status              = "em_execucao"
    etapa               = "inicio"
    origem              = $Origem
    pedido_id           = $PedidoId
    ultimo_inicio       = (Agora)
    ultimo_fim          = $null
    resultado           = ""
    ultimo_sucesso      = $ultimoSucesso
    proximo_liberado_em = $(if ($ant) { $ant.proximo_liberado_em } else { $null })
    computador          = $env:COMPUTERNAME
    log                 = $log
}
function Etapa($nome) { $estado.etapa = $nome; Grava-Json $estado $ArqEstado }
Etapa "inicio"

$status = [ordered]@{
    executado_em = (Get-Date).ToString("s")
    computador   = $env:COMPUTERNAME
    origem       = $Origem
    tickets      = [ordered]@{ status = "nao_executado"; detalhe = "" }
    horas        = [ordered]@{ status = "nao_executado"; detalhe = "" }
    log          = $log
}

function Rodar($nome, $script, $argumentos, $pasta) {
    Write-Host "==> $nome : $script $argumentos"
    $ini = Get-Date
    Push-Location $pasta
    & $Python $script @argumentos 2>&1 | Out-Host   # mostra/registra a saída sem misturá-la no status
    $codigo = $LASTEXITCODE
    Pop-Location
    $dur = [int]((Get-Date) - $ini).TotalSeconds
    if ($codigo -eq 0) { return [ordered]@{ status = "ok"; detalhe = "concluido em ${dur}s" } }
    return [ordered]@{ status = "erro"; detalhe = "codigo $codigo apos ${dur}s (ver log)" }
}

try {
    if (-not (Test-Path $Python)) {
        $status.tickets.status = "erro"; $status.tickets.detalhe = "Python nao encontrado: $Python"
        $status.horas = $status.tickets
    } else {
        # 1) Tickets
        if (-not $SoHoras) {
            Etapa "tickets"
            $jaHoje = (Test-Path $BaseTk) -and ((Get-Item $BaseTk).LastWriteTime.Date -eq (Get-Date).Date)
            if ($jaHoje -and -not $ForcarTickets -and -not $TicketsFull) {
                $status.tickets.status = "pulado"
                $status.tickets.detalhe = "base ja gerada hoje as " + (Get-Item $BaseTk).LastWriteTime.ToString("HH:mm")
                Write-Host "==> Tickets: $($status.tickets.detalhe)"
            } else {
                $a = @(); if ($TicketsFull) { $a += "--full" }
                $status.tickets = Rodar "Tickets" "scripts\extracao_servicos_tecnicos.py" $a $Freshdesk
            }
        }
        # 2) Horas
        if (-not $SoTickets) {
            Etapa "horas"
            $status.horas = Rodar "Horas" "scripts\extracao_horas_apontadas.py" @() $Painel
        }
    }

    # 3) Manifesto das bases (para a carga no painel)
    Etapa "manifesto"
    $itens = @(
        @{ tipo = "tickets"; formato = "json"; caminho = (Join-Path $SaidaTk "base_servicos_tecnicos.json") },
        @{ tipo = "horas";   formato = "json"; caminho = (Join-Path $Painel "output\horas_apontadas_${Ano}_painel.json") },
        @{ tipo = "tickets"; formato = "xlsx"; caminho = $BaseTk },
        @{ tipo = "horas";   formato = "xlsx"; caminho = (Join-Path $Painel "output\Horas Apontadas $Ano.xlsx") }
    )
    $bases = foreach ($i in $itens) {
        if (Test-Path $i.caminho) {
            $f = Get-Item $i.caminho
            [ordered]@{ tipo = $i.tipo; formato = $i.formato; caminho = $f.FullName; bytes = $f.Length
                        sha256 = (Get-FileHash -Algorithm SHA256 $f.FullName).Hash.ToLower()
                        gerado_em = $f.LastWriteTime.ToString("o") }
        } else {
            [ordered]@{ tipo = $i.tipo; formato = $i.formato; caminho = $i.caminho; bytes = 0; sha256 = $null; gerado_em = $null }
        }
    }
    Grava-Json ([ordered]@{ gerado_em = (Agora); origem = $Origem; pedido_id = $PedidoId
                           tickets = $status.tickets.status; horas = $status.horas.status; bases = @($bases) }) $ArqManif
} finally {
    Grava-Json $status (Join-Path $Aqui "ultima_atualizacao.json")

    # Sucesso = nenhuma extração com erro e horas executadas (execução completa)
    $erro = ($status.tickets.status -eq "erro") -or ($status.horas.status -eq "erro")
    $completa = ($status.horas.status -eq "ok")
    $fim = Get-Date
    $estado.ultimo_fim = $fim.ToString("o")
    $estado.etapa = "concluido"
    if ($erro) {
        $estado.status = "erro"
        $estado.resultado = "tickets: $($status.tickets.status) $($status.tickets.detalhe) | horas: $($status.horas.status) $($status.horas.detalhe)"
        # libera em 15 min, mas nunca antes da hibernação de um sucesso anterior
        $lib = $fim.AddMinutes($FALHA_MIN)
        if ($estado.ultimo_sucesso) {
            $h = ([datetime]::Parse($estado.ultimo_sucesso)).AddHours($HIBERNA_H)
            if ($h -gt $lib) { $lib = $h }
        }
        $estado.proximo_liberado_em = $lib.ToString("o")
    } elseif ($completa) {
        $estado.status = "ok"
        $estado.resultado = "tickets: $($status.tickets.status) | horas: $($status.horas.status)"
        $estado.ultimo_sucesso = $fim.ToString("o")
        $estado.proximo_liberado_em = $fim.AddHours($HIBERNA_H).ToString("o")
    } else {
        # execução parcial (ex.: -SoTickets do completo semanal): não mexe na hibernação
        $estado.status = "ok_parcial"
        $estado.resultado = "tickets: $($status.tickets.status) | horas: $($status.horas.status)"
    }
    Grava-Json $estado $ArqEstado
    Remove-Item $ArqTrava -Force -ErrorAction SilentlyContinue

    Write-Host "==> Status:" ($status | ConvertTo-Json -Depth 4 -Compress)
    Write-Host "==> Botão:" $estado.status "· liberado em" $estado.proximo_liberado_em
    Stop-Transcript | Out-Null
}
if ($status.tickets.status -eq "erro" -or $status.horas.status -eq "erro") { exit 1 }
exit 0
