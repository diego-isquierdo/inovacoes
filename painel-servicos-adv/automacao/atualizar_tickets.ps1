# Atualiza a base de tickets do Painel de Gestão · Serviços ADV (roda no computador do Diego).
#
#   Tickets (Freshdesk) -> extracao_servicos_adv.py (incremental por padrão)
#
# Por que no computador e não na nuvem: mesmo script usado pelo time Técnico,
# que roda no Freshdesk via rede da empresa.
#
# Resultado de cada execução:
#   automacao\ultima_atualizacao.json -> status resumido da extração
#   automacao\logs\atualizacao_tickets_AAAAMMDD_HHMMSS.log -> saída completa
#
# Uso (PowerShell):
#   .\atualizar_tickets.ps1            # incremental (rotina do Agendador)
#   .\atualizar_tickets.ps1 -Full       # relista o ano + verificação cruzada

param(
    [switch]$Full
)

$ErrorActionPreference = "Continue"
$Inov      = Join-Path $env:USERPROFILE "OneDrive - Starian\Projuris\Diego\Inovações"
$Freshdesk = Join-Path $Inov "MCP - Fresk\freshdesk_mcp"
$Aqui      = $PSScriptRoot
$Python    = Join-Path $Freshdesk ".venv\Scripts\python.exe"

$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Agora { (Get-Date).ToString("o") }
function Grava-Json($objeto, $caminho) {
    $json = $objeto | ConvertTo-Json -Depth 6
    $tmp = "$caminho.tmp"
    [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding $false))
    Move-Item -Path $tmp -Destination $caminho -Force
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path (Join-Path $Aqui "logs") | Out-Null
$log = Join-Path $Aqui "logs\atualizacao_tickets_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$status = [ordered]@{
    executado_em = (Get-Date).ToString("s")
    computador   = $env:COMPUTERNAME
    modo         = $(if ($Full) { "full" } else { "incremental" })
    tickets      = [ordered]@{ status = "nao_executado"; detalhe = "" }
    log          = $log
}

try {
    if (-not (Test-Path $Python)) {
        $status.tickets.status = "erro"
        $status.tickets.detalhe = "Python nao encontrado: $Python"
    } else {
        $a = @(); if ($Full) { $a += "--full"; $a += "--verify" }
        Write-Host "==> Tickets ADV : scripts\extracao_servicos_adv.py $a"
        $ini = Get-Date
        Push-Location $Freshdesk
        & $Python "scripts\extracao_servicos_adv.py" @a 2>&1 | Out-Host
        $codigo = $LASTEXITCODE
        Pop-Location
        $dur = [int]((Get-Date) - $ini).TotalSeconds
        if ($codigo -eq 0) {
            $status.tickets.status = "ok"
            $status.tickets.detalhe = "concluido em ${dur}s"
        } else {
            $status.tickets.status = "erro"
            $status.tickets.detalhe = "codigo $codigo apos ${dur}s (ver log)"
        }
    }
} finally {
    Grava-Json $status (Join-Path $Aqui "ultima_atualizacao.json")
    Write-Host "==> Status:" ($status | ConvertTo-Json -Depth 4 -Compress)
    Stop-Transcript | Out-Null
}
if ($status.tickets.status -eq "erro") { exit 1 }
exit 0
