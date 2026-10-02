# Cria (ou recria) no Agendador de Tarefas do Windows a atualização automática
# da base de tickets do time de Serviços ADV. Rode UMA vez no PowerShell
# (não precisa ser administrador):
#   .\agendar_atualizacao.ps1                     # dias úteis (seg-sex) às 20:00
#   .\agendar_atualizacao.ps1 -Horario "19:00"
#   .\agendar_atualizacao.ps1 -Remover
#
# A tarefa roda com o seu usuário logado (precisa do OneDrive e da rede da empresa/VPN).
# Diferente do time Técnico, esta tarefa só atualiza tickets (incremental) —
# não há ainda botão "Atualizar", vigia ou extração de horas própria para o ADV.

param(
    [string]$Horario = "20:00",
    [switch]$Remover
)

$ErrorActionPreference = "Stop"
$Nome   = "Painel Serviços ADV - Atualizar tickets"
$Script = Join-Path $PSScriptRoot "atualizar_tickets.ps1"
if (-not (Test-Path $Script)) { throw "Não encontrei $Script (os dois .ps1 precisam estar na mesma pasta)." }

if (Get-ScheduledTask -TaskName $Nome -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $Nome -Confirm:$false
}
if ($Remover) { Write-Host "Tarefa removida."; return }

$acao = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`""
$dias = "Monday","Tuesday","Wednesday","Thursday","Friday"
$gatilho = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $dias -At $Horario
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName $Nome -Action $acao -Trigger $gatilho -Settings $config `
    -Description "Extrai tickets (Freshdesk) para o Painel de Gestão · Serviços ADV" | Out-Null

$ok = Get-ScheduledTask -TaskName $Nome -ErrorAction SilentlyContinue
if (-not $ok) { throw "A tarefa não foi criada. Veja a mensagem de erro acima." }
Write-Host "OK: tarefa criada - '$Nome' (seg-sex às $Horario)."
Write-Host "Para rodar agora: Start-ScheduledTask -TaskName '$Nome'"
