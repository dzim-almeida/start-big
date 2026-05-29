// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use tauri_plugin_stronghold::Builder as StrongholdBuilder;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(
            StrongholdBuilder::new(|password| {
                use argon2::{hash_raw, Config, Variant, Version};

                // Configuração do Argon2 para derivação de chave
                // NOTA: Esses valores são para teste. Em produção, aumentar mem_cost
                let config = Config {
                    lanes: 4,
                    mem_cost: 4096,    // 4MB - valor baixo para teste
                    time_cost: 1,      // 1 iteração para teste
                    variant: Variant::Argon2id,
                    version: Version::Version13,
                    hash_length: 32,
                    ..Default::default()
                };

                let salt = "gyUw!mNy=WE)".as_bytes();
                let key =
                    hash_raw(password.as_ref(), salt, &config).expect("failed to hash password");

                key.to_vec()
            })
            .build(),
        )
        .plugin(tauri_plugin_keyring::init())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
