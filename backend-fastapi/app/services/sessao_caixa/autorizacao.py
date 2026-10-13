# ---------------------------------------------------------------------------
# ARQUIVO: services/sessao_caixa/autorizacao.py
# DESCRICAO: Caixa - quem autoriza a abertura e a sangria.
# ---------------------------------------------------------------------------

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.security import verify_password
from app.helpers.exceptions import BadRequestException
from app.db.crud.configuracao import seguranca as config_seg_crud
from app.db.crud.configuracao import vendas as config_vendas_crud


def _validar_autorizacao_sangria(
    db: Session,
    empresa_id: int,
    usuario_token: Dict[str, Any],
    codigo_gerente: Optional[str],
) -> None:
    """Sangria travada: ou quem opera é gerente, ou um supervisor libera na hora.

    Suprimento NÃO passa por aqui de propósito. Pôr dinheiro na gaveta não cria
    risco de desvio; tirar, sim. Travar os dois faria o operador chamar o gerente
    para colocar troco — o atrito que faz loja desligar o controle e voltar para
    o caderno.
    """
    config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
    if not (config_seg and config_seg.requer_pin_sangria):
        return
    # A partir daqui a loja EXIGE autorização para sangrar.

    # Master e quem tem permissão ampla não precisam pedir licença a ninguém.
    if usuario_token.get("is_master") is True:
        return
    permissoes = usuario_token.get("permissoes") or {}
    if permissoes.get("all") or permissoes.get("manage_sales"):
        return

    pin = getattr(config_seg, "pin_gerente", None)
    if not pin:
        # Exigir autorização sem PIN configurado travaria a sangria para sempre.
        # A loja que ligou a trava e não cadastrou o PIN precisa saber disso.
        raise BadRequestException(
            detail="A sangria exige autorização, mas nenhum PIN de gerente está "
                   "configurado em Configurações > Segurança"
        )
    # Sentinelas, e não frases: é o contrato que o frontend já usa para abrir o
    # modal de PIN em cancelamento, reabertura e desconto
    # (shared/composables/useGerenteAprovacao). Inventar mensagem nova aqui
    # deixaria a sangria de fora do fluxo que já existe.
    if not codigo_gerente:
        raise BadRequestException(detail="REQUER_APROVACAO_GERENTE")
    if not verify_password(codigo_gerente, pin):
        raise BadRequestException(detail="PIN_GERENTE_INVALIDO")


def _validar_autorizacao_abertura(
    db: Session,
    empresa_id: int,
    usuario_token: Dict[str, Any],
    codigo_gerente: Optional[str],
) -> None:
    """Abrir o caixa travado: ou quem opera é gerente, ou um supervisor libera.

    Abrir o turno é declarar o troco inicial — e o troco inicial é a base contra
    a qual o fechamento vai acusar falta ou sobra. Quem declara a base sozinho
    escolhe, na prática, o resultado da conferência do próprio turno.

    A CHAVE MORA EM `configuracoes_vendas`, ao lado das outras regras do caixa,
    e não em `configuracoes_seguranca` junto das irmãs de PIN. Foi decisão do
    dono, e está registrada no modelo e na migration `a5b6c7d8e9f0`. Mas o
    SEGREDO continua sendo um só: o `pin_gerente` lido logo abaixo é o mesmo que
    protege sangria, cancelamento, reabertura e desconto.

    Fechar o caixa NÃO passa por aqui: quem abriu precisa conseguir fechar, e
    exigir um gerente no fim do expediente deixaria a gaveta aberta até o dia
    seguinte — pior para a conferência do que o problema que resolveria.
    """
    config = config_vendas_crud.get_configuracao_vendas(db, empresa_id=empresa_id)
    if not (config and config.requer_pin_abrir_caixa):
        return
    # A partir daqui a loja EXIGE autorização para abrir o caixa.

    # SÓ O MASTER DISPENSA — e aqui a regra DIVERGE da sangria de propósito.
    #
    # `_validar_autorizacao_sangria` também libera quem tem `manage_sales` ou
    # `all`. Copiar aquela lista para cá tornava esta chave decoração: o cargo
    # que opera o PDV PRECISA de `manage_sales` para vender, então o balconista
    # — exatamente quem a trava existe para pegar — passava direto. Foi o que
    # aconteceu no primeiro teste na loja, com um cargo chamado "Caixa".
    #
    # `all` também fica de fora: é um bypass amplo de permissão, e uma trava de
    # supervisão que qualquer permissão ampla desliga não trava nada.
    if usuario_token.get("is_master") is True:
        return

    config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
    pin = getattr(config_seg, "pin_gerente", None) if config_seg else None
    if not pin:
        # Exigir autorização sem PIN configurado travaria a abertura para
        # sempre — e sem caixa aberto a loja não vende. A mensagem precisa dizer
        # exatamente onde resolver.
        raise BadRequestException(
            detail="A abertura de caixa exige autorização, mas nenhum PIN de "
                   "gerente está configurado em Configurações > Segurança"
        )
    # Sentinelas, e não frases: é o contrato que o frontend já usa para abrir o
    # modal de PIN em sangria, cancelamento, reabertura e desconto
    # (shared/composables/useGerenteAprovacao).
    if not codigo_gerente:
        raise BadRequestException(detail="REQUER_APROVACAO_GERENTE")
    if not verify_password(codigo_gerente, pin):
        raise BadRequestException(detail="PIN_GERENTE_INVALIDO")
