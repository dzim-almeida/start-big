mod backend;
mod config_server;
mod impressao;

use tauri::{Manager, RunEvent};

use backend::{cleanup_on_exit, AppState};
use config_server::{get_api_url, get_config, set_role_client, set_role_server};
use impressao::{
    descobrir_servidores_impressao, imprimir_raw, imprimir_rede, iniciar_servidor_impressao,
    listar_impressoras, obter_ip_local, parar_servidor_impressao, EstadoServidorImpressao,
};

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
            app.manage(AppState {
                process: std::sync::Mutex::new(None),
            });

            app.manage(EstadoServidorImpressao::default());

            #[cfg(not(debug_assertions))]
            {
                use crate::backend::setup_sidecar;
                use crate::config_server::gen_network_config_txt;
                use crate::config_server::load_config;

                let handle = app.app_handle();

                let server_config = load_config(&handle);
                if server_config.is_server {
                    setup_sidecar(
                        &handle,
                        &server_config.server_ip,
                        server_config.server_port,
                    )?;
                    gen_network_config_txt(
                        &handle,
                        obter_ip_local().unwrap_or_default(),
                        server_config.server_port,
                    );
                }
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
