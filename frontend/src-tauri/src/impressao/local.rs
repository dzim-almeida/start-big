#[derive(serde::Serialize)]
pub struct ImpressoraInfo {
    pub nome: String,
    pub padrao: bool,
}

#[tauri::command(async)]
pub fn listar_impressoras() -> Result<Vec<ImpressoraInfo>, String> {
    Ok(printers::get_printers()
        .into_iter()
        .map(|p| ImpressoraInfo {
            nome: p.name,
            padrao: p.is_default,
        })
        .collect())
}

#[tauri::command(async)]
pub fn imprimir_raw(nome_impressora: String, dados: Vec<u8>) -> Result<(), String> {
    let impressora = printers::get_printer_by_name(&nome_impressora)
        .ok_or_else(|| format!("Impressora '{}' não encontrada no Windows", nome_impressora))?;
    impressora
        .print(&dados, printers::common::base::job::PrinterJobOptions::none())
        .map(|_job_id| ())
        .map_err(|e| format!("Falha ao enviar para o spooler: {:?}", e))
}
