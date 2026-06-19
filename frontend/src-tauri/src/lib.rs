// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/

use std::net::TcpListener;
use std::sync::Mutex;
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct AppState {
    process: Mutex<Option<CommandChild>>,
    port: u16,
}

fn get_free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .expect("Falha ao busca uma porta livre no sistema")
        .local_addr()
        .unwrap()
        .port()
}

#[tauri::command]
fn get_backend_port(state: tauri::State<AppState>) -> u16 {
    state.port
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let port = get_free_port();

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![get_backend_port])
        .setup(move |app| {
            let sidecar_command = app
                .shell()
                .sidecar("erp-api")
                .expect("Falha ao criar o comando do sidecar FastAPI")
                .arg(port.to_string());

            let (mut rx, child) = sidecar_command
                .spawn()
                .expect("Falha ao inicializar o processo do FastAPI");

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                            println!("FastAPI [LOG]: {}", String::from_utf8_lossy(&line));
                        }
                        tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                            println!("FastAPI [ERR]: {}", String::from_utf8_lossy(&line));
                        }
                        _ => {}
                    }
                }
            });

            app.manage(AppState {
                process: Mutex::new(Some(child)),
                port,
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            let state = app_handle.state::<AppState>();

            if let Ok(mut process_guard) = state.inner().process.lock() {
                if let Some(process) = process_guard.take() {
                    let pid = process.pid();
                    #[cfg(target_os = "windows")]
                    {
                        use std::os::windows::process::CommandExt;
                        const CREATE_NO_WINDOW: u32 = 0x08000000;

                        let _ = std::process::Command::new("taskkill")
                            .args(["/F", "/T", "/PID", &pid.to_string()])
                            .creation_flags(CREATE_NO_WINDOW)
                            .output();
                    }

                    #[cfg(not(target_os = "windows"))]
                    {
                        let _ = process.kill();
                    }
                }
            }
        }
    });
}
