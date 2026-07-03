use std::sync::Mutex;

use tauri::{AppHandle, Manager};
use tauri_plugin_shell::{ShellExt, process::CommandChild};

pub struct AppState {
    pub process: Mutex<Option<CommandChild>>,
}

pub fn setup_sidecar(app_handle: &AppHandle, ip_address: &str, port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let state = app_handle.state::<AppState>();
    let mut process_guard = state.process.lock().unwrap();
    
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

    let sidecar_command = app_handle
        .shell()
        .sidecar("erp-api")
        .expect("Falha ao criar o comando do sidecar FastAPI")
        .args([ip_address, &port.to_string()]);

    let (mut rx, child) = sidecar_command
        .spawn()
        .expect("Falha ao iniciar o sidecar FastAPI");

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

    *process_guard = Some(child);

    Ok(())
}

pub fn cleanup_on_exit(app_handle: &tauri::AppHandle) {
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
        }
    }
}

