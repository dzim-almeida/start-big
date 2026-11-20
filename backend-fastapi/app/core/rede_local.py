"""
Rede da loja (LIC-04 §6.5, ACORDO D-21, F34).

A API local roda em `0.0.0.0` para os caixas da loja conseguirem chamá-la. Sem
filtro, qualquer computador que alcançasse a porta (por exemplo, por um roteador
mal configurado) também conseguiria. Este módulo é a segunda camada de proteção:
a primeira é o firewall do Windows, que usa a MESMA lista de redes (o `hooks.nsh`
do instalador e o `system.py` repetem `REDES_DA_LOJA`, e o teste CT-16 confere).
"""
import ipaddress  # biblioteca padrão do Python para comparar endereços IP

from starlette.responses import JSONResponse  # resposta de erro em JSON
from starlette.types import ASGIApp, Receive, Scope, Send  # tipos do "protocolo" ASGI

# Lista ÚNICA das redes da loja (vai também para o firewall, sem o "próprio computador").
# - 10/8, 172.16/12 e 192.168/16: as redes privadas que as lojas usam;
# - 169.254/16: o endereço que o Windows se dá quando o roteador falha em entregar IP.
REDES_DA_LOJA = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16"]

# O próprio computador. Só o middleware precisa dele: o firewall não filtra o
# tráfego local.
_LOCAIS = ["127.0.0.0/8", "::1/128"]

# Converte o texto ("10.0.0.0/8") em objetos de rede uma vez só, ao importar o módulo.
_REDES = [ipaddress.ip_network(rede) for rede in REDES_DA_LOJA + _LOCAIS]


def endereco_permitido(host: str) -> bool:
    """Diz se o endereço de quem chama está na rede da loja ou é este computador."""
    try:
        ip = ipaddress.ip_address(host)  # converte o texto em endereço IP
    except ValueError:
        return False  # texto que não é IP (ex.: nome de máquina) é recusado
    # `ip in rede` só faz sentido entre versões iguais (IPv4 com IPv4, IPv6 com IPv6).
    return any(ip in rede for rede in _REDES if ip.version == rede.version)


class ExigirRedeDaLoja:
    """
    Middleware: um "porteiro" que o FastAPI chama antes de cada requisição.

    Se o endereço de quem chama está fora da rede da loja, ele responde 403 e a
    requisição nem chega às rotas. Dentro da rede, passa a requisição adiante.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app  # o resto da aplicação (as rotas e os outros middlewares)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Só filtramos chamadas HTTP. O "lifespan" (startup/shutdown) não tem endereço.
        if scope["type"] == "http":
            # scope["client"] é a dupla (endereço, porta) de quem abriu a conexão
            cliente = scope.get("client")
            host = cliente[0] if cliente else ""
            if not endereco_permitido(host):
                # Mesmo formato dos outros erros que a tela trata por código (D-29).
                resposta = JSONResponse(
                    status_code=403,
                    content={
                        "error": "Fora da rede da loja",
                        "detail": {
                            "codigo": "FORA_DA_REDE_DA_LOJA",
                            "mensagem": "Esta API só aceita conexões da rede da loja.",
                        },
                    },
                )
                await resposta(scope, receive, send)  # responde o erro e para aqui
                return
        await self.app(scope, receive, send)  # dentro da rede: segue normalmente
