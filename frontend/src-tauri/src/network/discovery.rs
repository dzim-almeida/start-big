use serde::{Deserialize, Serialize};
use std::net::UdpSocket;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;
use tauri::{AppHandle, Emitter};

static LISTENER_ATIVO: AtomicBool = AtomicBool::new(false);

const DISCOVERY_PORT: u16 = 8888;
const BROADCAST_ADDR: &str = "255.255.255.255:8888";
const BROADCAST_INTERVAL_SECS: u64 = 5;
const SOCKET_TIMEOUT_SECS: u64 = 2;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DiscoveryPayload {
    pub app: String,
    pub role: String,
    pub ip: String,
    pub port: u16,
}

pub fn start_discovery(server_ip: String, server_port: u16) {
    thread::spawn(move || {
        let socket = UdpSocket::bind("0.0.0.0:0").expect("Falha ao abrir socket UDP para broadcast");
        socket
            .set_broadcast(true)
            .expect("Falha ao ativar modo broadcast");

        let payload = DiscoveryPayload {
            app: "startbig".to_string(),
            role: "server".to_string(),
            ip: server_ip,
            port: server_port,
        };

        let msg_bytes = serde_json::to_vec(&payload).unwrap();

        println!(
            "[discovery] Servidor de autodescoberta iniciado. Transmitindo em {}",
            BROADCAST_ADDR
        );

        loop {
            match socket.send_to(&msg_bytes, BROADCAST_ADDR) {
                Ok(_) => {
                    println!("[discovery] Ping enviado");
                }
                Err(e) => {
                    eprintln!("[discovery] Erro ao enviar broadcast: {}", e);
                }
            }

            thread::sleep(Duration::from_secs(BROADCAST_INTERVAL_SECS));
        }
    });
}

pub fn discover_servers(handle: AppHandle) {
    if LISTENER_ATIVO
        .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        println!("[discovery] Listener ja ativo, ignorando chamada duplicada");
        return;
    }

    thread::spawn(move || {
        let socket = match UdpSocket::bind(format!("0.0.0.0:{}", DISCOVERY_PORT)) {
            Ok(s) => s,
            Err(e) => {
                eprintln!(
                    "[discovery] Falha ao abrir socket UDP na porta {}: {}",
                    DISCOVERY_PORT, e
                );
                LISTENER_ATIVO.store(false, Ordering::SeqCst);
                return;
            }
        };

        socket
            .set_read_timeout(Some(Duration::from_secs(SOCKET_TIMEOUT_SECS)))
            .expect("Falha ao definir timeout do socket");

        println!(
            "[discovery] Terminal ouvindo transmissoes na porta {}...",
            DISCOVERY_PORT
        );

        let mut buf = [0; 1024];

        loop {
            if !LISTENER_ATIVO.load(Ordering::SeqCst) {
                println!("[discovery] Listener desativado, encerrando thread");
                break;
            }

            match socket.recv_from(&mut buf) {
                Ok((size, _src_addr)) => {
                    if let Ok(json_str) = std::str::from_utf8(&buf[..size]) {
                        if let Ok(payload) = serde_json::from_str::<DiscoveryPayload>(json_str) {
                            if payload.app == "startbig" && payload.role == "server" {
                                println!(
                                    "[discovery] Servidor encontrado: IP={}, Porta={}",
                                    payload.ip, payload.port
                                );
                                handle.emit("server_discovered", &payload).unwrap_or_else(
                                    |e| eprintln!("[discovery] Erro ao emitir evento: {}", e),
                                );
                            }
                        }
                    }
                }
                Err(ref e)
                    if e.kind() == std::io::ErrorKind::WouldBlock
                        || e.kind() == std::io::ErrorKind::TimedOut =>
                {
                    // Timeout do socket — continua ouvindo
                    continue;
                }
                Err(e) => {
                    eprintln!("[discovery] Erro ao receber pacote UDP: {}", e);
                }
            }
        }
    });
}

#[tauri::command]
pub fn iniciar_descoberta_servidores(app: AppHandle) {
    discover_servers(app.clone());
}

#[tauri::command]
pub fn parar_descoberta_servidores() {
    LISTENER_ATIVO.store(false, Ordering::SeqCst);
    println!("[discovery] Comando recebido para parar a descoberta.");
}
