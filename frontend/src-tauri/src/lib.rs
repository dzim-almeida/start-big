// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use tauri_plugin_stronghold::Builder as StrongholdBuilder;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[derive(serde::Serialize)]
struct ImpressoraInfo {
    nome: String,
    padrao: bool,
}

#[tauri::command(async)]
fn listar_impressoras() -> Result<Vec<ImpressoraInfo>, String> {
    Ok(printers::get_printers()
        .into_iter()
        .map(|p| ImpressoraInfo {
            nome: p.name,
            padrao: p.is_default,
        })
        .collect())
}

#[tauri::command(async)]
fn imprimir_raw(nome_impressora: String, dados: Vec<u8>) -> Result<(), String> {
    let impressora = printers::get_printer_by_name(&nome_impressora)
        .ok_or_else(|| format!("Impressora '{}' não encontrada no Windows", nome_impressora))?;
    impressora
        .print(&dados, printers::common::base::job::PrinterJobOptions::none())
        .map(|_job_id| ())
        .map_err(|e| format!("Falha ao enviar para o spooler: {:?}", e))
}

// ── Servidor de impressão na LAN ──
// O PC que tem a térmica USB emula uma impressora de rede: aceita bytes RAW
// por TCP (como a porta 9100 de uma térmica Ethernet) e repassa ao spooler.
// A descoberta UDP permite que os outros caixas o encontrem sem digitar IP.

const PORTA_DESCOBERTA: u16 = 9101;
const MENSAGEM_DESCOBERTA: &[u8] = b"BIGPDV_DISCOVER";

#[derive(Default)]
struct EstadoServidorImpressao(std::sync::Mutex<Option<std::sync::Arc<std::sync::atomic::AtomicBool>>>);

#[derive(serde::Serialize)]
struct ServidorDescoberto {
    nome: String,
    ip: String,
    porta: u16,
}

fn atender_conexao_impressao(
    mut conexao: std::net::TcpStream,
    nome_impressora: &str,
) -> Result<(), String> {
    use std::io::Read;

    conexao
        .set_read_timeout(Some(std::time::Duration::from_secs(10)))
        .map_err(|e| e.to_string())?;
    let mut dados: Vec<u8> = Vec::new();
    let mut buffer = [0u8; 4096];
    loop {
        match conexao.read(&mut buffer) {
            Ok(0) => break,
            Ok(n) => {
                dados.extend_from_slice(&buffer[..n]);
                if dados.len() > 1_000_000 {
                    return Err("Trabalho de impressão excede 1MB".into());
                }
            }
            Err(e) => return Err(e.to_string()),
        }
    }
    if dados.is_empty() {
        return Ok(());
    }
    let impressora = printers::get_printer_by_name(nome_impressora)
        .ok_or_else(|| format!("Impressora '{}' não encontrada", nome_impressora))?;
    impressora
        .print(&dados, printers::common::base::job::PrinterJobOptions::none())
        .map(|_| ())
        .map_err(|e| format!("{:?}", e))
}

#[tauri::command(async)]
fn iniciar_servidor_impressao(
    state: tauri::State<'_, EstadoServidorImpressao>,
    porta: u16,
    nome_impressora: String,
    nome_terminal: String,
) -> Result<(), String> {
    use std::sync::atomic::{AtomicBool, Ordering};
    use std::sync::Arc;
    use std::time::Duration;

    // Para o servidor anterior, se houver
    if let Some(flag) = state.0.lock().unwrap().take() {
        flag.store(false, Ordering::SeqCst);
    }

    let listener = std::net::TcpListener::bind(("0.0.0.0", porta))
        .map_err(|_| format!("Porta {} já está em uso neste PC", porta))?;
    listener.set_nonblocking(true).map_err(|e| e.to_string())?;

    let udp = std::net::UdpSocket::bind(("0.0.0.0", PORTA_DESCOBERTA))
        .map_err(|_| format!("Porta de descoberta {} já está em uso", PORTA_DESCOBERTA))?;
    udp.set_read_timeout(Some(Duration::from_millis(500)))
        .map_err(|e| e.to_string())?;

    let rodando = Arc::new(AtomicBool::new(true));
    *state.0.lock().unwrap() = Some(rodando.clone());

    // Thread TCP: recebe os bytes e imprime
    {
        let rodando = rodando.clone();
        let nome_impressora = nome_impressora.clone();
        std::thread::spawn(move || {
            while rodando.load(Ordering::SeqCst) {
                match listener.accept() {
                    Ok((conexao, _origem)) => {
                        if let Err(e) = atender_conexao_impressao(conexao, &nome_impressora) {
                            eprintln!("[servidor-impressao] erro ao imprimir: {}", e);
                        }
                    }
                    Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        std::thread::sleep(Duration::from_millis(200));
                    }
                    Err(e) => {
                        eprintln!("[servidor-impressao] erro no accept: {}", e);
                        std::thread::sleep(Duration::from_millis(500));
                    }
                }
            }
        });
    }

    // Thread UDP: responde à descoberta dos outros caixas
    {
        let rodando = rodando.clone();
        std::thread::spawn(move || {
            let mut buffer = [0u8; 64];
            while rodando.load(Ordering::SeqCst) {
                match udp.recv_from(&mut buffer) {
                    Ok((n, origem)) if &buffer[..n] == MENSAGEM_DESCOBERTA => {
                        let resposta = format!(
                            "{{\"nome\":{:?},\"porta\":{}}}",
                            nome_terminal, porta
                        );
                        let _ = udp.send_to(resposta.as_bytes(), origem);
                    }
                    _ => {} // timeout ou datagrama desconhecido — só checa a flag de novo
                }
            }
        });
    }

    Ok(())
}

