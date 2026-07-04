mod backend;
mod impressao;
mod config_server;

use tauri::{Manager, RunEvent};

use backend::{cleanup_on_exit, AppState};
use impressao::{
    descobrir_servidores_impressao, imprimir_raw, imprimir_rede, iniciar_servidor_impressao,
    listar_impressoras, obter_ip_local, parar_servidor_impressao, EstadoServidorImpressao,
};
use config_server::{load_config, set_role_client, set_role_server, get_api_url, get_config};

use crate::backend::setup_sidecar;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            listar_impressoras,
            imprimir_raw,
            iniciar_servidor_impressao,
            parar_servidor_impressao,
            descobrir_servidores_impressao,
            obter_ip_local,
            imprimir_rede,
            set_role_server,
            set_role_client,
            get_api_url,
            get_config
        ])
        .setup(move |app| {
            let server_config = load_config(app.app_handle());

            app.manage(AppState {
                process: std::sync::Mutex::new(None),
            });

            app.manage(
                EstadoServidorImpressao::default()
            );

            if server_config.is_server {
                setup_sidecar(app.app_handle(), &server_config.server_ip, server_config.server_port)?;
            }
        
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            cleanup_on_exit(app_handle);
        }
    });
}
