# ---------------------------------------------------------------------------
# ARQUIVO: app/services/fiscal/payload_destinatario.py
# DESCRIÇÃO: Bloco `destinatario{}` (NF-e, NFC-e e devolução avulsa), endereço
# e o idDest (local de destino).
#
# Saiu do payload_builder.py na F5 (07/10/2026), sem mudar comportamento: o
# código foi movido, não reescrito. O payload da nota não muda nem um byte
# (test_payload_fotografias.py).
# ---------------------------------------------------------------------------

import re
from typing import Optional
from app.db.models.cliente import Cliente, ClientePF, ClientePJ
from app.db.models.endereco import Endereco
from .tax_engine.types import ResultadoCalculo
from .payload_comum import _sanitizar_texto_sefaz, _so_digitos


def _montar_destinatario(cliente: Cliente) -> dict:
    dest: dict = {}

    if isinstance(cliente, ClientePJ):
        dest["cnpj"] = _so_digitos(cliente.cnpj)
        dest["razao_social"] = _sanitizar_texto_sefaz(cliente.razao_social)
        dest["nome"] = _sanitizar_texto_sefaz(cliente.razao_social)
        dest["inscricao_estadual"] = cliente.ie or ""
        # indicador_ie: 1=Contribuinte (tem IE), 9=Não contribuinte (sem IE)
        dest["indicador_ie"] = "1" if cliente.ie else "9"
    elif isinstance(cliente, ClientePF):
        dest["cpf"] = _so_digitos(cliente.cpf)
        dest["nome"] = _sanitizar_texto_sefaz(cliente.nome)
        dest["indicador_ie"] = "9"  # PF é sempre não contribuinte
    else:
        dest["nome"] = f"Cliente #{cliente.id}"
        dest["indicador_ie"] = "9"

    # Endereço do destinatário (primeiro endereço cadastrado).
    #
    # Grupo incompleto é rejeitado pela SEFAZ, e OMITIR TAMBÉM É — o comentário
    # anterior dizia que omitir era o mal menor, e a nota de teste provou o
    # contrário: 422 nomeando logradouro, número, bairro e município do
    # destinatário. Na NF-e o enderDest é obrigatório.
    #
    # A omissão continua aqui porque este mesmo construtor serve à NFC-e com
    # entrega a domicílio, e porque quem impede uma NF-e de chegar até aqui sem
    # endereço agora é o gate (`verificar_endereco_destinatario`), que recusa
    # ANTES de montar payload e reservar número, nomeando os campos que faltam
    # no cadastro do cliente. Este ponto é o último recurso, não a defesa.
    enderecos = getattr(cliente, "endereco", None)
    if enderecos and len(enderecos) > 0:
        endereco = _montar_endereco_destinatario(enderecos[0])
        if endereco:
            dest["endereco"] = endereco

    return dest


def _montar_destinatario_nfce(
    cliente: Optional[Cliente],
    documento_consumidor: Optional[str],
    entrega_domicilio: bool = False,
) -> Optional[dict]:
    """Destinatário da NFC-e — ou None para consumidor não identificado.

    Difere da NF-e em dois pontos, e os dois são exigência do modelo 65:

    1. **Pode não existir.** Na NF-e, sem cliente mandamos
       `{"nome": "CONSUMIDOR FINAL"}`. Na NFC-e o grupo `dest` inteiro é
       OMITIDO — mandá-lo só com um nome genérico, sem documento, é rejeitado.
    2. **Só o documento.** No varejo presencial não há endereço nem nome do
       comprador a informar; enviar o grupo de endereço incompleto derruba a
       autorização.

    Precedência: o cadastro do cliente vence, porque foi conferido; o CPF
    digitado no caixa é o caminho do consumidor de passagem.

    EXCEÇÃO — `entrega_domicilio` (indPres 4): aí as duas regras acima se
    invertem. A SEFAZ exige o grupo `dest` completo (rejeição 787) COM
    endereço (rejeição 788), porque a mercadoria vai circular até a casa do
    comprador. Nesse caso reusamos o destinatário da NF-e, que já monta nome
    e endereço.
    """
    if entrega_domicilio:
        if cliente is None:
            raise ValueError(
                "Entrega a domicílio exige um cliente identificado na venda: a "
                "NFC-e com indPres 4 é recusada sem os dados do destinatário "
                "(rejeição 787)."
            )
        destinatario = _montar_destinatario(cliente)
        if not destinatario.get("endereco"):
            raise ValueError(
                "Entrega a domicílio exige o endereço do cliente: a NFC-e com "
                "indPres 4 é recusada sem ele (rejeição 788)."
            )
        return destinatario

    if cliente is not None:
        if isinstance(cliente, ClientePJ) and cliente.cnpj:
            return {"cnpj": cliente.cnpj, "indicador_ie": "1" if cliente.ie else "9"}
        if isinstance(cliente, ClientePF) and cliente.cpf:
            return {"cpf": cliente.cpf, "indicador_ie": "9"}

    documento = re.sub(r"\D", "", documento_consumidor or "")
    if len(documento) == 11:
        return {"cpf": documento, "indicador_ie": "9"}
    if len(documento) == 14:
        return {"cnpj": documento, "indicador_ie": "9"}

    # Consumidor não identificado: a venda de balcão sem CPF é o caso normal.
    return None


