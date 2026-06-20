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

fn ip_e_privado(ip: std::net::IpAddr) -> bool {
    if let std::net::IpAddr::V4(v4) = ip {
        let o = v4.octets();
        return o[0] == 10
            || (o[0] == 172 && o[1] >= 16 && o[1] <= 31)
            || (o[0] == 192 && o[1] == 168);
    }
    false
}

// Descobre o IP LAN privado deste PC tentando múltiplos destinos e filtrando
// IPs públicos (ex: adaptadores Topaz Loopback, VPN, etc.)
fn ip_lan_privado() -> Option<std::net::IpAddr> {
    let candidatos = ["8.8.8.8:80", "192.168.0.1:80", "192.168.1.1:80", "10.0.0.1:80"];
    for dest in &candidatos {
        if let Ok(s) = std::net::UdpSocket::bind("0.0.0.0:0") {
            if s.connect(dest).is_ok() {
                if let Ok(addr) = s.local_addr() {
                    if ip_e_privado(addr.ip()) {
                        return Some(addr.ip());
                    }
                }
            }
        }
    }
    None
}

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
                        let ip_lan = ip_lan_privado()
                            .map(|ip| ip.to_string())
                            .unwrap_or_default();
                        let resposta = format!(
                            "{{\"nome\":{:?},\"porta\":{},\"ip\":\"{}\"}}",
                            nome_terminal, porta, ip_lan
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
            // Prefere o IP que o servidor incluiu no corpo (IP da LAN real),
            // com fallback para origem.ip() em servidores com versão antiga
            let ip = texto
                .split("\"ip\":\"")
                .nth(1)
                .and_then(|s| s.split('"').next())
                .filter(|s| !s.is_empty())
                .map(|s| s.to_string())
                .unwrap_or_else(|| origem.ip().to_string());
            if servidores.iter().any(|s| s.ip == ip) {
                continue;
            }
            let nome = texto
                .split("\"nome\":")
                .nth(1)
                .and_then(|s| s.split('"').nth(1))
                .unwrap_or("Caixa")
                .to_string();
            let porta = texto
                .split("\"porta\":")
                .nth(1)
                .and_then(|s| s.split(|c| c == ',' || c == '}').next())
                .and_then(|n| n.trim().parse::<u16>().ok())
                .unwrap_or(9100);
            servidores.push(ServidorDescoberto { nome, ip, porta });
        }
    }
    Ok(servidores)
}

#[tauri::command(async)]
fn obter_ip_local() -> Result<String, String> {
    ip_lan_privado()
        .map(|ip| ip.to_string())
        .ok_or_else(|| "Nenhum IP privado encontrado".to_string())
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
