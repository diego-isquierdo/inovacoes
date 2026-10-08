# Atualiza a base de tickets do Painel de Gestão · Integrações (roda no computador do Diego).
#
#   1) Tickets (Freshdesk)        -> extracao_integracoes.py (incremental por padrão)
#   2) Horas (Painel de Serviços) -> extracao_horas_apontadas.py (base global do ano)
#   3) Base de horas só da área Integração + manifesto -> ferramentas\*.py
#   Depois, a tarefa do Claude "Integrações · carregar bases no painel" (21:30) envia o que mudou.
#
# Por que no computador e não na nuvem: mesma arquitetura dos times Técnico e ADV,
# que acessam o Freshdesk via rede da empresa.
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
    horas        = [ordered]@{ status = "nao_executado"; detalhe = "" }
    manifesto    = [ordered]@{ status = "nao_executado"; detalhe = "" }
    log          = $log
}

try {
    if (-not (Test-Path $Python)) {
        $status.tickets.status = "erro"
        $status.tickets.detalhe = "Python nao encontrado: $Python"
    } else {
        $a = @(); if ($Full) { $a += "--full"; $a += "--verify" }
        Write-Host "==> Tickets Integrações : scripts\extracao_integracoes.py $a"
        $ini = Get-Date
        Push-Location $Freshdesk
        & $Python "scripts\extracao_integracoes.py" @a 2>&1 | Out-Host
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

    if ($status.tickets.status -ne "erro") {
        $Painel = Join-Path $Inov "MCP Painel de Serviços"
        $Ferr   = Join-Path (Split-Path $Aqui -Parent) "ferramentas"
        $ini = Get-Date
        Write-Host "==> Horas : scripts\extracao_horas_apontadas.py"
        Push-Location $Painel
        & $Python "scripts\extracao_horas_apontadas.py" 2>&1 | Out-Host
        $c1 = $LASTEXITCODE
        Pop-Location
        if ($c1 -eq 0) {
            Write-Host "==> Base de horas da área Integração"
            & $Python (Join-Path $Ferr "preparar_base_horas_integracoes.py") 2>&1 | Out-Host
            $c2 = $LASTEXITCODE
        } else { $c2 = 1 }
        $dur = [int]((Get-Date) - $ini).TotalSeconds
        if ($c1 -eq 0 -and $c2 -eq 0) { $status.horas.status = "ok"; $status.horas.detalhe = "concluido em ${dur}s" }
        else { $status.horas.status = "erro"; $status.horas.detalhe = "extracao=$c1 preparo=$c2 (ver log)" }
        Write-Host "==> Manifesto"
        & $Python (Join-Path $Ferr "gerar_manifesto_integracoes.py") 2>&1 | Out-Host
        if ($LASTEXITCODE -eq 0) { $status.manifesto.status = "ok" } else { $status.manifesto.status = "erro"; $status.manifesto.detalhe = "codigo $LASTEXITCODE (ver log)" }
    }
} finally {
    Grava-Json $status (Join-Path $Aqui "ultima_atualizacao.json")
    Write-Host "==> Status:" ($status | ConvertTo-Json -Depth 4 -Compress)
    Stop-Transcript | Out-Null
}
if ($status.tickets.status -eq "erro" -or $status.horas.status -eq "erro") { exit 1 }
exit 0
