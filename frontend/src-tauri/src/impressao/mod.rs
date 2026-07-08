mod local;
mod rede;

pub use local::{imprimir_raw, listar_impressoras};
pub use rede::{
    descobrir_servidores_impressao, imprimir_rede, iniciar_servidor_impressao, obter_ip_local,
    parar_servidor_impressao, EstadoServidorImpressao,
};
