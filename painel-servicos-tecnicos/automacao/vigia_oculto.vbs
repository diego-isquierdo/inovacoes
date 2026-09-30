' Roda o vigia_pedidos.ps1 sem abrir janela (o Agendador chama este arquivo a cada 5 min).
Dim pasta, cmd
pasta = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & pasta & "\vigia_pedidos.ps1"""
CreateObject("WScript.Shell").Run cmd, 0, True
