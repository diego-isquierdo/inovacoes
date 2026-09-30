# Cria (ou recria) no Agendador de Tarefas do Windows a atualização automática das bases.
# Rode UMA vez no PowerShell (não precisa ser administrador):
#   .\agendar_atualizacao.ps1                       # dias úteis às 07:30 e 12:30
#   .\agendar_atualizacao.ps1 -Horarios "08:00","14:00"
#   .\agendar_atualizacao.ps1 -Remover
#
# A tarefa roda com o seu usuário logado (precisa do OneDrive e da rede da empresa/VPN).
# Às segundas, a primeira execução do dia usa -TicketsFull (relista o ano + verificação).
# Cria também o "Vigia de pedidos" (a cada 5 min, 07:00–22:00): atende o botão Atualizar do painel.

param(
    [string[]]$Horarios = @("07:30", "12:30"),
    [switch]$Remover
)

$ErrorActionPreference = "Stop"   # qualquer falha interrompe e aparece na tela
$Nome   = "Painel Serviços Técnicos - Atualizar bases"
$Script = Join-Path $PSScriptRoot "atualizar_bases.ps1"
if (-not (Test-Path $Script)) { throw "Não encontrei $Script (os dois .ps1 precisam estar na mesma pasta)." }

if (Get-ScheduledTask -TaskName $Nome -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $Nome -Confirm:$false
}
if (Get-ScheduledTask -TaskName "$Nome (semanal full)" -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName "$Nome (semanal full)" -Confirm:$false
}
$NomeVigia = "Painel Serviços Técnicos - Vigia de pedidos"
$Vbs = Join-Path $PSScriptRoot "vigia_oculto.vbs"
if (Get-ScheduledTask -TaskName $NomeVigia -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $NomeVigia -Confirm:$false
}
if ($Remover) { Write-Host "Tarefas removidas."; return }

$acao = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`""
$dias = "Monday","Tuesday","Wednesday","Thursday","Friday"
$gatilhos = $Horarios | ForEach-Object { New-ScheduledTaskTrigger -Weekly -DaysOfWeek $dias -At $_ }
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName $Nome -Action $acao -Trigger $gatilhos -Settings $config `
    -Description "Extrai tickets (Freshdesk) e horas (Painel de Serviços) para o Painel de Gestão" | Out-Null

# Segunda-feira, 15 min antes do primeiro horário: extração completa de tickets
$primeiro = [datetime]::ParseExact($Horarios[0], "HH:mm", $null).AddMinutes(-15).ToString("HH:mm")
$acaoFull = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`" -TicketsFull -SoTickets"
Register-ScheduledTask -TaskName "$Nome (semanal full)" -Action $acaoFull `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $primeiro) -Settings $config `
    -Description "Extração completa semanal de tickets (verificação cruzada)" | Out-Null

# Vigia de pedidos do botão Atualizar: a cada 5 min, das 07:00 às 22:00, todos os dias, sem abrir janela
if (-not (Test-Path $Vbs)) { throw "Não encontrei $Vbs (precisa estar na mesma pasta)." }
$acaoVigia = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$Vbs`""
$gVigia = New-ScheduledTaskTrigger -Daily -At "07:00"
$gVigia.Repetition = (New-ScheduledTaskTrigger -Once -At "07:00" -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Hours 15)).Repetition
$cfgVigia = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName $NomeVigia -Action $acaoVigia -Trigger $gVigia -Settings $cfgVigia `
    -Description "Atende os pedidos do botão Atualizar do painel (pedido_atualizacao.json)" | Out-Null

# Conferência: as três tarefas precisam existir
$ok = Get-ScheduledTask -TaskName $Nome, "$Nome (semanal full)", $NomeVigia -ErrorAction SilentlyContinue
if (@($ok).Count -ne 3) { throw "As tarefas não foram criadas. Veja a mensagem de erro acima." }
Write-Host "OK: tarefas criadas - '$Nome' (dias úteis $($Horarios -join ', ')), '$Nome (semanal full)' (segundas $primeiro) e '$NomeVigia' (a cada 5 min, 07:00-22:00)."
Write-Host "Para rodar agora: Start-ScheduledTask -TaskName '$Nome'"
