# Primeiro envio do repositório "inovacoes" ao GitHub a partir do pacote gerado pelo Claude.
# Cria um clone local a partir do .bundle, aponta o origin para o GitHub e envia main + etiquetas.
# Precisa do git instalado e de acesso ao repositório (o git pede login na primeira vez).
#
# Uso:
#   .\enviar_github.ps1                                   # clone em C:\git\inovacoes
#   .\enviar_github.ps1 -Clone "D:\repos\inovacoes"

param(
    [string]$Clone = "C:\git\inovacoes",
    [string]$Remoto = "https://github.com/diego-isquierdo/inovacoes.git"
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git não encontrado. Instale em https://git-scm.com/download/win e rode de novo." }
$bundle = Get-ChildItem $PSScriptRoot -Filter "inovacoes_*.bundle" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $bundle) { throw "Nenhum inovacoes_*.bundle nesta pasta." }
git bundle verify $bundle.FullName
if ($LASTEXITCODE -ne 0) { throw "Pacote inválido: $($bundle.Name)" }

if (Test-Path (Join-Path $Clone ".git")) {
    Write-Host "Clone já existe em ${Clone}: trazendo o pacote para ele."
    Push-Location $Clone
    git fetch $bundle.FullName "refs/heads/main:refs/remotes/pacote/main" --tags
    git merge --ff-only pacote/main
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path $Clone) | Out-Null
    git clone -b main $bundle.FullName $Clone
    Push-Location $Clone
    git fetch --tags $bundle.FullName
}
git remote remove origin 2>$null
git remote add origin $Remoto
git push -u origin main
git push origin --tags
Pop-Location
Write-Host "OK: enviado para $Remoto (clone local em $Clone)."
