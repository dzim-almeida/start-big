!define FIREWALL_RULE_NAME "StartBigERP_API_Server"
!define FIREWALL_PING_RULE_NAME "StartBigERP_Ping_Server"

; Redes da loja (LIC-04, D-21): as regras da API e do mDNS so aceitam conexoes
; destas redes. E a MESMA lista do backend (app/core/rede_local.py, REDES_DA_LOJA);
; o teste CT-16 (test/core/test_rede_local.py) confere que as duas nao divergem.
!define REDES_DA_LOJA "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,169.254.0.0/16"

; Regras que o BACKEND cria quando a maquina vira servidor (app/core/system.py).
!define FIREWALL_BACKEND_API "StartBig-Server"
!define FIREWALL_BACKEND_MDNS "StartBig-mDNS"

!macro NSIS_HOOK_PREINSTALL
    ; O backend NAO e filho do app: roda como tarefa agendada (StartBigServer, como
    ; SYSTEM) a partir de $INSTDIR\erp-api.exe -- ver app/core/system.py.
    ;
    ; O template so mata o MAINBINARYNAME (CheckIfAppIsRunning), nunca o erp-api.
    ; Com o processo vivo, o Windows trava o .exe e o `File /a "/oname=erp-api.exe"`
    ; da Section Install nao consegue sobrescrever: o instalador conclui "com
    ; sucesso" e o cliente segue rodando o BACKEND ANTIGO. Foi o que segurou o fix
    ; do IMEI na loja em 01/08/2026 -- reinstalar o app nao adiantava nada.
    DetailPrint "Parando o servidor StartBig antes de atualizar..."

    ; /End encerra a instancia da task. Nao espera o processo morrer, e uma
    ; instalacao anterior pode ter deixado um erp-api orfao (sem task nenhuma),
    ; entao o taskkill logo abaixo cobre os dois casos.
    nsExec::Exec 'schtasks /End /TN "StartBigServer"'
    Pop $0

    nsExec::Exec 'taskkill /F /T /IM "erp-api.exe"'
    Pop $0

    ; Da tempo do Windows liberar o lock do arquivo antes da copia.
    Sleep 2000
!macroend

!macro NSIS_HOOK_POSTINSTALL
    DetailPrint "Configurando o Firewall do Windows para o Servidor API de Rede e Ping..."
    
    ; 1. Regra de Entrada TCP para a API (erp-api.exe), so da rede da loja (D-21).
    ; Apaga ANTES de criar: numa atualizacao, a regra antiga (aberta para qualquer
    ; endereco) nao pode sobrar ao lado da nova -- o firewall libera se QUALQUER
    ; regra liberar.
    nsExec::Exec 'netsh advfirewall firewall delete rule name="${FIREWALL_RULE_NAME}"'
    Pop $0
    nsExec::Exec 'netsh advfirewall firewall add rule name="${FIREWALL_RULE_NAME}" dir=in action=allow program="$INSTDIR\erp-api.exe" profile=any remoteip=${REDES_DA_LOJA} description="Recebe conexoes so da rede da loja."'
    Pop $0
    ${If} $0 != 0
        DetailPrint "AVISO: Nao foi possivel criar a regra de firewall da API automaticamente."
    ${EndIf}

    ; 1b. Regras que o backend criou ao virar servidor (porta da API e mDNS).
    ; O instalador nao sabe a porta da API (ela fica no system-config.json do
    ; usuario), entao nao recria: "set rule ... new remoteip=" so restringe as
    ; regras que JA existem, mantendo a porta. Nos caixas elas nao existem, o
    ; comando falha sem efeito e nenhuma regra nova e criada (LIC-04, Revisao 2).
    nsExec::Exec 'netsh advfirewall firewall set rule name="${FIREWALL_BACKEND_API}" new remoteip=${REDES_DA_LOJA}'
    Pop $0
    nsExec::Exec 'netsh advfirewall firewall set rule name="${FIREWALL_BACKEND_MDNS}" new remoteip=${REDES_DA_LOJA}'
    Pop $0

    ; 2. Regra de Entrada ICMPv4 (Ping) para testar a conectividade do servidor
    nsExec::Exec 'netsh advfirewall firewall add rule name="${FIREWALL_PING_RULE_NAME}" protocol=icmpv4:8,any dir=in action=allow description="Permite recebimento de Ping (ICMPv4) dos terminais da rede."'
    Pop $0
    ${If} $0 != 0
        DetailPrint "AVISO: Nao foi possivel criar a regra de firewall para Ping automaticamente."
    ${EndIf}

    ; 3. Religa o servidor que o PREINSTALL parou, ja com o binario novo.
    ; Falha (e nao faz nada) quando a task nao existe -- caso das maquinas de
    ; terminal, que nao rodam backend proprio.
    DetailPrint "Reiniciando o servidor StartBig..."
    nsExec::Exec 'schtasks /Run /TN "StartBigServer"'
    Pop $0
    ${If} $0 != 0
        DetailPrint "INFO: Nenhum servidor local para reiniciar (instalacao de terminal)."
    ${EndIf}
!macroend

!macro NSIS_HOOK_POSTUNINSTALL
    ; 1. Para e desinstala o servico do backend
    DetailPrint "Parando e desinstalando o servico do backend..."
    nsExec::Exec '"$INSTDIR\erp-api.exe" --stop --uninstall'
    Pop $0
    ${If} $0 != 0
        DetailPrint "AVISO: Nao foi possivel parar/desinstalar o servico do backend."
    ${EndIf}

    ; 2. Remove as regras do Firewall
    DetailPrint "Removendo regras do Firewall..."

    ; Remove a regra da API
    nsExec::Exec 'netsh advfirewall firewall delete rule name="${FIREWALL_RULE_NAME}"'
    Pop $0

    ; Remove a regra do Ping
    nsExec::Exec 'netsh advfirewall firewall delete rule name="${FIREWALL_PING_RULE_NAME}"'
    Pop $0
!macroend