# Campos sem os quais o grupo enderDest não é aceito pela SEFAZ.
_CAMPOS_ENDERECO_OBRIGATORIOS = ("logradouro", "numero", "bairro", "cidade", "cep")


def _montar_endereco_destinatario(end: Endereco) -> Optional[dict]:
    """Monta o endereço do destinatário, ou None se estiver incompleto."""
    if any(not getattr(end, campo, None) for campo in _CAMPOS_ENDERECO_OBRIGATORIOS):
        return None

    uf = end.estado.value if hasattr(end.estado, "value") else str(end.estado or "")
    if not uf:
        return None

    return {
        "logradouro": end.logradouro,
        "numero": end.numero,
        "complemento": end.complemento or "",
        "bairro": end.bairro,
        "cidade": end.cidade,
        "uf": uf,
        "cep": _so_digitos(end.cep),
    }


# idDest da NF-e
LOCAL_DESTINO_INTERNA = 1


LOCAL_DESTINO_INTERESTADUAL = 2


def _local_destino(resultado_calculo: Optional[ResultadoCalculo]) -> int:
    """
    idDest a partir do 1º dígito dos CFOPs que o motor decidiu.

    É a MESMA decisão que gerou o CFOP (tax_engine/resolver), então os dois
    nunca divergem — idDest 1 com CFOP 6.102 é Rejeição 523. Itens em grupos
    diferentes na mesma nota não existem: é erro de montagem, antes de
    reservar número.
    """
    if not resultado_calculo:
        return LOCAL_DESTINO_INTERNA
    grupos = {imp.cfop[0] for imp in resultado_calculo.itens if imp.cfop}
    if len(grupos) > 1:
        raise ValueError(
            f"Itens com CFOP de grupos diferentes na mesma nota ({', '.join(sorted(grupos))}): "
            f"a operação é interna OU interestadual."
        )
    return LOCAL_DESTINO_INTERESTADUAL if grupos == {"6"} else LOCAL_DESTINO_INTERNA


def _montar_destinatario_avulso(dados) -> dict:
    """Destinatário informado na hora, para nota de origem sem comprador identificado."""
    dest: dict = {
        "nome": _sanitizar_texto_sefaz(dados.nome_razao_social),
        "indicador_ie": str(dados.indicador_inscricao_estadual),
        "endereco": {
            "logradouro": _sanitizar_texto_sefaz(dados.logradouro),
            "numero": dados.numero,
            "complemento": _sanitizar_texto_sefaz(dados.complemento or ""),
            "bairro": _sanitizar_texto_sefaz(dados.bairro),
            "cidade": _sanitizar_texto_sefaz(dados.municipio),
            "uf": dados.uf,
            "cep": dados.cep,
        },
        # A Focus aceita o código IBGE no nível do destinatário; vai também no
        # endereço para a intermediária normalizar como preferir.
        "codigo_municipio": dados.codigo_municipio,
    }
    dest["endereco"]["codigo_municipio"] = dados.codigo_municipio
    if len(dados.cpf_ou_cnpj) == 14:
        dest["cnpj"] = dados.cpf_ou_cnpj
        dest["razao_social"] = dest["nome"]
        if dados.inscricao_estadual:
            dest["inscricao_estadual"] = dados.inscricao_estadual
    else:
        dest["cpf"] = dados.cpf_ou_cnpj
    return dest
