// ---------------------------------------------------------------------------
// ARQUIVO: hwid.rs
// DESCRIÇÃO: Obtém o identificador único da máquina (HWID) de forma nativa.
//            Windows: lê MachineGuid do registro.
//            Linux: lê /etc/machine-id.
// ---------------------------------------------------------------------------

/// Retorna o Hardware ID da máquina.
///
/// - Windows: `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid`
/// - Linux: `/etc/machine-id`
#[tauri::command]
pub fn obter_hwid() -> Result<String, String> {
    #[cfg(target_os = "windows")]
    {
        obter_hwid_windows()
    }

    #[cfg(target_os = "linux")]
    {
        obter_hwid_linux()
    }

    #[cfg(not(any(target_os = "windows", target_os = "linux")))]
    {
        Err("Sistema operacional não suportado para leitura de HWID".into())
    }
}

#[cfg(target_os = "windows")]
fn obter_hwid_windows() -> Result<String, String> {
    use winreg::enums::HKEY_LOCAL_MACHINE;
    use winreg::RegKey;

    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    let key = hklm
        .open_subkey("SOFTWARE\\Microsoft\\Cryptography")
        .map_err(|e| format!("Falha ao abrir chave do registro: {e}"))?;

    let guid: String = key
        .get_value("MachineGuid")
        .map_err(|e| format!("Falha ao ler MachineGuid: {e}"))?;

    Ok(guid.trim().to_string())
}

#[cfg(target_os = "linux")]
fn obter_hwid_linux() -> Result<String, String> {
    std::fs::read_to_string("/etc/machine-id")
        .map(|s| s.trim().to_string())
        .map_err(|e| format!("Falha ao ler /etc/machine-id: {e}"))
}