#[tauri::command(async)]
fn parar_servidor_impressao(state: tauri::State<'_, EstadoServidorImpressao>) -> Result<(), String> {
    if let Some(flag) = state.0.lock().unwrap().take() {
        flag.store(false, std::sync::atomic::Ordering::SeqCst);
    }
    Ok(())
}

#[tauri::command(async)]
fn descobrir_servidores_impressao() -> Result<Vec<ServidorDescoberto>, String> {
    use std::time::{Duration, Instant};

    let udp = std::net::UdpSocket::bind(("0.0.0.0", 0)).map_err(|e| e.to_string())?;
    udp.set_broadcast(true).map_err(|e| e.to_string())?;
    udp.set_read_timeout(Some(Duration::from_millis(300)))
        .map_err(|e| e.to_string())?;
    udp.send_to(MENSAGEM_DESCOBERTA, ("255.255.255.255", PORTA_DESCOBERTA))
        .map_err(|e| format!("Falha ao enviar broadcast de descoberta: {}", e))?;

    let mut servidores: Vec<ServidorDescoberto> = Vec::new();
    let inicio = Instant::now();
    let mut buffer = [0u8; 256];
    while inicio.elapsed() < Duration::from_millis(1500) {
        if let Ok((n, origem)) = udp.recv_from(&mut buffer) {
            let texto = String::from_utf8_lossy(&buffer[..n]);
            let ip = origem.ip().to_string();
            if servidores.iter().any(|s| s.ip == ip) {
                continue;
            }
            // Resposta esperada: {"nome":"...","porta":9100}
            let nome = texto
                .split("\"nome\":")
                .nth(1)
                .and_then(|s| s.split('"').nth(1))
                .unwrap_or("Caixa")
                .to_string();
            let porta = texto
                .split("\"porta\":")
                .nth(1)
                .and_then(|s| s.trim_end_matches('}').trim().parse::<u16>().ok())
                .unwrap_or(9100);
            servidores.push(ServidorDescoberto { nome, ip, porta });
        }
    }
    Ok(servidores)
}

#[tauri::command(async)]
fn obter_ip_local() -> Result<String, String> {
    let udp = std::net::UdpSocket::bind("0.0.0.0:0").map_err(|e| e.to_string())?;
    udp.connect("8.8.8.8:80").map_err(|e| e.to_string())?;
    Ok(udp.local_addr().map_err(|e| e.to_string())?.ip().to_string())
}

#[tauri::command(async)]
fn imprimir_rede(ip: String, porta: u16, dados: Vec<u8>) -> Result<(), String> {
    use std::io::Write;
    use std::net::{SocketAddr, TcpStream};
    use std::time::Duration;

    let endereco: SocketAddr = format!("{}:{}", ip, porta)
        .parse()
        .map_err(|_| format!("Endereço inválido: {}:{}", ip, porta))?;
    let mut conexao = TcpStream::connect_timeout(&endereco, Duration::from_secs(3))
        .map_err(|e| format!("Não foi possível conectar à impressora {}:{} ({})", ip, porta, e))?;
    conexao
        .set_write_timeout(Some(Duration::from_secs(5)))
        .map_err(|e| e.to_string())?;
    conexao
        .write_all(&dados)
        .and_then(|_| conexao.flush())
        .map_err(|e| format!("Falha ao enviar dados à impressora de rede: {}", e))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(EstadoServidorImpressao::default())
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
        .invoke_handler(tauri::generate_handler![
            greet,
            listar_impressoras,
            imprimir_raw,
            imprimir_rede,
            iniciar_servidor_impressao,
            parar_servidor_impressao,
            descobrir_servidores_impressao,
            obter_ip_local
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
