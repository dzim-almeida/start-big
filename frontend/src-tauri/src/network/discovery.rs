use mdns_sd::{ServiceDaemon, ServiceEvent, ServiceInfo};
use serde::{Deserialize, Serialize};
use std::net::IpAddr;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use tauri::{AppHandle, Emitter};

const TIPO_SERVICO: &str = "_startbig._tcp.local.";

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DiscoveryPayload {
    pub app: String,
    pub role: String,
    pub ip: String,
    pub port: u16,
}

#[derive(Default)]
pub struct EstadoDescoberta {
    daemon_servidor: Mutex<Option<ServiceDaemon>>,
    nome_servico: Mutex<Option<String>>,
    daemon_cliente: Mutex<Option<ServiceDaemon>>,
    parar_cliente: Mutex<Option<Arc<AtomicBool>>>,
}

impl EstadoDescoberta {
    fn parar_servidor(&self) {
        let mut daemon_guard = self.daemon_servidor.lock().unwrap();
        let mut nome_guard = self.nome_servico.lock().unwrap();

        if let (Some(daemon), Some(nome)) = (daemon_guard.as_ref(), nome_guard.as_ref()) {
            if let Err(e) = daemon.unregister(nome) {
                eprintln!("[discovery] Erro ao desregistrar servico mDNS: {:?}", e);
            }
        }

        if let Some(daemon) = daemon_guard.take() {
            if let Err(e) = daemon.shutdown() {
                eprintln!("[discovery] Erro ao encerrar daemon servidor: {:?}", e);
            }
        }

        *nome_guard = None;
    }

    fn parar_cliente(&self) {
        if let Some(flag) = self.parar_cliente.lock().unwrap().take() {
            flag.store(false, Ordering::SeqCst);
        }

        if let Some(daemon) = self.daemon_cliente.lock().unwrap().take() {
            if let Err(e) = daemon.shutdown() {
                eprintln!("[discovery] Erro ao encerrar daemon cliente: {:?}", e);
            }
        }
    }

    pub fn shutdown(&self) {
        self.parar_servidor();
        self.parar_cliente();
    }
}

pub fn start_discovery(estado: &EstadoDescoberta, server_ip: String, server_port: u16) {
    estado.parar_servidor();

    let ip = if server_ip == "0.0.0.0" {
        crate::impressao::obter_ip_local()
            .unwrap_or_else(|_| "127.0.0.1".to_string())
    } else {
        server_ip
    };

    let daemon = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("[discovery] Falha ao criar daemon mDNS: {:?}", e);
            return;
        }
    };

    let hostname = format!("{}.local.", gethostname());
    let instance_name = "startbig-server";

    let properties = [("app", "startbig"), ("role", "server")];

    let service_info = match ServiceInfo::new(
        TIPO_SERVICO,
        instance_name,
        &hostname,
        &ip,
        server_port,
        &properties[..],
    ) {
        Ok(info) => info,
        Err(e) => {
            eprintln!("[discovery] Falha ao criar ServiceInfo: {:?}", e);
            let _ = daemon.shutdown();
            return;
        }
    };

    let fullname = service_info.get_fullname().to_string();

    if let Err(e) = daemon.register(service_info) {
        eprintln!("[discovery] Falha ao registrar servico mDNS: {:?}", e);
        let _ = daemon.shutdown();
        return;
    }

    println!(
        "[discovery] Servico mDNS registrado: {} ({}:{})",
        fullname, ip, server_port
    );

    *estado.daemon_servidor.lock().unwrap() = Some(daemon);
    *estado.nome_servico.lock().unwrap() = Some(fullname);
}

pub fn discover_servers(estado: &EstadoDescoberta, handle: AppHandle) {
    estado.parar_cliente();

    let daemon = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("[discovery] Falha ao criar daemon mDNS cliente: {:?}", e);
            return;
        }
    };

    let receiver = match daemon.browse(TIPO_SERVICO) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("[discovery] Falha ao iniciar browse mDNS: {:?}", e);
            let _ = daemon.shutdown();
            return;
        }
    };

    let rodando = Arc::new(AtomicBool::new(true));

    *estado.parar_cliente.lock().unwrap() = Some(rodando.clone());
    *estado.daemon_cliente.lock().unwrap() = Some(daemon);

    println!("[discovery] Terminal buscando servidores via mDNS...");

    thread::spawn(move || {
        while rodando.load(Ordering::SeqCst) {
            match receiver.recv_timeout(Duration::from_secs(2)) {
                Ok(ServiceEvent::ServiceResolved(info)) => {
                    let port = info.get_port();
                    let ip = info
                        .get_addresses()
                        .iter()
                        .find(|addr| ip_e_privado(**addr))
                        .or_else(|| info.get_addresses().iter().next())
                        .map(|addr| addr.to_string())
                        .unwrap_or_default();

                    if ip.is_empty() {
                        continue;
                    }

                    let app_prop = info
                        .get_property_val_str("app")
                        .unwrap_or("startbig");
                    let role_prop = info
                        .get_property_val_str("role")
                        .unwrap_or("server");

                    let payload = DiscoveryPayload {
                        app: app_prop.to_string(),
                        role: role_prop.to_string(),
                        ip: ip.clone(),
                        port,
                    };

                    println!(
                        "[discovery] Servidor encontrado via mDNS: IP={}, Porta={}",
                        ip, port
                    );

                    handle.emit("server_discovered", &payload).unwrap_or_else(
                        |e| eprintln!("[discovery] Erro ao emitir evento: {}", e),
                    );
                }
                Ok(_) => {}
                Err(flume::RecvTimeoutError::Timeout) => continue,
                Err(flume::RecvTimeoutError::Disconnected) => {
                    println!("[discovery] Canal mDNS desconectado, encerrando thread");
                    break;
                }
            }
        }

        println!("[discovery] Thread de descoberta encerrada");
    });
}

#[tauri::command]
pub fn iniciar_descoberta_servidores(
    app: AppHandle,
    state: tauri::State<'_, EstadoDescoberta>,
) {
    discover_servers(&state, app);
}

#[tauri::command]
pub fn parar_descoberta_servidores(state: tauri::State<'_, EstadoDescoberta>) {
    state.parar_cliente();
    println!("[discovery] Comando recebido para parar a descoberta.");
}

fn gethostname() -> String {
    std::env::var("COMPUTERNAME")
        .or_else(|_| std::env::var("HOSTNAME"))
        .unwrap_or_else(|_| "startbig-host".to_string())
}

fn ip_e_privado(ip: IpAddr) -> bool {
    if let IpAddr::V4(v4) = ip {
        let o = v4.octets();
        return o[0] == 10
            || (o[0] == 172 && o[1] >= 16 && o[1] <= 31)
            || (o[0] == 192 && o[1] == 168);
    }
    false
}
