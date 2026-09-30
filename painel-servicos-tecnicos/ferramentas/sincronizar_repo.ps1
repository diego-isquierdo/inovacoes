# Copia as versões em uso do Painel Serviços Técnicos para um clone do repositório "inovacoes"
# e faz o commit. Não copia segredos nem dados (só a lista abaixo). Não faz push.
#
# Uso:
#   .\sincronizar_repo.ps1 -Clone "C:\git\inovacoes" -Mensagem "painel: ajuste no botão"
#   .\sincronizar_repo.ps1 -Clone "C:\git\inovacoes" -Mensagem "painel v0.6.0" -Etiqueta "painel-st-v0.6.0"

param(
    [Parameter(Mandatory = $true)][string]$Clone,
    [Parameter(Mandatory = $true)][string]$Mensagem,
    [string]$Etiqueta = ""
)
$ErrorActionPreference = "Stop"
$Inov   = Join-Path $env:USERPROFILE "OneDrive - Starian\Projuris\Diego\Inovações"
$ST     = Join-Path $Inov "Painel de Gestão\Serviços Técnicos"
$Dest   = Join-Path $Clone "painel-servicos-tecnicos"
if (-not (Test-Path (Join-Path $Clone ".git"))) { throw "Não é um clone git: $Clone" }

# origem -> destino (relativo a painel-servicos-tecnicos)
$mapa = @(
    @("$ST\MAPA.md", "MAPA.md"), @("$ST\PLANEJAMENTO.md", "PLANEJAMENTO.md"), @("$ST\LOG.md", "LOG.md"),
    @("$ST\extracao\PLANEJAMENTO_EXTRACAO.md", "extracao\PLANEJAMENTO_EXTRACAO.md"),
    @("$ST\extracao\PLANEJAMENTO_EXTRACAO_HORAS.md", "extracao\PLANEJAMENTO_EXTRACAO_HORAS.md"),
    @("$ST\automacao\atualizar_bases.ps1", "automacao\atualizar_bases.ps1"),
    @("$ST\automacao\agendar_atualizacao.ps1", "automacao\agendar_atualizacao.ps1"),
    @("$ST\automacao\vigia_pedidos.ps1", "automacao\vigia_pedidos.ps1"),
    @("$ST\automacao\vigia_oculto.vbs", "automacao\vigia_oculto.vbs"),
    @("$ST\automacao\LEIA-ME.md", "automacao\LEIA-ME.md"),
    @("$ST\automacao\mensageiro_prompt.md", "automacao\mensageiro_prompt.md"),
    @("$ST\automacao\PLANEJAMENTO_BOTAO_ATUALIZAR.md", "automacao\PLANEJAMENTO_BOTAO_ATUALIZAR.md"),
    @("$ST\automacao\poc\poc_botao.html", "automacao\poc\poc_botao.html"),
    @("$ST\painel\painel_v1.html", "painel\painel_v1.html"),
    @("$Inov\MCP - Fresk\freshdesk_mcp\scripts\extracao_servicos_tecnicos.py", "extracao\scripts\tickets\extracao_servicos_tecnicos.py"),
    @("$Inov\MCP - Fresk\freshdesk_mcp\scripts\README.md", "extracao\scripts\tickets\README_scripts_freshdesk.md"),
    @("$Inov\MCP Painel de Serviços\scripts\extracao_horas_apontadas.py", "extracao\scripts\horas\extracao_horas_apontadas.py"),
    @("$Inov\MCP Painel de Serviços\requirements.txt", "extracao\scripts\horas\requirements.txt"),
    @("$Inov\MCP Painel de Serviços\.env.example", "extracao\scripts\horas\.env.example")
)
foreach ($m in $mapa) {
    $alvo = Join-Path $Dest $m[1]
    New-Item -ItemType Directory -Force -Path (Split-Path $alvo) | Out-Null
    if (Test-Path $m[0]) { Copy-Item -Path $m[0] -Destination $alvo -Force; Write-Host "copiado  $($m[1])" }
    else { Write-Warning "não encontrado: $($m[0])" }
}
# salvaguarda: nenhum .env de verdade no destino
Get-ChildItem $Dest -Recurse -Force -Filter ".env" | ForEach-Object { throw "Arquivo .env encontrado em $($_.FullName): remova antes de versionar." }

Push-Location $Clone
git add -A painel-servicos-tecnicos
git status --short
git commit -m $Mensagem
if ($Etiqueta) { git tag -a $Etiqueta -m $Mensagem }
Pop-Location
Write-Host "Pronto. Para enviar: cd `"$Clone`"; git push; git push --tags"
