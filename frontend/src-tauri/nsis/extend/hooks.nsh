!define FIREWALL_RULE_NAME "StartBigERP_API_Server"

!macro NSIS_HOOK_POSTINSTALL

    DetailPrint "Configurando o Firewall do Windows para o Servidor API de Rede..."
    
    nsExec::Exec 'netsh advfirewall firewall add rule name="${FIREWALL_RULE_NAME}" dir=in action=allow program="$INSTDIR\erp-api.exe" profile=any description="Regra de Entrada TCP para permitir conexões de terminais ao servidor BigPDV."'
    Pop $0

    ${If} $0 != 0
        DetailPrint "AVISO: Não foi possível criar a regra de firewall automaticamente."
    ${EndIf}

!macroend

!macro NSIS_HOOK_POSTUNINSTALL

    DetailPrint "Removendo regras do Firewall..."

    nsExec::Exec 'netsh advfirewall firewall delete rule name="${FIREWALL_RULE_NAME}"'
    Pop $0

!macroend