# ---------------------------------------------------------------------------
# ARQUIVO: schemas/licenca/renovacao.py
# DESCRICAO: Schemas da licenca - renovacao paga (periodos, planos, cobranca).
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ===========================================================================
# Renovação de Assinatura (Etapa 6) — PIX e cartão
# ===========================================================================
#
# Dois vocabulários convivem aqui, de propósito:
#
#   - o que vai e volta da API StartBig usa camelCase (`valorCentavos`), como
#     todos os payloads das etapas anteriores;
#   - o que este backend devolve ao frontend da loja usa snake_case
#     (`valor_centavos`), como o resto da API local.
#
# A tradução mora num lugar só: `services/licenca/renovacao.py`. Se a nuvem
# renomear um campo, é lá que se conserta -- e em nenhum outro lugar.


class RenovacaoCredenciaisPayload(BaseModel):
    """Par que autentica a loja nos endpoints de renovação da API StartBig.

    O mesmo de `ValidarPayload`: não há token novo nem sessão à parte."""
    chave: str = Field(..., description="Chave de ativação (descriptografada)")
    hwid: str = Field(..., description="Hardware ID da máquina")


class RenovacaoPeriodoRead(BaseModel):
    """Um período comprável do plano da licença — resposta ao frontend."""
    codigo: str = Field(..., description="Código do período (ex: MENSAL)")
    nome: str = Field(..., description="Nome exibível (ex: Mensal)")
    valor_centavos: int = Field(..., description="Preço em centavos, decidido pelo servidor")
    dias: Optional[int] = Field(None, description="Dias somados ao vencimento, quando informado")
    meses: Optional[int] = Field(
        None,
        description=(
            "Meses do período. É o que a API manda hoje — `dias` fica nulo, e a "
            "tela usa o que vier."
        ),
    )
    desconto: Optional[float] = Field(
        None,
        description=(
            "Fração de desconto do período longo (0.05 = 5%). Vem da API; a tela "
            "só mostra, nunca calcula preço."
        ),
    )
    metodos: list[str] = Field(
        default_factory=list,
        description="Métodos aceitos neste período: PIX, CARTAO",
    )


class RenovacaoPlanosRead(BaseModel):
    """Períodos disponíveis, ou o aviso de que a renovação ainda não está no ar.

    `disponivel=False` NÃO é erro: é o estado normal enquanto a API de cobrança
    não subiu. O frontend usa isso para mostrar o botão como indisponível em vez
    de uma tela quebrada.
    """
    disponivel: bool = Field(..., description="False quando a API de cobrança ainda não responde")
    periodos: list[RenovacaoPeriodoRead] = Field(default_factory=list)
    motivo: Optional[str] = Field(None, description="Por que está indisponível, quando estiver")
    plano: Optional[str] = Field(
        None, description="Nome do plano contratado (ex: 'Plano Start')"
    )
    limite_terminais: Optional[int] = Field(
        None,
        description=(
            "Quantos computadores o plano permite ao mesmo tempo. Vem da licença "
            "LOCAL, não da API — o número já está aqui desde o cadastro."
        ),
    )


class CobrancaCreate(BaseModel):
    """Pedido de cobrança vindo da tela da loja."""
    metodo: str = Field(..., description="PIX ou CARTAO")
    periodo: str = Field(..., description="Código do período escolhido")


class CobrancaRead(BaseModel):
    """Cobrança criada.

    PIX e cartão devolvem o mesmo schema com metades diferentes preenchidas:
    PIX traz `pix_copia_e_cola` (e talvez o QR pronto), cartão traz
    `url_checkout` para o app abrir no navegador. Um schema só porque a tela é
    uma só -- quem decide o que mostrar é o `metodo`.
    """
    cobranca_id: str
    metodo: str
    valor_centavos: int
    descricao: Optional[str] = None
    expira_em: Optional[datetime] = None

    # PIX
    pix_copia_e_cola: Optional[str] = Field(
        None,
        description="BR Code. É o único campo obrigatório do PIX — o app desenha o QR a partir dele.",
    )
    qr_code_base64: Optional[str] = Field(
        None, description="Imagem pronta do QR, quando o servidor mandar"
    )

    # Cartão
    url_checkout: Optional[str] = Field(
        None, description="URL do checkout para abrir no navegador"
    )


class CobrancaStatusRead(BaseModel):
    """Status da cobrança, consultado enquanto a tela de pagamento está aberta."""
    cobranca_id: str
    status: str = Field(..., description="PENDENTE | PAGA | EXPIRADA | CANCELADA")
    pago_em: Optional[datetime] = None
    data_vencimento: Optional[datetime] = Field(
        None, description="Vencimento novo, quando a cobrança já foi paga"
    )
    licenca_renovada: bool = Field(
        False,
        description=(
            "True quando este backend JÁ revalidou a licença e gravou o vencimento "
            "novo. É o sinal de que a loja destravou — não basta `status=PAGA`."
        ),
    )
